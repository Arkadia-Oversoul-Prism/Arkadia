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

## 10. Follow-on: the live oracle is red on `main` itself (recorded, not repaired)

Running the guard's CI form (`--check --verify-live`) surfaced a **second, unrelated**
defect that this PR does not touch. It is recorded here because it is what a reviewer will
see in this PR's `lane-doc-currency` job, and because leaving it unexplained would invite
the wrong attribution.

**Observation.** `python scripts/lane_state.py --check --verify-live` on **unmodified
`main` `36f53be2`** exits **1**:

```
  DRIFT PR #508 (lane 4 open_prs) is recorded as open but is CLOSED without merging; the thread is dead
  DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging; the thread is dead
```

Identical output on this branch. The two extra DRIFTs are **not** caused by the freshness
change — the freshness path is a different function, and it now reports nothing.

**This is real drift, not an artifact.** Live PR state confirms it: `#508 state=CLOSED
merged=null`, `#563 state=CLOSED merged=null`.

**Why CI was green until now — a timing artifact, and the cleanest possible proof.**

| event | time (UTC) | guard verdict |
|---|---|---|
| `main` run 125 (`3a1088c5`) | 2026-10-25T05:13:04 | **success** |
| **#563 closed** | 2026-10-25T05:16:10 | — (3 min after the green run) |
| #569's `lane-doc-currency` run `40198315487` | 2026-10-25T13:35:36 | **success** |
| **#508 closed** | 2026-10-25T15:23:41 | — |
| this branch's run `40248995125` | 2026-10-26T00:22 | **failure** |

Every green run predates a closure; every run after the second closure is red. #563 was
closed three minutes after `main`'s last green run, and #508 eight hours after #569's. The
oracle is not flaky — it is **live**, and the recorded lane state went stale twice.

**Why `--verify-live` is the only step that reddens.** Its sibling steps in the same job all
passed: `Execute lane instruction-doc currency guard` = success, `Execute the wiring guard
(judges this workflow)` = success, `Execute the guard as the gate executes it` = success.
The offline assertions are green; only the step that reads live GitHub state fails. That is
the correct shape for a live oracle and it means **this PR's own guard tests pass**.

**Ownership: this is not this PR's scope.** The stale records live in
`docs/control-plane/parallel-ui/lane-state.json`, which this PR does not modify
(`git diff origin/main -- docs/control-plane/parallel-ui/lane-state.json` → empty).

- **#569 (`gate-hygiene/lane-state-refresh-01`) is the PR that owns it** and partially
  repairs it: its tree removes the `#563` record but **still carries `#508`**, so a
  worktree at #569's head re-measured live **also exits 1** (only one DRIFT instead of two).
  #569 therefore does not close this on its own.
- Five open PRs touch `lane-state.json` (#548, #553, #555, #568, #569), so any repair here
  would collide with four of them — the same composition hazard this repository has already
  recorded for derived-domain guards.
- Repairing it means re-measuring the lane PRs and re-pointing lanes 3 and 4, which is
  **lane-state bookkeeping**, not lane-*freshness* logic.

**Classified:** pre-existing on `main`, reproducible there, owned by another lane,
**recorded and proposed — not executed.** Discovery does not authorize execution.

### Note on the two NOTEs (also pre-existing, also not blocking)

The same run prints, and did so before this change:

```
  NOTE lane 3 (AGENT-03-SOLARIUN-KNOWLEDGE.md) declares PR #450, which is CLOSED without merging
  NOTE lane 4 (AGENT-04-ARKANA-WEAVER-LAB.md) declares PR #428, which is MERGED
```

The guard itself labels these `(lane not owned by this guard; reported, not blocking)`.
Verified live: `#450 state=CLOSED merged=null`, `#428 state=MERGED`. They do not affect the
exit code and are outside this PR's scope.

### Consequence for this PR's check status

`lane-doc-currency` shows **fail** on this PR, and it **also fails on `main` at the same
SHA** for the same two reasons. It is therefore **not attributable to this PR** — the
standard this repository already applies to `Vercel – arkadia-prism` /
`Vercel – console`, which are `failure` on `main` itself. The PR's own contract tests (39 +
51 nodes) and the architecture suite (11) pass, and the freshness defect this PR repairs is
observably gone from the live output.

---

## §7 — Correction: the liveness oracle had the same gap and failed OPEN (commit `38efd8c4`)

**A claim in this document's PR body was false and is corrected here.** It stated that
`_liveness_findings` "already carried this guard". It did not. What it carried was the
**absent-object** branch — a merge commit the clone cannot see *at all* — which reports
UNKNOWN and does fail closed. That is a different shape from the one this PR's own fixture
measures, and the false equivalence is exactly what the §5 measurement discipline exists to
catch.

### The defect, measured

`_liveness_findings` exists to catch a snapshot that still claims a **merged** PR is open.
On a depth-1 clone it returned **no finding** for precisely that case:

| clone | merge commit present | `--is-ancestor` | liveness verdict |
|---|---|---|---|
| depth-1 | `True` | `False` (graft truncates the walk) | **silent — no finding** |
| full | `True` | `True` | `already an ancestor of HEAD` |

The commit is present as an object, so the absent-object branch does not fire. The graft on
HEAD truncates the ancestry walk, `not an ancestor` is read as `not merged`, and the stale
open-claim passes. **Fail-open in the direction the oracle exists to guard.**

### The repair

After the ancestor check fails, split on `clone_is_shallow` and report UNKNOWN, not a pass.
Both remain findings; only the diagnosis and the instructed repair differ (fetch history vs
re-measure the lane PRs).

### Red-green proof (the negative control bites)

```
# fix removed:
FAILED tests/test_lane_instruction_doc_currency.py::test_liveness_reports_undecidable_for_a_present_but_unwalkable_merge_commit
E       assert []
1 failed, 40 passed in 0.67s

# fix restored:
41 passed in 0.66s
```

`assert []` *is* the silent pass, reproduced. The positive control proves a full clone still
names the stale claim, so the shallow branch cannot swallow the finding it exists to catch.

### Scope and standing

- Two files on this PR's own branch: `scripts/lane_state.py`,
  `tests/test_lane_instruction_doc_currency.py`. `lane-state.json` untouched.
- `python scripts/lane_state.py --check` → **exit 0** on this tree.
- The pre-existing live drift (`#508`, `#563`) and the two NOTEs (`#450`, `#428`) are
  unchanged, owned by #568/#569 and the lane owners, and were **not** repaired here.
- The `lane-doc-currency` failure on this PR is reproduced on `main` at the same SHA and is
  therefore not attributable to this PR.
- No merge, no deploy, no acceptance claimed.
