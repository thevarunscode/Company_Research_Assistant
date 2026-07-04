# Company Research Assistant — Build Plan & Architecture

An AI-powered assistant that researches any company from a **name** or **website URL**: it finds the official site (Serper.dev), crawls it, enriches with public search data, analyzes everything with an OpenRouter model of the user's choice, identifies competitors, and produces a downloadable PDF report — all behind a ChatGPT-style chat interface.

## 1. Goals & scope

### Core MVP (this build)
- [x] Accept **company name** or **website URL** as input
- [x] Resolve official website via Serper.dev when given a name
- [x] Crawl important pages (home, about, products, services, solutions, contact, pricing) with dedup + junk-page filtering
- [x] Enrich research with extra Serper queries (contact info, competitors)
- [x] AI analysis via OpenRouter (user-selectable model): summary, products/services, pain points, competitors
- [x] Competitor list with name + website
- [x] ChatGPT-style responsive UI with live progress steps
- [x] One-click professional PDF report download
- [x] README with setup + env var documentation

### Phase 2 (after MVP)
- [ ] Discord integration (bot token + channel ID settings, auto-send PDF after research)
- [ ] Public deployment (Render / Railway / Fly.io) with URL
- [ ] Extra polish: animations, source references, caching

## 2. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3 + FastAPI | Async-first (concurrent crawling), SSE streaming, Pydantic validation |
| HTTP client | httpx (async) | Concurrent page fetches + API calls |
| HTML parsing | BeautifulSoup4 | Robust content extraction |
| Search | Serper.dev REST API | Required by assignment |
| AI | OpenRouter chat completions | Required by assignment; OpenAI-compatible, any model |
| PDF | ReportLab | Server-side, professional layout, reusable later for Discord upload |
| Frontend | React 18 + Vite + TypeScript | Fast dev, typed API contracts |
| Styling | Tailwind CSS v4 | Rapid polished dark UI, responsive |
| Deployment | Single FastAPI process serving the built frontend | "Single unified project" requirement |

## 3. Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                           Browser (React SPA)                      │
│  ┌──────────┐  ┌───────────────────────────┐  ┌─────────────────┐  │
│  │ Sidebar  │  │  Chat area                │  │ localStorage    │  │
│  │ API keys │  │  hero → progress → report │  │ keys + model    │  │
│  │ model ▼  │  │  [Download PDF]           │  └─────────────────┘  │
│  └──────────┘  └───────────────────────────┘                       │
└───────┬──────────────────┬─────────────────────────┬───────────────┘
        │ GET /api/models  │ POST /api/research (SSE)│ POST /api/pdf
┌───────▼──────────────────▼─────────────────────────▼───────────────┐
│                        FastAPI (main.py)                           │
│                                                                    │
│   /api/research orchestrator (async generator → SSE events)        │
│   1. resolve   2. crawl      3. enrich     4. analyze    5. emit   │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐            │
│  │serper.py │ │crawler.py │ │serper.py  │ │  ai.py    │            │
│  └────┬─────┘ └────┬──────┘ └────┬──────┘ └────┬──────┘            │
│       │            │             │             │        pdf.py     │
└───────┼────────────┼─────────────┼─────────────┼──────────┬────────┘
        ▼            ▼             ▼             ▼          ▼
   Serper.dev   Company site   Serper.dev   OpenRouter   ReportLab
   (search)     (crawl pages)  (enrich)     (AI model)   (PDF bytes)
```

**Data flow for one research request:**

1. UI POSTs `{ query, model, serper_key?, openrouter_key? }` to `/api/research` and reads the SSE stream.
2. **Resolve** — if `query` parses as a URL, use it. Otherwise Serper-search `"<name> official website"`, skip aggregator domains (wikipedia, linkedin, crunchbase, …), take the first real domain. Knowledge-graph phone/address/description captured when present.
3. **Crawl** — fetch homepage → collect same-domain links → normalize + dedupe → score by path keywords (`about, product, service, solution, contact, pricing, …`) → drop junk (`login, signup, cart, privacy, terms, …`) → fetch top ~8 pages concurrently → extract visible text (~2.5k chars/page).
4. **Enrich** — two extra Serper queries: contact details and competitors/alternatives; snippets go into the AI context.
5. **Analyze** — one OpenRouter chat completion with all gathered context, prompted to return strict JSON (summary, products/services, pain points, competitors with websites, phone, address). Defensive JSON parsing (code-fence stripping, fallback repair).
6. **Emit** — `result` event with the full report; UI renders the ReportCard.
7. **PDF** — UI POSTs the report JSON to `/api/pdf`, receives a ReportLab PDF, triggers a blob download.

**Graceful degradation:** each stage is wrapped — if the crawl fails (blocked/bot-protected site), analysis proceeds on Serper data alone; if the knowledge graph is empty, the AI extracts contact info from crawled pages; any hard failure emits a friendly `error` event.

## 4. API contract

### `POST /api/research` → `text/event-stream`
```jsonc
// request
{ "query": "Stripe" | "https://stripe.com", "model": "anthropic/claude-sonnet-4.5",
  "serper_key": "…optional…", "openrouter_key": "…optional…" }

// events
{ "type": "status", "step": "resolve|crawl|enrich|analyze", "detail": "Crawling 8 pages…" }
{ "type": "result", "report": Report }
{ "type": "error", "message": "…" }
```

### `Report` schema (Pydantic)
```jsonc
{
  "company_name": "Figma",
  "website": "https://www.figma.com",
  "phone": "Not publicly listed",
  "address": "San Francisco, California, United States",
  "summary": "…",
  "products_services": ["Figma Design", "FigJam", "…"],
  "pain_points": ["…", "…"],
  "competitors": [ { "name": "Sketch", "website": "https://www.sketch.com" } ],
  "sources": ["https://www.figma.com/about", "…"]
}
```

### `POST /api/pdf` → `application/pdf`
Body: `Report` JSON. Returns the styled PDF (dark header band, Company Information, Products & Services, AI-Generated Pain Points, Competitors table).

### `GET /api/models` → curated + full OpenRouter model list (cached ~1h)

## 5. Project structure

```
AI enginner test/
├── PLAN.md                    # this file
├── README.md                  # setup, env vars, usage
├── backend/
│   ├── main.py                # FastAPI app, routes, SSE orchestrator, static mount
│   ├── models.py              # Pydantic schemas
│   ├── requirements.txt
│   ├── .env.example           # SERPER_API_KEY, OPENROUTER_API_KEY
│   └── services/
│       ├── serper.py          # search / resolve / enrich
│       ├── crawler.py         # async site crawler
│       ├── ai.py              # OpenRouter client + analysis prompt
│       └── pdf.py             # ReportLab report builder
└── frontend/
    ├── vite.config.ts         # dev proxy /api → :8000
    └── src/
        ├── App.tsx            # layout shell
        ├── lib/api.ts         # SSE client, pdf download, types
        └── components/
            ├── Sidebar.tsx    # keys, model select, how-it-works
            ├── Hero.tsx       # empty state + example chips
            ├── ChatInput.tsx  # bottom input bar
            ├── ProgressSteps.tsx
            └── ReportCard.tsx # rendered research result
```

## 6. Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `SERPER_API_KEY` | backend `.env` | Default Serper.dev key (sidebar value overrides per request) |
| `OPENROUTER_API_KEY` | backend `.env` | Default OpenRouter key (sidebar value overrides per request) |

No database, no auth, no persistent storage — reports live only in the browser session (per assignment).

## 7. Implementation order

1. Scaffold backend (FastAPI + static mount) and frontend (Vite + React + Tailwind) ✅
2. `serper.py` + `crawler.py`, verified standalone against a real site
3. `ai.py` + `/api/research` SSE orchestrator
4. Frontend: sidebar, chat flow, SSE progress, ReportCard
5. `pdf.py` + `/api/pdf` + download button
6. README + end-to-end verification

## 8. Verification checklist

- [ ] "Stripe" (name) → resolves stripe.com, crawls, full report with pain points + competitors
- [ ] "https://tesla.com" (URL) → skips resolution, works end-to-end
- [ ] PDF downloads and contains every report section
- [ ] Gibberish input → clean error message
- [ ] Bot-blocked site → degrades to Serper-only research
- [ ] `npm run build` → FastAPI serves the SPA on one port (unified deploy)
- [ ] Mobile viewport → sidebar collapses, layout stays usable
