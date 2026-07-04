"""OpenRouter client: turns crawled + searched context into a structured report."""

import asyncio
import json
import re

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are a senior business research analyst. You produce accurate, \
specific company intelligence based ONLY on the provided research material and \
well-established public knowledge. Never invent phone numbers, addresses, or URLs. \
If a detail is not in the material and not certain public knowledge, use "Not publicly listed"."""

ANALYSIS_PROMPT = """Analyze the following research material about a company and return \
a single JSON object with EXACTLY these fields:

{{
  "company_name": "Official company name",
  "website": "https://... official website",
  "phone": "Phone number, or 'Not publicly listed'",
  "address": "Headquarters address/city/country, or 'Not publicly listed'",
  "summary": "3-5 sentence professional summary: what the company does, its market, scale and positioning",
  "products_services": ["4-8 concrete named products or services"],
  "pain_points": ["4-6 specific, insightful business pain points or challenges this company likely faces right now — grounded in its industry, competition, business model and anything evident in the material. Each one full sentence."],
  "pricing": [{{"item": "Plan or product name", "price": "$12 per user/month"}}],
  "competitors": [{{"name": "Competitor", "website": "https://competitor.com"}}]
}}

Pricing rules: include ONLY prices explicitly stated in the research material (pricing \
pages, plan tables, product prices). Use the exact amounts and billing units shown. If \
the material contains no explicit prices, return an empty list [] — NEVER estimate or \
invent prices.

Competitor rules: 4-6 direct competitors that operate in the same industry with similar \
products/services (prefer same-country/market where relevant). Only real companies with \
their real primary website domains.

Return ONLY the JSON object — no markdown fences, no commentary.

=== RESEARCH MATERIAL ===
{context}
=== END MATERIAL ==="""


def build_context(
    query: str,
    website: str | None,
    kg_info: dict,
    pages: list[dict],
    enrichment: dict,
) -> str:
    parts = [f"User query: {query}", f"Official website: {website or 'unknown'}"]

    if any(kg_info.values()):
        parts.append("--- Google Knowledge Graph ---")
        for key, value in kg_info.items():
            if value:
                parts.append(f"{key}: {value}")

    if pages:
        parts.append("--- Crawled website pages ---")
        for page in pages:
            parts.append(f"[{page['title']}] ({page['url']})\n{page['text']}")

    if enrichment.get("contact"):
        parts.append("--- Public contact information (search results) ---")
        parts.extend(enrichment["contact"])

    if enrichment.get("competitors"):
        parts.append("--- Competitor research (search results) ---")
        parts.extend(enrichment["competitors"])

    if enrichment.get("pricing"):
        parts.append("--- Pricing research (search results) ---")
        parts.extend(enrichment["pricing"])

    return "\n\n".join(parts)


def _extract_json(raw: str) -> dict:
    """Parse model output defensively: strip fences, locate outermost object."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


async def analyze(context: str, model: str, api_key: str) -> dict:
    """Run the analysis, retrying briefly when the model is rate-limited (429)
    or the provider hiccups (5xx) — common on OpenRouter's free-tier models."""
    last_exc: Exception = RuntimeError("analysis failed")
    for attempt in range(3):
        try:
            return await _analyze_once(context, model, api_key)
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if exc.response.status_code in (429, 502, 503) and attempt < 2:
                await asyncio.sleep(6 * (attempt + 1))
                continue
            raise
    raise last_exc


async def _analyze_once(context: str, model: str, api_key: str) -> dict:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://company-research-assistant.app",
                "X-Title": "Company Research Assistant",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": ANALYSIS_PROMPT.format(context=context)},
                ],
                "temperature": 0.4,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise RuntimeError(data["error"].get("message", "OpenRouter error"))
    content = data["choices"][0]["message"]["content"]
    return _extract_json(content)
