# WEAVER-MVP2-06 — Proposal-Only Orchestration

## Invariant

Weaver may sequence existing plan/changeset/patch artifacts into an operator proposal, but the orchestration layer cannot execute, authorize, commit, or push.

## Autonomy state

`DISABLED_PROPOSAL_ONLY`

No authorization model is invented. Autonomy remains disabled until an independently defined authorization model exists.

## Hard boundaries

- No K15/K3 call.
- No PassSpec or PatchApproval creation.
- No file mutation.
- No commit.
- No push.
- Missing artifacts remain missing.
- Human/operator action remains required.
