# Arkadia — Deployment Options
> Produced: Phase 1, post-Railway analysis
> Purpose: select the cheapest, most stable home for the backend SQLite stack
> Decision needed: choose one option below, then run the deployment agent

---

## Context

Render free tier exhausted. Railway is configured (`railway.json` + `docs/deployment/RAILWAY.md` exist) but Railway's free tier has also been exhausted. This document evaluates three alternatives.

**Constraints:**
- Docker-based deploy (Dockerfile at root, entrypoint.sh reads `$PORT`)
- Health check: `GET /api/heartbeat`
- Persistent storage required for SQLite databases:
  - `knowledge/arkadia.db` (Knowledge OS index)
  - `data/solspire_projects.db` (SolSpire project store)
  - `data/oracle_store.json` + `data/job_store.json` + `data/goal_store.json` (kernel state — mirrored to Firestore as fallback)
- Python 3.11, ~1–2 workers, minimal CPU/RAM under idle conditions
- Total estimated RAM under load: 400–600MB

---

## Option A — Fly.io ⭐ Recommended

**Free allowance:** 3 shared-CPU VMs + 3GB persistent volumes (always free)
**Persistent volumes:** Yes — native `fly volumes`, can be mounted at `/arkadia-data`
**Docker:** Yes — builds from root Dockerfile directly
**SQLite compatibility:** Excellent — single-node, volume-mounted, WAL mode works perfectly
**Startup:** `fly launch` from repo root; Fly auto-detects Dockerfile

### Why this is the best option
Fly's persistent volume is the cleanest SQLite story: mount at `/arkadia-data`, set `ARKADIA_DB_PATH=/arkadia-data/arkadia.db` and `SOLSPIRE_DATA_DIR=/arkadia-data`, and databases survive every restart and redeploy. No code changes required — the environment variable injection already exists in `entrypoint.sh`.

### What you'd need to do
```bash
fly launch                           # generates fly.toml, detects Dockerfile
fly volumes create arkadia_data --size 3   # 3GB, free tier
```

Then in `fly.toml`:
```toml
[mounts]
  source = "arkadia_data"
  destination = "/arkadia-data"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  [[services.tcp_checks]]
    path = "/api/heartbeat"
```

Environment variables via:
```bash
fly secrets set SOVEREIGN_KEY=... GOOGLE_API_KEY=... ENVIRONMENT=production CORS_ALLOWED_ORIGINS=...
fly secrets set ARKADIA_DB_PATH=/arkadia-data/arkadia.db SOLSPIRE_DATA_DIR=/arkadia-data
```

### Limitations
- Free tier VMs are shared-CPU — expect cold starts of 2–5 seconds if idle
- 160GB outbound data/month free; above that, $0.02/GB (not a concern at current scale)

---

## Option B — Koyeb

**Free allowance:** 1 nano instance (0.1 vCPU / 256MB RAM)
**Persistent volumes:** No native persistent disk on free tier — ephemeral filesystem only
**Docker:** Yes — deploy from GitHub repo or pre-built image
**SQLite compatibility:** Problematic — 256MB RAM is marginal for Arkadia's stack; no persistent volume means databases reset on every restart

### Why this is second choice
Koyeb's free tier doesn't offer persistent volumes. This means:
- `data/oracle_store.json`, `data/job_store.json`, `data/goal_store.json` are wiped on restart
- `knowledge/arkadia.db` is wiped on restart
- **Firestore mirroring** (`api/firebase_store.py`) would keep kernel state alive for jobs/goals, but the Knowledge OS database would reset

This could be viable if you:
1. Rely on Firestore exclusively for job/goal durability
2. Accept that `knowledge/arkadia.db` rebuilds from corpus on each cold start
3. Stay within 256MB RAM (risky — Python + FastAPI + Gemini SDK alone approach 200MB)

**Verdict:** Only viable if Fly.io is unavailable. Not recommended as primary.

---

## Option C — Local-first + Cloudflare Tunnel

**Cost:** Free (Cloudflare Tunnel is free; the compute is a device you own)
**Persistent storage:** Yes — local filesystem, no limits
**Docker:** Optional — run Python directly
**SQLite compatibility:** Perfect — local disk, no restrictions
**Alignment with vision:** Highest — this is the "Sovereign Knowledge OS" model

### What this means
Run the Arkadia backend on any always-on device (old laptop, Raspberry Pi 5, mini PC, farm computer) and expose it via a Cloudflare Tunnel. The tunnel gives you a stable public HTTPS URL with no port-forwarding, no dynamic DNS, no firewall changes.

```bash
# On the host device:
pip install -r requirements.txt
./entrypoint.sh

# In a second terminal:
cloudflared tunnel --url http://localhost:8080
```

The tunnel URL (e.g. `https://abc123.trycloudflare.com`) becomes your `CORS_ALLOWED_ORIGINS` target and the URL you update in the frontend and bots.

For a permanent tunnel (stable URL, survives restarts):
```bash
cloudflared tunnel create arkadia
cloudflared tunnel route dns arkadia yourdomain.com
```

### Why this deserves serious consideration
The recon identified that Arkadia's central vision — "A Knowledge OS where memory survives" — depends on persistent SQLite state. Every cloud platform's free tier is an ongoing risk to that persistence. Local-first eliminates that risk permanently.

**Verdict:** Best long-term alignment. Requires always-on device. Recommend if you have a Raspberry Pi 5, old Mac Mini, or similar.

---

## Decision Matrix

| | Fly.io | Koyeb | Local + Cloudflare |
|---|---|---|---|
| Cost | Free (within limits) | Free (within limits) | Free (own hardware) |
| Persistent SQLite | ✅ Yes (volumes) | ❌ No (ephemeral) | ✅ Yes (local disk) |
| Docker deploy | ✅ Yes | ✅ Yes | Optional |
| RAM headroom | ✅ Shared (adequate) | ⚠️ 256MB (tight) | ✅ No limit |
| Setup effort | Low | Low | Medium |
| Cold starts | ⚠️ 2–5s idle | ⚠️ Similar | ✅ None |
| Sovereign alignment | Medium | Medium | ✅ Highest |
| **Recommended** | **⭐ Yes** | No | **⭐ If device available** |

---

## Migration from Railway/Render

Once a target is selected, the migration checklist is identical regardless of platform:

1. Set `ENVIRONMENT=production`, `SOVEREIGN_KEY`, `GOOGLE_API_KEY`, `CORS_ALLOWED_ORIGINS`
2. Mount volume at `/arkadia-data` and set `ARKADIA_DB_PATH`/`SOLSPIRE_DATA_DIR`
3. Update `CORS_ALLOWED_ORIGINS` on the backend to include the Prism frontend URL
4. Update `ORACLE_URL` environment variable in `bot/discord-bot.mjs` and `bot/telegram-bot.mjs` to the new backend URL
5. Update any frontend config that still references `https://arkadia-n26k.onrender.com`
6. Verify `GET /api/heartbeat` returns 200 before switching frontend traffic

---

## Recommended Next Step

**Choose Fly.io** unless you have an always-on device, in which case **Local + Cloudflare Tunnel** is the stronger long-term answer.

For Fly.io: the deployment agent needs to create `fly.toml` and run `fly launch` — no application code changes required.
