# gate10/gate-filter-selection-01 — a workflow that executes a test file must select it

**Status:** IMPLEMENTED — repair proven locally, PR open, human merge required.
**Branch:** `gate10/gate-filter-selection-01`
**Base:** `main` @ `850216fc99b0eab66a66f8a8290c0db33823b681`
**Sibling of:** `docs/control-plane/evidence/gate10-prism-console-contract-domain-completion-01/` (PR #439)

## 1. Defect (measured, not inferred)

Two guards already exist over workflow `paths` filters, and neither states this invariant:

| guard | invariant |
|---|---|
| `tests/test_m02a_ci_gate_integrity.py` | the `push` and `pull_request` filters of one workflow are identical |
| `tests/test_ci_gate_trigger_coverage.py` | a workflow that runs pytest selects its own file |

Both are silent when a workflow's filters **agree** while a test file its step *explicitly
names* is selected by neither. That is the measured state of `main` @ `850216fc`: three
workflows execute named test files that their `paths` filters do not select, so a change to
one of those files is judged by **no gate at all** — the "a guard no gate executes is
decoration" class, in its filter-selection form.

Measured by the new guard's own helpers against the pristine `HEAD` workflows
(`git show HEAD:<workflow>`), so the number is reproducible rather than transcribed:

| workflow | event | omitted guards |
|---|---|---|
| `prism-execution-workevent-governance.yml` | `pull_request` | 4 |
| `sg-02-fe-2-v.yml` | `pull_request` | 9 |
| `sg-02-fe-2-v.yml` | `push` | 9 |
| `solspire-r1-validation.yml` | `push` | 1 |

**Pre-repair total: 23** executed-but-not-selected findings. **Post-repair total: 0.**

The `sg-02-fe-2-v.yml` case is the sharpest: its step *SolSpire isolated runtime and
integration contract tests* is **blocking** (no `continue-on-error`) and runs nine named
guards, none of them selected. The nine are reached only through that step, so nothing else
runs them either — `provider-routing.yml` (the only other full-suite workflow) is
path-filtered to `weaver/**`, `providers/**` and a handful of named files.

## 2. Precondition verified before widening any filter

Widening a filter is only safe if the newly-selected guards pass on `main`, or the repair
would redden unrelated PRs. Measured: the 14 omitted guards named by the repaired filters
yield **86 passed, 1 skipped** (exit 0) on `main` @ `850216fc`.

## 3. The guard

`tests/test_gate_filter_selection.py` (294 lines, 44 nodes) states the invariant generically
over the live corpus:

> for every workflow W, every event E with a `paths` filter, and every tracked test file T
> that a step of W names as a pytest argument: E's filter must select T.

Two design points carry the soundness:

- **Execution, not mention.** `pytest` must be the *invoked command word* — directly, or
  after `python -m` — and the file must be an argument to it. `echo pytest tests/x.py` and a
  commented-out line yield nothing. (This is the defect PR #408 corrected in
  `test_solspire_route_composition_ci_wiring.py`; the same hole is not reopened here.)
- **Directory arguments are excluded.** `pytest tests/` and `pytest tests/architecture`
  reach every file beneath them; requiring a filter to enumerate that membership would
  restate the corpus and drift. Those are judged by `test_ci_gate_trigger_coverage.py` and
  the per-surface wiring guards, which derive their own domain at test time.

## 4. Repair (4 workflow files, 1 new test file)

| file | change |
|---|---|
| `.github/workflows/prism-execution-workevent-governance.yml` | +4 guards to `pull_request` paths |
| `.github/workflows/sg-02-fe-2-v.yml` | +9 guards to **both** `pull_request` and `push` paths |
| `.github/workflows/solspire-r1-validation.yml` | +1 guard to `push` paths |
| `.github/workflows/ci-gate-trigger-coverage.yml` | select + execute the new guard (self-wiring) |
| `tests/test_gate_filter_selection.py` | new guard |

`sg-02-fe-2-v.yml` is patched in both filters because
`tests/test_m02a_ci_gate_integrity.py` requires filter parity; the identical insertion keeps
that guard green. `solspire-r1-validation.yml` is repaired in `push` only, because that is
the only filtered event it declares (`workflow_dispatch` has no `paths`).

## 5. Proof

**Negative control (live, on the real workflow file).** Dropping
`tests/test_phase10_binding.py` from *both* `sg-02-fe-2-v.yml` filters — the realistic
regression shape — reddens **3** nodes: `test_detector_flags_the_omitted_named_guard`,
`test_no_workflow_omits_a_test_file_it_executes`, and
`test_executed_files_are_selected_or_the_workflow_is_unfiltered[sg-02-fe-2-v.yml]`.
Restored byte-identically (`git diff --stat` back to +26 insertions) and re-verified
`44 passed`. The filter-parity guard stayed green throughout, which is the measured
demonstration that this guard catches what the existing one cannot.

**Regression boundary (same environment, both trees).**

| tree | result |
|---|---|
| `main` @ `850216fc` (worktree) | 18 failed, 2642 passed, 21 skipped, 1 error |
| branch | 18 failed, 2686 passed, 21 skipped, 1 error |

Failing/error **node sets** are byte-identical — `comm -3` empty, both hashing to
`f536ec6b63b5a136fda92d2bb98b30935a8b010397f141fbb76a5eab7b9ab12c` (19 nodes).
The `+44 passed` is exactly the new file's node count (`--collect-only` → 44), not a
behavioural change. Attribute by node identity, never by totals: the same `main` SHA has
been reported as both 17 and 18 failing nodes by different measurements.

**Other checks:** architecture `11 passed`; CP10 mutation boundary `PASS` on the changed
path set; sibling workflow-scanning guards (`test_workflow_injection_boundary.py`,
`test_m02a_ci_gate_integrity.py`, and the four other `*_ci_wiring.py` guards) `163 passed`.
`api/main.py` is untouched (2505 lines, under the 2600 budget); `py_compile` OK.

## 6. Remaining uncertainty

- The repair is **source-level**. No dispatched CI run is claimed here; the gate's own
  execution on this PR is the runtime observation, and it will trigger because the filter
  selects `tests/test_gate_filter_selection.py` and `.github/workflows/**`.
- `sg-02-fe-2-v.yml` step 21 (`CP10-B broader backend regression`) remains
  `continue-on-error: true` with a self-satisfying `steps.<id>.outcome` assertion in step 35.
  That is a **separate** defect recorded in repository memory and is deliberately **not**
  repaired here — repairing it would widen this pass's scope into gate-enforcement
  semantics.
- The recurrence risk is structural: three hand-maintained lists per gate drift again on the
  next guard. Executing a derived domain directly (a committed runner script) removes the
  class, but widens an execution surface — a separate bounded workstream for sovereign
  review. Discovery does not authorize execution.
