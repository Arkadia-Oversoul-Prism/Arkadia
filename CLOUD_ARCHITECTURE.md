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

## Deploying OpenClaw to Railway

### Step 1 — Push openclaw/ to GitHub

The `openclaw/` directory is already in your repo with:
- `config.json` — Oracle endpoint + trigger config
- `package.json` — Node 22+ service definition
- `railway.json` — Railway deploy config

### Step 2 — Create Railway service

1. Go to [railway.app](https://railway.app) → sign up (free)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repo
4. Set the **root directory** to `openclaw/`
5. Railway detects `package.json` and deploys automatically

### Step 3 — Set environment variables in Railway

```
TELEGRAM_BOT_TOKEN    # From @BotFather on Telegram
WEBHOOK_SECRET        # Optional — secures incoming webhooks
```

### Step 4 — Verify

Once deployed, send a message to your Telegram bot. OpenClaw will:
1. Receive the message
2. POST to `https://arkadia-n26k.onrender.com/api/agent/spawn`
3. Poll `/api/job/{job_id}` until complete
4. Reply with the Oracle's response

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
