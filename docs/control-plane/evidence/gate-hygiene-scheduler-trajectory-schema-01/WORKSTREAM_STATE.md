# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/scheduler-trajectory-schema-01`
Reconstructed: 2026-10-05 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`
Stacked on PR #319 head `3d1829db87ee2e436354002842c9586e7bd58350`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, `origin/main` = `451e41a` (#317) |
| active workstream | gate-hygiene — hourly bounded-execution loop integrity |
| this pass | schema-enum refresh + stdlib-only CI-live conformance guard |
| PR | this branch (base = PR #319 branch), OPEN, pending review |
| depends on | PR #319 (`gate-hygiene/scheduler-trajectory-conformance-01`) — structural fix |
| frontier | G12-A `merged_acceptance_pending` → worker returns `NO_LEGAL_MOVE` (truthful) |

## Relationship to PR #319

PR #319 repairs the trajectory **structure** (`moves` un-nested) and adds a
structure guard. This pass repairs the **status vocabulary** the same trajectory
uses and adds a guard that reads the frozen schema. The two are complementary and
this branch is stacked on #319's head so the combined tree is what is judged.

## Defect and fix (measured)

| | pre-fix | post-fix |
|---|---|---|
| schema move-status enum | 7 statuses; missing `in_progress`, `merged`, `merged_acceptance_pending` | 10 statuses, superset |
| router vocabulary ⊆ enum | false (`in_progress`, `merged` absent) | true |
| live trajectory violations | 3 (`CONSOLE-COMPLETION-01`) | 0 |
| schema guard | `test_m08_*` skips without `jsonschema` | stdlib-only guard, cannot skip |
| guard reachability | schema enum judged by no CI gate | executed in scheduler workflow on `pull_request` + schedule |

## Next bounded task (proposed, not executed)

1. **`jsonschema` dependency** — install it (or vendor a minimal validator) so
   `tests/test_m08_trajectory_schema.py` runs instead of skipping. Separate
   dependency decision; do not fold into this pass.
2. **Other live trajectories** — the guard is parametrized over
   `docs/control-plane/TRAJECTORY-*.yaml`; a new trajectory with an out-of-enum
   status now fails CI rather than reaching `main` unjudged.

## Deterministic next-action block

- Current state: schema enum refreshed; stdlib guard added and executed in CI.
- Evidence: `EVIDENCE.md` in this directory; node-set fingerprints recorded.
- Blockers: none for this pass.
- Authorized action: sovereign review + merge of this branch (after #319).
- Forbidden: merging; deploying; installing `jsonschema` inside this pass.
- Completion condition: this branch merged, then #319, with the scheduler
  workflow green on `pull_request`.
