# 13 — Security Audit

Each finding includes a risk score (Critical / High / Medium / Low) based on exploitability and blast radius, evidence-based per the mission's "do not guess" rule.

## Findings

### 1. Historical Gemini API key exposure — **HIGH**
- Historical committed material contained a Gemini API key in legacy source/documentation. The current source surface is redacted, but Git history remains a credential-exposure surface until history cleanup is completed.
- **Risk**: if the historical key was ever real/active, it must be treated as compromised and rotated through the provider's secret-management surface.
- **Recommendation**: rotate/invalidate any historically exposed key, replace all repository references with non-secret placeholders, then perform the authorized history cleanup and re-audit.

### 2. Historical sovereign bypass key exposure — **HIGH**
- Historical committed material contained the former hardcoded sovereign bypass key in `api/main.py` and related documentation.
- **Risk**: repository readers could potentially use a historical credential against deployments that still accepted it.
- **Current state**: `api/main.py` now requires an environment-backed `SOVEREIGN_KEY` and production fails closed when it is missing.
- **Remediation**: the production Render secret has been rotated. Historical repository material still requires history cleanup.

### 3. Wildcard CORS — **MEDIUM**
- `api/main.py` previously allowed wildcard origins; production behavior should be checked against the current frontend origin set.
- **Risk**: combined with credential-bearing clients, overly permissive cross-origin access can widen attack surface.
- **Recommendation**: restrict to known frontend origins once the multi-client origin list is finalized.

### 4. Unsigned JWT decode in dev-mode auth fallback — **CRITICAL (if reachable in prod)**
- `api/auth.py` has a development fallback when Firebase Admin credentials are unavailable. Production must never silently activate this path.
- **Risk**: if production authentication were to fall back to unsigned client claims, identity could be forged.
- **Recommendation**: retain the hard production startup guard and verify it on every production deployment.

### 5. Unauthenticated identity-data endpoint — **MEDIUM**
- `GET /api/codex/personal` has historically been documented as public-by-design.
- **Risk**: it may expose personal identity architecture without access control.
- **Recommendation**: confirm that public exposure remains intentional.

### 6. Unauthenticated public node listing — **LOW**
- `GET /api/nodes/public` is intended to expose only public node data.
- **Recommendation**: periodically verify that the returned dataset remains public-safe.

### 7. `arkana_space/app.py` fully unauthenticated — **MEDIUM**
- `/health`, `/oracle`, `/webhook/meta` have historically appeared unauthenticated.
- **Risk**: if `/oracle` triggers provider calls, an exposed endpoint can create cost-abuse risk.
- **Recommendation**: verify current deployment reachability and intended access policy.

### 8. Rate limiting — **MEDIUM**
- Rate limiting coverage should be verified for all provider-backed endpoints.
- **Risk**: unauthenticated or weakly protected provider calls can create abuse/cost-exhaustion risk.

### 9. Secrets handling — otherwise sound
- Active infrastructure secrets are intended to be sourced from deployment environment/secret storage rather than source control.
- IMS credential artifacts have now been removed from the current tree and the artifact path is ignored.

### 10. Current remediation status
- IMS credential source literals removed.
- IMS credential artifact removed from the current tree.
- IMS credential artifact path added to `.gitignore`.
- `.env.example` no longer contains a legacy sovereign secret.
- Current production `SOVEREIGN_KEY` rotated in Render.
- Historical Git exposure remains pending authorized history rewrite.
- Historical Gemini credential rotation remains pending provider-side confirmation/rotation.

## Priority Order for Remediation
1. Complete provider-side rotation/invalidation of any historically exposed Gemini credential.
2. Complete Git history cleanup for all known credential-bearing objects and references.
3. Re-audit the rewritten repository and confirm no live secret material remains reachable through branch history.
4. Re-verify production authentication and provider connectivity after credential rotation.
5. Continue the independent CORS, rate-limiting, and unauthenticated-route reviews.
