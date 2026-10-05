# VERIFICATION — scheduler ↔ trajectory conformance (gate-hygiene)

Base main: `451e41a30fcbff4a65326e897a84818cc623b769`
Branch: `gate-hygiene/scheduler-trajectory-conformance-01`

## Commands and outcomes

| # | Command | Expected | Observed |
|---|---|---|---|
| 1 | `python -m pytest tests/test_scheduler_trajectory_conformance.py -q` | pass | **12 passed** |
| 2 | same, against pre-fix artifact (`git show HEAD:…`) | fail | **4 failed, 6 passed** (negative control) |
| 3 | guard with the workflow's `pull_request` block removed | fail | **1 failed** (`test_scheduler_workflow_selects_this_guard`); restored → 12 passed |
| 4 | `python -m pytest tests/test_ci_gate_trigger_coverage.py tests/test_engineering_scheduler_bootstrap.py tests/test_m08_trajectory_schema.py -q` | pass | **70 passed, 1 skipped** |
| 5 | `python -m pytest tests/architecture -q` | 11/11 | **11 passed** |
| 6 | `python -m py_compile api/main.py` | OK | **OK** |
| 7 | `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | no node-set delta | **identical fingerprint** |
| 8 | router decision on fixed trajectory | not `FAILED` | **`NO_LEGAL_MOVE`**, exit 0 |

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
