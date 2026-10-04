# WORKSTREAM STATE — gate10/boundary-contradiction-01

**Reconstructed at:** 2026-10-04, `main` = `357fbd83001924e909979fbaebdedbd991a2aadb`
**Branch:** `gate10/boundary-contradiction-01`
**Status:** CONTRADICTED — sovereign adjudication required

## Current state (live evidence)

- `main` HEAD `357fbd8` (Merge PR #244). Worktree clean before this branch.
- Open PRs at reconstruction: #243, #245, #246, #247, #248, #249, #250, #251.
- Architecture: 11/11. `api/main.py` 2582 / 2600 lines.
- Baseline node set on `main`: **29 nodes** (28 failed, 1 error);
  outcomes `5745314330ce11df9ee8c06986c506ac71a5883e4c2ff1f0a4902400e971bef6`.

## The open contradiction

`solspire/console_authority_router.py` (introduced `c052cee`, mounted `69a1c37`,
both in PR #234 `049abef`) exposes:

- `POST /solspire/authority/executions/{execution_id}/evidence` → `store.evidence(...)`
- `POST /solspire/authority/verification` → `store.verify(...)`

`RECONCILED-BOUNDARY-MAP-01.md` (Gate-03 §6.9, Gate-04 §6.10) records those
surfaces as **unexposed** ("no route creates or lists evidence or verification").
Two boundary tests assert exactly that and now fail. See `EVIDENCE.md` §3.

**Both dispositions are sovereign:**
(A) amend the boundary records + tests to admit the authorized Console surface;
(B) treat the routes as un-reconciled expansion and remove/reduce them.

## Do NOT do

- Do not repair the two evidence/verification boundary tests in a "test hygiene"
  pass — that presumes disposition (A).
- Do not merge PR #249 on the Phase 1 classification while this is open.
- Do not touch `weaver/autonomy` (sovereign-reserved), `AGENTS.md` oracle lines,
  or `REGISTERED_ARCHITECTURAL_DEBT`.

## Safe, non-blocked workstreams (separate bounded branches)

1. `test-hygiene/frontend-literal-pins-01` — PR #251 open.
2. `test-hygiene/review-route-boundary-false-positive-01` — PR #249 open; correct
   for the review/preview node only.
3. `gate-hygiene/weaver-echofield-resolver-import-repair-01` — PR #250 open;
   `provider-routing` failure is the pre-existing `test_autonomy.py` collection
   error, not a regression.
4. `gate-hygiene/baseline-node-set-reconciliation-02` — refresh the stale 18-entry
   fixture (stale entries + 11 unrecorded nodes).
5. `gate10/console-authority-route-authority-gate-01` — **conditional on
   disposition (A)**: the `/evidence` and `/verification` handlers enforce
   authentication only, not `Govern` authority; `/verification` defaults
   `verifier="human-console"`. If the routes are authorized, the authority gate
   should match `/proposals/{id}/authorize`'s requirement.

## Next action

Sovereign ruling on §3 (A) or (B). Re-entry condition: a recorded ruling in this
directory. Until then this workstream is held; unrelated safe workstreams above
may proceed.
