# GATE-10 / gate-hygiene - CP10 Enforcement-Step Truthfulness - Evidence

**Gate:** GATE-10 (Governed Execution) - gate hygiene / CI wiring
**Authority:** Human sovereign (merge and authorization retained exclusively by the sovereign)
**BASE_MAIN:** `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Branch:** `gate10/cp10-enforcement-step-truthfulness-01`
**Status:** IMPLEMENTED - guard strengthened and measured; merge is human-only.

## 1. Objective (bounded)

`.github/workflows/sg-02-fe-2-v.yml` ends in a step named
`Enforce CP10 executable gates` that re-asserts, in shell, the verdicts of the
earlier `continue-on-error` steps. The repository's own lesson
(`AGENTS.md`, "A green CI job can execute ZERO tests") stated:

> `steps.<id>.outcome` is not available inside a `run:` block; GitHub exposes it
> only to a step's `if:`. A `run:`-block guard must read `steps.<id>.conclusion`,
> or the decision must move to an `if:`.

This pass tests that claim against live evidence and, finding it **false as
stated**, replaces it with the measured behaviour and pins that behaviour with a
regression guard that cannot be disarmed.

**Bounded scope.** Two files change: the guard
`tests/test_m02a_ci_gate_integrity.py` and the prose it corrects in `AGENTS.md`.
No workflow, no production code, no authority surface, no gate promotion.

## 2. The `AGENTS.md` claim is contradicted by live runs

The claim, read literally, is that an enforcement step reading
`steps.<id>.outcome` collapses to a constant and cannot fail. Live runs
contradict it. Measured on `main` `f9ced6b6` (run `37954341298`, artifact
`cp10-evidence-f9ced6b6...`), the enforcement step executes **16** assertions:

```
test 'success' = success   x 15
test 'failure' = success   x  1     <- the 15th assertion
##[error]Process completed with exit code 1.
```

The single `failure` is the real `outcome` of the soft `browser` step; the step
therefore exits non-zero and **fails the job**. The same shape reproduces on
PR #354's head `ebb4077b` (run `37967556608`): 16 assertions, one `failure` at
position 15, exit 1.

A **third** independent observation, on this PR's own head `5abaf753`
(run `38012746127`, job `114096207224`, artifact `cp10-evidence-a0d7507a...`):

```
##[group]Run test 'success' = success
test 'success' = success   x 14
test 'failure' = success       <- position 15, the `browser` step
test 'success' = success   x  1
...
##[error]Process completed with exit code 1.
```

The enforcement step ran under `bash -e {0}`, aborted at the failing `test`, and
exited 1. The guard fires.

So `steps.<id>.outcome` **is** substituted inside this `run:` block, and the
enforcement step is **not** self-satisfying. The `AGENTS.md` paragraph is an
overclaim; the `test 'success' = success` lines are the *passing* assertions,
not evidence of a constant.

## 3. Change set

- `tests/test_m02a_ci_gate_integrity.py`
  - Extracted the two detector regexes into module-level constants
    (`_ENFORCED_BY_OUTCOME`, `_ENFORCED_BY_CONCLUSION`) and helpers
    `enforced_by_outcome()` / `enforced_by_conclusion()`; the existing guard
    `test_continue_on_error_gates_are_still_enforced_by_outcome` now uses the
    helper instead of an inline regex.
  - Added `test_enforcement_never_reads_step_conclusion` - fails if the
    enforcement step ever asserts `steps.<id>.conclusion`.
  - Added two controls: `test_outcome_detector_is_not_blind` (negative - the
    detector must flag the `.conclusion` form) and
    `test_outcome_detector_matches_the_live_form` (positive - the live `.outcome`
    form must be matched).
- `AGENTS.md` - corrected the false paragraph in the gate-hygiene section to the
  measured behaviour, recording the runs.

## 4. Why this is not decoration

The guard file is `tests/test_m02a_ci_gate_integrity.py`, which
`sg-02-fe-2-v.yml` already lists as a trigger path, so the guard executes under
the gate it protects. (This is the "a guard no workflow executes is decoration"
defect class the repository named in
`gate10-baseline-fingerprint-ci-wiring-01`; here the wiring already exists and
the guard is strengthened rather than duplicated.)

## 5. Proof

| Check | Command | Result |
|---|---|---|
| Guard file | `python -m pytest tests/test_m02a_ci_gate_integrity.py -q -rEf` | 64 passed, 3 failed (pre-existing, section 6) |
| New tests | `... -k "conclusion or detector"` | 3 passed |
| Teeth | mutate `steps.browser.outcome` -> `steps.browser.conclusion`, rerun | `test_enforcement_never_reads_step_conclusion` **fails** (1 failed); reverted |
| Architecture | `python -m pytest tests/architecture -q` | 11 passed |
| Boot | `python -m py_compile api/main.py` | OK |
| Boundary | `git status --porcelain \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS (exit 0) |
| Full suite | `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | 15 failed, 1857 passed, 20 skipped, 1 error |

**Regression boundary.** The failing/error node **set** is byte-identical to the
pre-change baseline (16 nodes = 15F + 1E); only the passed count moves, 1854 ->
1857, which is exactly the three tests added here. No node changed identity.

## 6. Pre-existing debt (recorded, not repaired)

The 3 failures in the guard file, and the 16-node baseline, are the CP10
`deploy/` allowlist omission owned by PR #354 (`deploy/n-atlas-server/` added by
`e074a63b`, merged `a27c6c80`). They are unchanged by this pass and are not
attributable to it.

## 7. CI status on this PR's head `5abaf753`

| Check | Result |
|---|---|
| Full-history secret scan | success |
| Vercel Preview Comments | success |
| native-arkadia-golden-workflow | success |
| bundle-beta-evidence | success |
| beta-beta-01-english / 02-hausa | success |
| `validate` (`sg-02-fe-2-v.yml`) | **failure** |
| CP10 mutation boundary step | **PASS** (`Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)`) |
| Enforcement step | ran, aborted at the real `browser` failure (exit 1) |

`validate` is **failure on `main` itself** (run `37954341298`, the same SHA the
baseline was measured at), so it is **not attributable to this PR**. The CP10
mutation-boundary step - the gate this workstream is about - passed on the
changed paths.

## 8. Remaining uncertainty / out of scope

The `fb_user` step is `continue-on-error: true` and is not enforced through
`.outcome` (it is treated as infrastructure by the existing guard's
`infra_only` set). Whether it should be enforced is a **separate** bounded
question; this PR only pins the *observed* state and the `.conclusion`
invariant. Not fixed here.

The `CP10-B broader backend regression` step runs `pytest tests/ -q` and hits
`Interrupted: 1 error during collection` (the CE-01 `weaver.autonomy`
module-vs-package collision), executing zero tests. Recorded, not repaired - it
is reserved to the sovereign.

## 9. Authorization required

Human merge only. No gate promotion, no authority change, no scope expansion.

## 10. Pass 4 - live re-measurement and CI disposition (gate-hygiene)

Measured at HEAD `fa5e4bf5`, same sandbox, `python -m pytest tests/ -q -rEf
--continue-on-collection-errors`:

| Tree | Result |
| --- | --- |
| `main` @ `f9ced6b6b9` | 83 failed, 1569 passed, 34 skipped, 32 errors |
| branch @ `fa5e4bf5` | 83 failed, 1572 passed, 34 skipped, 32 errors |

The failing/error **node set** is byte-identical on both trees:
`sha256 479b022a5bfe8e1f89645ca0e223180567b1dddb043038fc7b7bd1c7e86af10a`
(116 unique node lines = 83 `FAILED` + 78 `ERROR` lines, **161** nodes). The
only delta is `+3 passed` on the branch, which is exactly the three tests added
by this PR. Zero regression, zero fixed node.

**Supersedes the counts in §7.** §7 records `15 failed / 1 error` (16 nodes) as
the pre-change baseline; the live re-measurement here records **161** nodes
(83F + 32E) on both trees. The environment delta (32 errors here vs 1 in that
run) is a dependency / CI-vs-sandbox difference, not a regression, and is not
attributable to this PR. Per the standing rule the load-bearing invariant is
node **identity** - measured here as identical - while counts move with
environment. This pass re-measured rather than inheriting a prior fingerprint.

**CI disposition at `fa5e4bf5`** (`gh api commits/<sha>/check-runs`): `validate`
= failure; every other check-run (Full-history secret scan, Vercel Preview
Comments, beta-beta-01-english, beta-beta-02-hausa, bundle-beta-evidence,
native-arkadia-golden-workflow) = success. `validate` (the "Enforce CP10
executable gates" job) is **also failure on `main` HEAD `f9ced6b6b9`** (run
`37954341298`), so its red is pre-existing and not branch-introduced. The branch
head's only red is the job that is red on `main` itself; PR #388's own gates
pass.

Note (subject of this PR): a green `validate` *conclusion* can mask a step whose
own `outcome` is a failure, or that executes zero tests - `steps.<id>.outcome`
is not available inside a `run:` block, and a collection error lets `pytest`
exit 0 while running nothing. The truthful reading of the step is its log, not
the job conclusion.
