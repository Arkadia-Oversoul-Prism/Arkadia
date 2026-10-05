# WORKSTREAM STATE — architecture/main-line-budget-restoration-01

## Current state
`api/main.py` exceeds its 2600-line architecture budget on `main` @ `4550531`, so
`test_api_main_line_count_within_budget` fails on `main`. This branch restores the
budget by extracting the Arkana Signal route handlers verbatim into
`api/arkana_signal_routes.py`.

Status: **IMPLEMENTED / VERIFIED (repository evidence)** — awaiting sovereign review.

## Evidence
* `docs/control-plane/evidence/architecture-main-line-budget-restoration-01/EVIDENCE.md`
* Failure node-set delta: 1 fixed, 0 introduced (sha256 recorded in EVIDENCE §5).

## Next authorized action
Sovereign review + merge of this PR. No merge performed by the agent.

## Blockers / dependent workstreams
1. `arch/arkana-signal-gate-02-runtime` (#293) alone is **2719** lines — over budget.
   Composed with this extraction it is **2683** — still over budget. A further
   reduction (~83 lines) is required before the composed tree passes the gate.
2. #293 @ `2d0970a` carries a **SyntaxError** in `api/main.py` (literal `\n` escapes
   pasted into a hunk; P1-A boot-break class). Separate proposed workstream.

## Forbidden actions
Merge; self-authorization; scope expansion; repairing #293 inside this PR.
