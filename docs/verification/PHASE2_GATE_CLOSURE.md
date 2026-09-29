# Phase 2 Opening Gate — Closure Record

**Status:** CLOSED — PASS  
**Phase 1:** remains SEALED (`docs/verification/PHASE1_CLOSURE.md`)  
**Track 2 (sovereign layer):** NOT STARTED / unchanged  

---

## 1. Gate definition

Authenticated **browser** observation of the Engineering Lab via the **canonical** Firebase client path:

Disposable Firebase identity → LoginPage (`signInWithEmailAndPassword`) → `onAuthStateChanged` → `AuthContext.isAuthenticated` → SolSpire leaves `PRIVATE WORKSPACE` → Engineering Lab content → identity cleanup  

**Not allowed as PASS:** localStorage-only token, synthetic browser JWT, `isAuthenticated` override, Firebase mock, `require_auth` bypass, Level 3 / sovereign entanglement.

---

## 2. Evidence chain

| Order | Reference | Role |
|-------|-----------|------|
| 1 | `1b563bae72f979e906ae529b54874991cea20c14` | Phase 2 opening record |
| 2 | `c53497ba4b9d1f4325c18b9fabfaa1ff561d3664` | Option 3 `workflow_dispatch` Firebase web inputs + ephemeral harness + Playwright sign-in |
| 3 | `83294ff6af1706fbcca70ae84b315b3010516c53` | Browser step `pipefail` (Node exit visible to outcome) |
| 4 | `79ed239e78eba228aa54e2db1c937dd258bb9029` | Failure-time diagnostics (phases, redacted dump, screenshots) |
| 5 | **CP10 run `34434094368`** | **PASS** — [Actions](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/34434094368) @ `79ed239` |

### Runtime proof (excerpt)

```text
Unauthenticated route threshold PASS
[phase] identity_loaded email_domain=gmail.com
[phase] login_page url=http://127.0.0.1:5000/login
[phase] form_filled
[phase] signin_clicked
[phase] post_submit url=http://127.0.0.1:5000/login
[diag] bodySnippet=… NODE LOGIN … WELCOME TO ARKADIA … Getting to know you 1 / 18 …
Authenticated Engineering Lab lens: PASS
```

Enforce on that run: `Authenticated browser Engineering Lab lens: PASS`.

---

## 3. Prior NOT PASS runs — classification

| Cause class | Finding |
|-------------|---------|
| Incomplete dispatch config | Early runs missing `VITE_FIREBASE_AUTH_DOMAIN` prevented client Firebase init |
| Harness masking | `node \| tee` without `pipefail` could hide Node `exit 1` behind a green step |
| **Hydration timing** | With full config, sign-in succeeded; asserting Lab before AuthContext/`isAuthenticated` settled produced false `PRIVATE WORKSPACE` failures |

**Not architecture defects:** auth spine, disposable harness, LoginPage selectors, or Lab API `require_auth`.

---

## 4. What this does **not** claim

- Phase 2 product completion  
- Sovereign / Level 3 exclusive authority (Track 2)  
- Production mutation enabled  
- Autonomous mutation enabled  

---

## 5. Track 2 reminder

Sovereign access remains **authorization above** Firebase identity (`access_level` / admin-set claims / `require_sovereign`).  
**Level 3 ≠ exclusive architect** until Track 2 designs that distinction explicitly.

---

## 6. Constitutional summary

> The opening gate closed on **runtime evidence** of the **canonical** client path.  
> No bypass. No mock. No weakened boundary.
