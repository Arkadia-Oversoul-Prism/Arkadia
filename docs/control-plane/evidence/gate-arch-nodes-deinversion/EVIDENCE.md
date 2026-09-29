# GATE-ARCH — api/nodes.py layer inversion de-inversion — EVIDENCE

**Authorization:** human ("Proceed") on the recommended bounded workstream.
**Base:** `d48ad0e20fdf5d86f75c5cb3717fed3334608404` (merged `main`, PR #97).
**Branch:** `gate-arch/nodes-layer-inversion-deinversion`.
**Merge / production deploy:** HUMAN ONLY.
**Merge / deploy / self-authorization:** not performed.

---

## 1. Bounded objective

Resolve the pre-existing layer-boundary violation:

```
api/nodes.py: Layer 3 imports from Layer 1: 'api.ais_profile'  (ADR-015)
api/nodes.py: Layer 3 imports from Layer 1: 'api.lab_routes'   (ADR-015)
```

**Completion condition:** `tests/architecture` reports zero failures, with no
new failure introduced anywhere and no change to any canonical-test fingerprint.

**Regression boundary:** full suite must not gain any failure vs merged `main`.

**Authority boundary:** no merge, no deploy, no authority/identity change, no
test-registry (debt) edit, no scope expansion.

---

## 2. Precondition checks

| Check | Result |
|-------|--------|
| Ancestry / working tree | clean, on merged `main` `d48ad0e` |
| Provenance of the violation | introduced in PR **#39** (commit `167a1a1`); present on base `e9257bf`; **PR #97 did not touch `api/nodes.py`** |
| Protected surfaces | `api/nodes.py` is layer-3 **identity** (`ORTHOGONAL_GROUPS`); `api/auth.py` consumed read-only |
| Contradictory evidence | canonical test `tests/test_ais_w8_canonical_identity.py` asserts the literal `router.include_router(_ais_profile_router)` lives in `api/nodes.py` — see §4 |
| Freeze rule | `LAYER_MAP` registry may only be edited to *add debt (needs ADR)* or *remove debt (after fixing)*; the rule says **fix the import, not register it** |

---

## 3. Root cause

`api/nodes.py` (layer 3, identity) had grown two `include_router` composition
calls importing layer-1 API modules (`api.ais_profile`, `api.lab_routes`). A
composition act placed below the surface it composes — the classic FK-inversion.

---

## 4. Design decision (and the contradiction I refused to create)

Two candidate fixes:

**(a) Move both `include_router` calls to the composition root (`api/main.py`).**
Conventional, but it breaks the canonical identity assertion in
`tests/test_ais_w8_canonical_identity.py::test_w8_ais_projection_reuses_authenticated_uid`
(asserts the literal string is *in nodes.py*). That test is **already failing**
on base for unrelated, pre-existing reasons. Editing it would (i) touch a
protected canonical identity artifact and (ii) merely change *which* assertion
fails — i.e. change the failure fingerprint of a canonical test, attributable to
this work. Rejected.

**(b) Inject the sub-routers from the composition root (chosen).** `api/nodes.py`
exposes `configure_routers(ais_profile_router, lab_router)`; `api/main.py` calls
it **before** mounting the nodes router. This is the codebase's **own** documented
pattern (ADR-014 Decision 4), already used in this exact file for the tools
counter (Pass 06, `configure_tools_counter`). The literal
`router.include_router(_ais_profile_router)` remains in `nodes.py`, so the
canonical assertion is untouched and the w8 fingerprint is **identical**.

A third option (reclassify `api/nodes.py` as layer 1) was rejected: it changes
the orthogonal identity grouping → constitutional → ADR/human required.

Order-of-operations is load-bearing: FastAPI copies routes at include time, so
`configure_routers(...)` must run **before** `app.include_router(_nodes_router)`.

---

## 5. Changes

| File | Change |
|------|--------|
| `api/nodes.py` | Removed `from api.ais_profile import …` and `from api.lab_routes import …`; added named injected slots + `configure_routers()`; composition calls preserved |
| `api/main.py` | Composition root injects both sub-routers before mounting the nodes router |
| `tests/architecture/LAYER_MAP.py` | Corrected a now-stale comment only (no debt entry added/removed) |
| `tests/test_nodes_composition_seam.py` | **New** guard: AST invariant + real seam behavior + truthful no-injection state |

No debt-registry entry was added. No test assertion was weakened. No identity,
auth, or route path changed.

---

## 6. Verification

| Gate | Result |
|------|--------|
| `py_compile api/nodes.py api/main.py` | PASS |
| `pytest tests/architecture -q` | **11 passed / 0 failed** (was 10 / 1) |
| `pytest tests/test_nodes_composition_seam.py` | **3 passed** |
| `pytest` lab + nodes seam suites | **55 passed** |
| Full suite | **49 failed / 887 passed / 12 skipped / 2 errors** |
| App boot | PASS — `/api/lab/overview` 401, `/api/me/ais-profile` 401, `/api/me/identity-spine` 401, `/api/codex/personal` 200, `/api/nodes/public` 200 |

### 6.1 Baseline comparison

```
merged main : 50 failed / 883 passed / 12 skipped / 2 errors
after       : 49 failed / 887 passed / 12 skipped / 2 errors
```

- **Introduced:** none (`comm -13` empty).
- **Resolved:** `test_layer_boundaries.py::test_no_layer_inversions`.
- **Canonical w8 test:** failure fingerprint **byte-identical** to base
  (pre-existing, unchanged — not touched by this work).

---

## 7. Known limitations / unresolved risks

- The 49 remaining failures are pre-existing debt (frontend-source assertions,
  agent-run, etc.) — out of scope; baseline debt is its own workstream.
- `test_ais_w8_canonical_identity.py` still fails on unrelated stale assertions
  (`load_user_profile_store(user["uid"])` and `"ais_capability_portfolio"` are
  no longer literal in `api/ais_profile.py`). Recorded, **not** silently fixed.
- `api/nodes.py` remains classified layer-3 identity; the injection resolves the
  inversion without reclassification.

---

## 8. Rollback

Revert the merge commit / delete the branch. Changes are confined to 4 files;
`api/nodes.py` reverts to its direct-import form. No data migration.

---

## 9. Exact references

- Base: `d48ad0e20fdf5d86f75c5cb3717fed3334608404`
- Branch: `gate-arch/nodes-layer-inversion-deinversion`
- Verdict: **VERIFIED**
