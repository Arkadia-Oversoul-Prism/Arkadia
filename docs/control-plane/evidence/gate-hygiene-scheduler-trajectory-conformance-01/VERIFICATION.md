# VERIFICATION — scheduler ↔ trajectory conformance (gate-hygiene)

Base main: `451e41a30fcbff4a65326e897a84818cc623b769`
Branch: `gate-hygiene/scheduler-trajectory-conformance-01`

## Commands and outcomes

| # | Command | Expected | Observed |
|---|---|---|---|
| 1 | `python -m pytest tests/test_scheduler_trajectory_conformance.py -q` | pass | **16 passed** |
| 2 | same, against pre-fix artifact (`git show 451e41a:…`) | fail | **4 failed, 12 passed** (negative control) |
| 3 | guard with the workflow's `pull_request` block removed | fail | **1 failed** (`test_scheduler_workflow_selects_this_guard`); restored → 16 passed |
| 4 | `python -m pytest tests/test_ci_gate_trigger_coverage.py tests/test_engineering_scheduler_bootstrap.py tests/test_m08_trajectory_schema.py -q` | pass | **74 passed, 1 skipped** |
| 5 | `python -m pytest tests/architecture -q` | 11/11 | **11 passed** |
| 6 | `python -m py_compile api/main.py` | OK | **OK** (2432 lines, unchanged) |
| 7 | `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | no node-set delta | **identical fingerprint** (117 nodes both sides) |
| 8 | router decision on fixed trajectory | not `FAILED` | **`NO_LEGAL_MOVE`**, exit 0 |
| 9 | collected-node diff, `main` vs branch | +16 guard | **+19** — the 16 guard nodes **plus 3** |

### Item 4 corrected (measurement supersedes the earlier figures)

Item 4 was recorded as **70 passed, 1 skipped** and then **58 passed, 1 skipped**; re-measured
in this environment the group is **74 passed, 1 skipped** (75 collected). The earlier figures
did not reproduce and are superseded by this measurement. Per file on the branch:
`tests/test_ci_gate_trigger_coverage.py` **42 passed** (39 on `main`),
`tests/test_engineering_scheduler_bootstrap.py` **13 passed**,
`tests/test_m08_trajectory_schema.py` **3 passed, 1 skipped**.

### Item 9 — the CI-live change also extended a pre-existing guard (+3 nodes)

The new `pull_request` trigger made the scheduler workflow visible to the pre-existing
generalised guard `tests/test_ci_gate_trigger_coverage.py`, which parametrizes over every
workflow that runs pytest. Three new parametrizations are collected for
`arkadia-engineering-scheduler.yml`, and all three pass:

```
tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[arkadia-engineering-scheduler.yml]   PASSED
tests/test_ci_gate_trigger_coverage.py::test_architecture_fitness_is_selected_by_the_surfaces_it_judges[arkadia-engineering-scheduler.yml]   PASSED
tests/test_ci_gate_trigger_coverage.py::test_push_and_pull_request_filters_are_identical[arkadia-engineering-scheduler.yml]   PASSED
```

So the scheduler is now judged by a guard this workstream did not author, on top of its own
guard. `tests/architecture` is **not** run by this workflow, so
`test_architecture_fitness_is_selected_by_the_surfaces_it_judges` correctly does not require
a `tests/architecture/**` path — that surface is covered by `provider-routing.yml`.

## Fingerprints

```
main 451e41a : outcomes f33d69dfbc1d91761e94fe469ea0da02565d9670222989aaec97457d634f2169
               ids      6dde9f16eccab26056bad272120080e625d3f85f4a7c3df19659f194857dfd17
branch       : outcomes f33d69dfbc1d91761e94fe469ea0da02565d9670222989aaec97457d634f2169
               ids      6dde9f16eccab26056bad272120080e625d3f85f4a7c3df19659f194857dfd17
```

Node-set delta: `only in main: []`, `only in branch: []` → **zero regression**.

## Preconditions checked

- Clone on `main`, remote `origin` = canonical repo, `origin/main` = `451e41a` (real commit).
- Working tree: only the intended change + the new test + a generated
  `docs/control-plane/evidence/attention-events.jsonl` (untracked runtime output of
  `weaver/attention_bus.py`; **not committed** — no history, not a tracked convention).
- Scheduler workflow permissions: `contents: read`, `actions: read` — no self-merge path.
- `api/main.py` untouched; boot-code compile verified.

## Classification

**VERIFIED** (repository-source). Merge and deploy remain human-only. No runtime/production
observation is claimed.
