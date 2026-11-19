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
