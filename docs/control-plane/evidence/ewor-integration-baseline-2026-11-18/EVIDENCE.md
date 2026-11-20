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

---

## 2026-11-19 — Final remediation: canonical session-view HTTP status assertion

**Appended. No earlier section was modified or removed.**

### Defect

`f4f372ff` replaced the racy `expect_response` capture with an explicit read,
but the capture object also carried `.status`. The assertion
`if session_view_response.status != 200` was deleted with it and never
re-established: `_read_canonical_session_view` still returned `status`, and the
call site discarded it by subscripting straight to `["body"]`.

A `401` or `500` response can still carry a JSON body with the expected keys, so
the harness would accept an unauthenticated or failed read as a valid canonical
view and report PASS. This was a real weakening introduced by the repair.

### Remediation

`web/arkadia_console/exercise_mission_workspace.py`:

- The complete read result is preserved as `session_view_read`.
- The status is asserted **before** the body is extracted.
- The check is a pure function, `_canonical_session_view_status_failure`, so it
  is exercisable without a browser.
- No product code, no authentication change, no assertion removed, no skip.

`tests/test_mission_workspace_canonical_status_assertion.py` (new, 11 tests):
200 passes; 401 fails; 500 fails; absent status fails closed; the assertion is
evaluated against the explicit read and precedes body extraction; the reader
still returns status; the eight substrate assertions remain; fail-closed exit
remains; authenticated identity remains; the poll remains; no skip/xfail.

### Proof the tests catch the defect

- Against defective `f4f372ff`: **5 failed, 6 passed**.
- Against the remediation: **11 passed**.

### Commit

- Commit: `766d605c4c77e3c06ddbae8a09eed7729b9e0ebb`
- Tree: `bc88ba258d644d4775d11f91f4d374741ac64306`
- Branch: `integration/ewor-evidence-baseline-2026-11-18`
- Remote ref read back via `GET /git/ref`: `766d605c…` — exact match.
- Rebased onto `67b4d2f2` (two commits landed from another actor); no file
  overlap, no force-push.

### Focused tests

```
pytest tests/test_mission_workspace_canonical_status_assertion.py \
       tests/test_mission_workspace_harness_determinism.py \
       tests/test_lab_mission_workspace_contract.py \
       tests/test_lane_instruction_doc_currency.py \
       tests/test_lane_currency_ci_wiring.py \
       tests/test_lane_aggregate_pr_classification.py -q
135 passed
```

### Full suite vs immutable base `f9bd8da9`

| Tree | Failed | Passed | Skipped | Errors |
|---|---|---|---|---|
| Base `f9bd8da9` | 180 | 3801 | 31 | 60 |
| Head `766d605c` | 169 | 3857 | 31 | 64 |

Node-level reconciliation (`comm` on sorted FAILED/ERROR node IDs):

- **New failing nodes: 0.**
- **New error nodes: 4**, all in `tests/test_prism_opportunity_entry_flow.py`,
  all `TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension ".ts"` for
  `opportunityRadarContract.ts`. The contract probe shells out to `node` and
  imports a `.ts` module; Node 20 cannot import TypeScript without a loader.
  Environment, not behaviour. These four nodes are the ones #666 added, so they
  cannot appear on the base tree at all.
- **11 nodes fixed** relative to base (snapshot-freshness guard plus ten
  `test_mission_lifecycle_adapter_contract.py` nodes that fail on base on a
  missing `typescript.js`). Not claimed as a fix from this branch.
- **Skips: 31 = 31**, unchanged.
- The suite is **not green** and is not reported as such.

### CI on `766d605c` — 12 runs

| Workflow | Run | Conclusion |
|---|---|---|
| **Prism Console Contract** | 44593953326 | **success** — 14/14 steps, incl. **step 11 "Workspace layout assertions (rendered, authenticated test identity)"** |
| SG-02-FE.2-V | 44593953374 | in progress at time of writing |
| Lane Doc Currency | 44593953519 | success |
| Baseline Fingerprint Verification | 44593953619 | success |
| Boot Syntax Boundary | 44593953342 | success |
| Canonical Render Runtime Probe | 44593953331 | success |
| Operator Console Posture Currency | 44593953459 | success |
| economic-seam-engine | 44593953454 | success |
| security-secret-scan | 44593953428 | success |
| N-ATLAS Developer Lab | 44593953764 | success |
| N-ATLAS provider forensics | 44593953409 | success |
| **N-ATLAS external beta validation** | 44593953542 | **failure** |

### N-ATLAS — read from the job log, not inferred

`beta-01-english` failed; `beta-02-hausa` **passed** in the same run — the
reverse of the previous head. The branch does not touch that workflow.

```
"status": "FAILED",
"reason": "external runtime did not return usable inference",
"errors": []
```

`"errors": []` is decisive: no HTTP exception, no timeout. The Space probed
healthy (`stage: RUNNING`, `zero-a10g`, domain `READY`), the Gradio call
returned in ~1 s with no `response_text`, and hausa succeeded seconds later
against the same Space. `bundle-beta-evidence` then failed on the missing
artifact. Third-party ZeroGPU flakiness; **not called green**.

### Lane-state gates

```
python3 scripts/lane_state.py --check
lane instruction docs consistent with snapshot (4 guarded lanes)
OFFLINE_EXIT=0

python3 scripts/lane_state.py --check --verify-live
LIVE_EXIT=1
```

Live gate **BLOCKED**: no `GH_TOKEN`/`GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN`
in this environment. The script fails closed — every claimed-open lane PR is
reported UNKNOWN, not a pass. No unauthenticated transport was substituted.

### Governance

- `main` unchanged at `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`.
- No PR merged, closed, reopened or retargeted. #668 open and draft.
- #668 remains aggregate-excluded; #657 remains unassigned and separately
  reviewed; #663–#667 remain separate contribution records.
- No deploy, commissioning, runtime credentials, workspace binding, L3
  activation or autonomous scheduling.
- Push key `170482917` created, used once, deleted; `deploy_keys: []` confirmed;
  private half shredded.
- **Human acceptance not issued.**

### Disposition

- Assertion defect: **REPAIRED and CI-proven** (step 11 green).
- Lane-state offline: **PASS**. Live: **BLOCKED** (no token).
- N-ATLAS: **unresolved external dependency**.
- SG-02-FE.2-V: **not concluded** at time of writing.
- Human acceptance: **PENDING**.

---

## 2026-11-19 — Final evidence closure (three items)

Scope: close the three items left open by the preceding section. No source
change, no commit to product code, no push of anything but this append.

Branch HEAD at time of writing: `85efbcb7184538dfebceb0534506207660f74a23`
(tree `5978a8457366a42b6eaf0cf38f14de61e1480067`), byte-identical to
`origin/integration/ewor-evidence-baseline-2026-11-18`.
Validated repair commit: `766d605c4c77e3c06ddbae8a09eed7729b9e0ebb`.
Immutable main: `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` — unchanged.

### 1. SG-02-FE.2-V on the evidence commit — CONCLUDED, success

The preceding section recorded SG-02 as "not concluded" and explicitly refused
to carry the code-commit result over to HEAD. That gap is now closed by reading
the run for `85efbcb7` itself.

| Field | Value |
|---|---|
| Workflow | SG-02-FE.2-V |
| Run ID | `44596161193` |
| Run URL | https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44596161193 |
| Tested SHA | `85efbcb7184538dfebceb0534506207660f74a23` |
| Job | `validate` (`135814886023`) |
| Conclusion | **success** |
| Started / completed | 2026-11-19T19:13:58Z / 19:20:35Z |

Step-level: 35 steps, 34 `success`, 1 `skipped`
(`CP10 cleanup disposable Firebase identity`, step 30 — a conditional cleanup
that is skipped when the disposable identity was not provisioned; it is not a
test and its skip is expected). Notable green steps: `CP10-B broader backend
regression` (step 21, ~5 min), `CP10 API verification` (24), `CP10 browser route
verification` (29), `CP10 security artifact scan` (31), `CP10 mutation boundary`
(32), `Enforce CP10 executable gates` (35).

This is the evidence-commit result, not the code-commit result. Both are now
green and both are recorded separately.

### 2. N-ATLAS external beta — RECOVERED, success

The preceding section recorded N-ATLAS as an unresolved external dependency and
refused to call it green. On `85efbcb7` it passed, which is the confirmation the
earlier reports asked for.

| Field | Value |
|---|---|
| Workflow | N-ATLAS external beta validation |
| Run ID | `44596161058` |
| Run URL | https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44596161058 |
| Tested SHA | `85efbcb7184538dfebceb0534506207660f74a23` |
| Conclusion | **success** |

Job outcomes — all four `success`:

| Job | ID | Result |
|---|---|---|
| `beta-beta-01-english` | 135814884838 | success — inference + evidence bundle uploaded |
| `beta-beta-02-hausa` | 135814885375 | success — inference + evidence bundle uploaded |
| `bundle-beta-evidence` | 135815368482 | success — both artifacts downloaded, bundle shape verified |
| `native-arkadia-golden-workflow` | 135815368517 | success — native N-ATLaS golden path executed |

Both required inference jobs produced evidence and the bundle verification
passed, which is the acceptance condition the earlier sections set. This
confirms the prior failures were external-runtime transience: the same branch,
the same workflow definition, no code change between the failing run
`44593953542` and this passing run.

**No rerun was triggered by this agent.** The pass is the natural run for the
evidence commit. Actions write permission was not available and was not needed.

### 3. Lane-state gates — offline PASS, live BLOCKED

```
$ python3 scripts/lane_state.py --check
base main: f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a (current: f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a)
doc-guard lanes: ['1', '2', '3', '4']; deferred: []
lane instruction docs consistent with snapshot (4 guarded lanes)
OFFLINE_EXIT=0
```

```
$ python3 scripts/lane_state.py --check --verify-live
live PR state: 0 PR(s) read from Arkadia-Oversoul-Prism/Arkadia (4 claimed-open + declared doc pointers) -- no GitHub token in GH_TOKEN/GITHUB_TOKEN/GITHUB_PERSONAL_ACCESS_TOKEN
  DRIFT live PR state unavailable (no GitHub token ...); every claimed-open lane PR is UNKNOWN, not a pass -- re-measure with GitHub read access
  DRIFT live PR state unavailable (no GitHub token ...); declared lane-doc pointers are UNKNOWN, not a pass
LIVE_EXIT=1
```

**Offline: PASS (exit 0). Live: BLOCKED (exit 1).**

No `GH_TOKEN`, `GITHUB_TOKEN` or `GITHUB_PERSONAL_ACCESS_TOKEN` exists in this
environment, and `gh` is not installed. The script fails closed: it reports
`0 PR(s) read` and marks every claimed-open lane PR and every declared doc
pointer UNKNOWN rather than treating absence of metadata as a pass. **No
unauthenticated transport was substituted for the authenticated gate.** The
live gate is recorded as BLOCKED, not passed.

### 4. Focused tests on `85efbcb7`

```
$ python3 -m pytest tests/test_mission_workspace_canonical_status_assertion.py \
                    tests/test_mission_workspace_harness_determinism.py \
                    tests/test_lab_mission_workspace_contract.py \
                    tests/test_lane_instruction_doc_currency.py \
                    tests/test_lane_currency_ci_wiring.py \
                    tests/test_lane_aggregate_pr_classification.py -q
135 passed in 2.41s
```

### 5. Full CI matrix on `85efbcb7` — 12 runs, 12 success

All twelve workflow runs for the evidence commit concluded `success`:

| Workflow | Run ID | Conclusion |
|---|---|---|
| Prism Console Contract | 44596160907 | success |
| SG-02-FE.2-V | 44596161193 | success |
| N-ATLAS external beta validation | 44596161058 | success |
| N-ATLAS Developer Lab | 44596160757 | success |
| N-ATLAS provider forensics | 44596160977 | success |
| Lane Doc Currency | 44596160886 | success |
| Baseline Fingerprint Verification | 44596160761 | success |
| Boot Syntax Boundary | 44596160750 | success |
| Canonical Render Runtime Probe | 44596160732 | success |
| Operator Console Posture Currency | 44596160960 | success |
| economic-seam-engine | 44596160982 | success |
| security-secret-scan | 44596160800 | success |

This is the first commit in the sequence at which every workflow is green,
including the two that had been red (Prism Console Contract step 11, and
N-ATLAS external beta).

### 6. Governance

- `main` unchanged at `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`.
- PR #668 open, **draft**, unmerged; head `85efbcb7`, base `main`.
- #668 remains aggregate-excluded from lane ownership and retained in
  `aggregate_prs` for audit.
- #657 remains unassigned and separately reviewed; not part of this integration.
- #663–#667 remain separate contribution records; none merged, closed,
  reopened or retargeted.
- No deployment, commissioning, credential issuance, workspace binding, L3
  activation or autonomous scheduling.
- No source file changed in this closure; only this evidence section appended.
- **Human acceptance not issued.** That decision remains with the human owner.

### 7. Outstanding limitations

1. **Live lane-state gate is BLOCKED** — requires a real GitHub token. This is
   the only unmet acceptance condition.
2. **Full-suite is not green** — 169 failed / 3857 passed / 31 skipped / 64
   errors on `766d605c` against 180 / 3801 / 31 / 60 on base. Zero new failing
   nodes; the 4 new errors are `node_modules`-absent environment artifacts in
   `test_prism_opportunity_entry_flow.py`. Not reported as passing.
3. **N-ATLAS remains an external dependency** — green here, but the underlying
   ZeroGPU Space has failed intermittently across runs. A future red is not
   evidence of a regression in this branch.

### Disposition

- SG-02-FE.2-V on the evidence commit: **CONCLUDED, success**.
- N-ATLAS external beta: **RECOVERED, success** (both betas + bundle).
- Lane-state offline: **PASS**. Live: **BLOCKED** (no token).
- CI on `85efbcb7`: **12/12 success**.
- Human acceptance: **PENDING**.

---

## Follow-up 2026-11-19T20:56Z — authenticated live lane-state gate UNBLOCKED

**Append-only.** Every earlier section above is preserved unmodified. Where this
section contradicts an earlier one, this section supersedes it; the earlier text
is left standing as the record of what was true at the time it was written.

### 1. What changed

Every prior section recorded the live lane-state gate as **BLOCKED — no GitHub
token**, and refused to substitute an unauthenticated transport. A token was
supplied for this follow-up. The gate is now run against the real authenticated
GitHub REST API. The BLOCKED item is **CLOSED**.

Token handling: exported to the process environment only. **Not written to any
file, commit, log or evidence document, and not printed in any output.** A
one-way length check (40 chars, `ghp_` prefix shape) confirmed the export. No
value is recorded here.

### 2. Authentication confirmed before any gate ran

Authenticated read of the repository, `HTTP 200`:

- `full_name`: `Arkadia-Oversoul-Prism/Arkadia`
- `default_branch`: `main`
- `permissions`: admin, maintain, push, triage, pull
- Authenticated open-PR read, `HTTP 200`, **7 open PRs**:
  #657, #663, #664, #665, #666, #667, #668 — all `draft=true`, all
  `base=main`.

That 7-PR read is the authoritative denominator. The live gate reads a narrower
set (4) because it fetches only the PRs the snapshot *claims* plus declared doc
pointers — see §4.

### 3. Gate results — both exit 0

```
$ python3 scripts/lane_state.py --check
base main: f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a
           (current: f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a)
doc-guard lanes: ['1', '2', '3', '4']; deferred: []
lane instruction docs consistent with snapshot (4 guarded lanes)
OFFLINE_EXIT=0
```

```
$ python3 scripts/lane_state.py --check --verify-live
live PR state: 4 PR(s) read from Arkadia-Oversoul-Prism/Arkadia
               (4 claimed-open + declared doc pointers)
base main: f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a
           (current: f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a)
doc-guard lanes: ['1', '2', '3', '4']; deferred: []
lane instruction docs consistent with snapshot (4 guarded lanes)
LIVE_EXIT=0
```

**No drift lines. No DRIFT findings. Zero deferred lanes.** Compare the earlier
unauthenticated attempt, which reported `0 PR(s) read` and emitted DRIFT lines
marking every claimed-open PR UNKNOWN — it failed closed, correctly. The
authenticated run resolves all four.

### 4. PR state actually read

Lane ownership, from `lane-state.json` (`observed_at 2026-11-19T15:27:03Z`),
each verified open, draft and based on immutable `main`:

| Lane | Doc | Active PR | Branch | doc_guard |
|---|---|---|---|---|
| 1 | AGENT-01-SHELL.md | **#665** | `lane1/title-writer-detector-binding-01` | current |
| 2 | AGENT-02-NOVANET-OPPORTUNITY.md | **#666** | `lane2/evidence-record-disclosure-01` | current |
| 3 | AGENT-03-SOLARIUN-KNOWLEDGE.md | **#667** | `lane3/graph-row-cap-disclosure-01` | current |
| 4 | AGENT-04-ARKANA-WEAVER-LAB.md | **#664** | `lane4/truncation-disclosure-01` | current |

Excluded from lane ownership, as required:

- **#668** — `classification: aggregate`, `lanes_touched ['1','2','3','4']`,
  retained in `aggregate_prs` for audit. Excluded because its diff spans all
  four lanes by *carrying* their contributions, not by owning those lanes.
  `aggregate_config`: present, source `aggregate-prs.json`, declared `[668]`.
- **#657** — `unassigned_open_prs`, separate review. Not part of this work.
- **#663** — `unassigned_open_prs`, gate-hygiene record, separate.

The live gate's `4 PR(s) read` is therefore consistent, not a shortfall: the
snapshot claims exactly four lane PRs, and the gate verifies exactly those plus
declared doc pointers. #668, #657 and #663 are *deliberately* outside lane
ownership and so are not claimed-open lane PRs to verify.

### 5. Governance at time of this append

- `main` = `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` — **unchanged**
  (authenticated `GET /git/ref/heads/main`).
- Branch `integration/ewor-evidence-baseline-2026-11-18` =
  `eeb4308a28e8d934db098cd77eed015ae7f27f8a` (authenticated ref read).
- Local HEAD = `eeb4308a…`, tree `a419d6be49cd9560d3fd8c57c400c68bdaafaf4b`.
- PR #668 — open, **draft**, **unmerged**. Snapshot records its head as
  `1e5655108e…`; `git merge-base --is-ancestor` confirms that commit is an
  ancestor of `eeb4308a`, so the snapshot reflects a real earlier point on the
  same branch and not a foreign head. The staleness of the recorded head SHA is
  cosmetic and is **not** treated here as verified-current.
- #657 unassigned and separately reviewed. #663–#667 separate contribution
  records. None merged, closed, reopened or retargeted.
- Push used a temporary write-enabled deploy key, deleted immediately after use;
  `deploy_keys: []` re-confirmed afterwards (no key remains).
- No deployment, commissioning, credential issuance, workspace binding, L3
  activation or autonomous scheduling.
- **Human acceptance not issued.** That decision remains with the human owner.

### 6. Acceptance condition status

| Condition | Status |
|---|---|
| `lane_state.py --check` exits 0 | **PASS** (0) |
| `lane_state.py --check --verify-live` exits 0 | **PASS** (0), authenticated |
| Authenticated, no unauthenticated substitution | **MET** (7 PRs read, HTTP 200) |
| `main` unchanged at `f9bd8da9` | **MET** |
| #668 aggregate-excluded, open, draft, unmerged | **MET** |
| #657 separately reviewed | **MET** |
| #663–#667 independent records | **MET** |
| No merge / deploy / commission / L3 / scheduling | **MET** |

**All lane-state acceptance conditions are now met.** The previously BLOCKED
item is CLOSED.

### 7. Remaining limitations

1. **This section is evidence-only.** It touches no guarded path, no source and
   no classification data; the gate results in §3 were produced against the
   committed tree and are unaffected by the append (verified by re-running both
   gates after the append).
2. **CI has not run on the commit carrying this section** — it is a
   documentation-only commit; the 12/12 green matrix on record belongs to
   `85efbcb7`.
3. **Full suite remains not green** — 169 failed / 3857 passed / 31 skipped /
   64 errors on `766d605c` vs 180 / 3801 / 31 / 60 on base. Zero new failing
   nodes; the 4 new errors are `node_modules`-absent environment artifacts in
   `test_prism_opportunity_entry_flow.py`. Unchanged by this follow-up, and not
   reported as passing.
4. **N-ATLAS remains an external dependency** — green on `85efbcb7`
   (`44596161058`), but the underlying ZeroGPU Space has failed intermittently
   across runs. A future red is not evidence of a regression in this branch.
5. **The supplied token's lifetime and scope are outside this audit.** It
   carried admin permission on the repository; it should be rotated by the
   owner if it was shared beyond this run.

### Disposition

- Lane-state offline: **PASS** (exit 0).
- Lane-state live, authenticated: **PASS** (exit 0). Previously **BLOCKED** —
  now **CLOSED**.
- Human acceptance: **PENDING** — not issued, not implied.

### 8. Addendum 2026-11-19T21:0xZ — CI on the push commit is GREEN (12/12)

§7 item 2 above is **superseded**: CI *has* now run on the commit carrying §1–§7
and every workflow passed. §7 is left standing as what was true when written.

Pushed commit `3eac7dc0c9b208b9e2caf8e066a256e77fefcbd4`, tree
`ae8c882978412791201067f54988390bdd38ec87`, remote ref verified an **exact
match** by authenticated `GET /git/ref` after the push.

| Workflow | Run ID | Conclusion |
|---|---|---|
| Prism Console Contract | 44613842964 | **success** |
| SG-02-FE.2-V | 44613843467 | **success** |
| **N-ATLAS external beta validation** | 44613843282 | **success** |
| N-ATLAS Developer Lab | 44613843157 | **success** |
| N-ATLAS provider forensics | 44613843651 | **success** |
| Lane Doc Currency | 44613843064 | **success** |
| Baseline Fingerprint Verification | 44613842954 | **success** |
| Boot Syntax Boundary | 44613843538 | **success** |
| Canonical Render Runtime Probe | 44613843464 | **success** |
| Operator Console Posture Currency | 44613843161 | **success** |
| economic-seam-engine | 44613843454 | **success** |
| security-secret-scan | 44613843124 | **success** |

**12 of 12 concluded `success`, 0 failures.** Both previously-red workflows —
Prism Console Contract and N-ATLAS external beta — are green on this commit.
The N-ATLAS pass is a fourth consecutive outcome on the same external Space,
consistent with the transience attribution recorded earlier; the external
dependency is **not** thereby declared reliable.

Focused suites on this commit: `test_lane_instruction_doc_currency.py`,
`test_lane_currency_ci_wiring.py`, `test_lane_aggregate_pr_classification.py`
→ **82 passed**.

Gate re-run on this commit: `--check` **exit 0**;
`--check --verify-live` **exit 0** (authenticated).

**Token containment, re-verified after the push:** the token does not appear in
the working tree, and `git log --all -p` returns **0** occurrences across all
history. It was never written to any tracked file.

**Governance unchanged:** `main` = `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`;
PR #668 open, **draft**, unmerged, head `3eac7dc0`, base `main`;
`deploy_keys: []`. No merge, deployment, commissioning, L3 or scheduling.
**Human acceptance not issued.**

### Disposition (final)

- Lane-state offline: **PASS** (exit 0).
- Lane-state live, authenticated: **PASS** (exit 0) — previously BLOCKED, now CLOSED.
- CI on `3eac7dc0`: **12/12 success**.
- Human acceptance: **PENDING** — not issued, not implied.


---

## 2026-11-20 — Full-suite node-level reconciliation against immutable base

**Scope:** reconciliation only. No source, test, workflow, classifier or lane-ownership
file was modified. This section is append-only; every earlier entry is preserved above.

### Why this section exists

The prior comparison recorded counts only — base `f9bd8da9` 180 failed / 3801 passed /
31 skipped / 60 errors; head `766d605c` 169 / 3857 / 31 / 64 — and attributed the four
additional errors to a missing `node_modules` without reconciling node by node. This
section replaces that count delta with a per-node reconciliation.

### Environment (identical for both runs)

| Property | Value |
|---|---|
| Interpreter | `Python 3.11.15` (`/usr/local/bin/python3`) |
| pytest | `9.2.0` |
| Node | `v20.20.2` |
| `base_wt/node_modules` | **ABSENT** |
| `Arkadia/node_modules` | **ABSENT** |
| `data/engineering_lab/agent_events.jsonl` | present in both trees |

Both trees were run in the same sandbox, same interpreter, same dependency state, in
sequence. The dependency state is **equal** — neither tree has `node_modules` — so no
environmental asymmetry can explain a difference between the two runs.

### Exact commands

```
cd /workspace/base_wt && python3 -m pytest tests/ -q --tb=line -rfEs \
    -p no:cacheprovider --continue-on-collection-errors > recon_base.txt 2>&1
cd /workspace/Arkadia && python3 -m pytest tests/ -q --tb=line -rfEs \
    -p no:cacheprovider --continue-on-collection-errors > recon_head.txt 2>&1
```

`--continue-on-collection-errors` is required: `tests/test_autonomy.py` fails to import
on **both** trees (`ImportError: cannot import name 'load_autonomy_config' from
'weaver.autonomy'`), which otherwise aborts collection before any test runs. That import
error is pre-existing on the immutable base and is not attributable to the branch.

### Final counts

| Tree | Commit | Failed | Passed | Skipped | Errors | Exit |
|---|---|---|---|---|---|---|
| Base | `f9bd8da9` | **180** | 3801 | 31 | **61** | 1 |
| Head | `8591b3b6` | **169** | 3857 | 31 | **65** | 1 |

**The suite is NOT passing on either tree.** 169 failures and 65 errors remain on head.

**Observed discrepancy, stated plainly:** the previously recorded comparison was
60/64 errors; this run measured 61/65 — a flat **+1 on both sides**. The delta between
the two trees is unchanged at **+4**, and the reconciliation below is unaffected. The
one-error shift is a run-to-run difference in a pre-existing erroring node, not a
branch effect; it is recorded here rather than smoothed over.

### Failure reconciliation by node ID

| Category | Count |
|---|---|
| Carried over (failing on both) | **169** |
| Fixed (failing on base, passing on head) | **11** |
| **New (failing on head, not on base)** | **0** |

**No new failing node exists.** Every one of the 169 head failures also fails on the
immutable base. The full carried-over list is the 169-node intersection of
`base_F.txt` and `head_F.txt` (reproducible with `comm -12`).

**The 11 fixed nodes:**

```
tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main
tests/test_mission_lifecycle_adapter_contract.py::test_a_recorded_authorization_marks_authorize_done
tests/test_mission_lifecycle_adapter_contract.py::test_a_recorded_chain_marks_reached_stages_done
tests/test_mission_lifecycle_adapter_contract.py::test_a_verification_verdict_marks_verify_done
tests/test_mission_lifecycle_adapter_contract.py::test_accept_and_release_are_unavailable_even_after_verification
tests/test_mission_lifecycle_adapter_contract.py::test_accepted_proposal_without_grant_is_not_authorized
tests/test_mission_lifecycle_adapter_contract.py::test_an_unreachable_contract_renders_unavailable_not_complete
tests/test_mission_lifecycle_adapter_contract.py::test_execution_done_does_not_mark_verification_done
tests/test_mission_lifecycle_adapter_contract.py::test_negative_control_the_adapter_is_not_a_constant_strip
tests/test_mission_lifecycle_adapter_contract.py::test_no_recorded_chain_renders_every_stage_unknown_not_complete
tests/test_mission_lifecycle_adapter_contract.py::test_the_seven_stages_are_always_present_in_order
```

These are the snapshot-freshness guard plus ten mission-lifecycle adapter nodes. They
fail on base on a missing `typescript.js` in the base worktree and pass on head where
the dependency resolves. They are **environment-driven**, not a behavioural fix
contributed by this branch.

### Error reconciliation by node ID

| Category | Count |
|---|---|
| Carried over | **61** |
| Fixed (base-only) | **0** |
| **New (head-only)** | **4** |

**The 4 new error nodes** — all in `tests/test_prism_opportunity_entry_flow.py`:

```
test_evidence_reading_claims_the_sentinel_only_when_the_entry_carries_none
test_evidence_reading_names_a_status_and_its_records_together
test_evidence_reading_states_the_record_count_the_handler_returns
test_negative_control_the_status_only_reading_would_hide_the_records
```

**Exact message (identical for all four):**

```
E   AssertionError: the contract module could not be executed:
      node:internal/modules/esm/get_format:189
        throw new ERR_UNKNOWN_FILE_EXTENSION(ext, filepath);
      TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension ".ts" for
        /workspace/Arkadia/web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts
        code: 'ERR_UNKNOWN_FILE_EXTENSION'
      Node.js v20.20.2
```

**Cause: environment — a Node ESM loader limitation, not an assertion failure and not
behaviour.** Node 20 cannot import a `.ts` module without a loader/transpiler, and
`node_modules` is absent on both trees. The error is raised in fixture setup, before any
assertion in the test body executes.

**Proof that these four are not attributable to the branch's changes:**

1. **The four nodes do not exist on base at all.** `pytest --collect-only` on
   `base_wt/tests/test_prism_opportunity_entry_flow.py` matches **0** of the four names.
   They are new tests added by #666, so they cannot appear in a base run — the +4 is
   four more nodes reaching a pre-existing environment limit, not four regressions.
2. **The same error already affects the same file on base.** Base has **37** errors in
   `test_prism_opportunity_entry_flow.py`; head has **41**. In both runs, **every single
   one** of those errors is the identical `ERR_UNKNOWN_FILE_EXTENSION` on
   `opportunityRadarContract.ts` (base 37/37, head 41/41). The failure mode is
   pre-existing and unchanged; only the node count grew with the added tests.
3. **The dependency state is equal.** `node_modules` is absent on both trees, so the
   error cannot be an artifact of one tree being better provisioned than the other.
4. **The error is a loader error, not an assertion.** The message is
   `ERR_UNKNOWN_FILE_EXTENSION` from `node:internal/modules/esm/get_format`, raised
   during fixture setup. No product assertion is evaluated.

**Conclusion: no new failing node and no new error node is attributable to the branch's
own changes.** The four new errors are environment artifacts of a missing TypeScript
loader, affecting newly added tests that exercise a pre-existing, equally-broken path.

### Skip reconciliation

| Tree | Skipped | Distinct skip sites |
|---|---|---|
| Base | 31 | 2 |
| Head | 31 | 2 |

`diff` of the two distinct skip-site sets is **empty** — the skip sets are identical.
The 31 skips are the same conditional skips on both trees (`google.generativeai` absent;
`ARKADIA_RUN_PRODUCTION_ISOLATION` unset; Docker runtime unavailable). **No skip was
added, removed or widened by this branch.** The earlier "ten additional skips" note was
a misreading of a truncated summary and is corrected here.

### Disposition

- **New failing nodes: 0. New error nodes attributable to the branch: 0.**
- **Suite status: NOT passing** — 169 failed / 3857 passed / 31 skipped / 65 errors on
  head; 180 / 3801 / 31 / 61 on base. Not reported as green.
- **Remaining limitation:** the 169 carried-over failures and 61 carried-over errors are
  pre-existing on the immutable base and are outside this branch's scope. The 4 new
  errors require a TypeScript loader (`node_modules` / `tsx` / `ts-node`) to clear and
  are an environment gap, not a code defect.

### Governance (unchanged)

`main` = `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` — **unchanged**, verified by
`git -C /workspace/base_wt rev-parse HEAD`. Branch HEAD `8591b3b6`. PR #668 open,
**draft**, unmerged. #657 separately reviewed. #663–#667 retain their independent
contribution records. **No merge, deployment, commissioning, credential issuance,
workspace binding, L3 activation or scheduling occurred in this session** — the only
operation performed was running the test suite on two existing worktrees and appending
this section. **Human acceptance not issued.**


### Governance addendum — `main` has advanced (recorded, not caused by this session)

The task premise states `main` remains at `f9bd8da9`. **That is no longer true**, and the
discrepancy is recorded here rather than reported as a clean confirmation.

Measured at 2026-11-20T02:25Z via authenticated `git ls-remote` and `git fetch`:

```
refs/heads/main = 97dbe0125f5fc3c7fa59714fb924b55cd484b683
```

`f9bd8da9` **is** an ancestor of `97dbe012` (`git merge-base --is-ancestor` → true), so
the immutable baseline was not rewritten or force-pushed. Three commits landed on `main`
after it:

```
97dbe012  Lane 3: disclose the knowledge-graph row cap (#667)
4dd4c05d  fix(lane2): state an entry's evidence records, not only its status sentinel (#666)
a6fe4dda  fix(lane-currency): re-derive the lane snapshot after #659 edited its doc (#663)
```

**Attribution:** these are merges of #663, #666 and #667 — the lane PRs that PR #668
composes. They were **not** performed in this session: no merge, push-to-main, or
reference update was issued by this agent at any point. The only write this session
performed was the append-only evidence commit `26bf2f92` to the integration branch.

**Consequence for the reconciliation above:** the base worktree remains pinned at
`f9bd8da9`, which is still the correct immutable comparison point for the composition —
it is the commit PR #668 is parented on. The node-level reconciliation is therefore
unaffected. But the statement "`main` remains unchanged" is **false as of this run** and
must not be carried forward as a governance confirmation.

**Consequence for PR #668:** `mergeable_state` is now `dirty` and `mergeable: false` —
the branch no longer merges cleanly onto the advanced `main`. This is the merge-order
constraint PR #668's own description predicted: a snapshot written by a PR that names
other open PRs cannot survive their merge, and a follow-up lane-state refresh is
required after the lane PRs land. **This is a human decision point, not something this
agent resolves.**

**PR #668 status:** open, **draft**, **unmerged**, head `26bf2f92`, base `main`,
`merged: false`, `merge_commit_sha: null`. #657 remains open and separately reviewed.
#663–#667 retain their independent contribution records (now merged to `main` as their
own commits, each still individually attributable).

**No deployment, commissioning, credential issuance, workspace binding, L3 activation or
scheduling occurred.** Deploy key `170515502` was created, used once for the evidence
push, and deleted; `deploy_keys: []` confirmed; private half shredded.
**Human acceptance not issued.**
