# WORKSTREAM STATE — gate hygiene / scheduler bootstrap test-spec repair

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.

## Pass record — 2026-09-30 (heartbeat)

- **BASE_MAIN:** `002b189dd95e41c9b4f4cca33d08b4121453d289`
  (*"Merge pull request #141 from Arkadia-Oversoul-Prism/gate-hygiene/f02-steward-filter-provenance-01"*,
  2026-09-30 02:22:31 +0100). Established by `git fetch --all --prune` then
  `git log -1 origin/main`; unchanged across the pass.
- **Open PRs (live, via `gh pr list`):** **#142–#147**, all `mergeStateStatus: CLEAN`.
  None touches `tests/test_engineering_scheduler_bootstrap.py` — no duplicate work, no
  conflict with this pass.
- **Branch:** `gate-hygiene/scheduler-bootstrap-testspec-repair-01`.
- **Working tree:** single file modified — `tests/test_engineering_scheduler_bootstrap.py`.
  `weaver/engineering_router.py` pristine (`git diff` vs `HEAD` empty).
- **Trajectory:** `ARKADIA-TRUTHFULNESS-01` — status `authorized-for-review-gated-execution`,
  `max_active_moves: 1`, `review_gate: required_after_every_move`. **All ten moves
  `completed`** (M01–M09, M02A). No move is advanced by this pass.
- **Observation, not touched:** the run contract's declared baseline
  (`main := 6038989`, `804 passed / 54 failed / 12 skipped`, `architecture 9/10`) is
  **stale**. Measured live below. Recorded, not "corrected" in the contract.

## Fingerprint (measured this pass, not remembered)

Both runs used `--continue-on-collection-errors`, because the full suite otherwise
**aborts at collection** on the two pre-existing import errors and reports nothing else.
Any future pass comparing against a baseline must use the same flag or the comparison is
meaningless.

```
BASE_MAIN 002b189 (change reverted) : 20 failed / 1041 passed / 11 skipped / 2 errors
this branch                        : 18 failed / 1044 passed / 11 skipped / 2 errors
delta                              : -2 failed / +3 passed   (exactly the 2 target tests)
architecture                       : 11/11
py_compile api/main.py             : pass   (api/main.py = 2519 / 2600 lines, untouched)
vite build                         : environment-blocked (not attempted)
```

Note the pass count rises by 3, not 2: the repair adds one new test
(`test_live_trajectory_dry_run_is_truthful`) and converts two failures to passes.

## Falsifiability

NC-1/NC-2/NC-3 (router ignores `depends_on`; artifact stops naming the move; human artifact
misreports status) each produce the expected failure. Router restored to pristine after
every control. The repaired tests can distinguish correct routing from incorrect routing —
they are not tautological.

## Debt disposition

Rows 38–39 of `BASELINE_TEST_DEBT_CLASSIFICATION.md` (classified `DRIFT`) are **repaired**
by this pass and should be re-classified as **STALE_ASSERTION** — the defect was in the
test specification, not in the router. See `EVIDENCE.md` §1.

The remaining 18 failures / 2 collection errors are **fingerprint-unchanged** and were not
touched. They are not attributable to this pass.

## Next bounded task (proposed, not started)

Attribution work on the fingerprint-stable remainder is available and bounded, but each
group has a different character and should not be bundled:

- `test_steward_filter.py` (3) — appears related to PR #141's `f02-steward-filter-provenance`
  lineage; check whether #141 regressed or the tests are stale **before** touching.
- `test_spiral_grove_*` (6) — may share one root cause; verify before assuming.
- `test_solspire_r{1,2,3}_*` (4) — governance convergence; touches authority-adjacent
  surfaces, so treat as higher-risk and confirm scope with the sovereign first.
- `test_autonomy.py` / `test_render_codex.py` collection errors — pre-existing import
  defects, documented since at least the prior pass.

## Publication

Branch pushed; PR opened from `gate-hygiene/scheduler-bootstrap-testspec-repair-01` against
`main`. **READY_FOR_SOVEREIGN_MERGE.** No merge, no force-push, `main` untouched.
