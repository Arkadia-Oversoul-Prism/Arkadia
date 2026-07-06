# 13 — Security Audit

Each finding includes a risk score (Critical / High / Medium / Low) based on exploitability and blast radius, evidence-based per the mission's "do not guess" rule.

## Findings

### 1. Hardcoded Gemini API key in committed files — **HIGH**
- `archive/legacy_python/entrypoint.sh` line 30: hardcoded key `AIzaSyCGBWv8tDCevIAc1flyFKN8twx3wq9jQ-Y`.
- `DEPLOYMENT_GUIDE.md` lines 25/39/54: same key repeated as a documentation "example."
- **Risk**: if this key is still active, it is fully exposed in git history and any public mirror/fork. Even if labeled "legacy"/"example," a real-looking key string in a doc invites accidental reuse.
- **Recommendation**: rotate this key immediately if it was ever real/active, then scrub or replace with an obviously-fake placeholder (`AIzaSy_EXAMPLE_KEY_DO_NOT_USE`) in the doc.

### 2. Hardcoded sovereign bypass key — **HIGH**
- `api/main.py` line 36: `SOVEREIGN_KEY = "arkadia-forge-2026"` hardcoded in source, gating sovereign-only endpoints (e.g. GET on `/api/orders`, `/api/ims/inquiry`).
- **Risk**: anyone with repo read access has permanent access to sovereign-gated data regardless of Firebase auth state, and the key cannot be rotated without a code deploy.
- **Recommendation**: move to an environment secret; treat current value as compromised and rotate on next deploy.

### 3. Wildcard CORS — **MEDIUM**
- `api/main.py` lines 186–190: `allow_origins=["*"]`, all methods, all headers.
- **Risk**: combined with cookie/token-based auth this could enable cross-origin credential leakage; currently mitigated somewhat by Firebase bearer-token auth (not cookies) but still overly permissive for a production API serving sovereign-gated data.
- **Recommendation**: restrict to known frontend origins (Vercel domain(s), Replit dev domain) once the multi-client (bots + web + mobile) origin list is finalized.

### 4. Unsigned JWT decode in dev-mode auth fallback — **CRITICAL (if reachable in prod)**
- `api/auth.py` lines 31–41, 197: when `FIREBASE_SERVICE_ACCOUNT_JSON` is unset, `get_current_user` decodes the JWT payload **without verifying its signature**, trusting client-supplied claims (including `node_key`) at face value.
- **Risk**: if this env var is ever accidentally unset in a production deploy, any client can forge a token claiming any `node_key`/sovereign identity.
- **Recommendation**: add a hard `if ENVIRONMENT == "production" and not FIREBASE_SERVICE_ACCOUNT_JSON: raise RuntimeError(...)` startup guard so the dev-mode path can never silently activate in prod. This is the single highest-priority security fix identified in this audit.

### 5. Unauthenticated identity-data endpoint — **MEDIUM**
- `api/nodes.py` line 35: `GET /api/codex/personal` — explicitly documented in-code as "No auth required. Serves Zahrune's full identity architecture directly."
- **Risk**: intentional per the code comment (single-owner personal codex, likely meant to be public-by-design for this specific person), but worth flagging since it serves what could be sensitive personal data with zero access control. Confirm this is intentional product behavior, not an oversight.

### 6. Unauthenticated public node listing — **LOW**
- `api/nodes.py` line 109: `GET /api/nodes/public` — unauthenticated, but scoped to "public" node data by name; lower risk if the data is genuinely meant to be public.

### 7. `arkana_space/app.py` fully unauthenticated — **MEDIUM**
- `/health`, `/oracle`, `/webhook/meta` all appear unauthenticated. If `/oracle` triggers a real Gemini call, this is an open, unmetered LLM proxy — potential for cost-abuse if the URL becomes known.

### 8. No rate limiting observed anywhere — **MEDIUM**
- No rate-limiting middleware was identified on any FastAPI route in this pass. Combined with finding #7 and the wildcard CORS, this raises abuse/cost-exhaustion risk for any Gemini-backed endpoint (`/api/commune/resonance`, `/api/ceo/chat`, `/arkadia/generate`, `arkana_space` `/oracle`).

### 9. Secrets handling — otherwise sound
- Most secrets (`CORPUS_GITHUB_TOKEN`, `CORPUS_GDRIVE_API_KEY`, `GEMINI_API_KEY`, Firebase creds) are correctly sourced from environment variables via `os.environ.get(...)` patterns, not hardcoded, per `api/key_manager.py` and `corpus/*.py`.

### 10. NOT FOUND
- No hardcoded database connection strings (Postgres/MongoDB) in the active codebase (only in the isolated `GovernanceSpirit` sub-app, which correctly uses env vars).
- No `docker-compose.yml` or GitHub Actions workflow files exist, so no CI-embedded-secret risk from that vector.
- No explicit `/admin/debug`-style endpoint found.

## Priority Order for Remediation
1. **Critical**: Guard the dev-mode unsigned-JWT auth fallback from ever activating in production (#4).
2. **High**: Rotate/remove the hardcoded Gemini key in `archive/legacy_python/entrypoint.sh` and `DEPLOYMENT_GUIDE.md` (#1); move `SOVEREIGN_KEY` to an env secret (#2).
3. **Medium**: Tighten CORS (#3); add rate limiting to LLM-backed endpoints (#8); confirm `arkana_space` endpoints are intentionally open or add auth (#7).
4. **Low**: Confirm `/api/codex/personal` and `/api/nodes/public` unauthenticated-by-design status is still desired (#5, #6).
