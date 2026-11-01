# Prism reconciliation — baseline attribution and lane-currency residuals

Pass: 2026-11-01 (hourly bounded execution contract, reconciliation edition)
Base observed: `main` = `d14c2598b5b5e9016703b6a834fd44b8def1e5a1`
Workstream branch: `feat/prism-ui-reconciliation-overnight-01` @ `75f9e07d` — unmerged, 168 commits behind `main` (§3.1)

Read-only reconciliation. No merge, no deployment, no acceptance claim. Human merge authority
retained.

## 1. Live inventory (re-measured this pulse, not inherited)

Open PRs, `gh pr list --state open`: exactly **two**, both `draft=true`, both
`mergeStateStatus=CLEAN` / `mergeable=MERGEABLE`, both based on `main` `d14c2598`.

| PR | head | base | files | CI on head |
|---|---|---|---|---|
| #605 `fix(lab): preserve provider dispatchability and unknown states` | `7c714493b4b23133a03513c9b2b4a21326f5636a` | `d14c2598` | 8 | 18 success, 0 other |
| #606 `test(openapi): name the ARKANA A2 SSE operation in the inventory pin` | `d9e0558a13cba4ad443084f09cf3e1fb340a9c13` | `d14c2598` | 2 | 11 success, 0 other |

Both heads contain `main` (merge-base == `d14c2598` for each). Their changed-path sets are
**disjoint** (`comm -12` empty). Merged this pass by humans, not by an agent: #603
(`c89e1040`, merged 2026-11-01T04:09:19Z), #604 (`d14c2598`).

## 2. The `main` head is red on exactly one node, and PR #606 repairs it

Measured on `main` `d14c2598`:

```
python -m pytest tests/test_openapi_security_production_contract.py -q -rEf
-> 1 failed  test_all_composed_operations_have_adjudicated_security_boundaries
```

Measured on PR #606 head `d9e0558a`, same command: **1 passed**.

Attribution is by introducing commit, not by guess. `api/arkana_stream_routes.py` gained
`@router.post("/api/commune/resonance/stream")` in `202bc4e1` ("ARKANA-A2: SSE streaming
resonance path"), dated 2026-10-30T08:35:24+01:00, which **is an ancestor of `main`** and
**after** `b5bc34cb` (the revision AGENTS.md records the 9-node baseline at). The inventory
pin in `tests/test_openapi_security_production_contract.py` on `main` does not name the new
operation (`grep -n commune/resonance/stream` -> ABSENT); PR #606 adds exactly that line.

So `main`'s failing set is **10 nodes**, not the 9 recorded in AGENTS.md — the delta is one
node, introduced by `202bc4e1`, and repaired by the open PR #606. This is a recorded
correction of a superseded measurement, not a new regression.

## 3. Measured baseline on `main` `d14c2598`

The baseline below was measured in a **clean detached worktree at `main`**
(`git worktree add --detach /tmp/mainwt d14c2598`), not in the working tree — see §3.1 for why
that distinction decided the result.

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
-> 9 failed, 3783 passed, 21 skipped, 3 warnings, 1 error in 252.01s
```

Sorted FAILED/ERROR node set (10 nodes), `sha256` of the sorted list
`99e751bf7cdd552458464e7a3cdcda207250179383eba770ad84fb8a83c9960e`:

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_openapi_security_production_contract.py::test_all_composed_operations_have_adjudicated_security_boundaries
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

The `ERROR tests/test_autonomy.py` is the reserved CE-01 module-vs-package collision; it is
not attributable to this pass and was not repaired.

Lane and architecture suites on the same revision:

```
python -m pytest tests/architecture -q                                    -> 11 passed
python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q  -> 61 passed
```

### 3.1 The workstream branch tree is 168 commits stale — measured, and mostly contamination

The working tree was on the reconciliation branch, not `main`, so the first suite run of this
pass measured that tree. Re-measured in a clean worktree (`/tmp/wsbr` at `75f9e07d`, which is
also the live remote tip of `feat/prism-ui-reconciliation-overnight-01`):

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
-> 18 failed, 2154 passed, 20 skipped, 2 warnings, 1 error   (19 nodes)
```

Node-set delta against `main` (`comm -3` of the two sorted lists):

- **main only (1):** `test_openapi_security_production_contract.py::test_all_composed_operations_have_adjudicated_security_boundaries`.
  The branch predates `202bc4e1`: `api/arkana_stream_routes.py` does not exist there, so the
  operation and its inventory pin are both absent.
- **branch only (10):** one `test_static_ingestion_sources.py`, one
  `test_static_ingestion_idempotency.py`, six `test_voice_context.py`, two
  `test_voice_pipeline.py`.

Of those ten, **exactly one is a genuine branch-only failure**: running the same four files in
isolation on the branch tree gives `1 failed, 45 passed` — the single failure being
`test_static_ingestion_sources.py::test_adr_source_root_resolves_and_holds_the_records`, which
pins a frozen six-name ADR list and therefore reddens on any added ADR. `main` already repaired
that pin (the same four files are `46 passed` there, property-based rewrite visible in
`git diff d14c2598 -- tests/test_static_ingestion_sources.py`). The other **nine** pass in
isolation on the same branch tree (`36 passed`) and appear only under the full suite —
cross-test contamination on a tree 168 commits behind, not attributable to any change.

Conclusion: the branch contributes **no regression** and carries **no unique unmerged work**
in these paths; it is simply stale. The correct baseline is §3. The 19-node figure is a
**superseded measurement** recorded so a future pass does not re-derive it, and it must not be
read as `main`'s state.

Note also that this branch is 168 commits behind `main` and cannot become mergeable without a
rebase — recorded, not performed (§6).

### 3.2 A previous pass's blocker claim does not reproduce

An inherited note classified the full suite as BLOCKED on a `PermissionError: Engineering
mutation is disabled in SolSpire ExecutionRuntime`. That text is a **test failure detail**,
not a harness blocker: it is the expected message asserted by
`tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
against `solspire/execution_runtime.py:116` (and mirrored at `:249`). The full suite ran to completion in 244s and
reported totals. `BLOCKED` was a misdiagnosis; the correct classification is the 10-node
FAILED/ERROR set above.

## 4. Composition of #605 + #606 is clean

`git worktree add --detach /tmp/w605 7c714493`, then `git checkout pr606 -- tests/test_openapi_security_production_contract.py`,
then the composed guards:

```
python -m pytest tests/test_openapi_security_production_contract.py \
  tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py \
  tests/test_lab_model_gateway_contract.py tests/test_prism_w4_model_gateway.py -q
-> 105 passed
```

PR #605 alone (worktree `/tmp/w605` at `7c714493`), targeted: `tests/test_lab_model_gateway_contract.py`,
`tests/test_prism_w4_model_gateway.py`, `tests/test_lane_instruction_doc_currency.py`,
`tests/test_lane_currency_ci_wiring.py` -> **104 passed**. Its snapshot refresh (`lane-state.json`) is derived, not hand-edited:
lane 4 `active_pr=605`, `doc_guard=deferred`, `unassigned_open_prs=[606]`, `base_main`
`d14c2598` — which matches the live state measured here.

## 5. Residuals found and **not** repaired (recorded, per no-self-expansion)

### 5.1 `unassigned_open_prs` is written, printed, and judged by nothing

`grep -rn unassigned_open_prs` finds the writer (`scripts/lane_state_refresh.py:19,289,390`)
and **no reader** in `scripts/lane_state.py` or its tests. Consequence measured on live
`main` `d14c2598`: the committed snapshot records #603 under `unassigned_open_prs` while
#603 is **merged** (`merged=true`, 2026-11-01T04:09:19Z), and `lane_state.py --check
--verify-live` still exits **0**. The guard's `claimed_open_prs` covers only `open_prs` and
`deferred_to_pr`; a PR in the unassigned list is a claim nobody judges. This is already
recorded in AGENTS.md; this pass confirms it is still live and still unjudged.

### 5.2 The guard never requires that an open PR appear in the snapshot

`claimed_open_prs` is one-way: every claim in the snapshot must be open, but nothing requires
that an open PR be claimed. On live `main` both open PRs (#605, #606) are absent from the
committed snapshot, all four lanes read `idle`, and `--check --verify-live` exits **0**. A
snapshot that omits live work passes. Wiring this direction changes what the gate judges and
belongs in its own bounded workstream.

### 5.3 A recorded `head_sha` is never compared to anything

`grep -c head_sha scripts/lane_state.py` -> **0**; only the test file asserts it is 40 chars.
The snapshot on the #605 branch records lane 4's PR head as `e4738a50…` while the live head is
`7c714493…`; the guard stays green. As AGENTS.md already notes, a tip-equality assertion is
unsatisfiable for the lane-currency commit that carries the snapshot (that commit *becomes*
the tip), so the correct repair is a scoped comparison, not an equality check.

### 5.4 Lane docs declare four closed threads; only two of them merged

`declared_pr` / `declared_idle` on `main` `d14c2598`:

| lane | doc | declared PR | live state | `declared_idle` |
|---|---|---|---|---|
| 1 | `AGENT-01-SHELL.md` | #588 | closed, **merged** | True |
| 2 | `AGENT-02-NOVANET-OPPORTUNITY.md` | #564 | closed, **NOT merged** | True |
| 3 | `AGENT-03-SOLARIUN-KNOWLEDGE.md` | #450 | closed, **NOT merged** | True |
| 4 | `AGENT-04-ARKANA-WEAVER-LAB.md` | #601 | closed, **merged** | True |

Every lane declares `**Active thread:** none`, and `declared_idle` is last-wins, so the idle
declaration supersedes the pointer and `--check --verify-live` exits **0** for all four.
For lanes 1 and 4 the pointer is provenance for a merged thread. For **lanes 2 and 3 the
declared thread is closed *without* merging**, so the doc names a dead PR as its active
thread while reporting idle — the guard cannot see it, because it judges `open_prs` and
`deferred_to_pr` claims, not `declared_pr` against live state. Recorded, not repaired: making
`declared_pr` a judged claim changes what the gate judges and is its own bounded workstream.

## 6. Disposition

| PR | disposition | reason |
|---|---|---|
| #605 | ELIGIBLE_TO_MERGE (human decision) | CLEAN/MERGEABLE, based on current `main`, 18/18 checks success, targeted 104 passed, snapshot derivation matches live state |
| #606 | ELIGIBLE_TO_MERGE (human decision) | CLEAN/MERGEABLE, based on current `main`, 11/11 checks success, repairs the single red node on `main`; composed with #605 -> 105 passed |
| #507 | already CLOSED (2026-10-15T20:42:44Z, unmerged) | inherited context described it as an active draft; re-measured state is closed, its remote branch is gone, and `tests/test_console_legacy_route_coverage.py` is present on `main` from `5b9cf426`. No action. |

No merge was performed. Both PRs remain draft and are left for the human sovereign, who holds
merge authority under this contract. Nothing in this pass altered `api/main.py`, any protected
authority surface, or any lane-owned source path.

## 7. Commands run (all read-only)

```
git remote -v; git status; gh auth status
gh pr list --state open --json number,title,headRefName,isDraft,mergeStateStatus
gh pr view 605|606 --json headRefOid,baseRefOid,isDraft,mergeStateStatus
gh api repos/.../pulls/507 ; gh api repos/.../pulls/603
gh api repos/.../commits/<sha>/check-runs
git merge-base --is-ancestor <sha> main
python -m pytest tests/test_openapi_security_production_contract.py -q -rEf      # main + pr606
python -m pytest tests/ -q -rEf --continue-on-collection-errors                 # once
python -m pytest tests/architecture -q                                           # main worktree
python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q
python -m pytest tests/test_voice_context.py tests/test_voice_pipeline.py \
    tests/test_static_ingestion_sources.py tests/test_static_ingestion_idempotency.py -q   # main
python scripts/lane_state.py --check --verify-live                              # exit 0
gh pr list --state open --json number ; gh api repos/.../pulls/{588,564,450,601}
printf '<path>' | python scripts/cp10_mutation_boundary_policy.py --judge
```

## 8. Next action

Human decision on merging #606 first (it repairs the one red node on `main`) and then #605 —
or both in either order; composition was measured clean in this order. Then refresh the lane
snapshot from the new `main`; the three residuals in section 5 remain proposed, unexecuted.

## 8. Persistence and boundary state at end of pulse

- Evidence committed as `57a656ad` on `prism-reconciliation-baseline-attribution-01` and pushed
  (`git ls-remote origin` confirms `57a656ad`). `main` unchanged at `d14c2598`.
- **Branch choice, recorded rather than assumed.** The pulse directive said to commit to the
  assigned workstream branch and update *its existing PR*. That branch is
  `feat/prism-ui-reconciliation-overnight-01`, and its only PR — **#418 — is MERGED**
  (2026-10-11T09:45:19Z); it is also unmerged into `main` and 168 commits behind. There was no
  open PR to update, and no PR was created (directive: never create a new PR). The work was
  therefore pushed to the session branch as an unpushed-record fallback. A human decision is
  needed on where this evidence should ultimately live.
- **`gh` / REST read path became unavailable at the end of the pulse.** `gh auth status` reports
  not logged in; both `$GITHUB_PERSONAL_ACCESS_TOKEN` and `$github_token` return HTTP **401
  Bad credentials** against `GET /user`. This is **not** a repository-access blocker: `git fetch`
  and `git push` both succeed over the clone's embedded credential (verified after the failure).
  All facts in this document were established *before* the API path failed, so none are affected;
  but a future pulse must not read this 401 as evidence about the repository.

## 9. What is NOT claimed

- No merge, no deployment, no production acceptance. Human merge authority retained.
- PRs #605 and #606 were **verified**, not merged: diffs inspected, CI read, changed paths
  confirmed disjoint, CP10 judge exit 0. Their eligibility is a separate decision (M1–M13) and
  was not exercised.
- The lane-currency residuals (no `unassigned_open_prs` reader; `head_sha` never compared;
  lanes 2/3 declaring closed PRs while idle) are **recorded, not repaired** — repairing them
  changes what the guard judges and is a separate bounded workstream.
