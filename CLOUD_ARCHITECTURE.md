# Arkadia Sovereign Cloud Architecture

## Live Endpoints

| Service | URL | Platform |
|---|---|---|
| Oracle Backend | https://arkadia-n26k.onrender.com | Render |
| Prism Frontend | https://arkadia-prism.vercel.app | Vercel |
| OpenClaw Gateway | Deploy via Railway (see below) | Railway |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                      TRIGGERS                            │
│  Telegram · WhatsApp · Webhook · Cron · curl · Prism UI │
└──────────────────────┬───────────────────────────────────┘
                       │  POST /api/agent/spawn
                       │  { intent, agent, context, source }
┌──────────────────────▼───────────────────────────────────┐
│             ORACLE — arkadia-n26k.onrender.com           │
│  FastAPI · Gemini fallback chain · kernel workers        │
│  goal scheduler · weaver self-evolution · RAG corpus     │
│  Returns job_id immediately. Workers execute async.      │
└────────┬───────────────────────────┬─────────────────────┘
         │                           │
    /api/job/{id}              /api/goals
    (poll result)         (persistent directives)
         │                           │
┌────────▼───────────────────────────▼─────────────────────┐
│                     STATE                                │
│  Primary:  Firebase Firestore (set FIREBASE_SERVICE_    │
│            ACCOUNT_JSON in Render env vars)             │
│  Fallback: local JSON files in data/ (ephemeral)        │
└──────────────────────────────────────────────────────────┘
         │
┌────────▼───────────────────────────────────────────────┐
│          PRISM — arkadia-prism.vercel.app              │
│  React dashboard · IMS interface · distribution layer  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│          OPENCLAW — Railway (Node 22+)                 │
│  Telegram/WhatsApp gateway · tool execution runtime   │
│  Calls Oracle /api/agent/spawn · polls /api/job/{id}  │
└────────────────────────────────────────────────────────┘
```

---

## Deploying to Render (Oracle Backend)

The Oracle auto-deploys from GitHub whenever you push to `main`.

### Required Environment Variables (set in Render dashboard)

```
GOOGLE_API_KEY                   # Gemini AI — required for Oracle reasoning
GITHUB_PERSONAL_ACCESS_TOKEN     # Corpus sync from repo
SOVEREIGN_KEY                    # Access control
FIREBASE_SERVICE_ACCOUNT_JSON    # Enables Firestore state persistence
```

### Test the spawn endpoint

```bash
curl -X POST https://arkadia-n26k.onrender.com/api/agent/spawn \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Generate an Ifa reading for the Arkadia lattice",
    "agent": "oracle",
    "source": "test"
  }'
```

Expected response:
```json
{
  "job_id": "job_abc123",
  "status": "queued",
  "agent": "oracle",
  "source": "test",
  "poll_url": "/api/job/job_abc123"
}
```

### Poll for result

```bash
curl https://arkadia-n26k.onrender.com/api/job/job_abc123
```

---

## Deploying OpenClaw (Choose One)

The `openclaw/` directory contains a `Dockerfile` that works on both platforms below.

---

### Option A — Render.com ✅ Recommended (you already have an account)

**Pros:** Same dashboard as Oracle, GitHub auto-deploy, no new accounts needed.  
**Con:** Free tier sleeps after 15min — add a second UptimeRobot monitor for OpenClaw too.

1. Go to [render.com](https://render.com) → your existing dashboard
2. Click **New +** → **Web Service**
3. Connect your GitHub repo
4. Set **Root Directory** → `openclaw`
5. Set **Runtime** → **Docker**
6. Set **Instance Type** → **Free**
7. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` — from @BotFather on Telegram
   - `WEBHOOK_SECRET` — optional, secures incoming webhooks
8. Click **Create Web Service**

Render builds the Dockerfile and deploys. Auto-redeploys on every push to `main`.

---

### Option B — Fly.io (Never sleeps — better for persistent agents)

**Pros:** Free tier always keeps 1 machine running. No sleep. Better for real-time triggers.  
**Con:** Requires the flyctl CLI for first deploy.

**Install flyctl (one time):**
```bash
curl -L https://fly.io/install.sh | sh
fly auth signup   # or: fly auth login
```

**Deploy:**
```bash
cd openclaw
fly launch        # first time — reads fly.toml, creates the app
fly deploy        # every subsequent push
```

**Set secrets:**
```bash
fly secrets set TELEGRAM_BOT_TOKEN=your_token_here
fly secrets set WEBHOOK_SECRET=your_secret_here
```

**Monitor:**
```bash
fly status   # check machine health
fly logs     # live log stream
```

---

### Verify (same for both)

Once deployed, send a message to your Telegram bot. OpenClaw will:
1. Receive the message
2. `POST https://arkadia-n26k.onrender.com/api/agent/spawn`
3. Poll `/api/job/{job_id}` every 2s until complete
4. Reply with the Oracle's result in Telegram

---

## Enabling Firebase Persistence

By default, jobs and goals persist to ephemeral local files. When Render's
free tier restarts the service, those files reset.

To enable Firestore persistence (survives all restarts):

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Open your project → **Project Settings** → **Service Accounts**
3. Click **Generate new private key** → download the JSON file
4. In Render dashboard → Environment → add:
   - Key: `FIREBASE_SERVICE_ACCOUNT_JSON`
   - Value: paste the entire JSON as a single line
5. Redeploy. The Oracle will now sync jobs and goals to Firestore.

---

## Keeping Oracle Awake (Free Tier)

Render's free tier sleeps after 15 minutes of inactivity.
See `UPTIMEROBOT_SETUP.md` for the 5-minute setup to prevent this.

---

## Development Workflow

```
Edit code in Replit (or locally)
        ↓
git push origin main
        ↓
Render auto-redeploys Oracle (2–3 min)
Vercel auto-redeploys Prism (1–2 min)
        ↓
Test against live endpoints
```

Replit's frontend dev server proxies all `/api` calls to the live Render
Oracle — so you always develop against the real brain, not a simulation.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/agent/spawn` | Spawn an agent job (OpenClaw entry point) |
| GET | `/api/job/{id}` | Poll job status + result |
| GET | `/api/jobs` | List all jobs |
| POST | `/api/goals` | Create a persistent goal |
| GET | `/api/goals` | List all goals |
| POST | `/api/commune` | Direct Oracle conversation |
| GET | `/api/metrics` | System metrics (workers, jobs, goals) |
| GET | `/api/ark-date` | Current Ark Date coordinate |
| GET | `/api/scrolls` | List corpus scrolls |
| POST | `/api/scrolls` | Upload a scroll to corpus |
