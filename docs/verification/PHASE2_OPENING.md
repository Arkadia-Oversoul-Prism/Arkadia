# Phase 2 Opening Record

**Status:** OPENING GATE CLOSED — PASS (see PHASE2_GATE_CLOSURE.md)  
**Opened by:** explicit human command (2026-09-10)  
**Phase 1:** remains **SEALED** (`docs/verification/PHASE1_CLOSURE.md`)  

---

## 1. Opening obligation (unchanged from Phase 1 deferral)

> Legitimate **authenticated browser** verification of the Engineering Lab —  
> without bypassing `require_auth`, without mock auth presented as production auth,  
> without weakened boundary, without manufacturing PASS from DEFERRED.

| Label | Meaning |
|-------|---------|
| Prior | `DEFERRED BY ACCEPTANCE CRITERIA` (Phase 1) |
| Target | `PASS` only with direct browser runtime evidence of an **authenticated** Lab session |
| Forbidden | Treating DEFERRED/BLOCKED as PASS |

---

## 2. What “legitimate” means (source-proven constraints)

| Layer | Authority | Implication for CP10 |
|-------|-----------|----------------------|
| SolSpire UI gate | `useAuth().isAuthenticated` (Firebase `onAuthStateChanged`) | Browser must present a **Firebase-authenticated** client session, not only a localStorage token |
| Lab API | `require_auth` on `/api/lab/overview` | Server must accept the same session’s token under the **active** auth mode |
| Production | `ENVIRONMENT=production` requires Firebase Admin credentials | CI must not pretend to be production while using unsigned JWT |
| Dev/CI without Firebase SA | Existing **dev-mode** unsigned JWT decode for **API** tests only | Does **not** by itself satisfy **browser** `isAuthenticated` (Firebase client SDK) |

**Conclusion:** The Phase 2 browser gate cannot be closed by injecting `arkadia_token` alone. It requires a **real client sign-in path** (Firebase test user / CI secrets) or an **explicitly authorized** alternate that still does not weaken production `require_auth`.

---

## 3. Current gate state

| Item | State |
|------|--------|
| Phase 2 design scope beyond this gate | **Not opened** |
| Authenticated browser Lab | **NOT PASS** — prerequisite credentials **not established** in CP10 |
| Environmental blocker | No CP10-configured Firebase test user / client auth secret for Playwright |
| Implementation this turn | **Opening record only** — no auth bypass, no gate weakening |

---

## 4. Minimum path to PASS (when authorized and secrets available)

1. Provide CI-only Firebase **test** credentials (or equivalent client sign-in) via GitHub Actions secrets — not committed to the repo.  
2. Playwright: sign in through the **existing** client auth flow (or Firebase client API using those secrets).  
3. Navigate to `/solspire/engineering-lab`.  
4. Assert **absence** of unauthenticated threshold (`PRIVATE WORKSPACE` / sign-in card) and **presence** of Engineering Lab observation UI (e.g. Lab system/observation content).  
5. Optionally re-check Lab API with the session token under the same environment.  
6. Record **PASS** only from that evidence; never from deferral language.

Until steps 1–5 succeed: gate remains **NOT PASS**.

---

## 5. Non-goals for this opening

- Phase 2 product expansion, autonomy, mutation authority  
- Changing Phase 1 seal meaning  
- `require_auth` bypass or production Firebase disable  
- Mock authenticated UI without real session semantics  

---

## 6. Authority

| Ceiling | State |
|---------|--------|
| Autonomous mutation | DISABLED |
| Production mutation | DISABLED |
| Human authorization | Required for credential provisioning and any harness change that exercises the gate |

**Next actionable step (human):** provision legitimate CI browser-auth secrets, then authorize a bounded CP10 browser-step extension.

---

**Gate closure:** `docs/verification/PHASE2_GATE_CLOSURE.md` — PASS on CP10 run `34434094368` @ `79ed239`.
