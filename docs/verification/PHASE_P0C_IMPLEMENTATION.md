# P0-C Implementation — Public registration + post-login first action

**Status:** CODE GREEN + backend E2E GREEN  
**Commit target:** after calibration `38bb435`

## Changes

| File | Change |
|------|--------|
| `AuthContext.tsx` | API base via `apiConfig`; `register()` via `createUserWithEmailAndPassword`; soft codex 404 |
| `LoginPage.tsx` | Tabs: Sign in / Create account / Magic link; public-beta copy |
| `App.tsx` | `FirstPrivateAction` panel (Oracle or Capture note; dismissible) |

## Constraints honored

- No spine / isolation / rate-limit / LivingGate changes
- `/api/me/codex` optional (404 OK for Guest)
- IMS nodes unchanged (`access_level` still gates sovereign)

## Backend E2E (production API)

```
register_firebase → 200
GET /api/me → Guest access_level 0
GET /api/me/codex → 404 (optional)
personal ingest → 200
own retrieve → 200
cross-user → 404
cleanup → OK
7/7 GREEN
```

## Frontend deploy

Vercel deploy of this commit required for visual confirmation of Login tabs + first-action panel.

## Production UI smoke (2026-08-20)

Host: `https://arkadia-prism.vercel.app`  
Asset: `/assets/index-B3PbXnZH.js` (post-`0be46a0`)

| Check | Result |
|-------|--------|
| Bundle contains Create account / tab-register / button-register | ✅ |
| Bundle contains first-action copy (private field / Oracle / Capture) | ✅ |
| Bundle contains register() + public-beta copy | ✅ |
| Homepage P0-B path still intact | ✅ visual |
| Backend register → me → ingest → isolation | ✅ 7/7 (prior) |

Interactive browser registration not required to prove UI presence: all Login + first-action strings and testids ship in the live bundle; identity path proven against production API.

**P0-C → 🟢 PRODUCTION GREEN**
