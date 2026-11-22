# Gate hygiene — SolSpire R3 mutation-refusal contract

**Date:** 2026-11-22
**Base main:** `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Branch:** `gate-hygiene/solspire-r3-mutation-refusal-contract-01`
**Authority:** none requested — no merge, no deployment, no production acceptance.

## 1. Defect (measured on a clean `main` checkout)

`tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
is **red on `main`**:

```
$ python -m pytest tests/test_solspire_r3_execution_runtime.py -q
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
PermissionError: Engineering mutation is disabled in SolSpire ExecutionRuntime;
use the governed Weaver K15 -> K3 path. Blocked tools: fs_write
  solspire/execution_runtime.py:115
```

The test expected `runtime.execute(plan)` to **return** an `Execution` whose first
result carried `ok == False`, `code == "MUTATION_DISABLED"` and an `error`
naming K15/K3. The implementation raises `PermissionError` before any execution
is created.

The defect was invisible to CI: `.github/workflows/solspire-r3-validation.yml`
triggered only on `push` to `refs/heads/recon/solspire-r0`, so **no workflow
executed this file on `main`**. This is the already-recorded class "a guard no
workflow executes is decoration".

## 2. Which side is canonical — measured, not assumed

The raise is the canonical contract on three independent pieces of evidence:

1. **The method documents it.** `ExecutionRuntime.execute` docstring: "Start a
   SolSpire execution after rejecting engineering mutations. … Any engineering
   mutation tool is blocked *before a worker thread is created*."
2. **A production consumer depends on it.** `solspire/voice_pipeline.py:865-867`
   wraps `get_runtime().execute(plan, …)` in `except PermissionError as exc:` and
   converts the refusal into `EXECUTION_FAILED`. Replacing the raise with a
   returned result would silently change that consumer's behaviour.
3. **The `MUTATION_DISABLED` envelope belongs to a different surface.**
   `solspire/tools_github.py::commit_file` returns `{"ok": False, "code":
   "MUTATION_DISABLED", …}` and is pinned by `tests/test_solspire_r2_github_mutation.py`.
   The test imported that envelope's shape into the runtime, which never used it.

History agrees: `d6585687` (refactor) did not raise; the test was written at
`a42a1fe1`; `144d6015` ("Converge SolSpire and Weaver mutation boundaries")
introduced the pre-execution raise and the test was never updated.

## 3. Change

- `tests/test_solspire_r3_execution_runtime.py`
  - The stale expectation is replaced with the canonical one: `execute()` raises
    `PermissionError`; the message names the blocked tool and the governed
    `K15 -> K3` path; and no execution record is created (the refusal is
    pre-execution, which is the docstring's claim).
  - Parametrized over **all four** members of `_ENGINEERING_MUTATION_TOOLS`
    (`fs_write`, `github_commit`, `git_commit`, `git_push`) so the guard binds to
    the whole set rather than the one tool the original test used.
  - The read-only counterpart (`test_runtime_still_supports_read_only_workflow_steps`)
    is retained and referenced, so a runtime that refused *every* tool could not
    pass.
- `.github/workflows/solspire-r3-validation.yml`
  - `push` now also selects `main`; a `pull_request` trigger with an **identical**
    `paths` filter is added. Both name the workflow's own file and the test file
    it executes, satisfying `tests/test_ci_gate_trigger_coverage.py`
    (self-selection + push/pull symmetry) and
    `tests/test_gate_filter_selection.py` (executes -> selects).

No production code, no authority surface, and no governance module is changed.

## 4. Verification

| Check | Command | Result |
|---|---|---|
| Repaired suite | `pytest tests/test_solspire_r3_execution_runtime.py -q` | **6 passed** (4 parametrized + 2 retained) |
| Negative control | disable the refusal in `execution_runtime.py`, re-run | **4 failed, 2 passed** — exactly the parametrized nodes; file restored byte-identically (`git diff --stat` empty), **6 passed** |
| Trigger coverage | `pytest tests/test_ci_gate_trigger_coverage.py -q` | **99 passed** |
| Gate filter selection | `pytest tests/test_gate_filter_selection.py tests/test_ci_gate_trigger_coverage_ci_wiring.py -q` | **58 passed** |
| Gate integrity + injection + architecture | `pytest tests/test_m02a_ci_gate_integrity.py tests/test_workflow_injection_boundary.py tests/architecture -q` | **137 passed** |
| YAML parses | `yaml.safe_load(solspire-r3-validation.yml)` | ok |

`ci-gate-trigger-coverage.yml` selects `.github/workflows/**`, so this workflow
change is itself judged on `pull_request` and on `push` to `main`.

## 5. Boundary classification

- Repository-source repair: **VERIFIED** (tests above).
- CI execution of the widened gate: **NOT CLAIMED** until a run exists at the
  branch head; a push/PR run is the observation that closes it.
- Merge, deployment, production acceptance: **NONE** — human authority.

## 6. Recorded, not repaired (separate workstreams)

- `tests/test_solspire_r1_governance_convergence.py` has **2** failures on `main`
  (a `pass_id` divergence between the SolSpire and Weaver builders, and an
  `execute_patch` literal absent from `weaver/governance.py`). Repairing them
  touches `weaver/governance.py`, an authority-adjacent surface, so it is
  proposed rather than executed.
- `data/engineering_lab/` is created as untracked runtime output by the test
  session; sandboxing it is owned by open PR #688 and is not staged here.
