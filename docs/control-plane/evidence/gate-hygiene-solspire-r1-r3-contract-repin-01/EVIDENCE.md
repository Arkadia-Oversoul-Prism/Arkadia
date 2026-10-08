# EVIDENCE — gate-hygiene/solspire-r1-r3-contract-repin-01

| field | value |
|---|---|
| base main | `f96d5fd27d40110196ec22b114808efc0eb9dc05` |
| branch | `gate-hygiene/solspire-r1-r3-contract-repin-01` |
| objective | repair three uncovered failing nodes — `test_solspire_r1_governance_convergence.py` ×2 and `test_solspire_r3_execution_runtime.py` ×1 — test-side only |
| change set | `tests/test_solspire_r1_governance_convergence.py`, `tests/test_solspire_r3_execution_runtime.py`, this evidence dir, `AGENTS.md` (append only) |
| production code touched | **none** — no source, policy, authority, or mutation path changed |
| architecture | 11/11 |
| full suite (main) | 16F / 1770P / 22S / 1E |
| full suite (branch) | **13F / 1773P / 22S / 1E** |
| node delta | **−3 removed, 0 added** |
| node-set sha256 (main) | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` |
| node-set sha256 (branch) | `60ad29ee7d25afed3465bf72dda388265ee1185f8a89dfd859ac970ea6166919` |
| `api/main.py` | untouched, compiles, 2462 / 2600 |
| status | **VERIFIED** (targeted + full-suite delta measured against a freshly built `main` worktree) |
| authorization | sovereign merge only |

## 1. Why these three nodes

They are the genuinely **uncovered** failures on `main`: no open PR modifies
`tests/test_solspire_r1_governance_convergence.py`,
`tests/test_solspire_r3_execution_runtime.py`, `solspire/execution_runtime.py`,
`solspire/project_execution.py`, or `weaver/governance.py`. Verified by enumerating all open PRs
and their changed files (`GET /pulls/{n}/files`) — zero hits.

They are also **contract re-pins**, not behaviour defects: in each case the production boundary is
intact and the assertion still describes a superseded refusal *shape* or a superseded module
location. Nothing here changes what the system does.

## 2. `test_r1_solspire_builders_delegate_to_weaver` — unequal arguments

The node compares SolSpire's builder output against the canonical Weaver builder output, but it
passed a `pass_id` to only one side:

```
sol_spec       = build_pass_spec_for_patch(project, patch, repo_root=repo_root)
canonical_spec = weaver_build_spec(patch, pass_id="mvp1-r1-patch", objective="R1 Project", ...)
```

SolSpire derives a default when the caller supplies none
(`solspire/project_execution.py:47`,
`f"mvp1-{hashlib.sha256((patch.get('patch_id') or 'x').encode()).hexdigest()[:10]}"`, introduced in
`3bf582f1` WEAVER-MVP1). The canonical builder requires one. The test therefore compared two
*different arguments* and reported the expected difference as a delegation failure:

```
AssertionError: assert 'mvp1-50c0ee9b89' == 'mvp1-r1-patch'
```

Measured: with **equalized inputs** the two builders produce byte-identical `PassSpec` and
`PatchApproval` dictionaries. The property under test (SolSpire delegates to Weaver) holds; the
harness did not exercise it. The repair passes the same `pass_id` and `objective` to both sides.

## 3. `test_r1_weaver_governance_is_canonical` — superseded module location

The node asserted `"execute_patch" in inspect.getsource(weaver.governance)`. `execute_patch` is
canonical Weaver code, but it lives in `weaver.execution` — the module that performs the governed
K3 execution — not in the narrowly scoped `weaver.governance`. The node pinned a module
*location* that the convergence deliberately moved.

Measured on the live tree:

- `"def execute_patch" in inspect.getsource(weaver.execution)` → **True**
- `"def execute_patch" in inspect.getsource(weaver.governance)` → **False**
- `solspire.project_execution.execute_patch is weaver.execution.execute_patch` → **True**

The repair pins the real owner, asserts the narrow governance module does *not* carry a local copy,
and proves SolSpire re-exports that same object. This is the stronger statement: the original
assertion would also pass if `governance` carried a divergent duplicate.

## 4. `test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` — refusal shape drifted

The node asserted the **per-step result-dict** refusal:

```
execution = runtime.execute(_plan("fs_write"), owner_uid="r3-user")
assert execution.results[0]["code"] == "MUTATION_DISABLED"
assert "K15" in execution.results[0]["error"]
```

The runtime was later converged (ancestor `144d6015`) to reject the plan **before a worker thread
exists**, so `execute()` raises and no `Execution` is ever returned. Measured on the live tree:

- `_ENGINEERING_MUTATION_TOOLS = frozenset({"fs_write", "git_commit", "git_push", "github_commit"})`
- each tool → `PermissionError` naming both `K15` and `K3` and the offending tool
- `"MUTATION_DISABLED" in inspect.getsource(solspire.execution_runtime)` → **False**
- read-only step (`fs_list`) still completes → the runtime remains available for non-engineering work

The boundary is unchanged and in fact *stronger* (refusal precedes execution). The per-step branch
at `solspire/execution_runtime.py:243` is now unreachable for engineering tools — it survives only
as dead defensive code. The repair asserts the raise, and adds `runtime._executions == {}` to prove
refusal precedes execution.

The pre-repair expectation is retained **verbatim** in the node docstring, per the repository's
practice for strict-pin reconciliation, so the drift stays reconstructable.

A **non-vacuity guard** (`{"fs_write", "github_commit"} <= _ENGINEERING_MUTATION_TOOLS`) prevents
the loop from passing if the tool set is ever emptied.

## 5. Regression proof — node identity, not counts

Full suite run on a freshly built `origin/main` worktree and on the branch, same environment, same
flags (`-q -rEf --continue-on-collection-errors -p no:randomly`), `pyyaml` installed and
`PYTHONPATH=<repo>/archive/legacy_python` set:

| tree | result |
|---|---|
| `main` `f96d5fd2` | 16 failed, 1770 passed, 22 skipped, 1 error |
| branch | 13 failed, 1773 passed, 22 skipped, 1 error |

`comm` on the sorted `FAILED`/`ERROR` node lists:

**Removed (repaired):**
```
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**Added (regressions):** *none*

Residual `main` debt is untouched and unattributed to this change: `test_autonomy.py` collection
error (CE-01 module-vs-package collision, reserved to the sovereign), 3 × `test_m02a_ci_gate_integrity`,
3 × `test_steward_filter`, 2 × `test_engineering_lab_api` (carried by open PR #356),
`test_ci_gate_trigger_coverage[n-atlas-developer-lab.yml]` (carried by open PR #355), plus 4 others.

## 6. Guard results

| check | result |
|---|---|
| `tests/architecture` | **11 passed** |
| R1 + R3 + `test_weaver_mvp2_exec_binding.py` (workflow-owned) | **21 passed** |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` budget | 2462 / 2600 |

## 7. Remaining uncertainty

- `_ENGINEERING_MUTATION_TOOLS` is private (underscore-prefixed). The test imports it, as the
  pre-repair node already did for the runtime and `_plan`; no new coupling class is introduced.
- The dead per-step branch at `execution_runtime.py:243` is left in place. Removing it is a
  source-side decision and is **not** in this change set.
- The `-1` in `test_engineering_lab_api` is carried by open PR #356, which is green and awaiting
  sovereign review; it will land when that PR merges.

## 8. Authorization

Sovereign merge only. No production code, authority path, or mutation path is modified.
