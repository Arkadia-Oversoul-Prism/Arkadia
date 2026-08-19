# P0-C — Public Registration + Post-Login Onboarding

**Status:** CALIBRATION ONLY (no implementation in this pass)

**Date:** 2026-08-20  
**Baseline:** P0-B sealed (`57f794d`); Phase 0C + Phase 1 released

---

## 1. Objective

Open a safe acquisition path:

```
Guest Oracle (works)
        ↓
Create account (missing)
        ↓
Authenticated private field (uid ownership already works)
        ↓
One clear first private action (onboarding — missing)
```

Do **not** reopen isolation, rate limiting, LivingGate, or IMS architecture.

---

## 2. Current-state inspection

### Frontend auth

| Surface | Finding |
|---------|---------|
| `AuthContext.tsx` | `signIn`, magic link, `signOut` only — **no `createUser` / register** |
| `LoginPage.tsx` | Password + magic link; IMS framing (“Only IMS-authenticated nodes…”) |
| Post-login | `onSuccess → setView('home')` — no private-memory first action |
| Firebase client | `lib/firebase.ts` — web config present when `VITE_FIREBASE_*` set |

### API base mismatch (blocker for profile UX)

| Consumer | Env |
|----------|-----|
| `AuthContext` | **only** `VITE_API_BASE_URL` (empty if unset → relative `/api/me` on Vercel origin → fail) |
| `apiConfig.ts` | `VITE_API_BASE_URL` → Render fallback |
| Oracle / commune | `VITE_API_URL` or `apiConfig` |
| `.env.production` | sets `VITE_API_URL` only |

**Implication:** even existing sign-in may not load `/api/me` profile in production unless `VITE_API_BASE_URL` is set on Vercel.

### Backend identity

| Surface | Finding |
|---------|---------|
| Firebase Identity Toolkit **signUp** | **Enabled** (probed live; disposable users work — Phase 0C harness) |
| `GET /api/me` | Exists (`api/nodes.py`); requires auth; returns `build_user_profile` |
| `build_user_profile` | Any valid Firebase uid → profile; non-IMS → `access_level: 0`, `role: Guest` |
| `GET /api/me/codex` | 404 unless IMS `node_key` — **expected**; not required for private notes |
| Personal ingest / search / Oracle memory | Scoped by **Firebase uid** — IMS node **not** required |

### What already works without registration UI

- Guest Oracle (P0-B)
- Authenticated private notes + isolation (Phase 0C) for any Firebase uid
- Rate limits keyed by uid (Phase 1)

---

## 3. Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| No public **Create account** UI | **P0** | Product funnel closed |
| No `createUserWithEmailAndPassword` in AuthContext | **P0** | Backend Firebase allows it |
| Login copy still IMS-only | **P0** | Contradicts public beta |
| No post-login “first private action” | **P0** | User lands on Home with no guidance |
| AuthContext API base vs `apiConfig` | **P0** | Profile fetch fragile in prod |
| `/api/me/codex` 404 for non-IMS | **OK** | Soft-handle; don’t block onboarding |
| Email verification / abuse | **P1** | Rate limit helps; verify later |
| LivingGate rewrite | **Out of scope** | Explicitly held |

---

## 4. Intended journeys

### A. Registration (acquisition)

1. Home → Sign in for private memory → Login  
2. Toggle **Create account**  
3. Email + password → Firebase `createUserWithEmailAndPassword`  
4. Auto-session → `GET /api/me` (Guest profile ok)  
5. Land on **post-login onboarding** (not blank Home)

### B. Post-login onboarding (activation)

One screen / one primary action, e.g.:

- “Save your first private note” **or**  
- “Ask the Oracle — this session is now yours”

Then exit to Oracle or Personal capture. No diagnostic, no IMS, no LivingGate.

### C. Existing IMS nodes

Password / magic login unchanged; sovereign tools still gated by `access_level`.

---

## 5. Acceptance criteria (proposed)

| # | Criterion |
|---|-----------|
| 1 | User can create account from UI without operator/IMS |
| 2 | New uid can `POST /api/personal/ingest-note` successfully |
| 3 | New uid private note isolated from others (0C still holds) |
| 4 | Login page allows Sign in **and** Create account |
| 5 | IMS-only error copy removed for public path |
| 6 | Post-login: one clear first private action within one click |
| 7 | AuthContext uses same API base resolution as `apiConfig` |
| 8 | Non-IMS `/api/me/codex` 404 does not block session |
| 9 | No changes to ownership SQL, rate limiter, or LivingGate |
| 10 | Disposable registration test + cleanup (extend Phase 0C style) |

---

## 6. Smallest validated implementation sequence

When authorized:

1. **Fix AuthContext API base** (use `apiConfig` / Render fallback) — unblocks profile  
2. **Add `register(email, password)`** via Firebase client `createUserWithEmailAndPassword`  
3. **LoginPage:** Create account mode + public-beta copy  
4. **Post-login:** minimal first-action panel (capture note **or** Oracle with memory)  
5. **Smoke:** register → ingest → search own marker → second user cannot see it  

No Admin SDK required for registration (client signUp already proven).

---

## 7. Explicit non-goals

- LivingGate rewrite  
- IMS productization as signup gate  
- OAuth providers (Google etc.) in first slice  
- Email verification enforcement (document as follow-up)  
- Distributed rate limit / WAF  
- New memory spine  

---

## 8. Risk notes

| Risk | Mitigation |
|------|------------|
| Open signup spam | Existing Phase 1 limits; optional CAPTCHA later |
| Users expect IMS codex | Copy: private memory works; IMS is deeper optional path |
| Vercel env drift | Single API base helper; document `VITE_API_BASE_URL` |

---

## 9. Recommendation

**Authorize slice 1 only:** API base fix + register() + LoginPage Create account + thin post-login first action.

Defer full onboarding checklist and email verification to slice 2.

**Awaiting explicit implement authorization.**
