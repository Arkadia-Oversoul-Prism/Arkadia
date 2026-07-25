# Arkadia Oracle Temple — Railway Deployment

**Service:** Python/FastAPI backend (`api/main.py`)  
**Builder:** Dockerfile (root `Dockerfile`)  
**Port:** Railway-injected `$PORT` (picked up automatically by `entrypoint.sh`)  
**Health check:** `GET /api/heartbeat`

---

## Overview

The backend was previously hosted on Render (free tier, now exhausted).
Railway hosts the same Docker image with no application code changes.
`railway.json` at the repo root configures the build and deploy behaviour.

---

## Environment Variables

Set these in the Railway service dashboard under **Variables**.

### Required

| Variable | Description |
|---|---|
| `ENVIRONMENT` | Set to `production` to enable fail-fast auth and sovereign-key checks |
| `SOVEREIGN_KEY` | Strong random secret — required when `ENVIRONMENT=production` |
| `GOOGLE_API_KEY` | Google Gemini API key — oracle and planner |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins, e.g. `https://your-prism.vercel.app` |

### Recommended

| Variable | Description |
|---|---|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub PAT (scope: `repo read`) — enables corpus auto-sync |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Full JSON string of Firebase service account — enables Firestore persistence |
| `ARKADIA_DB_PATH` | Path to knowledge SQLite DB. Set to `/arkadia-data/arkadia.db` when using a volume (see below) |
| `SOLSPIRE_DATA_DIR` | Directory for runtime SQLite and JSON snapshots. Set to `/arkadia-data` when using a volume |

### Optional

| Variable | Description | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for OpenClaw trigger | — |
| `WEBHOOK_SECRET` | HMAC secret for incoming webhook verification | — |
| `SOLSPIRE_WORKERS` | Background kernel worker thread count | `2` |
| `SOLSPIRE_GOAL_TICK_SECONDS` | Goal scheduler interval (seconds) | `15` |
| `ARKADIA_RECURSIVE_ENABLED` | Enable autonomous weaver | `false` |
| `ARKADIA_RECURSIVE_DEPTH` | Recursive reasoning depth | `3` |
| `ARKADIA_RECURSIVE_INTERVAL` | Recursive interval (seconds) | `1.0` |

---

## Persistent Storage

Arkadia uses two SQLite databases that must survive container restarts:

| Database | Default path | Purpose |
|---|---|---|
| `knowledge/arkadia.db` | Controlled by `ARKADIA_DB_PATH` | Knowledge OS — corpus, vault index |
| `data/runtime.db` | `$SOLSPIRE_DATA_DIR/runtime.db` | Runtime state — jobs, goals, corpus sync state |

Railway volumes are configured in the dashboard (**not** in `railway.json`).

### Steps to add a persistent volume

1. In the Railway service, go to **Settings → Volumes**.
2. Add a new volume. Set the **mount path** to `/arkadia-data`.
3. Set the following environment variables:
   ```
   SOLSPIRE_DATA_DIR=/arkadia-data
   ARKADIA_DB_PATH=/arkadia-data/arkadia.db
   ```
4. Redeploy. Both databases will now persist across restarts and redeployments.

> **Note:** Without a volume, both databases are ephemeral — lost on every restart.
> Firebase (`FIREBASE_SERVICE_ACCOUNT_JSON`) provides an alternative durability
> path for jobs and goals if a volume is not configured.

---

## Deployment Steps

### First deployment

1. Push this repository to GitHub (already done).
2. In Railway: **New Project → Deploy from GitHub repo → select this repo**.
3. Railway detects `railway.json` and uses the root `Dockerfile` automatically.
4. Set all **Required** environment variables in the Variables tab.
5. Add a persistent volume mounted at `/arkadia-data` (see above).
6. Click **Deploy**. Watch logs — the startup sequence prints:
   ```
   Starting Arkadia Oracle Temple...
   Configuration:
     GOOGLE_API_KEY:  set (oracle + planner active)
     Starting server on port: <PORT>
   ```
7. Verify the health check: `curl https://<your-railway-domain>/api/heartbeat`

### Subsequent deployments

Railway auto-deploys on every push to `main` (`autoDeploy` is enabled by default).
To deploy manually: **Deployments → Deploy → select commit**.

---

## Migration from Render

| Item | Action |
|---|---|
| Environment variables | Copy all from Render dashboard → Railway Variables |
| SQLite databases | Export from Render ephemeral disk (if accessible) or accept cold start |
| Firebase state | No action — Firestore data is cloud-resident and carries over automatically |
| Frontend `ORACLE_URL` | Update `bot/.env.example` and any deployed frontend to the new Railway domain |
| CORS | Add the Railway service domain to `CORS_ALLOWED_ORIGINS` |

The old Render URL referenced in code is `https://arkadia-n26k.onrender.com`.
Replace it with `https://<your-railway-domain>.railway.app` in:
- Any deployed frontend environment variables (`VITE_ORACLE_URL` etc.)
- `bot/.env.example` → `ORACLE_URL`

---

## Health Check

Railway polls `GET /api/heartbeat` every 30 seconds after deploy.
The endpoint is defined at line 678 of `api/main.py` and returns a JSON status object.
`healthcheckTimeout` is set to 300 s to allow for slow cold-start container pulls.

---

## Rollback

Railway keeps a full deployment history.

1. Go to **Deployments** in the Railway service dashboard.
2. Find the last known-good deployment.
3. Click **Rollback to this deployment**.

The rollback is instant — it restarts the container from the previously built image.
No code changes are required.

To rollback to Render (if the free tier is restored):
1. Re-enable the Render service.
2. Update `CORS_ALLOWED_ORIGINS` and frontend `ORACLE_URL` to point back to the Render domain.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: SOVEREIGN_KEY is required` | `ENVIRONMENT=production` set but `SOVEREIGN_KEY` missing | Add `SOVEREIGN_KEY` to Railway Variables |
| `[AUTH] Auth module failed to load in production` | `FIREBASE_SERVICE_ACCOUNT_JSON` missing or malformed | Add the full JSON string, or unset `ENVIRONMENT` if Firebase not needed |
| Health check fails — 502 | App still booting (large corpus sync on cold start) | Increase `healthcheckTimeout` in `railway.json` |
| Databases reset on every deploy | No persistent volume configured | Add Railway volume at `/arkadia-data` (see above) |
| CORS errors from frontend | Railway domain not in `CORS_ALLOWED_ORIGINS` | Add `https://<your-railway-domain>.railway.app` to the variable |
