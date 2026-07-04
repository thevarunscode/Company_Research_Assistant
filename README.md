# Research AI — Company Research Assistant

An AI-powered company research assistant. Enter a **company name** (Stripe, Tesla) or a **website URL** (https://stripe.com) and get:

- Company information (website, phone, address)
- Products & services
- AI-generated pain points
- Competitor analysis (names + websites)
- A professional, downloadable **PDF report**

All behind a modern, responsive, ChatGPT-style chat interface with live research progress.

![Stack](https://img.shields.io/badge/FastAPI-Python-green) ![Stack](https://img.shields.io/badge/React-Vite%20%2B%20Tailwind-blue) ![AI](https://img.shields.io/badge/AI-OpenRouter-orange) ![Search](https://img.shields.io/badge/Search-Serper.dev-yellow)

## How it works

```
name/URL → Serper.dev (find official site) → async crawler (important pages)
        → Serper.dev (contact + competitor enrichment) → OpenRouter (AI analysis)
        → live report in chat → ReportLab PDF download
```

1. **Resolve** — if you give a name, Serper.dev finds the official website (aggregator domains like Wikipedia/LinkedIn are skipped, Google Knowledge Graph data is captured).
2. **Crawl** — an async crawler (httpx + BeautifulSoup) fetches the homepage, discovers same-domain links, dedupes them, skips junk (login/signup/privacy/blog/assets), prioritizes About / Products / Services / Solutions / Pricing / Contact pages, and extracts clean text from up to 8 pages concurrently.
3. **Enrich** — extra Serper.dev queries collect public contact details and competitor signals.
4. **Analyze** — everything is sent to the OpenRouter model you pick (any OpenRouter model is supported); it returns a structured report: summary, products/services, pain points, competitors.
5. **Report** — results render in the chat with live progress (SSE), and one click downloads a styled PDF (ReportLab).

## Project structure

```
├── backend/               # FastAPI app
│   ├── main.py            # API routes, SSE orchestrator, serves frontend build
│   ├── models.py          # Pydantic schemas
│   └── services/
│       ├── serper.py      # Serper.dev search / site resolution / enrichment
│       ├── crawler.py     # async website crawler
│       ├── ai.py          # OpenRouter client + analysis prompt
│       └── pdf.py         # ReportLab PDF report builder
├── frontend/              # React + Vite + TypeScript + Tailwind v4
├── api/index.py           # Vercel serverless entry point
├── vercel.json            # Vercel config (build, rewrites, function limits)
└── PLAN.md                # architecture & build plan
```

## Setup

### Prerequisites
- Python 3.12+ · Node.js 20.19+/22.12+ (22.11 works with the pinned Vite 6)
- A [Serper.dev](https://serper.dev) API key (free tier available)
- An [OpenRouter](https://openrouter.ai) API key

### 1. Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then paste your keys (optional — see below)
.venv/bin/uvicorn main:app --port 8000
```

### 2. Frontend (dev)

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173, proxies /api → :8000
```

### 3. Unified production mode (single process)

```bash
cd frontend && npm run build  # FastAPI now serves the SPA itself
# open http://localhost:8000
```

## Environment variables

| Variable | Where | Required | Purpose |
|---|---|---|---|
| `SERPER_API_KEY` | `backend/.env` (or Vercel env) | optional* | Default Serper.dev key |
| `OPENROUTER_API_KEY` | `backend/.env` (or Vercel env) | optional* | Default OpenRouter key |

\* Keys can also be entered in the app sidebar (stored in your browser's localStorage and sent per request). A key entered in the sidebar **overrides** the server default. At least one of the two sources must provide each key.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/research` | POST | Runs the research pipeline; streams SSE progress events, ends with the report JSON |
| `/api/pdf` | POST | Takes a report JSON, returns the styled PDF |
| `/api/models` | GET | Full OpenRouter model list (cached 1 h) for the model picker |
| `/api/health` | GET | Health check |

## Deployment (Vercel)

The repo is Vercel-ready:

```bash
npm i -g vercel
vercel            # from the repo root
```

- `vercel.json` builds the frontend to static files and runs the FastAPI app as a single Python serverless function (`api/index.py`) with `maxDuration: 60`.
- Set `SERPER_API_KEY` and `OPENROUTER_API_KEY` in the Vercel project settings (or let users paste keys in the sidebar).

Also deployable anywhere a single process can run (Render, Railway, Fly.io):
`uvicorn main:app --host 0.0.0.0 --port $PORT` after `npm run build`.

## Tech choices

| Concern | Choice | Notes |
|---|---|---|
| Search | Serper.dev | official-site resolution, knowledge graph, enrichment |
| AI | OpenRouter | any model, user-selectable in the sidebar |
| Crawling | httpx + BeautifulSoup | async, concurrent, dedup + junk filtering |
| PDF | ReportLab | professional server-side reports |
| UI | React + Tailwind v4 | ChatGPT-style, responsive, live SSE progress |
