# WORKSTREAM STATE — gate07/router-schema-vocabulary-closure-01

Trajectory: `ARKADIA-CONSOLE-COMPLETION-01`
Move class: bounded engineering guard (enforcement half of the router/schema seam)
PR: #334
Branch: `gate07/router-schema-vocabulary-closure`
Base: `main` @ `17e626cd27f8ea1e31f711fb787e6c7e5027ec70`
Head: `b4ca6dd`

## Current state

IMPLEMENTED → **VERIFIED locally, CI-observed**. The reverse seam (`schema ⊆ router`) is now
asserted, and the guard executed in CI on the PR head
(`mvp2-validation`, run `37523684594`, step "Engineering-router status truthfulness guard",
**39 passed in 0.45s** — matching local).

Not merged. Not promoted. No authority change.

## Evidence

- `docs/control-plane/evidence/gate07-router-schema-vocabulary-closure-01/EVIDENCE.md`
- Guard: `tests/test_router_schema_vocabulary_closure.py` (17 passed)
- Non-vacuity: 7 assertions fail against the pre-fix silent-skip router; router restored
  byte-identical (`c355b387c2f3b315cd0564357f4f097da3861043d8f92d34c6bfa7b4be94ac1d`)

## Relationship to adjacent work

- **PR #332** (`gate07/trajectory-status-vocabulary-decision-01`) — the **decision record** for
  the same seam; docs-only, explicitly no execution. This move is its **enforcement** half and
  does not duplicate it: #332 chooses *whether* to close the vocabulary (sovereign), #334 keeps
  the seam *observed* either way. Not merged together; neither mutates the other.
- **PR #322** (`gate07/router-status-truthfulness-01`) — predecessor; made the silent skip
  nameable. This guard keeps it named. Supersedes its `merged_acceptance_pending`-absent note
  (true at base `451e41a`, false after schema refresh `e611edd`).

## Blocker / boundary

Sovereign review and merge. Closing the four unroutable statuses (`aborted`, `blocked`,
`failed`, `merged_acceptance_pending`) is **sovereign** — recorded, not repaired.

## Next bounded task (for the next heartbeat — reconstruct, do not assume)

None selected. Candidate queue, in preference order:

1. Observe PR #334 CI to completion; if the `Vercel – console` failure is the only red, classify
   it pre-existing (measured failure on `main` @ `17e626c`) and leave it.
2. If the sovereign decides the vocabulary question in #332, the follow-on (teaching the router
   the chosen states, or repairing trajectory data) becomes its own bounded move — do not begin
   it inside #334.
3. Otherwise re-derive the active gate/frontier from `TRAJECTORY-CONSOLE-COMPLETION-01.yaml`
   rather than from this file.

## Pre-existing debt (not attributable to this move)

- `Vercel – console` = **failure on `main` @ `17e626c`** (commit status). Not caused by #334.
- Full suite: 10 failed / 1 error, node set identical to `main`
  (`sha256 fdc792071b6b4af45ea91782de08992605a04b40ed62ce9d00b771cdf2843cb1`, 11 nodes).
