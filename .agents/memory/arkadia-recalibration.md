---
name: Arkadia system recalibration
description: Findings and decisions from a full-repo dependency/architecture audit (docs/recon/) and the cleanup that followed. Read before touching engine/parsers/schemas, frontend routing deps, root package.json, or openclaw deploy configs.
---

## Dead execution stacks (archived, not deleted)
`engine/`, `parsers/`, `schemas/` formed an isolated intent-execution stack never wired into
`api/main.py`'s registered routers. Confirmed via import-graph trace (nothing reachable from the
live FastAPI app imports them). Moved to `archive/dead_execution_stacks/` rather than deleted, in
case old ADRs referencing them need the code for context. `kernel/` and `solspire/` are the two
live execution stacks (`solspire/console_router.py` is a distinct domain — project-management
console — not a duplicate of `kernel/`).

## Orphaned duplicates (archived)
- `gate/` → `archive/legacy_frontend/gate/` (legacy static landing page, not mounted or built anywhere).
- `sonata/` (legacy Java Android app) → `archive/legacy_android/sonata/`. Superseded by
  `sonata-android/` (Kotlin); CI (`.github/workflows/build-apk.yml`) only builds the Kotlin one.
- `attached_assets/arkadia_spirit/GovernanceSpirit/` (a full nested React+Express+Postgres app,
  accidental attachment) → `archive/GovernanceSpirit_duplicate/`.
- `static/index.html` and `static/dashboard.html` were **NOT** removed — `api/main.py` mounts
  `static/` at `/static`, so they're still technically live even though superseded by the React
  frontend at `web/public_prism/`.

**Why:** the recon audit (docs/recon/) flagged these as top redundancy risks; each needed a
grep-based reachability check before removal since "present in the repo" and "wired into a live
path" are not the same thing here.

## Root package.json was pure drift, not a second frontend
The repo had a root `package.json` (React 19, Vite 8, Tailwind 4) alongside the real shipped
frontend `web/public_prism/package.json` (React 18.3, Vite 5, Tailwind 3). It had no `vite.config`,
no `src/`, no `scripts`, and nothing in `.replit`/`vercel.json`/CI referenced it — it wasn't building
anything, just sitting there as a stale, mismatched manifest. Deleted outright (not archived).
**Why:** this exact mismatch class caused the earlier Vercel Tailwind v3/v4 crash (see
vercel-tailwind-postcss.md) — an unused duplicate manifest with different major versions is a
recurring source of "which package.json actually applies here" confusion.
`react-router-dom` and `wouter` were also removed from `web/public_prism/package.json` — grep
confirmed zero imports anywhere in `web/public_prism/src`; navigation is a plain `useState<View>`
switch in `App.tsx`, not URL-based routing.

## Sovereign-key gate hardening
`api/main.py` previously defaulted `SOVEREIGN_KEY` to a hardcoded string
(`os.environ.get("SOVEREIGN_KEY", "arkadia-forge-2026")`) when the env var was unset, and several
gate checks compared `provided_key != SOVEREIGN_KEY` without checking either side was non-empty —
meaning an unset key plus an unset/empty provided key would pass the gate.
**Fix pattern applied everywhere this gate is checked:** `if not SOVEREIGN_KEY or not provided_key
or provided_key != SOVEREIGN_KEY: reject`. Also added a production guard in `api/auth.py`:
`_init_firebase()` now raises at startup instead of silently falling into unsigned-JWT dev-mode when
`FIREBASE_SERVICE_ACCOUNT_JSON` is unset AND `ENVIRONMENT=production` is set.
**How to apply:** any new sovereign-gated endpoint must use the same not-empty-on-both-sides pattern,
not a bare `!=` comparison. Render's env config must set `ENVIRONMENT=production` for the auth guard
to actually engage there.

## Confirmed live deploy targets (per user, 2026-07-15)
Five deploy targets total: Render (API backend, and confirmed live for the `openclaw/` WhatsApp
gateway — its `fly.toml`/`railway.json` were removed, `render.yaml` kept), Vercel (frontend),
Railway (Discord/Telegram `bot/`), HuggingFace Spaces (`arkana_space/`). Don't reintroduce
Fly.io/Railway configs for `openclaw/` without re-confirming with the user first.

## A leaked API key was found and redacted, but git history still has it
A real Gemini API key was hardcoded in `archive/legacy_python/entrypoint.sh` and
`DEPLOYMENT_GUIDE.md`. Both were redacted to env-var placeholders, but the key is still visible in
git history to anyone with repo access — redaction only prevents *future* exposure. If this recurs,
tell the user the key must be rotated at the provider console regardless of file edits.
