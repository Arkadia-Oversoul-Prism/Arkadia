# Open-PR composition-conflict oracle — evidence

**Contract:** ARK-OPS-CONTINUOUS-001 (cycle 2026-11-22)
**Starting `main`:** `bb19aabda34d59594615b0279a45e9cbd3d8204d` (`origin/main`, local HEAD, 0 ahead / 0 behind)
**Branch:** `gate10/open-pr-composition-conflict-oracle-01`
**Authority:** implementation + evidence only. No merge, no deployment, no acceptance.

## 1. Verified gap

GitHub's `mergeable` field answers *one* question: can this PR merge into its **base**
(`main`). It cannot answer "can these two open PRs both merge", which is the question that
decides merge order for a queue. `scripts/open_pr_inventory.py` carried only the per-PR
answer, so composition was reconstructed by hand — repeated `git worktree add` + `git merge`
sessions recorded in this repository's own operating notes.

Measured live at `bb19aab` with `GET /repos/.../pulls?state=open`: **16 open draft PRs**
(#675, #679-#693), every one of them `MERGEABLE` against `main`. A per-PR answer therefore
distinguishes none of the 120 possible pairs.

Manual measurement of all 120 pairs (`git merge-tree --write-tree`, read-only) found
**exactly one** conflicting pair:

| pair | verdict | conflicted path |
|---|---|---|
| #681 x #687 | CONFLICT | `tests/test_gate2_production_observation.py` |

Both PRs repair different soundness defects in `scripts/gate2_production_observation.py`
(#681: served-artifact app identity; #687: cold-start page classification). The script
auto-merges; only the test file conflicts, because each PR appends a section at the same
anchor (the file's final line at their common base `034d8879`).

## 2. Change (bounded, two files)

`scripts/open_pr_inventory.py` — extends the existing inventory module rather than adding a
parallel tool:

- `merge_conflict_paths(a, b, repo)` — `git merge-tree --write-tree --name-only`, which
  performs the merge in the object database (no worktree, no index, no network).
- `conflict_verdict(paths)` — `CLEAN` / `CONFLICT` / `UNPROVABLE`.
- `conflict_matrix(refs)` — every unordered pair, once.
- CLI `--conflicts --ref LABEL=REV ... [--git-repo PATH] [--json]`; requires no token and
  makes no HTTP call.

`tests/test_open_pr_inventory.py` — six appended tests driving the **real** `git merge-tree`
path against a real temporary repository (no fixture stands in for the code under test).

### Fails closed

`merge_conflict_paths` returns `None` — not `[]` — when git cannot answer (unresolvable
revision, non-conflict git error, subprocess failure). An unanswered composition question
must not read as a pass; `UNPROVABLE` is its own verdict.

## 3. Verification

| Command | Result |
|---|---|
| `python -m pytest tests/test_open_pr_inventory.py -q` | **13 passed** (7 pre-existing + 6 new) |
| `python scripts/open_pr_inventory.py --conflicts --ref ... x16` | **120 pairs judged: 119 CLEAN, 1 CONFLICT, 0 UNPROVABLE** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `printf '<paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** |
| `python -m py_compile scripts/open_pr_inventory.py tests/test_open_pr_inventory.py` | clean |

### Negative controls

1. `test_merge_conflict_paths_is_silent_for_disjoint_edits` — a pair that composes must read
   `[]`; without this, a constant-true detector would report every pair as conflicting and
   would "pass" the conflict test.
2. `test_merge_conflict_paths_is_unprovable_for_an_unknown_revision` — an unresolvable
   revision yields `None`, and `conflict_verdict(None) == "UNPROVABLE"`.
3. `test_conflict_matrix_reports_every_pair_once_with_its_verdict` — the matrix over three
   revisions must contain both a `CONFLICT` and a `CLEAN` row, so it cannot be satisfied by
   a detector that is constant in either direction.

## 4. Composition verification (integration review, not just the pair test)

Measured in a detached worktree at `refs/pr/681`:

```
git merge refs/pr/687
  Auto-merging scripts/gate2_production_observation.py
  CONFLICT (content): Merge conflict in tests/test_gate2_production_observation.py
```

The conflict is purely additive — one `<<<<<<<`/`=======`/`>>>>>>>` region where both PRs
append their own section after the same final line. Resolving by keeping **both** sections
(the union of the two appended blocks) and running the composed file:

| tree | result |
|---|---|
| `refs/pr/681` alone | passes its own section |
| `refs/pr/687` alone | passes its own section |
| composed (#681 + #687, additive resolution) | **56 passed** |

The composed `scripts/gate2_production_observation.py` also carries no duplicated logic:
`detect_served_app`/`served_identity` (#681) read the served shell's identity, while
`is_cold_start`/`COLD_START_MARKER` (#687) classify the provider boot page. They are
adjacent concerns, not two implementations of one.

**Recommendation (advisory; merge execution is human-only under GOV-03):** merge one of
#681/#687 first, then rebase the other and keep both appended sections. The rebase is
textual only — the composed tree is green, so no design adjudication is required.

## 5. Baseline attribution

Environment: python 3.13, `pytest 9.2.0`, `pyyaml` and `requirements.txt` installed in this
sandbox (pytest was absent at session start).

- First full-suite pass **before** dependency install:
  `145 failed, 2715 passed, 23 skipped, 144 errors` — the 144 errors are import errors from
  the missing dependency set, not repository debt. Recorded as an **environment** result, not
  a baseline.
- Targeted re-run of the 143 files that failed in that pass, **after** install:
  `29 failed, 1860 passed, 2 skipped, 1 error`.
- The 30 remaining failing/error nodes decompose as: 17 order-dependent (each passes in
  isolation — e.g. `test_tool_execution_perimeter.py` 41 passed alone), 10 blocked on the
  absent `web/arkadia_console/node_modules/typescript`, and 3 governed deferrals
  (`SH-07` shared-session key — "awaits architectural gate"; `F-01` sessionStorage proxy —
  sovereign decision; CE-01 `weaver.autonomy` module/package collision — sovereign). The
  remainder are already owned by open PRs (#690, #683, #693, #691).
- This change touches no file in that failing set; `tests/test_open_pr_inventory.py` is not
  in the baseline node set. Attribute by node identity, not by count.

## 6. Observations recorded, not repaired

- **The composition oracle is not CI-executed.** `tests/test_open_pr_inventory.py` is run by
  no workflow (`grep -rn test_open_pr_inventory .github/` -> 0 matches). Wiring it is the
  "a guard no workflow executes is decoration" class and needs its own bounded pass; it is
  **not** performed here.
- **`data/engineering_lab/agent_events.jsonl` is written into the working tree by a test
  run** and is not gitignored (observed: the file appeared after the full-suite pass and was
  deleted, not committed). This corroborates open PR #688
  (`gate-hygiene/engineering-lab-event-log-sandbox-01`) — do not duplicate it.
- **Production is revision-consistent:** `GET https://arkadia-qzu4.onrender.com/api/version`
  at this cycle returned `source_revision == bb19aabda34d59594615b0279a45e9cbd3d8204d` with
  `revision_conflict: false`. Source<->runtime consistency only; production acceptance
  remains **NOT CLAIMED**.
- `python scripts/lane_state.py --check --verify-live` -> exit 0 (4 guarded lanes consistent).
- `python scripts/agents_md_encoding_audit.py` -> exit **1** (clean, oracle-reproduced,
  `alterations=0`), the documented clean-and-corroborated status.

## 7. Next action

Human review of this PR; merge execution remains human-only. The single follow-on item this
pass identified but did not perform: wire `tests/test_open_pr_inventory.py` into a gate, and
apply the measured merge order for #681/#687 (rebase the second, keep both appended
sections).
