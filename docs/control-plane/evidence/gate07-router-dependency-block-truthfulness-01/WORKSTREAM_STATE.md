# WORKSTREAM STATE — gate07 router dependency-block truthfulness

- **Workstream**: GATE-07 durable Weaver loop (router observability)
- **Pass**: `gate07/router-dependency-block-truthfulness-01`
- **Trajectory**: `ARKADIA-CONSOLE-COMPLETION-01`
- **BASE_MAIN**: `17e626cd27f8ea1e31f711fb787e6c7e5027ec70` (#333)
- **Status**: IMPLEMENTED — proof complete, CI pending, sovereign merge required
- **Authority boundary**: no merge, no deploy, no gate promotion, no vocabulary repair

## Defect

`select_next_move` reported only the moves it could not route because their **status** was
unrecognized. A move whose status is legal but whose **dependency is unmet** was dropped, and
the fallback `no legal pending move (all complete or dependencies unresolved)` spoke for it.

On `docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml`, `G12-B` is the sole `in_progress`
move and depends on `G12-A`. It never appeared in the session blockers. The fallback also fused
"blocked frontier" and "trajectory complete" into one phrase, so the two were indistinguishable.

## Change

- `weaver/engineering_router.py` — `select_next_move` tracks dependency-blocked frontier moves
  (id, dependency id, dependency status) and emits a `dependency-blocked frontier: …` blocker.
  The `unrecognized move status` blocker and the fallback are unchanged.
- 5 guard tests, including a dependency-cycle case chosen so no `unrecognized` blocker can mask
  the assertion, and a positive control that a routable frontier is not reported as blocked.

## Evidence

`docs/control-plane/evidence/gate07-router-dependency-block-truthfulness-01/EVIDENCE.md`

## Proof

- `tests/test_engineering_router_status_truthfulness.py`: 14 passed (+5)
- router/scheduler/schema/bootstrap guard set: 49 passed
- `tests/architecture`: 11 passed
- full suite: failing/error node set identical to main
  (`f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48`), passed +5
- non-vacuity: 3 failed with the pre-fix router restored
- CP10 mutation-boundary judge: PASS

## Open frontier (reported, not repaired)

`merged_acceptance_pending` (on `G12-A`/`G12-C`) still has no router meaning. Closing it is a
**sovereign vocabulary decision** — tracked by PR #332, pinned by PR #334. This pass reports the
blocked chain either way; it does not close the vocabulary seam and does not unblock G12-B.

## Next bounded task (proposed, not executed)

`gate07/router-dependency-block-surface-01` — have the router emit the blocked frontier as a
structured field (`blocked_frontier: [{move, depends_on, status}]`) alongside the prose blocker,
so a consumer need not parse operator-facing text. Composes with #335 (which prints `blockers`).
Blocked on nothing; not started.

## Deterministic next-action block

- **Current state**: branch `gate07/router-dependency-block-truthfulness-01` from `17e626cd`,
  working tree contains the router reporting fix, 5 guard tests, and this evidence.
- **Evidence**: the table above; live CLI output for both trajectories.
- **Blockers**: none for this pass. Sovereign merge is the only gate.
- **Authorized action**: open PR; sovereign review.
- **Forbidden actions**: merge, deploy, promote gate, edit trajectory statuses, edit
  `ACTIVE_STATUSES`/`TERMINAL_DONE`.
- **Completion condition**: PR open, CI green, `dependency-blocked frontier` named in the
  session result for the console trajectory.
