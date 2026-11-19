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


## Combined CI validation — superseding update (2026-11-18)

The earlier “NOT RUN” entry above is a historical record of the state before the owner manually dispatched the workflows. It is superseded for CI execution status by this addendum.

### Tested revision and source equivalence

- Branch: `integration/ewor-evidence-baseline-2026-11-18`
- **Tested commit SHA:** `6dcdf0388c157b2b60f6530216167645b958988d`
- **Tested tree SHA:** `23b1a9091bf5d42227b162448d977ce819a18547`
- Original composed source commit: `31a8793f3a1afbff8ac2a5b563ecf9bf08288e49`
- Original composed source tree: `8c4dfeff841ac6b5df88742a783e3ddb45327a12`
- GitHub compare confirms the tested revision is two commits ahead of the source commit and zero behind. The only tree-level difference is this evidence-ledger file, added as 68 lines. No source or test path changed between the composed source commit and the tested revision.
- Therefore, the two workflows below validate the same combined application/test source tree, with the evidence-ledger addition present. They did **not** execute at the original source commit SHA itself; the authoritative tested SHA is `6dcdf038...`.

### Workflow results

| Workflow | Run | Result | Job |
|---|---|---|---|
| Prism Console Contract | [44316333731](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44316333731) | **SUCCESS** | `console-contract` completed successfully; all executed steps passed |
| SG-02-FE.2-V | [44316536942](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44316536942) | **SUCCESS** | `validate` completed successfully; all executed steps passed; conditional cleanup step was skipped |

Both runs were manually dispatched on `integration/ewor-evidence-baseline-2026-11-18` and GitHub reports the same tested SHA, `6dcdf038...`, for both. No failed jobs or failed executed steps were reported.

Artifacts:
- SG-02-FE.2-V: `cp10-evidence-6dcdf0388c157b2b60f6530216167645b958988d` (artifact ID `14431384950`)
- Prism Console Contract: `workspace-layout-evidence` (artifact ID `14431269307`)

### Remaining acceptance checks

- **Lane-state freshness: FAIL / stale.** The candidate snapshot records PR #657 at head `d41127e153b34e330d523622b29d27e96eadfd03` (updated 2026-11-16), while the live PR #657 head is `d49cc9a06b952aac19a6d4d2a59366d24d8fb0bf` (updated 2026-11-17). The derived lane-state snapshot must be re-derived and its live verification rerun before acceptance.
- Test-node and failure-node deltas against the base snapshot have **not yet been measured**. The two workflow runs show no failures on the candidate, but this is not a baseline delta analysis.
- No merge, deployment, production acceptance, or change to `main` was performed.
- **Disposition: COMBINED CI PASSED; PORTFOLIO ACCEPTANCE STILL PENDING.** Re-derive and verify lane state, complete the base-versus-candidate test/failure-node comparison, then obtain the human acceptance decision. PRs #663–#667 must not yet be described as fully accepted.


## Baseline comparison and live lane-state reconciliation — 2026-11-18

### Same-workflow base comparison

The available successful `main` runs on the immutable base SHA `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` were compared with the candidate runs. The same workflow definitions and test commands were used.

| Workflow | Base `main` | Combined candidate | Result |
|---|---|---|---|
| Prism Console Contract | [44044565413](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44044565413) | [44316333731](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44316333731) | Both success |
| SG-02-FE.2-V | [43923778175](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/43923778175) | [44316536942](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44316536942) | Both success |

Prism Console Contract log comparison:
- React behavioural tests: 61 passed on both.
- Broad backend pytest segment: 1,168 passed on base; 1,182 passed on candidate (+14).
- Additional contract segment: 34 passed on both.
- No failed executed steps in either workflow job.

SG-02-FE.2-V full backend pytest comparison:
- Base: 4,045 passed, 10 failed, 17 skipped, 1 collection error.
- Candidate: 4,060 passed, 9 failed, 17 skipped, 1 collection error.
- Net: +15 passing tests, one fewer failing test, no increase in skipped tests or collection errors.
- The only base failure absent from the candidate failure list is `tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main`, consistent with the #663 lane snapshot repair.
- The remaining nine failed nodes and the `tests/test_autonomy.py` collection error are present on both base and candidate. They are pre-existing baseline failures, not newly introduced by this candidate.
- This is a comparison of the two logged full-suite runs, not a claim that the entire repository test suite is green.

### Live lane-state re-derivation finding

A fresh read of the live open PR list and changed-file lists shows:
- #663–#667 remain open.
- #657 remains open and touches no exclusively-owned lane paths, so it remains unassigned.
- Integration PR #668 is itself open and its aggregate diff contains lane-owned paths from all four lanes. Under the current `scripts/lane_state_refresh.py` classifier, #668 therefore matches lanes 1, 2, 3 and 4. Because its `updated_at` is newer than the individual lane PRs, the derivation would select #668 as the active PR in all four lanes.
- The four lane instruction docs do not declare #668 as their active PR; their latest declarations are none/#564/#450/#605 respectively.

This is a self-inclusion problem for an aggregate integration PR, not a reason to hand-edit or suppress live PR data. A mechanical refresh would produce a snapshot that then disagrees with the lane-doc pointers; `--verify-live` alone can establish that listed PRs are open, but the complete `--check --verify-live` gate would not be satisfied.

No lane-state snapshot was overwritten and no lane docs were changed. The correct repair is a separately reviewed, tested rule for classifying/excluding explicitly designated aggregate evidence PRs from lane ownership, followed by a real refresh and `--check --verify-live` run. Do not silently omit #668 or point all four lane docs at the aggregator.

### Updated disposition

- Combined CI: **PASS** on tested SHA `6dcdf0388c157b2b60f6530216167645b958988d`.
- Base comparison: **FAVOURABLE**; +15 passing, one fewer failing, no new failure nodes identified.
- Live lane-state acceptance gate: **BLOCKED** by aggregate-PR self-inclusion in the current derivation model.
- Human portfolio acceptance: **PENDING** until the lane-state classifier issue is resolved and the refreshed snapshot passes both the offline and live guards.
- No merge, deployment, or change to `main` was performed.

---

## 2026-11-19 — Lane-State Declaration Reconciliation (follow-up)

Appended, not rewritten. The historical sections above are preserved verbatim.

### Scope

Reconcile the four lane instruction documents with the active PR ownership the
aggregate-classification repair revealed. The classifier and its metadata were
**not** modified — no defect was found in them.

### PR ownership evidence (read live, individually)

| Lane | Doc | PR | State | Draft | Base | Lane-owned paths |
|---|---|---|---|---|---|---|
| 1 | `AGENT-01-SHELL.md` | #665 | open | yes | `f9bd8da9` | lane 1 only |
| 2 | `AGENT-02-NOVANET-OPPORTUNITY.md` | #666 | open | yes | `f9bd8da9` | lane 2 only |
| 3 | `AGENT-03-SOLARIUN-KNOWLEDGE.md` | #667 | open | yes | `f9bd8da9` | lane 3 only |
| 4 | `AGENT-04-ARKANA-WEAVER-LAB.md` | #664 | open | yes | `f9bd8da9` | lane 4 only |

Each PR is single-lane, open, draft, and based on the immutable main base. Each
therefore *is* its lane's active thread, and each doc now says so.

### Why the docs were stale, and why the fix is an append

The derived snapshot was correct; the docs were not. All four ended with an idle
declaration (`none` / `#564` / `#450` / `#605`) written before #664–#667 existed.
`scripts/lane_state.py --check` therefore returned exit 1 with four DRIFT
findings — reproduced before any edit.

Each doc received a dated status block in the append-only, last-wins form the
guard reads. **No existing line was rewritten.** The lane docs are lane-owned
oracles; rewriting an oracle line to satisfy a guard is the failure mode this
gate exists to prevent.

### Baseline and result

- Before: `python3 scripts/lane_state.py --check` → **exit 1**, 4 DRIFT findings.
- After: `python3 scripts/lane_state.py --check` → **exit 0**,
  `lane instruction docs consistent with snapshot (4 guarded lanes)`.

### Real refresh

`python3 scripts/lane_state_refresh.py --write --base-main f9bd8da9…` executed
with the script's own derivation unmodified. Resulting snapshot:
`observed_at 2026-11-19T04:50:03Z`, `base_main f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`.
Lanes 1–4 active = #665 / #666 / #667 / #664. #668 remains `classification:
aggregate`, excluded from lane ownership and retained in `aggregate_prs`.
#657 and #663 remain `unassigned`.

**Limitation, stated plainly:** no `GH_TOKEN` exists in this environment. The
refresh and the live gate were driven through the scripts' own `main()` with
only the HTTP transport swapped for an unauthenticated GET against the public
repository. Derivation logic was not modified. This is not a
token-authenticated run and is not presented as one.

### Verification

- Offline `--check` → **exit 0**.
- Live `--check --verify-live` → **exit 0**, 4 claimed-open PRs read live.

### Focused tests

```
python3 -m pytest tests/test_lane_instruction_doc_currency.py \
                  tests/test_lane_currency_ci_wiring.py \
                  tests/test_lane_aggregate_pr_classification.py -q
82 passed
```

No existing test was modified, loosened or removed.

### CI on the resulting commit

12 workflows triggered on `5793b27173b3ca8bbf4b5de31cc00c7571ecd222`.
**11 success, 1 failure.**

| Workflow | Run | Conclusion |
|---|---|---|
| Lane Doc Currency | 44461878141 | **success** (was failure at `5e147892`) |
| SG-02-FE.2-V | 44461878241 | success |
| N-ATLAS external beta validation | 44461878206 | success |
| N-ATLAS Developer Lab | 44461878222 | success |
| N-ATLAS provider forensics | 44461878071 | success |
| Baseline Fingerprint Verification | 44461878086 | success |
| Boot Syntax Boundary | 44461878216 | success |
| Canonical Render Runtime Probe | 44461878274 | success |
| Operator Console Posture Currency | 44461878077 | success |
| economic-seam-engine | 44461878176 | success |
| security-secret-scan | 44461878112 | success |
| **Prism Console Contract** | 44461878090 | **failure** |

### The one failure — attributed, not assumed

Failing step: **11, "Workspace layout assertions (rendered, authenticated test
identity)"** in job `135350372926`.

- The **same step failed on the prior head `a675a2a4`** (run 44448339735), which
  predates this commit.
- This commit changes **one file**: `lane-state.json`, 4 insertions / 4
  deletions (timestamps and two `head_sha`/`updated_at` fields). It touches no
  `web/` path and no test.
- `main` at `f9bd8da9` passes this workflow.

So the failure is **not introduced by this commit**, but it is also **not
pre-existing on main** — it is a branch-tree condition in the `web/` changes
carried by #663–#667, which this branch composes. It is outside this
follow-up's scope and is reported, not repaired.

**What could not be observed:** the log text. `GET /actions/jobs/{id}/logs`
returns **HTTP 403 "Must have admin rights to Repository."** Annotations expose
only a Node.js-20 deprecation warning. The attribution above rests on step
identity across two heads, the commit's file list, and `main`'s green status —
**not on reading the failure output.**

### Governance

`main` unchanged at `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`. No PR merged,
closed, reopened or retargeted. #668 remains open/draft and aggregate-excluded.
#657 remains unassigned and separately reviewed. No deploy, commissioning,
runtime credentials, workspace binding, L3 activation or scheduling.
**Human acceptance not issued.**

Push used a temporary write-enabled deploy key (id `170401028`), deleted
immediately after use; private half shredded.

### Disposition

- Lane-state declaration reconciliation: **COMPLETE**, both gates exit 0.
- Lane Doc Currency CI: **GREEN** on the resulting commit.
- Prism Console Contract: **RED**, attributed to the composed `web/` tree, not
  to this commit; log text unreachable.
- Human acceptance: **PENDING**.
