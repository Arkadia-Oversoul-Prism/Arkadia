# GATE-10 — OpenAPI security-metadata trigger-filter parity + execution of the trigger-coverage guard

## Objective

Repair the measured defect on `main` where a workflow declares an asymmetric
`push` / `pull_request` `paths` filter, and close the class that let it land: the
guard which states trigger-parity was executed by **no** workflow on a
workflow-only change.

## Observed defect (live evidence)

| Fact | Value |
| --- | --- |
| `main` at first observation | `7097d6a4` — "Declare OpenAPI security metadata per operation" |
| `main` at repair base | `36df0ea8` — "test: add production authenticated Render acceptance workflow" |
| failing node on `main` @ `36df0ea8` | `tests/test_ci_gate_trigger_coverage.py::test_push_and_pull_request_filters_are_identical[openapi-security-metadata.yml]` |
| failure message | `Extra items in the right set: 'tests/test_forge_openapi_security_boundary.py'` |

Commit `7097d6a4` added `.github/workflows/openapi-security-metadata.yml` with
`tests/test_forge_openapi_security_boundary.py` present in the `pull_request` `paths`
filter but absent from the `push` filter.

## Attribution (which commit introduced the failure)

Measured on `main` @ `36df0ea8`: the failing/error node set **minus** the new gate node
hashes to
`716df34bc5a6ad51dd122ffb09175f1be7883f85a5f4bc07dc12831109b0a45e`, which equals the
recorded baseline at `7b672157`. The asymmetric filter is the only new failure and is
introduced by `7097d6a4`.

## Root cause of the class — the guard executed nowhere

`grep -rn test_ci_gate_trigger_coverage .github/workflows/` named no dedicated gate. Its
only execution site was the full-suite step inside `provider-routing.yml`
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`), and that workflow is
path-filtered to `weaver/**`, `providers/**` and a handful of named files. A commit that
changes only a workflow — precisely the surface this guard judges — therefore runs the
guard nowhere.

Runtime proof: at `36df0ea8` `commits/<sha>/check-runs` returns `total_count: 1`, and the
single run is `Full-history secret scan`. No gate judged the merge that left `main` red.

This is the repository's own named class: *a guard no workflow executes is decoration*,
already closed for `test_baseline_fingerprint.py` and `test_boot_syntax_boundary.py`.

## Change (bounded)

1. `.github/workflows/openapi-security-metadata.yml` — add
   `tests/test_forge_openapi_security_boundary.py` to the `push` `paths` filter so it
   matches `pull_request` (one inserted line).
2. `.github/workflows/ci-gate-trigger-coverage.yml` (new) — a dedicated gate that runs
   `tests/test_ci_gate_trigger_coverage.py` and its wiring guard, path-filtered to
   `.github/workflows/**` so a workflow-only change executes it. Mirrors the established
   `boot-syntax.yml` pattern. `workflow_dispatch` present; `permissions: contents: read`.
3. `tests/test_ci_gate_trigger_coverage_ci_wiring.py` (new) — states the invariant over
   **every** workflow that runs the guard: a workflow runs it on `pull_request`; the
   filter selects **every tracked workflow file** (domain derived from `git ls-files` at
   test time, never restated); the step can fail the job. Carries its own detector
   controls.

## Verification

| Check | Command | Result |
| --- | --- | --- |
| Defect repaired | `pytest tests/test_ci_gate_trigger_coverage.py -q` | before: 1 failed / 74 passed; after: **75 passed** |
| Filter parity | yaml parse of both filters | `push == pull: True` |
| Wiring guard | `pytest tests/test_ci_gate_trigger_coverage_ci_wiring.py -q` | **7 passed** |
| Guard + wiring | `pytest tests/test_ci_gate_trigger_coverage*.py -q` | **85 passed** |
| CP10 corpus integrity | `pytest tests/test_m02a_ci_gate_integrity.py -q` | **68 passed** |
| CP10 admission (judge) | `scripts/cp10_mutation_boundary_policy.py --judge` | all changed paths ADMIT (exit 0) |

### Negative control (the wiring guard bites)

Removing the `.github/workflows/**` entry from the real gate file reddens
`test_guard_workflow_is_selected_by_every_tracked_workflow[ci-gate-trigger-coverage.yml]`
(`1 failed, 6 passed`); restoring the file byte-identically returns **7 passed**.

### Regression boundary

Full suite compared by failing/error **node set**, not counts:

| Tree | Result | Node-set sha256 |
| --- | --- | --- |
| `main` @ `36df0ea8` | 18 failed, 2614 passed, 20 skipped, 1 error | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` |
| branch head | 18 failed, 2626 passed, 20 skipped, 1 error | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` |

`comm -3` on the node sets is empty — **zero node-set delta**. The `+12 passed` is the
new guard file plus the generic workflow-scanning suites that gain a passing node for each
new workflow file (the console gate node has left the failing set because the defect is
repaired).

## Remaining uncertainty / limitations

- `tests/test_ci_gate_trigger_coverage.py`'s own domain is **every workflow that runs
  pytest**. The new gate is dispatched on the corpus of workflow files, but if a future
  workflow runs `pytest` while declaring no `paths` filter, GitHub executes it on every
  change and the guard's node is still judged — this is the intended coverage.
- `test_ci_gate_trigger_coverage.py` asserts `push == pull`. Workflows that legitimately
  restrict `push` to `branches: [main]` while broadening `pull_request` are out of scope;
  no such workflow is currently failing the guard.
- No production/deployment claim is made. This is a repository-source and CI-wiring repair.

## Authority boundary

No merge, no production action. A human merges. No deferred follow-on work is included.

## Composition note (recorded, not executed)

PR #447 and PR #450 both modify `.github/workflows/prism-console-contract.yml` and are
**not** textually disjoint. They are not part of this repair; recorded so a batch merge
does not treat them as independent.
