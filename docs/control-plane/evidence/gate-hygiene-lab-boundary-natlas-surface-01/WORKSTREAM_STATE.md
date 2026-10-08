# WORKSTREAM_STATE — gate-hygiene/lab-boundary-natlas-surface-01

**Last update**: 2026-10-08
**BASE_MAIN**: `f96d5fd2` (== origin/main at reconstruction time)
**Branch**: `gate-hygiene/lab-boundary-natlas-surface-01`
**Status**: READY FOR SOVEREIGN MERGE (test-only)

## Current state

The Engineering Lab boundary guard (`tests/test_engineering_lab_api.py`) described the
Lab surface as it stood before PR #353. PR #353 deliberately added the N-ATLaS
external-tester surface, so two guards in that file now fail on `main` for reasons that
are not boundary violations. This branch aligns the guard with the surface that exists,
and tightens it with an explicit assertion on the anonymous Lab surface set.

## Evidence (measured this pass)

* `python -m pytest tests/test_engineering_lab_api.py -q` -> **5 passed**
  (was 3 passed / 2 failed on `main`).
* `python -m pytest tests/architecture -q` -> **11 passed** (unchanged; budget note in
  AGENTS.md says 11/11 is canonical).
* Full suite node-set delta vs `main`: **17 -> 15** nodes; the `diff` is exactly the two
  repaired nodes; zero new failures.
  * main: outcomes `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798`,
    ids `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224`.
  * branch: outcomes `d9d7c736c0f38f48a35f48ff11ed11bebb19fc59cb00c8e9215af19099cfd74e`,
    ids `5127ffedd32c32c8ac98b21da66e1c10eee8a7ec8175633826bd2d0a9b0e3ac1`.

## Baseline reconstruction (this pass)

* `main` `f96d5fd2` full suite, with `pytest-asyncio` installed per `requirements.txt`:
  **16 failed / 1770 passed / 22 skipped / 1 error** (17 nodes).
* Without `pytest-asyncio` the async node in `tests/test_natlas_developer_lab.py`
  errors; the dependency is declared in `requirements.txt` but the current CI job does
  not install it.
* `tests/fixtures/baseline_node_set.txt` records only **10** nodes; **10 of the live 17
  are absent from it**. The fixture has drifted and is not a usable baseline. Repairing
  it is a separate bounded workstream (proposed, not executed).

## Coverage map of the 17-node main baseline (who fixes what)

| nodes | file | owner |
|-------|------|-------|
| 3 | `test_m02a_ci_gate_integrity.py` | PR #354 (open, green) |
| 1 | `test_ci_gate_trigger_coverage.py[n-atlas-developer-lab.yml]` | PR #355 (open, green) |
| 1 | `test_ais_capability_profile_onboarding.py` | PR #347 (open) |
| 1 (ERROR) | `test_autonomy.py` | CE-01 module-vs-package collision — reserved (sovereign) |
| 3 | `test_steward_filter.py` | `weaver/filters/steward.py` logic — no PR yet |
| 7 | AIS/identity/ReasoMate/SolSpire governance | unrelated subsystems — no PR yet |
| 2 | `test_engineering_lab_api.py` | **this PR** |

## CI observation (PR #356, head `a05fc8f7`, 2026-10-08)

All three triggered workflows completed **success**:
`security-secret-scan`, `N-ATLAS external beta validation` (run `37723231559`),
`SG-02-FE.2-V` (run `37723231567`).

SG-02-FE.2-V step-level read (not the job conclusion):
* step 19 `CP10-A Lab tests` — `11 passed in 0.53s` (**real**, and it covers the
  repaired file: `tests/test_engineering_lab_api.py` is a trigger path);
* step 32 `CP10 mutation boundary` — `Mutation boundary PASS (M02A legitimate-surface +
  constitutional denylist)`;
* step 21 `CP10-B broader backend regression` — `Interrupted: 1 error during collection`
  (`tests/test_autonomy.py`, the CE-01 `weaver.autonomy` module-vs-package collision).
  The suite ran **zero** tests in CI. This is pre-existing `main` debt, not attributable
  to this branch.
* step 35 `Enforce CP10 executable gates` — prints `Executable CP10 gates: PASS (browser
  step outcome success)`. As AGENTS.md records, `steps.<id>.outcome` is not available
  inside a `run:` block, so this step's assertions are the literal string
  `test 'success' = success` and **cannot fail**. It is not evidence of the CP10-B
  result; step 21's log is.

The CI job does not install `pytest-asyncio` (declared in `requirements.txt`), so the
full suite is not a usable CI signal for this change. The full-suite node-set delta
recorded above is a **local** measurement.

## Dependencies / interactions

* PRs #337 and #338 (AEAS SSE transport) both edit `api/lab_routes.py` and share base
  `f96d5fd2`. If either adds a mutating Lab endpoint, it must extend
  `ALLOWED_MUTATION_ENDPOINTS` in the same change; otherwise that guard will fail on
  the composed tree. Recorded so the conflict is not discovered silently at merge time.

## Next bounded task (proposed, not executed)

* Repair `tests/fixtures/baseline_node_set.txt` so the recorded baseline is the live
  10-independent set, with a guard that re-derives it. Separate workstream.
* The 7-node AIS/identity/ReasoMate/SolSpire governance cluster and the 3
  `test_steward_filter.py` nodes need their own bounded workstreams. Not touched here.

## Authorization boundary

Human merge only. No production, governance, identity, or authority surface is touched.
