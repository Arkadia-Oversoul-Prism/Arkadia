# WORKSTREAM STATE — GATE-07 router clean-stop contract

## Workstream
GATE-07 durable Weaver loop. Active sub-move: `G07-CLEAN-STOP-CONTRACT`.

## Current state (measured at base main `74e8ea53a30213db8783e6733679d2f11903de0b`)
- The worker → attention composition seam could not separate a clean stop from a
  blocked frontier: `_engineering_result_is_blocked` treated any `NO_LEGAL_MOVE` with
  blockers as blocked, and `select_next_move` supplied the clean-stop fallback *as* a
  blocker. Result: every idle hourly session was pushed as a false HIGH `WEAVER_BLOCKED`.
- Repair: named sentinel `CLEAN_STOP_BLOCKER` (router) consumed by the builder; a clean
  stop is the sentinel and nothing else.

## Evidence
- `docs/control-plane/evidence/gate07-router-clean-stop-contract-01/EVIDENCE.md`
- Full-suite failing/error node set unchanged:
  `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` (11 nodes) on both
  baseline and change. No regression.
- New guard `tests/test_router_clean_stop_contract.py` → 11 passed (with a negative
  control and a workflow-selection guard).

## Dependencies / relationship to the open batch
- PR #329 (`gate07/worker-attention-composition-guard-01`, lane 1) declares the clean
  stop quiet-path as a **strict xfail**. This PR's change makes that xfail fail (XPASS),
  proving the repair; #329's xfail must be flipped to a plain assertion before/or with
  its merge. Compose the two; do not merge #329 alone on a green xfail.
- PR #336 edits `select_next_move` (adds `dependency_blocked`) — this PR edits the
  fallback string and a new module constant only. No common hunk; conflict-free apply
  verified.
- PR #332 records the `merged_acceptance_pending` vocabulary decision (no execution);
  `ACTIVE_STATUSES` is deliberately untouched here.

## Blockers
None. No authority boundary crossed. Merge is sovereign-only.

## Next bounded task
Reconcile `merged_acceptance_pending` (schema admits it; router routes on
`ACTIVE_STATUSES` that exclude it) — coordinate with PR #332's recorded decision and
PR #336's router edit.
