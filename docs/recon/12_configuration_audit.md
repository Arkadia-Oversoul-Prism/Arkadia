# 12 — Configuration Audit

## Deployment Targets (5 independent services)
| Service | Source dir | Target(s) | Config files |
|---|---|---|---|
| Main API | `api/` (root) | Render (per replit.md: `https://arkadia-n26k.onrender.com`) | `/Dockerfile`, `/requirements.txt` |
| Frontend | `web/public_prism/` | Vercel (per replit.md: `https://arkadia-prism.vercel.app`) | `web/public_prism/vercel.json`, root `/vercel.json` |
| Discord/Telegram bot | `bot/` | Railway (per replit.md) | `bot/Dockerfile`, `bot/package.json` |
| WhatsApp gateway | `openclaw/` | Render **and/or** Fly.io **and/or** Railway (three configs present simultaneously — unreconciled) | `openclaw/render.yaml`, `openclaw/fly.toml`, `openclaw/railway.json`, `openclaw/Dockerfile` |
| Secondary API | `arkana_space/` | HuggingFace Spaces (implied by its lean Dockerfile/requirements) | `arkana_space/Dockerfile`, `arkana_space/requirements.txt` |

**Contradiction flagged**: `openclaw/` has three separate hosting-provider config files. This either means (a) intentional multi-provider redundancy/failover, or (b) leftover configs from provider migrations. Not resolvable from static analysis alone — needs owner confirmation.

## Key Config Files by Layer
- **TypeScript**: `web/public_prism/tsconfig.json` (not individually inspected this pass for strictness settings — flagged as a gap).
- **Vite**: `web/public_prism/vite.config.ts` — proxies `/api` → `http://localhost:8000` in dev (added for the dashboard per replit.md); does **not** proxy `/static`, which the active IMS Archive bugfix work in this session identified as a real dev-environment gap (iframe URLs to `/static/ims/*` resolve against the frontend origin, not the backend, unless `VITE_API_BASE_URL` is explicitly set).
- **Tailwind**: `web/public_prism/tailwind.config.js` (v3 config format).
- **ESLint/Prettier**: not confirmed present in this pass (no explicit mention in any exploration output) — flagged as a gap; likely absent given the improvisational inline-style-heavy codebase.
- **Firestore rules**: `/firestore.rules` at repo root — governs Firestore collection access (`users`, `jobs`, `goals`, conversation subcollections). Not read line-by-line this session for rule strictness — flagged as a Security Audit follow-up.
- **`.replit`**: defines the four workflows currently configured in this environment (`Arkadia Discord Bot`, `Arkadia Frontend`, `Arkadia Oracle Temple`, mockup sandbox preview server).

## CI/CD
**NOT FOUND**: no `.github/workflows/*` directory, no `docker-compose.yml`. Deployment appears to be manual/platform-triggered (Render/Vercel/Railway auto-deploy on push) rather than via a custom pipeline.

## Environment Variables (per replit.md + confirmed code references)
Confirmed required: `GEMINI_API_KEY`, `GITHUB_TOKEN`, `VITE_FIREBASE_*` (4 vars), `FIREBASE_STORAGE_BUCKET`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `FORGE_STORAGE`, `SOLSPIRE_WORKERS`, `SOLSPIRE_GOAL_TICK_SECONDS`, `TELEGRAM_ASYNC_JOBS`, `CORPUS_*` family (source toggles), `VITE_API_BASE_URL`.
Additional discovered but **not listed in replit.md** (documentation gap): `CORPUS_GITHUB_TOKEN`, `CORPUS_GDRIVE_API_KEY` (referenced in `corpus/*.py` per security scan), and whatever Telegram-token-named vars `openclaw/render.yaml` declares (not individually enumerated this session).

## Feature Flags
- `TELEGRAM_ASYNC_JOBS` (bool) — toggles kernel job-based async flow in the Telegram bot vs. synchronous default.
- `FORGE_STORAGE` (`auto`/`firebase`/`github`) — controls image upload destination.
- No centralized feature-flag system (e.g. LaunchDarkly) — flags are ad hoc environment variables read directly at call sites.

## Contradictions Identified
1. Three simultaneous deploy configs for `openclaw/` (Render + Fly.io + Railway).
2. Root `package.json` dependency versions (React 19/Vite 8/Tailwind 4) do not match the actually-shipped frontend (React 18/Vite 5/Tailwind 3) — risk of confusion for anyone running root-level `npm install`/`npm run` commands expecting them to affect the frontend.
3. `replit.md`'s TF-IDF/summarization claims do not match the confirmed simpler implementations in code (priority-tier scoring, sliding-window history) — a documentation-drift issue, not a runtime contradiction.
