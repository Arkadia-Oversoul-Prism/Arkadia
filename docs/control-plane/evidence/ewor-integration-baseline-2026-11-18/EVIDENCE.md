# EWOR Integration Evidence Baseline — 2026-11-18

## Purpose and separation

This is a separate integration candidate. It does not alter or replace the verified `main` snapshot and must not be retroactively counted as part of that audit.

## Immutable source baseline

- Repository: `Arkadia-Oversoul-Prism/Arkadia`
- Base branch: `main`
- Base SHA: `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`
- Integration candidate commit before this ledger: `31a8793f3a1afbff8ac2a5b563ecf9bf08288e49`
- Integration branch: `integration/ewor-evidence-baseline-2026-11-18`
- Composition: exact changed-file blobs from PR heads #663–#667 overlaid on the base tree; no source changes from #657 included.
- Resulting scope: 17 changed paths (4 evidence records, 1 derived lane-state snapshot, 4 test files, 8 console source/contract files).

## Included contribution records

| PR | Contribution | Per-PR checks at composition | Scope |
|---|---|---:|---|
| #663 | Re-derive lane-state snapshot after merged #659 doc change | 7/7 green | Derived state + evidence; no authority/source surface |
| #664 | Disclose bounded Engineering Lab output truncation | 16/16 green | Lane 4 UI/helper/test/evidence |
| #665 | Bind title-writer sweep test to its detector | 10/10 green | Lane 1 test/evidence |
| #666 | Show opportunity evidence-record count alongside status | 16/16 green | Lane 2 UI/contract/test |
| #667 | Disclose Knowledge Graph provenance row cap | 16/16 green | Lane 3 UI/contract/test/evidence |

Per-PR check results are recorded observations from the individual PR heads. They are not a substitute for tests on this combined tree.

## Excluded contribution

- PR #657 (Chief Agent founding scaffold) is intentionally excluded from this baseline. It is a broad 53-file / +9,707-line change touching executive identity, token/authority, revocation, Lab runtime, API composition and Weaver authorization. Its head is based on an older base revision, and two checks were failing at inspection (native golden workflow and console contract). It requires a separate security, governance and compatibility review against current GOV-03. Exclusion is not rejection or deletion; the PR remains open and preserved.

## Composition checks and limitations

- Changed-path overlap among #663–#667: none.
- Combined tree was assembled as one commit parented directly to the immutable base SHA above.
- The combined commit tree was read back and compared with the base; it is one commit ahead, zero commits behind, with exactly the 17 listed paths changed.
- No combined CI run is recorded yet at the time this ledger was authored. A combined run is required before any contribution is described as accepted in the final portfolio.
- No merge, deployment, production acceptance or change to `main` was performed.

## Acceptance gates

1. Run the full relevant CI suite against this exact combined tree.
2. Inspect any failures as integration failures, not as proof that an individual PR is defective.
3. Confirm the derived lane-state snapshot remains current against live PR state at the point of final validation.
4. Reconcile test-node deltas and failure-node deltas against the base.
5. Record the final tested SHA, CI run links, and a human acceptance decision.
6. Keep GOV-03 in force: merge execution remains human-only.

## Portfolio treatment

Until the acceptance gates pass, present:
- **Verified product snapshot:** `main` at `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`.
- **Additional engineering contributions:** PRs #663–#667, individually green and composed into this separately tracked candidate, pending combined validation.
- **Separate high-risk workstream:** PR #657, preserved and under independent review.

Do not collapse these three evidence classes into one maturity claim.


## Combined CI validation attempt — 2026-11-18

- Branch head inspected: `f70483dd4d133d37b417f8838691668376f30853` (ledger commit; parent is the composed source commit `31a8793f3a1afbff8ac2a5b563ecf9bf08288e49`).
- Exact candidate source commit: `31a8793f3a1afbff8ac2a5b563ecf9bf08288e49`; candidate tree: `8c4dfeff841ac6b5df88742a783e3ddb45327a12`.
- Relevant workflow inspection: `Prism Console Contract` is path-filtered for PR events and supports `workflow_dispatch`; `SG-02-FE.2-V` is path-filtered for PR/push and supports `workflow_dispatch`. The Engineering Scheduler workflow supports PR and `workflow_dispatch`, but its PR path filter does not match this candidate's changed paths.
- Execution result: **NOT RUN**. The connected GitHub actions interface available in this session exposes workflow-run inspection and rerun operations, but no workflow-dispatch operation. The repository fetch interface is read-only for workflow endpoints. No synthetic PR, branch push, or other trigger workaround was created.
- CI run IDs/links: none. Combined test result: none. Failure-node delta: not measured. This is not a passing or failing test result.
- Disposition: **NOT ACCEPTED** for the EWOR portfolio pending combined CI execution on the exact candidate commit/tree, failure inspection, lane-state freshness check, and human acceptance.
- Portfolio remains split: verified `main` snapshot at `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`; additional PR #663–#667 contributions remain individually green but combined-validation-pending.
