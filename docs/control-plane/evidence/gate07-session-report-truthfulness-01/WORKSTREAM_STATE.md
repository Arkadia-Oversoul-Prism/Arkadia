# WORKSTREAM STATE — gate07 session report truthfulness

- **Workstream**: GATE-07 durable Weaver loop (scheduler observability)
- **Pass**: `gate07/scheduler-session-report-truthfulness-01`
- **Trajectory**: `ARKADIA-CONSOLE-COMPLETION-01`
- **BASE_MAIN**: `17e626cd27f8ea1e31f711fb787e6c7e5027ec70` (#333)
- **Status**: IMPLEMENTED — proof complete, CI pending, sovereign merge required
- **Authority boundary**: no merge, no deploy, no gate promotion, no vocabulary repair

## Defect

The hourly session report printed `Status`/`Move` but not the router's `blockers`. Run
37523927861 stopped `NO_LEGAL_MOVE` while its session result named two unroutable frontier moves
(`G12-A`, `G12-C` — status `merged_acceptance_pending`). With attention delivery unconfigured, the
run log is the only human-readable artifact, so a live frontier read as "nothing to do".

## Change

- `Session report` step now reads `engineering-session-result.json` and prints `Blockers:`, or
  `Blockers: (session result unavailable)` when the runner step was skipped (pull_request).
- 4 guard tests, including a negative control fed the literal pre-fix report body.

## Evidence

`docs/control-plane/evidence/gate07-session-report-truthfulness-01/EVIDENCE.md`

## Proof

- `tests/test_scheduler_trajectory_conformance.py`: 20 passed (+4)
- scheduler/attention/router guard set: 61 passed
- `tests/architecture`: 11 passed
- full suite: failing/error node set identical to main
  (`f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48`), passed +4
- non-vacuity: 3 failed with the pre-fix report step restored

## Open frontier (reported, not repaired)

Four trajectory statuses have no router meaning: `aborted`, `blocked`, `failed`,
`merged_acceptance_pending`. The last two occur on `G12-A`/`G12-C` of the live trajectory. Repair
is a **sovereign vocabulary decision** — tracked by PR #332
(`trajectory-status-vocabulary-decision-01`) and pinned by PR #334
(`router-schema-vocabulary-closure-01`). This pass reports the seam; it does not close it.

## Next bounded task (proposed, not executed)

`gate07/scheduler-report-status-surface-01` — have the report name the unroutable moves by id and
status on their own line, so the log is actionable without opening the JSON artifact. Blocked on
the vocabulary decision only if the decision changes the status names.

## Deterministic next-action block

- **Current state**: branch `gate07/scheduler-session-report-truthfulness-01` from `17e626cd`,
  working tree contains the report-step fix, 4 guard tests, and this evidence.
- **Evidence**: the table above; live defect run 37523927861.
- **Blockers**: none for this pass. Sovereign merge is the only gate.
- **Authorized action**: open PR; sovereign review.
- **Forbidden actions**: merge, deploy, promote gate, edit trajectory statuses, edit `weaver/`
  router semantics.
- **Completion condition**: PR open, CI green, `Session report` naming blockers on a scheduled run.
