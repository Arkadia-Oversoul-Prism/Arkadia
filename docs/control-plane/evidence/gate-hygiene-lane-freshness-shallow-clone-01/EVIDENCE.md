# Lane freshness guard: a truncated clone is not a rewritten `main`

Branch: `gate-hygiene/lane-freshness-shallow-clone-01`
Base main: `36f53be22d753ffe269f05cbf3fb39212f744207` (== `origin/main`, 0 ahead / 0 behind)
Measured: 2026-10-26
Status: **IMPLEMENTED** — targeted proof complete; full-suite baseline recorded; merge is the sovereign's.

## 1. The defect

`scripts/lane_state.py::_freshness_findings` decides whether the snapshot's
`base_main` still describes the current `main`. When
`is_ancestor_of_head(base)` returns false it emits:

> `snapshot base_main <a> is not an ancestor of HEAD <b>; the recorded provenance is
> void (was main rewritten?), so freshness is UNKNOWN, not a pass -- re-measure the
> lane PRs against the current main`

That message asserts a **rewrite**. But `git merge-base --is-ancestor` exits non-zero
for two different reasons, and the guard could not tell them apart:

| cause | what is true | correct response |
|---|---|---|
| `main` really was rewritten / `base_main` orphaned | the commit is unreachable from HEAD | re-measure the lane PRs |
| the clone's history is **truncated** | the commit *is* an ancestor in the real history; the graft stops the walk | fetch history and re-run |

`_liveness_findings` already guards this class (its wording is
`commit <sha> is not in this clone (shallow checkout?)`). `_freshness_findings` did not.

## 2. The measurement that separates the two

Same tree, same `base_main` (`68acf89f3045a01b0ba04038fabac4edfb5f937e`), same `main`
(`36f53be2`), only the clone depth differs:

| clone | `git rev-parse --is-shallow-repository` | `commit_is_present(base)` | `is_ancestor_of_head(base)` | `lane_state.py --check` |
|---|---|---|---|---|
| depth-1 | `true` | `true` | `false` | reports DRIFT ("was main rewritten?") |
| full (`git fetch --unshallow`) | `false` | `true` | `true` | **exit 0** — "lane instruction docs consistent with snapshot (2 guarded lanes)" |

The commit is **present in both** clones. Only the ancestry *walk* was truncated, so the
depth-1 verdict was an artifact of the checkout, not a fact about `main`. This is
decisive: had `main` been rewritten, `--unshallow` could not make the commit an ancestor.

Full-clone `--check` output (the oracle):

```
base main: 68acf89f3045a01b0ba04038fabac4edfb5f937e (current: 36f53be22d753ffe269f05cbf3fb39212f744207);
guarded paths: docs/control-plane/parallel-ui/AGENT-01-SHELL.md, AGENT-02-NOVANET-OPPORTUNITY.md,
AGENT-03-SOLARIUN-KNOWLEDGE.md, AGENT-04-ARKANA-WEAVER-LAB.md, lane-state.json
doc-guard lanes: ['1', '2']; deferred: ['3', '4']
lane instruction docs consistent with snapshot (2 guarded lanes)
EXIT_CHECK=0
```

## 3. Why this is worth repairing rather than tolerating

The check exists to stop a superseded snapshot from laundering stale lane pointers, so
failing closed is correct. The defect is not that it failed — it is **which** failure it
reported. The two causes demand opposite repairs, and the emitted instruction
("re-measure the lane PRs against the current main") sends an operator to investigate a
rewrite that never happened, while the actual repair — `fetch-depth: 0` — goes unstated.
A mis-diagnosis that costs an operator an hour is a defect even when the exit code is
"safe".

## 4. The change

`scripts/lane_state.py` only:

- **new `clone_is_shallow(repo=REPO) -> bool`** — read-only `git rev-parse
  --is-shallow-repository`. A git failure returns `False`, so the caller falls back to
  the ancestry verdict rather than claiming a truncation it did not observe.
- **`_freshness_findings` splits the non-ancestor branch.** Both remain findings (no
  weakening of the fail-closed property); only the diagnosis and the instructed repair
  differ. The shallow message says *shallow*, names the truncated walk, and instructs
  `fetch-depth: 0 / git fetch --unshallow`. The full-clone message is byte-identical to
  the previous text, so a genuine rewrite is reported exactly as before.

The shallow message deliberately does **not** contain the word "rewritten" — a test
asserts its absence, so the two verdicts cannot be conflated by rewording.

## 5. Proof

`tests/test_lane_instruction_doc_currency.py` — **39 passed** (was 37; +2 controls).

| control | shape | asserts |
|---|---|---|
| `test_freshness_names_a_truncated_clone_instead_of_a_rewritten_main` | real `git clone --depth 1` from a scratch origin, with the base commit fetched via a side branch so it is *present but unwalkable* — the measured artifact exactly | finding says `shallow`, does **not** say `rewritten` |
| `test_freshness_still_reports_a_rewritten_main_on_a_full_clone` | full clone, a real orphan commit kept alive on a side branch, HEAD reset back | finding says `rewritten`, does **not** say `shallow` |

The second is the necessary complement: without it the shallow branch could swallow the
rewritten-`main` finding and the guard would be silent on the defect it exists to catch.

**Negative control (live, not synthetic):** with the `clone_is_shallow` branch removed
from the real `scripts/lane_state.py`, the suite reddens —
`1 failed, 38 passed` (`test_freshness_names_a_truncated_clone_instead_of_a_rewritten_main`).
Restored byte-identically: `39 passed`.

Neither control is a mock: both build real repositories and exercise the real
`merge-base --is-ancestor` path the live check uses.

Other runs:

- `python -m pytest tests/test_lane_currency_ci_wiring.py tests/test_lane_instruction_doc_currency.py -q`
  → **51 passed**
- `python -m pytest tests/architecture -q` → **11 passed**
- `python -m py_compile scripts/lane_state.py` → OK

## 6. Baseline (one full-suite pass, as permitted)

`python -m pytest tests/ -q -rEf --continue-on-collection-errors` at `36f53be2`:
EXIT=1, **8 failed / 3457 passed / 17 skipped / 1 error** (233.93s).

Failing/error node set (9 nodes) — all pre-existing, none attributable to this change:

1. `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical`
2. `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
3. `test_autonomy.py` (ERROR — CE-01 `weaver.autonomy` module-vs-package collision, reserved to the sovereign)
4. `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate`
5. `test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set`
6. `test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated`
7. `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`
8. `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key`
9. (error node from #3)

The two `test_engineering_lab_api.py` pins and the Landing-copy pin are recorded as
**unowned drift** elsewhere in `AGENTS.md`; repairing them edits an authority surface and
is sovereign-only. They are not touched here.

**Not measured:** a second full-suite pass on the branch. Attribution is by the targeted
suites above plus the fact that this change adds no node to any other file's import
surface — `scripts/lane_state.py` is imported by no other module in the repository.

## 7. Reconciliation with the open lane PRs (measured, not assumed)

Live at `36f53be2`, all three **OPEN / draft / CLEAN**:

| PR | branch | base | head | touches `scripts/lane_state.py`? |
|---|---|---|---|---|
| #567 | `gate-hygiene/lane-guard-authority-boundary-01` | `main` | `bebb6ed4` | no — evidence + `lane_scope_probe.py` only |
| #568 | `gate-hygiene/lane-guard-fixed-scope-01` | **#567's branch** (stacked) | `686dd44a` | yes — scope/enforced-set + base-branch checks |
| #569 | `gate-hygiene/lane-state-refresh-01` | `main` | `d75ba224` | no — `lane-state.json` + evidence |

- **No open PR claims this defect.** `git show <branch>:scripts/lane_state.py` for all
  three branches contains only the pre-existing `_liveness_findings` shallow wording; none
  adds a shallow guard to `_freshness_findings`.
- **#568 is the only file-level overlap**, and its `lane_state.py` diff does **not** touch
  `_freshness_findings`'s internals — the sole match is the *call site* context line
  (`findings += _freshness_findings(state, base_main)`, unchanged) inside a larger hunk
  that swaps `current_lanes(state)` for `enforced_lanes(state)`. Different function,
  different region. A textual conflict is possible but the semantic overlap is nil; if
  git reports a conflict it will be in `main()`'s assembly block, resolved by keeping both
  edits.
- **#568 is stacked on #567** (its `baseRefName` is
  `gate-hygiene/lane-guard-authority-boundary-01`, not `main`). Merging a stacked PR lands
  its base branch's commits too. This is a real merge hazard and it is **already the
  subject of #568's own guard**; it is recorded here for the sovereign's ordering decision
  and is **not** this PR's scope.
- This PR branches from `main` and is deliberately independent of all three, so it can
  merge in any order.

## 8. Scope and non-goals

**In scope:** the shallow/rewrite split in `_freshness_findings`, the `clone_is_shallow`
helper, two controls, this record.

**Explicitly not in scope** (discovery does not authorize execution):

- the lane-guard **scope** question (#568's subject) — untouched;
- the `lane-state.json` refresh (#569's subject) — untouched;
- the authority-boundary incident (#567's subject) — untouched;
- any repair of the eight pre-existing baseline failures;
- any change to `.github/workflows/lane-doc-currency.yml` (it already carries
  `fetch-depth: 0`, which is why the artifact appears in ad-hoc clones and not in CI).

## 9. Authorization boundary

No merge, no deployment, no production claim. Branch pushed, PR opened as **draft**,
left draft. Human merge authority is final.
