# GATE-10 · CP10-B broad-suite collection continuation — the "executes nothing" defect

Bounded repair. One token in one workflow plus a regression guard. No application
code, no authority surface, no `api/main.py`, no merge.

- **BASE_MAIN** := `850216fc99b0eab66a66f8a8290c0db33823b681` (`gate10: repair ADR-016
  static-corpus freshness pin`, 2026-10-11T20:39:56+01:00)
- **Branch** := `gate10/cp10-broad-suite-collection-continuation-01`
- **Measured** 2026-10-12 in the canonical clone, pytest 9.1.1 / PyYAML 6.0.3.

## 1. The defect (reproduced at `850216fc`)

`sg-02-fe-2-v.yml` step `CP10-B broader backend regression` ran the whole suite
with `continue-on-error: true` and **no** `--continue-on-collection-errors`:

```
run: python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
```

A bare `python -m pytest tests/ -q` on this tree yields
`1 skipped, 76 errors in 5.70s` — the session is **interrupted** by the collection
errors (dependency-shaped in this environment, e.g. `providers/local.py` →
`ModuleNotFoundError: No module named 'httpx'`, plus the known CE-01
`weaver.autonomy` module-vs-package collision), so **zero tests execute**.

Runtime corroboration (recorded in the prior reconnaissance, run `38186457230`,
head `12f8a0a6`), the CP10-B step log:

```
2026-10-12T00:02:44.3072158Z ##[group]Run python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
2026-10-12T00:02:54.5891640Z !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

### Why it matters (the coverage hole, measured)

Exactly **two** broad-suite surfaces exist repo-wide (a step running `pytest` with a
directory/whole-suite target rather than named files, enumerated by parsing every
`.github/workflows/*.yml`):

| Workflow | Step | `continue-on-error` | flag |
|---|---|---|---|
| `provider-routing.yml` | Broader test suite | `None` (judging) | **present** |
| `sg-02-fe-2-v.yml` | CP10-B broader backend regression | `true` (reporting) | **absent** |

`provider-routing.yml` is path-filtered to `.github/workflows/provider-routing.yml`,
`weaver/**`, `providers/**`, `tests/architecture/**` and three named test files. It is
**not** selected by `spiral_grove/**` or `lab/**`. `sg-02-fe-2-v.yml` **is** selected by
those paths (its `push`/`pull_request` filters include `spiral_grove/**`, `lab/**`,
`api/lab_routes.py`, `lab/council/**`, `lab/evolution/**`, `lab/execution/**`). So
without the flag, a `spiral_grove/**` or `lab/**` pull request reaches **no**
whole-suite execution at all.

`continue-on-error` is **not** the defect — a non-judging surface need not gate. The
defect is that the step also *executes nothing*, so it cannot even *report* the debt it
exists to surface.

## 2. The repair

One token, in one already-selected file:

```diff
-        run: python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
+        run: python -m pytest tests/ -q --continue-on-collection-errors 2>&1 | tee cp10-backend.log
```

Plus a comment naming the defect class. The step **stays** `continue-on-error: true`:
it reports the suite and its pre-existing debt, it does not gate. The flag does not hide
debt — the collection errors and pre-existing failures are still reported — it only stops
the session aborting before the suite runs. This mirrors the already-merged,
already-executed form in `provider-routing.yml`:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

**Does not turn `main` red for debt it did not introduce.** The step is non-gating, so its
status is unchanged; only its *content* changes from "nothing" to "the suite, reported".
The downstream enforcement step asserts `steps.backend.outcome`, which is unaffected.

## 3. The guard (and its controls)

`tests/test_ci_suite_collection_continuation.py` is extended, not rewritten. The existing
file deliberately exempted `continue-on-error` steps from its judging-surface assertion
(`_judging_broad_suite_steps`); that exemption is exactly the gap Defect A fell through.
The new assertion covers the reporting surface **generically**, parametrized over every
`.github/workflows/*.yml`:

- `test_broad_suite_steps_reach_the_suite` — every broad-suite step must carry the flag,
  whether or not it gates.
- `test_negative_control_live_workflow_flags_the_pre_repair_step` — strips the flag from
  the **real** `sg-02-fe-2-v.yml` text and asserts the detector flags it. A synthetic
  fixture would not prove the assertion reads the live file.
- `test_positive_control_live_workflow_step_carries_the_flag` — the live file must carry
  the flag, or the control proves nothing.
- `test_negative_control_continue_on_error_step_is_not_a_judging_surface` (pre-existing) —
  `continue-on-error` still disqualifies a step from *judging*.

The guard is itself **judged**: `provider-routing.yml`'s `pull_request.paths` names
`tests/test_ci_suite_collection_continuation.py`, so editing this file executes the guard.

### Live negative control (performed, then restored byte-identically)

Stripped the flag from the real `.github/workflows/sg-02-fe-2-v.yml`:

```
FAILED tests/test_ci_suite_collection_continuation.py::test_broad_suite_steps_reach_the_suite[sg-02-fe-2-v.yml]
E  AssertionError: sg-02-fe-2-v.yml: broad-suite step 'CP10-B broader backend regression'
   runs the whole suite without --continue-on-collection-errors; the known collection
   error interrupts the session and no test executes
1 failed, 85 passed in 0.82s
```

Restored byte-identically (`git diff --stat` → 9 insertions, 1 deletion, the intended
change only) → `86 passed`.

## 4. Verification

| Check | Result |
|---|---|
| `pytest tests/test_ci_suite_collection_continuation.py -q` | **86 passed** |
| live negative control (flag stripped from real workflow) | **1 failed** (the intended node) |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | OK (`api/main.py` untouched) |
| CP10 boundary judge on the changed paths | **PASS** (exit 0) |
| workflow YAML parse | OK, 34 steps; `continue-on-error: True` preserved |

### Regression boundary

`api/main.py` untouched (boot-code budget unaffected). No authority surface, no
`api/lab_routes.py`, no `scripts/cp10_mutation_boundary_policy.py`. The change set is
`.github/workflows/sg-02-fe-2-v.yml` and
`tests/test_ci_suite_collection_continuation.py` only.

## 5. Composition with sibling PRs (measured, not assumed)

Two open GATE-10 PRs touch the contested file `.github/workflows/sg-02-fe-2-v.yml`:

- **#458** (`gate10/select-every-test-file-a-gate-executes`, head `30c87f26`) — trigger
  paths (`on: paths`, ~line 26) and a blocking SolSpire isolated-runtime step.
- **#459** (`gate10/ci-verdict-steps-can-fail`, head `12f8a0a6`) — the Grove step's
  `id: grove` / `set -o pipefail` / outcome assertion (~line 187).

This repair touches the **CP10-B step** (~line 210-222), a region disjoint from both.
Composition was checked by `git apply --3way` of each sibling patch onto this branch's
head (`4f876645`) in a detached worktree:

```
git worktree add --detach /tmp/wt-compose 4f876645
git apply --3way /tmp/pr459.patch   # exit 0
git apply --3way /tmp/pr458.patch   # exit 0
git status --short | grep -E '^(UU|AA|DD)'   # NO CONFLICTS
grep -n continue-on-collection-errors .github/workflows/sg-02-fe-2-v.yml
  -> 251: run: python -m pytest tests/ -q --continue-on-collection-errors ...
```

**Semantic check (conflict-free is not proof of compatibility):** on the composed tree,

```
pytest tests/test_ci_suite_collection_continuation.py \
       tests/test_gate_filter_selection.py \
       tests/test_ci_gate_trigger_coverage.py -q
  -> 217 passed
```

All three guards hold together, and the CP10-B step survives composition with the flag
intact. Merge order is the sovereign's; the three regions are textually and semantically
independent.

## 6. What is NOT claimed

- No merge. Human sovereign retains merge authority.
- This is a **repository-source** repair; the flag's effect in CI is proven by the
  already-merged `provider-routing.yml` precedent and by local reproduction, not by a new
  CI run of `sg-02-fe-2-v.yml` on this branch (the branch is not yet pushed).
- Defect B (`steps.<id>.outcome` unavailable in `run:`) is **owned by #459**; Defect C
  (the `tests/` directory-argument exclusion in #458's guard) is **owned by #458**.
  Recorded as corroboration only; not duplicated here.
- The 177 broad-suite-only test files are **not** classified as decoration: a real
  whole-suite surface covers them once CP10-B reaches the suite.
