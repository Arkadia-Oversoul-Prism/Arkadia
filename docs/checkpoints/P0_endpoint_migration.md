# Checkpoint P0 — Production Endpoint Migration
> Status: COMPLETE
> Commit type: chore(deployment)

## Summary
Migrated all active production references from the exhausted Render instance
(`arkadia-n26k.onrender.com`) to the live instance (`arkadia-kw64.onrender.com`).

## Files Updated
| File | Change |
|---|---|
| `api/main.py` | CORS default origin (comment + 2 code lines) |
| `bot/discord-bot.mjs` | `ORACLE_URL` fallback default |
| `bot/telegram-bot.mjs` | `ORACLE_URL` fallback default |
| `bot/.env.example` | Example env var value |
| `openclaw/config.json` | `base_url` field |
| `web/public_prism/src/lib/apiConfig.ts` | `RENDER_URL` constant |
| `CLOUD_ARCHITECTURE.md` | Deployment table + ASCII diagram (4 references) |
| `UPTIMEROBOT_SETUP.md` | Monitor URL |
| `sonata-android/README.md` | Example URL in settings instructions |
| `.agents/memory/phase0-security.md` | CORS production default in memory file |

## Preserved as Historical Context (not updated)
| File | Reason |
|---|---|
| `docs/adr/ADR-013-phase0-security-hardening.md` | Historical ADR — old URL is part of the decision record |
| `docs/recon/12_configuration_audit.md` | Recon snapshot — historical |
| `docs/deployment/RAILWAY.md` | Already notes it as "old Render URL" |
| `DEPLOYMENT_OPTIONS.md` | Migration checklist item — references the old URL as the thing being migrated away from |

## Manual Action Required
`web/public_prism/.env.production` — `VITE_API_URL` could not be updated by the agent
(env files are protected). **User must set this environment variable:**
```
VITE_API_URL=https://arkadia-kw64.onrender.com
```
Either update the Vercel environment variable in the Vercel dashboard, or update `.env.production` manually before the next frontend deploy.

## Verification
- `pytest tests/architecture/ -q` → 10/10 ✅
- Zero remaining active references to `arkadia-n26k.onrender.com` in runtime code ✅
- Historical references preserved in ADRs and recon documents ✅
