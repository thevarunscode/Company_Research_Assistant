# 🚀 Deployment Guide — Vercel & Netlify (in depth)

This app is a **FastAPI (Python) backend + React (Vite) frontend**. That shape matters for platform choice:

| Platform | Can it run the whole app? | How |
|---|---|---|
| **Vercel** | ✅ Yes, fully unified | Static frontend + FastAPI as a Python serverless function |
| **Netlify** | ⚠️ Frontend only | Netlify has **no Python runtime** for functions — pair it with a free Python host (Render) for the backend |
| Render (bonus) | ✅ Yes, fully unified | One long-running process; `render.yaml` included |

**Recommendation: Vercel** — one repo, one deploy, one URL, zero backend babysitting. Use the Netlify path only if you specifically want Netlify.

All the config files referenced below (`vercel.json`, `api/index.py`, `netlify.toml`, `render.yaml`) already exist in this repo — you don't need to write anything.

---

# Part 1 — Vercel (recommended, ~10 minutes)

## 1.0 How it works

```
your-app.vercel.app
├── /            → frontend/dist  (static files, served from Vercel CDN)
└── /api/*       → api/index.py   (ONE Python serverless function running FastAPI)
```

Three repo files make this happen:

- **`api/index.py`** — Vercel's entry point. It adds `backend/` to `sys.path` and re-exports the FastAPI `app`. Vercel auto-detects an ASGI app and hosts it.
- **`vercel.json`** — tells Vercel to build the frontend (`cd frontend && npm install && npm run build`), publish `frontend/dist`, route `/api/*` to the function, and fall back everything else to `index.html` (SPA routing). Also sets `maxDuration: 60` and 1 GB memory for the function.
- **`requirements.txt`** (repo root) — Python deps Vercel installs for the function. (Note: `uvicorn` is intentionally absent — Vercel hosts the ASGI app itself.)

## 1.1 Prerequisite: push the repo to GitHub

```bash
cd "/Users/sanatankhemariya/Desktop/AI enginner test"
git add -A && git commit -m "Company Research Assistant"
# create an empty repo on github.com, then:
git remote add origin https://github.com/<you>/company-research-assistant.git
git push -u origin main
```

(`.gitignore` already excludes `backend/.env`, `node_modules`, `dist`, `.venv` — your keys will NOT be pushed.)

## 1.2 Deploy — Option A: Dashboard (easiest)

1. Go to **https://vercel.com** → sign up / log in **with GitHub**.
2. Click **"Add New… → Project"**.
3. **Import** your `company-research-assistant` repo.
4. Vercel reads `vercel.json` automatically — do **not** override Framework/Build settings; leave "Framework Preset" as **Other**.
5. Expand **Environment Variables** and add both (for all environments):
   | Name | Value |
   |---|---|
   | `SERPER_API_KEY` | your Serper key |
   | `OPENROUTER_API_KEY` | your OpenRouter key |
6. Click **Deploy**. First build takes 1–2 min.
7. You get `https://<project>.vercel.app` — that's your public submission URL.

Every subsequent `git push` to `main` auto-redeploys.

## 1.3 Deploy — Option B: CLI

```bash
npm i -g vercel
cd "/Users/sanatankhemariya/Desktop/AI enginner test"
vercel login                      # opens browser
vercel                            # first deploy (answers: link to new project, defaults)
vercel env add SERPER_API_KEY     # paste key, select all environments
vercel env add OPENROUTER_API_KEY
vercel --prod                     # production deploy
```

## 1.4 Vercel limits vs. this app (why it fits)

| Limit | Vercel allows | This app uses |
|---|---|---|
| Function bundle (uncompressed) | 250 MB | ~45 MB (ReportLab+Pillow are the heaviest) |
| Request/response payload | 4.5 MB | ~1 KB requests, 3–50 KB PDFs |
| Streaming | Supported (SSE works on the Python runtime) | progress events, a few KB |
| Function duration (Hobby) | 60 s default; up to **300 s with Fluid Compute** | typical research run 20–60 s |
| Memory | 1024 MB (set in `vercel.json`) | well under |

**Enable Fluid Compute** (recommended): Project → Settings → Functions → enable **Fluid Compute**, then you may raise `maxDuration` in `vercel.json` up to 300. This removes any risk of a slow site + slow free model exceeding 60 s.

## 1.5 Verify the deployment

```bash
curl https://<project>.vercel.app/api/health          # → {"status":"ok"}
curl https://<project>.vercel.app/api/models | head -c 200
```

Then open the URL, research "Stripe", download the PDF.

## 1.6 Vercel troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Build fails at `npm run build` | Node version | Project → Settings → General → Node.js Version → 20.x or 22.x |
| `/api/*` returns 404 | `vercel.json` not picked up | Ensure it's at the **repo root** and the project's Root Directory setting is the repo root (not `frontend/`) |
| `/api/*` returns 500 immediately | Python import error | Check Deployments → your deploy → Functions → logs; usually a missing dep in root `requirements.txt` |
| Research dies at ~60 s | duration limit | Enable Fluid Compute + raise `maxDuration` (see 1.4) |
| 402/429 errors in the app | OpenRouter credits / free-model rate limits | Not a deployment issue — pick a free model or add credits |
| Progress steps all appear at once at the end | very rare SSE buffering | Refresh once; if persistent, check the function logs — the app still completes correctly |

---

# Part 2 — Netlify (frontend) + Render (backend), ~20 minutes

## 2.0 Why the split

Netlify Functions run **JavaScript/TypeScript/Go only** — there is no Python runtime, so FastAPI cannot execute on Netlify. The standard architecture is:

```
your-app.netlify.app          (React frontend, Netlify CDN)
        │  fetch(VITE_API_BASE + '/api/…')
        ▼
your-api.onrender.com         (FastAPI on Render, free tier)
```

The frontend already supports this: every API call is prefixed with the **`VITE_API_BASE`** environment variable (empty = same origin, which is why Vercel/local need nothing).

## 2.1 Step 1 — deploy the backend on Render

1. Go to **https://render.com** → sign up with GitHub.
2. Click **"New → Web Service"** → connect your repo.
3. Settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Under **Environment Variables** add `SERPER_API_KEY` and `OPENROUTER_API_KEY`.
5. Click **Create Web Service** → after the build you get `https://<service>.onrender.com`.
6. Verify: `curl https://<service>.onrender.com/api/health` → `{"status":"ok"}`.

(Alternatively click "New → Blueprint" and Render reads the included `render.yaml` — that variant also builds the frontend, making Render alone a full single-URL deployment. For the Netlify pairing, the simpler backend-only settings above are enough.)

**Free-tier caveat:** Render free services **sleep after 15 min idle**; the first request after sleep takes ~50 s to cold-start. For a hiring demo, open the app once before your evaluator does, or pay $7/mo for always-on.

## 2.2 Step 2 — deploy the frontend on Netlify

1. Go to **https://netlify.com** → sign up with GitHub.
2. **"Add new site → Import an existing project"** → pick your repo.
3. Netlify reads the included **`netlify.toml`** (base `frontend/`, build `npm install && npm run build`, publish `dist/`, SPA fallback redirect). Don't override.
4. Before deploying, add the env var that points the frontend at Render:
   - **Site configuration → Environment variables → Add:**
     `VITE_API_BASE` = `https://<your-service>.onrender.com` *(no trailing slash)*
   - ⚠️ This is a **build-time** variable (Vite inlines it) — if you add or change it later you must trigger **"Clear cache and deploy site"**.
5. Deploy → you get `https://<site>.netlify.app`.

CLI variant:

```bash
npm i -g netlify-cli
netlify login
netlify init                        # link repo, accepts netlify.toml settings
netlify env:set VITE_API_BASE https://<service>.onrender.com
netlify deploy --build --prod
```

## 2.3 CORS — already handled

Cross-origin calls (netlify.app → onrender.com) work because the backend ships with permissive CORS (`allow_origins=["*"]` in `backend/main.py`). To lock it down post-submission, replace `"*"` with your Netlify URL.

## 2.4 Why not Netlify's `/api/*` proxy?

`netlify.toml` contains a commented-out proxy redirect (`/api/* → onrender.com/api/:splat`) that would keep calls same-origin. It works for quick requests, but Netlify's proxy **buffers responses and times out around ~30 s**, which can kill the long-running SSE research stream mid-flight. The `VITE_API_BASE` direct-call approach streams straight from Render with no middleman — use it. (The proxy stays in the file as an option for `/api/pdf`-style short calls if you ever want it.)

## 2.5 Netlify + Render troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| UI loads, every research fails instantly | `VITE_API_BASE` missing/wrong at build time | Set the env var, then **Clear cache and deploy** |
| First research takes ~1 min then works | Render free-tier cold start | Warm it up first, or paid instance |
| Browser console shows CORS errors | backend CORS narrowed incorrectly | Keep `allow_origins=["*"]` or include your exact Netlify origin |
| Research dies ~30 s in (only if using the proxy) | Netlify proxy timeout | Switch to `VITE_API_BASE` direct calls (2.2 step 4) |
| `npm run build` fails on Netlify | Node version | `netlify.toml` → add `[build.environment] NODE_VERSION = "22"` or set it in the UI |
| PDF downloads an empty/failed file | backend URL unreachable from browser | Verify `https://<service>.onrender.com/api/health` in a browser tab |

---

# Part 3 — Which one for the submission?

| | Vercel | Netlify + Render |
|---|---|---|
| URLs to manage | **1** | 2 (users only see 1) |
| Matches "single unified project" | ✅ perfectly | acceptable (one repo, one visible URL) |
| Cold starts | minimal | ~50 s on Render free after idle |
| Long research runs | needs Fluid Compute for >60 s | unlimited duration on Render |
| Setup effort | ~10 min | ~20 min |

**Ship Vercel as the submission URL.** Keep the Netlify/Render path as proof you understand multi-platform deployment — the configs are in the repo either way.

# Post-deploy checklist (either platform)

- [ ] `/api/health` returns `{"status":"ok"}` on the public URL
- [ ] Research by **name** ("Stripe") completes with live progress
- [ ] Research by **URL** ("https://tesla.com") completes
- [ ] Free model selected by default (works with $0 OpenRouter credits)
- [ ] PDF downloads and opens
- [ ] Test on a phone (or DevTools mobile view) — sidebar collapses to drawer
- [ ] Add the public URL to `README.md` before submitting
