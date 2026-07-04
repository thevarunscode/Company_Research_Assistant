# 🔑 API Keys Setup Guide

This app needs exactly **two** API keys. Both have free options and take about 5 minutes total to get.

| Key | Service | What it's used for | Cost |
|---|---|---|---|
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) | Google search: finding official websites, contact info, competitor research | **Free** — 2,500 free queries on signup, no credit card |
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) | AI analysis: summary, pain points, competitor identification | Free models available; paid models need ~$5 credit |

---

## 1. Serper.dev API key (≈ 2 minutes)

Serper.dev gives programmatic access to Google search results.

### Steps

1. Go to **https://serper.dev**
2. Click **"Sign Up"** (top right).
3. Sign up with Google, or email + password. No credit card is asked.
4. After signing in you land on the **Dashboard**. You get **2,500 free search credits** automatically (each research run in our app uses ~3 credits).
5. In the left menu click **"API Key"** (or go to https://serper.dev/api-key).
6. Your key is shown as a long hex string, e.g.:
   ```
   a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4
   ```
7. Click the **copy** icon next to it.

### Verify the key works (optional but recommended)

Paste your key in place of `YOUR_KEY_HERE` and run in a terminal:

```bash
curl -s https://google.serper.dev/search \
  -H "X-API-KEY: YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"q": "Stripe official website"}' | head -c 400
```

✅ **Good:** you see JSON with `"organic": [...]` results.
❌ **Bad:** `{"message":"Unauthorized"}` → the key was copied wrong (check for spaces).

---

## 2. OpenRouter API key (≈ 3 minutes)

OpenRouter is a single API gateway to hundreds of AI models (Claude, GPT, Gemini, Llama, DeepSeek…). Our app lets you pick any of them from the sidebar.

### Steps

1. Go to **https://openrouter.ai**
2. Click **"Sign in"** (top right) → continue with Google, GitHub, or MetaMask/email.
3. Once signed in, click your **profile icon (top right) → "Keys"**
   (direct link: https://openrouter.ai/settings/keys).
4. Click **"Create Key"**.
   - **Name:** anything, e.g. `company-research-app`
   - **Credit limit:** leave blank (or set a cap like $5 for safety)
5. Click **Create** — the key is shown **once**. It looks like:
   ```
   <YOUR_OPENROUTER_API_KEY>
   ```
6. **Copy it immediately** and store it somewhere safe (you can't view it again — only delete and recreate).

### Do I need to pay?

Two options:

- **Free models (no payment at all):** OpenRouter hosts free models (their IDs end with `:free`, e.g. `deepseek/deepseek-chat-v3-0324:free`, `meta-llama/llama-3.3-70b-instruct:free`). Pick one from the sidebar's "All OpenRouter models" list. Rate limits are stricter and quality varies, but it costs $0.
- **Paid models (recommended for the demo):** click **profile → "Credits"** (https://openrouter.ai/settings/credits) → **"Add Credits"** → add **$5** (card/PayPal/crypto). That's enough for hundreds of research runs — one run with Claude Sonnet 4.5 costs roughly $0.01–0.03, with GPT-4o-mini or Gemini Flash well under $0.01.

### Verify the key works (optional)

```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer YOUR_OPENROUTER_API_KEY" | head -c 300
```

✅ **Good:** JSON with `"data": {...}` showing your key label and usage.
❌ **Bad:** `"error"` with `401` → wrong/expired key.

---

## 3. Put the keys in `.env`

From the project root:

```bash
cd backend
cp .env.example .env
```

Then open `backend/.env` in any editor and paste your real keys:

```env
SERPER_API_KEY=a1b2c3d4e5f67890a1b2c3d4e5f67890a1bXXXXX
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

**Rules:**
- No quotes, no spaces around `=`
- One key per line
- The file must be exactly `backend/.env` (not `.env.txt` — beware editors adding extensions)
- Never commit this file — it's already in `.gitignore` ✅

### Restart the backend so it picks up the keys

```bash
# stop the running server (Ctrl+C if in foreground), then:
cd backend
.venv/bin/uvicorn main:app --port 8000
```

`.env` is read once at startup — a restart is required after editing it.

---

## 4. Alternative: paste keys in the app sidebar instead

You can skip `.env` entirely: open the app → left sidebar → paste both keys into **"OpenRouter API Key"** and **"Serper.dev API Key"** → **Save Configuration**.

- Sidebar keys are stored only in your browser (localStorage) and sent with each request.
- A sidebar key **overrides** the `.env` key.
- This is also how someone else can use your deployed app with their own keys.

---

## 5. Final check — full end-to-end test

With the backend running and keys in place:

```bash
curl -s -N -X POST http://localhost:8000/api/research \
  -H 'Content-Type: application/json' \
  -d '{"query": "Figma", "model": "openai/gpt-4o-mini"}'
```

You should see a stream of progress events ending with `{"type": "result", ...}`.
Or just open **http://localhost:8000**, type `Figma`, and hit **Research →**.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Missing API key(s): Serper.dev, OpenRouter" | `.env` not found or server not restarted | Confirm the file is at `backend/.env`, restart uvicorn |
| "Serper.dev search failed (403)" | Invalid Serper key or free credits exhausted | Re-copy key from https://serper.dev/api-key; check remaining credits on the dashboard |
| "OpenRouter request failed (401)" | Wrong/revoked OpenRouter key | Create a fresh key at https://openrouter.ai/settings/keys |
| "OpenRouter request failed (402)" | No credits and a paid model selected | Add $5 credit, or switch to a `:free` model in the sidebar |
| "OpenRouter request failed (429)" | Rate limit (common on `:free` models) | Wait a minute or switch models |
| Works in sidebar but not from `.env` | Editor saved `.env.txt` or added quotes | `ls -la backend/` to check the filename; remove quotes |

### When you deploy (Vercel)

Set the same two variables in **Vercel → your project → Settings → Environment Variables**:
`SERPER_API_KEY` and `OPENROUTER_API_KEY` — then redeploy. Sidebar keys work there too.
