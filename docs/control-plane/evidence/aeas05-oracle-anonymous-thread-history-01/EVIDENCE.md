# AEAS-05 — `/oracle` anonymous 401 from the always-mounted thread-history slice

Bounded workstream. Restores a green canonical browser-smoke gate by not spending an
owner-scoped read the anonymous visitor cannot satisfy.

## Observation

- `main` = `7b67215735945584e89fec50f97fe74dddfcbf28` (2026-10-11 16:18 +0100).
- Live `Canonical Render Browser Smoke` (`run=38150620909`, head `56ada9dd`) -> **failure**.
  The failing step is `Exercise canonical production routes`; its report shows `result: FAIL`
  with exactly one bad route:

  ```
  { "path": "/oracle", "status": 200,
    "console_errors": ["Failed to load resource: the server responded with a status of 401 ()"],
    "page_errors": [], "navigation_error": null }
  ```

  Every other probed route (`/`, `/solariun`, `/solariun/engineering-lab`, `/operator`,
  `/n-atlas-lab`, `/n-atlas-tester`) is clean, and the later `main`(s) publish only
  `Arkadia Genesis Agent: skipped`, `security-secret-scan: success`,
  `Canonical Render Acceptance Record: success`, so this run is the open red gate.

## Root cause

- `web/arkadia_console/src/App.tsx` renders `/oracle` (surface `arkana`) **without** a
  `requiresAuth` gate. `ArkanaPage` mounts `<ArkanaThreadHistory />` unconditionally.
- `ArkanaThreadHistory` hydrated `GET /api/commune/threads` on mount.
  `api/commune_threads.py` requires an identity; `_user_id()` raises
  `HTTPException(401, "Authentication required")` for an anonymous caller.
- So an anonymous visit to a **public** surface always fires a request it cannot satisfy:
  the browser logs `401`, which the smoke gate counts as a console error.
- The chat contract (`askArkana`) is public — the surface is intended public. The defect is
  that the protected *sub-read* was spent unconditionally, not that reads are protected.

## Change

- `web/arkadia_console/src/components/arkana/ArkanaThreadHistory.tsx`
  - The exported shell now gates on the shared identity context (`useAuth()`), not a
    page-local re-derivation.
  - `loading` -> `<Loading label="Verifying identity..." />`.
  - authenticated -> mounts the read (`AuthenticatedThreadHistory`), unchanged in behaviour.
  - not authenticated -> `<ContractState state="auth-required" />` and **no request**.
  - A shared `ThreadHistoryFrame` renders the panel heading/copy in all three states so the
    surface shape is stable; no literal `"/api/commune/threads..."` is introduced (the
    registry `endpoints.arkanaThreads` remains the single declared base).
- `tests/test_prism_w4_arkana_thread_history.py` — three additions inside the console
  contract domain:
  - the exported shell must not mount the owner-scoped read and must gate through
    `useAuth()` / `isAuthenticated` / `loading`;
  - a **negative control** feeds the detector the pre-fix shell (must report) and a gated
    shell (must stay silent);
  - the gate must not hide the read — the authenticated slice still reads the registry
    collection.

The test file lives in the `Prism Console Contract` gate filter
(`.github/workflows/prism-console-contract.yml`), so the new invariant is enforced by CI.

## Verification (measured, same environment)

| check | command | result |
| --- | --- | --- |
| new detector flags the real pre-fix source | `git show origin/main:...ArkanaThreadHistory.tsx` -> `spends_anonymous_protected_read(exported_component_body(...))` | `True` |
| same detector on the repaired source | working tree | `False` |
| W4 + console guards | `pytest tests/test_prism_w4_arkana_thread_history.py` (+ registry/routing/acceptance/shell/wiring) | **105 passed** |
| console gate (exact workflow step) | the 15 guard files from `prism-console-contract.yml` | **283 passed** |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| boot syntax | `python -m py_compile api/main.py`; `pytest tests/test_boot_syntax_boundary.py` | OK; **5 passed** |
| frontend build | `corepack pnpm install --frozen-lockfile && corepack pnpm build` (tsc --noEmit + vite) | **exit 0** |

`api/main.py` is untouched.

## Runtime boundary — stated precisely

The browser-smoke gate observes the **canonical production origin**
`https://arkadia-qzu4.onrender.com`, not the branch. A PR run therefore cannot itself
observe the `/oracle` route without a 401; the observable that closes this pass is the
**gate run at the merge commit**. The claim here is a repository-source claim:

- source: the anonymous shell no longer issues the owner-scoped read;
- guard: a CI-executed test pins that invariant, with a negative control;
- runtime: **NOT CLAIMED** until the smoke gate runs on the post-merge revision.

Production acceptance remains **NOT CLAIMED** (ADR-016; merge + deployment are human acts).

## Composition

Live open PRs at measurement: #448, #447, #445, #436, #432. None modifies
`ArkanaThreadHistory.tsx` or `tests/test_prism_w4_arkana_thread_history.py`. #447
(`gate10/prism-console-contract-domain-completion-01`) also touches the console gate
workflow and `tests/test_prism_console_ci_wiring.py`; this change touches neither, so the
two are textually disjoint. #447's derived-domain work should keep
`tests/test_prism_w4_arkana_thread_history.py` in the domain — it already is.

## Authorization

Merge, deployment, and acceptance are reserved to the human sovereign. This PR requests
review only.

## CI execution at the branch head (measured)

Branch head `e1f5b0e085aa75b62af9d0979336708d4da540c6`: **14/14 check-runs
`completed/success`**, including the two gates this change binds to —
`Prism Console Contract` (the W4 guard domain) and `Boot Syntax Boundary`. `SG-02-FE.2-V`
and `N-ATLAS Developer Lab` also completed success.

Main then advanced `7b672157` -> `7097d6a4` (OpenAPI security metadata; disjoint paths:
`api/openapi_security.py`, `api/main.py`, four new OpenAPI tests, two workflows). The branch
was **merged forward** (not rebased) onto `7097d6a4` as `f5775304`, because force-push is
forbidden by the execution contract. Composed-tree verification after the merge: architecture
**11 passed**, `py_compile api/main.py` OK, and the eight bound guards **67 passed**. Branch
head `f5775304` re-measured at **14/14 check-runs success**; PR #449 is `mergeable: true`,
`mergeable_state: clean`, non-draft.

## Superseded measurements (retained, not restated)

- The pre-rebase tree `e1f5b0e0` was based on `7b672157`; it is superseded by `f5775304`.
- An earlier local attempt rebased onto `7097d6a4` (producing `972d64ed`) was discarded
  because publishing it would have required a force-push. No force-push was performed.
