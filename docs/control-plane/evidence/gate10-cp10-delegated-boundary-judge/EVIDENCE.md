# GATE-10 / CP10 — Delegated Boundary Judgement — Evidence

**Gate:** GATE-10 (Governed Execution) — CP10 mutation boundary / M02A CI gate integrity
**Authority:** Human sovereign (merge and authorization retained exclusively by the sovereign)
**BASE_MAIN:** `02fe88c812b573313553bd32c6037484fa97c17f`
**Branch:** `gate10/cp10-delegated-boundary-judge`
**Status:** VERIFIED (tests + CLI runtime evidence); merge is human-only.

## 1. Objective (bounded)

The CP10 mutation boundary keeps **two hand-maintained copies of the same allowlist**:
`LEGIT` in `scripts/cp10_mutation_boundary_policy.py` and an inline `legit='...'` regex
literal inside the `.github/workflows/sg-02-fe-2-v.yml` mutation step. The fitness tests
prove the *module*; the gate executes the *shell copy*. The two had already drifted
(a surface admitted in one and not the other), so the executed decision and the proven
decision could disagree — the repository's own memory calls this out as "known
composability risk" and names the recommended structural fix: *have the workflow execute
the tested policy module and keep the shell literal only as a mirror assertion*.

This pass implements exactly that recommendation, no more.

## 2. Change set

| File | Change |
|---|---|
| `scripts/cp10_mutation_boundary_policy.py` | +`judge_paths()`; `__main__` refactored to `main(argv)` with a `--judge` mode that reads changed paths on stdin and returns the verdict as an exit status. `--resolve-range` and the positional-args mode are unchanged in behaviour. |
| `.github/workflows/sg-02-fe-2-v.yml` | The mutation step no longer carries `legit=`. It pipes `git diff --name-only` into `python scripts/cp10_mutation_boundary_policy.py --judge` and fails on a non-zero exit. The `forbid` (V2/V3) and no-autonomy stages are untouched. |
| `tests/test_m02a_ci_gate_integrity.py` | The three drift tests (`_workflow_legit_regex()` + `re.match` parity) are replaced by tests over the **CLI the workflow actually runs**: delegation is asserted, the absence of a second copy is asserted, and the CLI verdict is checked against the public API on the tracked corpus, lookalikes, root docs and the empty change set. |

The inventory itself was **not** widened or narrowed. `opportunity_radar/` is already
admitted on `main` (landed before this pass), so this change is orthogonal to PR #118 —
verified below, and no file in #118's diff is touched here.

## 3. Verification

```
python -m py_compile api/main.py            -> OK, 2519 lines (budget 2600, untouched)
yaml.safe_load(.github/workflows/...)       -> OK, 1 job, push paths 21 / pull_request paths 21
pytest tests/test_m02a_ci_gate_integrity.py -> 49 passed
pytest tests/test_m02a_ci_gate_integrity.py tests/architecture -q -> 60 passed
```

Runtime evidence for the delegated decision (the exact shell the workflow runs):

```
printf 'web/public_prism/src/App.tsx\nAGENTS.md\ndocs/a/b.md\nknowledge/x.py\n' \
  | python scripts/cp10_mutation_boundary_policy.py --judge   -> rc=0  PASS
printf 'secret-backdoor/bin/x\n' | ... --judge                -> rc=1  rejected
printf '' | ... --judge                                       -> rc=0  (empty change set is bounded trivially)
python scripts/cp10_mutation_boundary_policy.py --resolve-range -> rc=0 (fallback HEAD^)
```

The delegated verdict also judges its **own** change set:
`git diff --name-only origin/main` piped into `--judge` -> `rc=0`.

`push.paths` and `pull_request.paths` are already at parity on `main` (21 each, symmetric
difference empty), so no trigger-path change was needed and none was made.

## 4. Scope discipline

An `--emit-legit` mode (print `LEGIT.pattern` for a mirror assertion) was drafted during this
pass and **removed before commit**: nothing consumed it and it was untested surface. The
remaining change is the minimum that closes the drift defect.

## 5. Baseline comparison and remaining uncertainty

| | `main` @ `02fe88c` | this branch |
|---|---|---|
| contract-recorded baseline | 804 / 54 / 12 / 2 collection errors @ `6038989` | — |
| re-measured this pass | see EVIDENCE §5 note | pending full-suite completion |
| `tests/architecture` | 11/11 (per prior classification record) | **60 passed** together with the M02A gate test |

Remaining uncertainty, stated rather than hidden:

- The contract's recorded baseline (`804 passed / 54 failed / 12 skipped / 2 errors`) is
  anchored at `6038989`; `origin/main` has since advanced to `02fe88c`, so counts are not
  directly comparable. The **failure fingerprint**, not the count, is the attribution unit.
- A full-suite run was started on this branch this pass and is the next heartbeat's
  first reconstruction input; it is not claimed here as complete.
- The pre-existing `ModuleNotFoundError: No module named 'arkadia_drive_sync'` collection
  error and the `google.generativeai` deprecation warning are baseline debt, untouched.

## 6. Authority boundary

No merge, no push to `main`, no workflow autonomy added. The gate still originates no
authority: it reads a change set and returns a verdict. The sovereign merges.
