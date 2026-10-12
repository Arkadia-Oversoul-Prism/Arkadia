# gate10 — history-depth CI wiring

**Branch:** `gate10/history-depth-ci-wiring-01`
**Commit:** `c3af93b1492d766b201f4baacfeb0440e1f08a45`
**BASE_MAIN:** `6109c72ab9eedc2593d2cc6c50ebd01596c80072` (2026-10-12T05:36:48Z)
**PR:** #482 (draft)
**Verification state:** VERIFIED (repository-source + CI runtime observation). No production claim.

---

## 1. Defect

`provider-routing.yml` is the only whole-suite **judging** surface in the repository
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`, step 8 "Broader test
suite", no `continue-on-error`). It used the default depth-1 checkout.

`tests/test_agents_md_encoding_adjudication.py` resolves pinned revisions out of git
history through `scripts/agents_md_encoding_audit.py`. On a shallow clone
`git cat-file -t 6c43218a48a4` fails, so `exit_code()` returns **2** ("undecided") where a
provably clean file earns **1**.

## 2. Evidence — same SHA, same environment

| measurement | result |
|---|---|
| local, full clone | 18 failed / 2877 passed / 20 skipped / 1 error |
| main CI run `38224653480` (head `6109c72a`) | 21 failed / 2859 passed / 21 skipped / 1 error |
| `comm -13` local vs CI | exactly the 4 adjudication nodes |
| `comm -23` local vs CI | empty |
| `--depth 1` clone, same commit, adjudication file | `4 failed, 13 passed, 6 skipped` |
| full history, same commit, same file | `18 passed, 5 skipped` |

Node-set sha256: main CI `4d72c6b79c85ac97e4114aedd06479fee755ebf40b7dc60626f58ff3379b456f`
(22 nodes); local `7eaa2c116c12b9e0a3993229db647bb76655c95983534db58a6fb171ceed6f6c` (18 nodes).

## 3. Repair

`.github/workflows/provider-routing.yml`:

- `fetch-depth: 0` on the checkout (+12, with rationale comment)
- `tests/test_history_depth_ci_wiring.py` added to the `pull_request` path filter (+1)
- `tests/test_history_depth_ci_wiring.py` added to the `push` path filter (+1)

No `continue-on-error` touched. No step added or removed. No command changed.

## 4. Runtime proof — the repair was observed, not asserted

Branch CI run `38228844451`, `event=pull_request`, head `c3af93b1`:

- `provider-routing` **triggered on the pull_request event** — the self-selection repair
  bites at runtime, not merely in a source assertion.
- Step 8 log contains **zero** occurrences of `test_agents_md_encoding_adjudication`.
- Result: `17 failed, 2883 passed, 16 skipped, 2 warnings, 1 error in 212.62s`.

Node-set delta, main CI (22) vs branch CI (18):

```
comm -23 (fixed by branch):  4 nodes, all tests/test_agents_md_encoding_adjudication.py
comm -13 (newly broken):     empty
```

The job is still `failure` — on **pre-existing, unrelated** debt (the
`ERROR tests/test_autonomy.py` CE-01 module-vs-package collision and the sqlite
contamination class owned by open PR #481). This PR does not claim a green job; it claims
the four clone-depth nodes are gone and nothing new appeared.

## 5. Guard

`tests/test_history_depth_ci_wiring.py` — 15 tests, generic over the repository.

Domains derived, not listed:

- **executing** — workflows whose steps actually invoke pytest over a corpus containing a
  history-dependent guard (tokenised command; `pytest` must be the invoked word)
- **judging** — executing workflows minus those whose step *or* job carries
  `continue-on-error` / `if: false`

Assertions: every executing workflow fetches full history; every judging workflow selects
itself and the guard in its `pull_request` paths filter.

Controls: a prose mention is not an execution; a shallow checkout is not full history; an
unrelated workflow is not in the domain; and a positive control asserting the two domains
are genuinely distinct — if they collapse, the exemption detector stopped working and the
fetch-depth invariant would silently narrow.

**Live negative control on the pristine workflow** (detached worktree at `6109c72a`,
guard copied in): `2 failed, 13 passed`. With the repair: `15 passed`.

Measured domains at `6109c72a`: executing `['provider-routing.yml', 'sg-02-fe-2-v.yml']`,
judging `['provider-routing.yml']`, guards
`{'tests/test_agents_md_encoding_adjudication.py': '6c43218a48a4'}`.

## 6. Regression boundary

`tests/test_gate_filter_selection.py`, `tests/test_ci_gate_trigger_coverage.py`,
`tests/test_ci_suite_collection_continuation.py` and the new guard → **194 passed**.
`tests/architecture` → **11 passed**. `python -m py_compile api/main.py` clean;
`api/main.py` untouched (2505 lines, budget 2600).

## 7. Not done here — deliberately

1. The CP10-B execution defect (`sg-02-fe-2-v.yml` step `CP10-B broader backend regression`
   runs the whole suite without `--continue-on-collection-errors`, so it executes zero
   tests) is **not repaired**. Confirmed the flag is still absent on `main`. It is a
   separate bounded repair on a separate file.
2. The sqlite contamination class is owned by open **PR #481**; not touched, not duplicated.
3. **PR #462 was closed by the sovereign with an explicit precondition.** This pass did not
   re-open, re-run, or modify it. PR #482 is a different file, different defect and
   different repair, but the same *family* (a whole-suite CI surface that misreports). It is
   opened as a **draft** and no merge is solicited. If the sovereign intends that family to
   be paused, #482 should be closed and will not be re-opened.

## 8. Authority

No merge, no deployment, no acceptance. Human authority final.
