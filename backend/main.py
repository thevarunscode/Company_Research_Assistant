"""Company Research Assistant — FastAPI backend.

Serves the research API (SSE), PDF generation, the OpenRouter model list,
and the built React frontend as static files (single unified deployment).
"""

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from models import Report, ResearchRequest
from services import ai, crawler, serper
from services.pdf import build_pdf

load_dotenv()

app = FastAPI(title="Company Research Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

URL_PATTERN = re.compile(
    r"^(https?://)?([a-z0-9-]+\.)+[a-z]{2,}(/\S*)?$", re.IGNORECASE
)

_models_cache: dict = {"data": None, "at": 0.0}


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _looks_like_url(query: str) -> bool:
    q = query.strip()
    return " " not in q and bool(URL_PATTERN.match(q))


async def _research_events(req: ResearchRequest):
    serper_key = req.serper_key or os.getenv("SERPER_API_KEY", "")
    openrouter_key = req.openrouter_key or os.getenv("OPENROUTER_API_KEY", "")

    if not serper_key or not openrouter_key:
        missing = [
            name for name, key in
            [("Serper.dev", serper_key), ("OpenRouter", openrouter_key)] if not key
        ]
        yield _sse({
            "type": "error",
            "message": f"Missing API key(s): {', '.join(missing)}. "
                       "Add them in the sidebar or the server .env file.",
        })
        return

    query = req.query.strip()
    website: str | None = None
    kg_info: dict = {}
    company_hint = query

    try:
        # 1. Resolve the official website.
        if _looks_like_url(query):
            website = query if query.startswith(("http://", "https://")) else f"https://{query}"
            parsed = urlparse(website)
            website = f"{parsed.scheme}://{parsed.netloc}"
            company_hint = parsed.netloc.removeprefix("www.").split(".")[0].capitalize()
            yield _sse({"type": "status", "step": "resolve",
                        "detail": f"Using provided website: {website}"})
        else:
            yield _sse({"type": "status", "step": "resolve",
                        "detail": f'Searching for the official website of "{query}"…'})
            try:
                website, kg_info = await serper.resolve_website(query, serper_key)
            except httpx.HTTPStatusError as exc:
                yield _sse({"type": "error",
                            "message": f"Serper.dev search failed ({exc.response.status_code}). "
                                       "Check your Serper API key."})
                return
            if website:
                yield _sse({"type": "status", "step": "resolve",
                            "detail": f"Official website found: {website}"})
            else:
                yield _sse({"type": "status", "step": "resolve",
                            "detail": "No official website found — continuing with search data only."})

        # 2. Crawl the website.
        pages: list[dict] = []
        if website:
            yield _sse({"type": "status", "step": "crawl",
                        "detail": f"Crawling {urlparse(website).netloc}…"})
            crawl_result = await crawler.crawl_site(website, max_pages=8)
            pages = crawl_result["pages"]
            if pages:
                yield _sse({"type": "status", "step": "crawl",
                            "detail": f"Analyzed {len(pages)} pages "
                                      f"({crawl_result['discovered']} discovered)."})
            else:
                yield _sse({"type": "status", "step": "crawl",
                            "detail": "Site blocked crawling — falling back to public search data."})

        # 3. Enrich from public sources.
        yield _sse({"type": "status", "step": "enrich",
                    "detail": "Collecting contact details and competitor signals…"})
        domain = urlparse(website).netloc if website else ""
        enrichment = await serper.enrich(company_hint, domain, serper_key)

        # 4. AI analysis via OpenRouter.
        yield _sse({"type": "status", "step": "analyze",
                    "detail": f"Generating insights with {req.model}…"})
        context = ai.build_context(query, website, kg_info, pages, enrichment)
        try:
            raw = await ai.analyze(context, req.model, openrouter_key)
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 401:
                detail = "Check your OpenRouter API key."
            elif code == 402:
                detail = ("Your OpenRouter account has no credits — switch to a free model "
                          "(marked 'Free' in the sidebar) or add credits at openrouter.ai.")
            elif code == 429:
                detail = ("This free model is rate-limited right now. Try again in a minute "
                          "or pick a different free model in the sidebar.")
            else:
                detail = "The selected model may be unavailable — try another."
            yield _sse({"type": "error",
                        "message": f"OpenRouter request failed ({code}). {detail}"})
            return

        report = Report(
            company_name=raw.get("company_name") or company_hint,
            website=raw.get("website") or website or "",
            phone=raw.get("phone") or "Not publicly listed",
            address=raw.get("address") or "Not publicly listed",
            summary=raw.get("summary") or "",
            products_services=raw.get("products_services") or [],
            pain_points=raw.get("pain_points") or [],
            pricing=[
                p for p in (raw.get("pricing") or [])
                if isinstance(p, dict) and p.get("item") and p.get("price")
            ],
            competitors=[
                c for c in (raw.get("competitors") or [])
                if isinstance(c, dict) and c.get("name")
            ],
            sources=[p["url"] for p in pages],
        )
        yield _sse({"type": "result", "report": report.model_dump()})

    except Exception as exc:  # last-resort guard so the stream always terminates cleanly
        yield _sse({"type": "error", "message": f"Research failed: {exc}"})


@app.post("/api/research")
async def research(req: ResearchRequest):
    return StreamingResponse(
        _research_events(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/pdf")
async def generate_pdf(report: Report):
    pdf_bytes = build_pdf(report)
    filename = re.sub(r"[^a-z0-9]+", "-", report.company_name.lower()).strip("-") or "company"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}-research-report.pdf"'},
    )


@app.get("/api/models")
async def list_models():
    if _models_cache["data"] and time.time() - _models_cache["at"] < 3600:
        return _models_cache["data"]
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            resp.raise_for_status()
            raw = resp.json().get("data", [])
    except Exception:
        raw = []
    models = sorted(
        ({"id": m["id"], "name": m.get("name", m["id"])} for m in raw),
        key=lambda m: m["name"].lower(),
    )
    payload = {"models": models}
    if models:
        _models_cache.update(data=payload, at=time.time())
    return payload


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve the built frontend (single unified deployment).
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
