# Evidence — main.py line-budget restoration

Workstream: architecture / baseline-debt (own bounded workstream)
Branch: `gate07/main-py-line-budget-restore`
Base: `main` @ `e9257bf121ab205b2ea958d55b31dc0368801214`
Authority: no K15/K3, no identity, no authorization-path change. Not a merge.

## 1. Objective (bounded)

Restore `api/main.py` within its 2600-line architecture budget, repairing
`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget` — a
protected architecture fitness test — without changing any route path, response shape, or
auth behaviour.

## 2. Baseline reconstruction (live evidence)

Reconstructed from the canonical clone at `/workspace/project/Arkadia`, branch `main`,
`origin/main` = `e9257bf` (merge commit, PR #93). Recorded independent fingerprints with the
repo venv (`/workspace/project/Arkadia/.venv/bin/python`, the only interpreter with pytest):

| ref | passed | failed | skipped | errors |
|---|---|---|---|---|
| `6038989` (contract BASE_MAIN) | 804 | 54 | 12 | 0 |
| `e9257bf` (HEAD) | 842 | 51 | 12 | 2 |

- `6038989` reproduces the contract baseline **exactly** (804/54/12).
- Set-diff `6038989 → e9257bf`: **3 repaired, 0 new**:
  - `tests/test_m02a_ci_gate_integrity.py::test_trajectory_next_move_is_m02a`
  - `tests/test_weaver_mvp2_05.py::test_semantic_graph_is_read_only_and_non_authoritative`
  - `tests/test_weaver_mvp2_07.py::test_frontend_uses_existing_execution_routes_only`
  — attributable to PR #91. The +38 passed are newly added tests. **No regressions from PR #93.**
- Architecture: 11 collected, **9 passed / 2 failed at both refs** → both failures are
  pre-existing baseline debt, not causal to PR #93.

## 3. Root cause of the repaired failure

`api/main.py` grew past budget on `main` *after* the last reconciliation:

- 2598 @ `332b9d8` (2026-09-15)
- 2606 @ `f278557` (2026-09-19, Arkana thread router mount)
- 2607 @ `fe5947b` (2026-09-19) → **over budget**

Pure drift; never repaired. The block extracted was the self-contained
Phase 5-8 Jobs + Goals routes (~1994–2093) — no coupling to identity, authority, or
governance code.

## 4. Change

- **Added** `api/loop_routes.py` — the Jobs + Goals routes as an `APIRouter`, verbatim
  paths/handlers (`/api/jobs`, `/api/job/create`, `/api/job/{job_id}`,
  `/api/job/{job_id}/trace`, `/api/goals`, `/api/goals/{goal_id}`).
- **Changed** `api/main.py` — the 100-line block replaced by a composition-root mount
  (`from api.loop_routes import router as _loop_router` + `app.include_router(_loop_router)`).
  `_job_store()` / `_goal_store()` are retained in `main.py` because the spawn/CEO/metrics
  paths still reference them.

`api/main.py`: **2607 → 2512 lines** (budget 2600).

## 5. Verification (runtime evidence)

- `python -m py_compile api/main.py` → **OK**
- `python -m py_compile api/loop_routes.py` → **OK**
- `pytest tests/architecture -q` → **10 passed / 1 failed** (was 9/2).
  The only remaining failure is the pre-existing `api/nodes.py` layer inversion (§6).
  `test_api_main_line_count_within_budget` → **PASS**.
- Route registration confirmed via `app.openapi()`: all six extracted paths present,
  215 total paths.
- `pytest tests/ -q --continue-on-collection-errors` → **843 passed / 50 failed / 12 skipped / 2 errors**
  - **New failures: 0**
  - **Repaired: 1** — `test_api_main_line_count_within_budget`
  - Fingerprint otherwise identical to HEAD.

## 6. Remaining debt (NOT touched — deliberately out of scope)

`test_no_layer_inversions` still fails with 2 violations, both pre-existing:
`api/nodes.py` (Layer 3) imports `api.ais_profile` (Layer 1) and `api.lab_routes` (Layer 1),
introduced by `bb52847` (2026-08-30) and `f4dc07c` (2026-09-09) — after the 2026-08-25
CONSOLIDATION PASS 07 reconciliation.

**CONTRADICTED — do not patch around.** The fix is blocked by a direct test-vs-test
conflict: `tests/test_ais_w8_canonical_identity.py::test_w8_ais_projection_reuses_authenticated_uid`
asserts `"router.include_router(_ais_profile_router)" in api/nodes.py` — i.e. a test
*requires* the exact structure the architecture detector *forbids*. Resolving it changes an
identity-boundary test, so it needs its own bounded pass with sovereign visibility. Recorded
here as the next bounded task candidate.

## 7. Uncertainty

- The frontend `pnpm build` was not run (environment-blocked at baseline; unaffected by a
  backend-only change).
- `test_autonomy.py` and `test_render_codex.py` remain collection errors (baseline).
