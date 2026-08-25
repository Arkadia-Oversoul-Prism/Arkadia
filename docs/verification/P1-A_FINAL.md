# P1-A FINAL — Production Recovery Verification (Recovery Pass 2)

**Date:** 2026-08-25
**Start HEAD:** `52718e6` (origin/main tip at session start)
**End HEAD:** `eed15b3` (origin/main — contains fix `63c3a65` + this report)
**Implementation under test:** `cd24bb1` + boot fix `63c3a65`

---

## 1. EXECUTION STATUS

**GREEN**

Production now serves the P1-A routes and the full two-user production matrix passes
(27/27). The root cause of the prior PARTIAL was found and fixed.

The previous pass concluded "deployment lag". **That diagnosis was wrong.** `cd24bb1`
shipped a **Python SyntaxError in `api/main.py`** (a nested `try` inside the Knowledge OS
`try:` block left the outer `try` with no `except`/`finally`, line ~312). Every Render
deploy of `cd24bb1` or later failed at process boot, so Render kept serving the last
healthy **pre-P1-A** image. Production was never "behind" — it was being asked to run a
revision that cannot start. Landing the boot fix (`63c3a65`) caused Render to build a
working image and the P1-A routes came live within ~3 minutes of push.

No security or ownership regression was found at any point.

---

## 2. DEPLOYMENT STATE

| Check | Result |
|-------|--------|
| origin/main tip | `eed15b3` (contains `63c3a65` fix) |
| Production host | `https://arkadia-kw64.onrender.com` |
| `GET /api/knowledge/status` | **200** |
| OpenAPI `GET /api/me` | **present** |
| OpenAPI `PATCH /api/me` | **present** ✅ |
| OpenAPI `POST /api/messages`, `GET /api/messages/inbox`, `GET /api/messages/thread/{peer_uid}` | **present** ✅ |
| Unauth `PATCH /api/me` | **401** (route live, auth-gated) |
| Unauth `GET /api/messages/inbox` | **401** (route live, auth-gated) |

Root cause (exact): `cd24bb1` inserted the messages-router mount inside the Knowledge OS
`try:` block without closing it:

```python
try:                                    # outer try — never closed
    from api.knowledge_routes import router as _knowledge_router
    app.include_router(_knowledge_router)
try:                                    # line 312 → SyntaxError
    from api.messages import router as _messages_router
```

Fix (`63c3a65`): two clean `try/except` blocks (Knowledge OS mount, then ReasoMate
messages mount). 6 insertions / 4 deletions, router-mount block only. No P0 path touched.
Pushed to `main` with a user-supplied PAT (env token was read-only for this repo).

---

## 3. IDENTITY VERIFICATION

| Criterion | Evidence | Level |
|-----------|----------|-------|
| Email-hint IMS matching removed from runtime identity | `build_user_profile` never calls `get_node_by_email_hint`; repo-wide grep = **zero callers** (dead code) | **CODE-VERIFIED** |
| Identity authority = Firebase `uid` (never client-supplied) | `require_auth` → `verify_firebase_token` → `claims["uid"]`; PATCH/messages ignore body `uid`/`sender_uid` | **PRODUCTION-PROVEN** |
| Fresh user = Guest, `node_key: null`, `access_level: 0`, no `ims_id` | prod matrix §A (checks 5-7) | **PRODUCTION-PROVEN** |
| Signup → display name persisted via PATCH | `AuthContext.tsx` createUser → getIdToken → `PATCH /api/me {display_name}` | **CODE-VERIFIED** |
| Identity derived from auth uid (A uid == provisioned; A ≠ B) | prod matrix checks 3-4 | **PRODUCTION-PROVEN** |

## 4. PROFILE VERIFICATION (`PATCH /api/me`)

| Test | Result | Level |
|------|--------|-------|
| A PATCH display_name → 200 | PASS | **PRODUCTION-PROVEN** |
| A GET reflects persisted value | PASS | **PRODUCTION-PROVEN** |
| B PATCH own name → 200 | PASS | **PRODUCTION-PROVEN** |
| A unaffected by B's PATCH | PASS | **PRODUCTION-PROVEN** |
| B PATCH with `uid: A` in body → ignored (server uses auth uid) | PASS | **PRODUCTION-PROVEN** |
| Unauthenticated PATCH → 401 | PASS | **PRODUCTION-PROVEN** |

Server allowlist: `display_name, username, bio, avatar_url` (`api/nodes.py:90`,
`api/auth.py:189`). Profile store: `data/user_profiles/{uid}.json`, keyed by auth uid.

## 5. MESSAGING VERIFICATION (`/api/messages`)

Contract: `POST /api/messages {recipient_uid, content}` (sender always = auth uid);
`GET /api/messages/thread/{peer_uid}`; `GET /api/messages/inbox`.

| Test | Result | Level |
|------|--------|-------|
| A→B send 200, `sender_uid == A` | PASS | **PRODUCTION-PROVEN** |
| B→A send 200, `sender_uid == B` | PASS | **PRODUCTION-PROVEN** |
| Thread persisted (2 msgs, both directions) | PASS | **PRODUCTION-PROVEN** |
| A reads thread w/ B; B reads thread w/ A | PASS | **PRODUCTION-PROVEN** |
| B inbox lists A with last message | PASS | **PRODUCTION-PROVEN** |
| Third user C reads A-B thread → 0 msgs; C inbox empty | PASS | **PRODUCTION-PROVEN** |
| Unauthenticated send → 401 | PASS | **PRODUCTION-PROVEN** |
| `sender_uid` spoof → ignored (sender = auth uid) | PASS | **PRODUCTION-PROVEN** |

**Peer discovery:** requires the recipient Firebase uid — accepted P1-A limitation.
A↔B exchange works reliably via uid entry; directory UX recorded as future work.

## 6. ECHOFEILD REGRESSION

| Check | Result | Level |
|-------|--------|-------|
| `/api/echoes` handler untouched (diff = router-mount block only) | confirmed `git diff` | **CODE-VERIFIED** |
| Authed fresh user `GET /api/echoes` → 200, `personal: []` server-side, public scrolls present | prod probe | **PRODUCTION-PROVEN** |
| Personal entries injected client-side from auth-gated Knowledge OS (not server) | `api/main.py:1551-1555` | **CODE-VERIFIED** |
| No Zahrune/canon fallback in Echofeild components | grep `PersonalEchofeild.tsx`, `UniversalEchofeildMatrix.tsx` → none | **CODE-VERIFIED** |
| `test_echofield_core.py` | PASS | API-PROVEN (local) |

## 7. CANON / IMS ISOLATION

| Check | Result | Level |
|-------|--------|-------|
| `get_node_by_email_hint` zero runtime callers | repo grep | **CODE-VERIFIED** |
| Fresh authed user `GET /api/me/codex` → **404** (no IMS session) — no canon content as private codex | prod probe | **PRODUCTION-PROVEN** |
| Fresh user profile: no `ims_id`/`access_level`/canon role | prod matrix checks 5-7 | **PRODUCTION-PROVEN** |
| Canon node applies only with explicit admin-set Firebase custom claim (`node_key`) | `api/auth.py:210-213` | **CODE-VERIFIED** |

## 8. GRAPH MOBILE VERIFICATION

`KnowledgeGraphView.tsx` (P1-A revision): graph + legend row uses `flexWrap` so the side
panel stacks below the canvas on narrow viewports; canvas `minHeight: 320` with bounded
`min(55vh, 520px)`; container `minHeight: min(70vh, 640px)`; SVG sized from the container
bounding box with a `ResizeObserver` rebuild; `touchAction: 'none'` for touch gestures. A
normal mobile viewport gets a usable ~320px interactive graph, not a squeezed panel.
**CODE-VERIFIED** (layout review). Visual/interactive pass on a real device:
NOT-VERIFIED (no device lab here).

## 9. SECURITY MATRIX

| Test | Result | Level |
|------|--------|-------|
| A identity ≠ B identity (uid-derived) | PASS | **PRODUCTION-PROVEN** |
| A profile cannot be changed by B | PASS | **PRODUCTION-PROVEN** |
| A messages reach B / B reach A | PASS | **PRODUCTION-PROVEN** |
| C cannot read A-B threads or inbox | PASS | **PRODUCTION-PROVEN** |
| Unauth profile PATCH → 401; unauth message send → 401 | PASS | **PRODUCTION-PROVEN** |
| Unauth personal ingest (P0) still rejected | `test_phase_0c` + two-user runner | **PRODUCTION-PROVEN** |
| `uid`/`sender_uid` spoof attempts ignored | PASS | **PRODUCTION-PROVEN** |

## 10. P0 REGRESSION MATRIX

| Gate | Result | Level |
|------|--------|-------|
| `63c3a65` diff touches only router-mount block (no P0 path) | `git diff` | **CODE-VERIFIED** |
| P1-1 two-user runner (identity, memory isolation, NovaNet ownership, delete-own, unauth 401) — 21 checks | **GREEN (0 fail)** on live prod | **PRODUCTION-PROVEN** |
| Local P0 suites (`test_isolation`, `test_echofield_core`, `test_transmissions_ownership`, `test_rate_limit`, `test_governance_layer`, `test_key_pool`) | 66/66 PASS | API-PROVEN (local) |
| Full local suite | 186 passed; 5 failed + 2 collection errors — **identical with fix stashed** (pre-existing: `steward_filter`, `gate_status`, `gate_serve_script`, `autonomy`/`render_codex` imports; unrelated to P1-A) | API-PROVEN (local) |

## 11. PROOF LEVELS SUMMARY

| Capability | Level |
|------------|-------|
| Root cause of prior 405/404 (SyntaxError in `cd24bb1`) | **PRODUCTION-CONSISTENT** (explains all evidence; fix brought routes live) |
| Production `PATCH /api/me` | **PRODUCTION-PROVEN** |
| Production `/api/messages` A↔B | **PRODUCTION-PROVEN** |
| Profile ownership enforcement | **PRODUCTION-PROVEN** |
| Sender identity from auth | **PRODUCTION-PROVEN** |
| Silent IMS identity matching removed | **PRODUCTION-PROVEN** (fresh user = Guest) |
| Canon/IMS isolation (codex 404) | **PRODUCTION-PROVEN** |
| Echofeild no-regression | **PRODUCTION-PROVEN** |
| Graph mobile | **CODE-VERIFIED** |

## 12. DEFERRED ITEMS (accepted for P1-A)

- Full AIS questionnaire on signup (no IMS/canon substitute used — boundary verified clean)
- Avatar file-upload pipeline (URL field only)
- Peer directory/discovery UX (uid entry remains the supported mechanism)
- Deeper Spiral Codex private productization (see §13)

## 13. KNOWN LIMITATIONS

1. Peer messaging requires knowing the recipient Firebase uid (no directory).
2. Avatar is a URL field only (no upload pipeline).
3. Spiral Codex gap: identity isolation is proven (fresh user codex → 404; no canon leak),
   but the Codex has not been re-productized as a private-only surface. Documented gap,
   not silently expanded.
4. Env `GITHUB_TOKEN` is read-only for this repo; a `ghp_…` PAT with Contents:write was
   required to push. Rotate/revoke the supplied PAT after this pass (it transited chat).

## 14. OPEN LOOPS

| Item | Class |
|------|-------|
| Visual device-lab pass on mobile graph | NON-BLOCKING (layout CODE-VERIFIED) |
| Spiral Codex private productization | DEFERRED |
| AIS onboarding / avatar upload / peer directory | DEFERRED |

## 15. COMMITS (this recovery pass)

| Commit | Content |
|--------|---------|
| `63c3a65` | `fix(p1-a): repair malformed try/except nesting that broke api/main.py boot` |
| `f0fdf72` | `docs(p1-a): final recovery report — root cause + deploy blocker` |
| `eed15b3` | `docs: note deploy fix pushed to main` |
| *(this update)* | `docs(p1-a): production evidence → GREEN` |
| `tests/production/p1a_verify.py` | production two-user P1-A verification harness (new) |

## 16. FINAL GATE

**GREEN**

All required P1-A acceptance criteria are production-proven:

- ✅ production profile PATCH works
- ✅ profile ownership enforced (owner-only; uid spoof ignored)
- ✅ silent IMS identity matching removed (fresh user = Guest, no canon)
- ✅ production messaging route works
- ✅ A→B and B→A messaging work
- ✅ sender identity derives from authentication
- ✅ unauthenticated messaging rejected (401)
- ✅ P0 isolation intact (two-user runner GREEN)
- ✅ Echofeild remains user-derived (no server-side personal leak, no canon fallback)
- ✅ mobile graph usable (layout CODE-VERIFIED)
- ✅ no canon identity leaks into private identity (codex 404 for fresh user)
- ✅ no second memory system introduced

## 17. NEXT ACTION

1. **Rotate/revoke** the `ghp_…` PAT supplied for this pass (it transited chat).
2. Optional: run the `tests/production/p1a_verify.py` harness on a schedule as a smoke test.
3. P1-B / structural audit remain **out of scope** for this pass and were not started.

**STOP.**
