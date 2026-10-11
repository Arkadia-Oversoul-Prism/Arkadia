# EVIDENCE — prism-console-contract-ci-gating-01

Bounded objective: make the console-contract guards **executed** by a workflow, so the
console boundary (`web/arkadia_console` + `api/frontend_routes.py`) is judged by a gate
rather than only by a human running the suite by hand.

Authority: read-only reconstruction, repository mutation on a dedicated branch, PR.
No merge, no deployment, no production acceptance. `main` is untouched.

## 1. Measurement that established the gap

At `main` `f390526ab14e122fef358ef9b9e1cd438509463c` (2026-10-11T13:19:23+01:00):

```
grep -l arkadia_console .github/workflows/*.yml
# sg-02-fe-2-v.yml
# n-atlas-developer-lab.yml
# canonical-render-browser-smoke.yml
# canonical-render-runtime-probe.yml
```

Of those four, **only** `n-atlas-developer-lab.yml` executes a console-contract guard,
and only one of them:

```
grep -n 'test_canonical_frontend_routing' .github/workflows/n-atlas-developer-lab.yml
# 22:      - "tests/test_canonical_frontend_routing.py"
# 50:        run: python -m pytest tests/test_canonical_frontend_routing.py -q
```

`sg-02-fe-2-v.yml` runs `python -m pytest tests/ -q` on a step that is
`continue-on-error: true` (recorded pre-existing debt), so its console-guard coverage
cannot fail the job. `canonical-render-*.yml` run no `pytest` at all
(`grep -n pytest .github/workflows/canonical-render-browser-smoke.yml` → 0 matches); they
are browser/runtime probes.

**Conclusion:** eleven of the twelve console-contract guards had no executing gate. A
rewrite of a console guard, of the console source, or of the serving path produced no
contract check-run.

## 2. Derived domain (from `git ls-files`, not from prose)

A guard belongs to the domain when it names the console tree or the serving path.
Derivation is at test time in `tests/test_prism_console_ci_wiring.py::_console_domain`.

The first derivation used slash-only needles and returned **6** guards, silently
omitting six that build the path with `Path` segments
(`"web" / "arkadia_console"`). The guard's own
`test_domain_is_derived_and_not_empty` assertion on
`tests/test_canonical_frontend_routing.py` caught it — that file references
`api.frontend_routes` and `tmp_path / "web" / "arkadia_console" / "dist"` and no
slash-joined literal. Needles now include the joined spellings; the domain is **12**:

```
tests/test_aeas05_canonical_frontend_acceptance.py
tests/test_canonical_frontend_routing.py
tests/test_console_endpoint_registry_contract.py
tests/test_console_shell_nav_contract.py
tests/test_frontend_arkadia_console_rebuild_01.py
tests/test_frontend_script_assets_resolve.py
tests/test_knowledge_os_boundary.py
tests/test_knowledge_search_boundary.py
tests/test_prism_opportunity_radar_module.py
tests/test_prism_w4_arkana_thread_history.py
tests/test_prism_w4_lab_read_model.py
tests/test_solariun_knowledge_slice_01.py
```

Measured: `184 passed in 3.96s` for the whole domain on `main`.

## 3. Change

| Path | Change |
| --- | --- |
| `.github/workflows/prism-console-contract.yml` | new gate: executes the 12 guards, `paths` filter covers the judged surfaces + every guard + itself, `workflow_dispatch` present, `permissions: contents: read` |
| `tests/test_prism_console_ci_wiring.py` | new wiring guard (21 tests), domain derived from `git ls-files`, generic invariants + 13 detector controls |
| `docs/control-plane/evidence/prism-console-contract-ci-gating-01/EVIDENCE.md` | this record |

`api/main.py` is untouched; `python -m py_compile api/main.py` → OK.

## 4. Invariants the wiring guard states

Stated over every workflow that references the domain (not against one file), so a
second wiring is judged by the same rule and deleting this one cannot make the
assertions vacuous:

1. At least one workflow executes the **whole** derived domain. A mention is not an
   execution: `pytest` must be the invoked command word (`pytest x`,
   `python -m pytest x`), and the guard must be an argument to it (file, `file::test`,
   or the containing directory).
2. A complete gate is selected by `web/arkadia_console/**`, `api/frontend_routes.py`,
   every guard it runs, and its own file.
3. A complete gate is dispatchable (`workflow_dispatch`).
4. A complete gate's executing steps can fail the run (no step/job
   `continue-on-error`, no step/job `if: false`).

Invariant 4 is deliberately scoped to the *complete* gate(s): `sg-02-fe-2-v.yml` runs
the suite on a `continue-on-error: true` step as pre-existing debt owned by another
workstream, and repairing it here would be scope expansion. That debt is recorded, not
fixed.

## 5. Proof

### 5.1 Wiring guard

```
python -m pytest tests/test_prism_console_ci_wiring.py -q -rEf
# 21 passed in 3.67s
```

### 5.2 Live negative controls (on the real workflow file, restored byte-identically)

Each mutation was applied to `.github/workflows/prism-console-contract.yml`, the guard
run, and the file restored from a copy verified by `sha256sum -c`:

| Mutation | Guard result |
| --- | --- |
| executing step → `echo pytest -q` (mention, not execution) | `2 failed, 17 passed, 2 skipped` |
| job-level `continue-on-error: true` on the real gate | `2 failed, 17 passed, 2 skipped` |
| one guard dropped from the `paths` filter | `1 failed, 20 passed` |
| restore | `.github/workflows/prism-console-contract.yml: OK` |

The 2 skipped nodes in mutations A and B are the `test_complete_gate_*` parametrisations
— with no complete gate left, they have no case to run. That is the invariant reporting
the defect, not a silent pass: the domain assertion reddens in the same run.

### 5.3 Detector controls (in-file, 13)

Positive: the wired shape, and `pytest tests/ -q` (directory invocation). Negative:
`echo <guards>`, comment-only mention, `echo pytest <guards>`,
`printf %s pytest <guards>`, `echo 'python -m pytest <guards>'`, partial domain,
undispatched gate, filter selecting one guard, step/job `continue-on-error`, step/job
`if: false`. A workflow that does not mention the domain is not judged.

### 5.4 Protected surfaces

```
python -m pytest tests/architecture -q      # 11 passed
python -m py_compile api/main.py            # OK (boot code, P1-A guard)
printf '<both new paths>' | python scripts/cp10_mutation_boundary_policy.py --judge
# Mutation boundary PASS (M02A legitimate-surface + constitutional denylist); exit 0
```

The two new paths are admitted by the existing CP10 rules (`tests/…`,
`.github/workflows/…`); no allowlist edit was needed.

### 5.5 Regression — failing/error node SET unchanged

Both trees measured in this same environment with
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`:

| Tree | Result | Failing/error nodes |
| --- | --- | --- |
| `main` `f390526` (baseline) | `22 failed, 2342 passed, 22 skipped, 1 error` | 23 |
| branch | `22 failed, 2368 passed, 22 skipped, 1 error` | 23 |

`comm -3` on the sorted node lists is **empty** — zero new, zero repaired. The `+26
passed` is attributed by `--collect-only` per file, not inferred:

| File | base | branch |
| --- | --- | --- |
| `tests/test_prism_console_ci_wiring.py` (new) | — | 21 |
| `tests/test_ci_gate_trigger_coverage.py` (iterates `.github/workflows/*.yml`) | 63 | 66 |
| `tests/test_workflow_injection_boundary.py` (iterates `.github/workflows/*.yml`) | 35 | 36 |
| `tests/test_ci_suite_collection_continuation.py` | 38 | 39 |
| whole suite | 2385 | 2411 |

A new workflow file adds passing nodes to the generic workflow-scanning suites by
construction (+5). 21 + 5 = 26, which is exactly the observed delta.

## 6. Runtime proof — the gate executes (observed)

The gate is no longer a source-level claim. Opening PR #435 fired the `pull_request`
event, and the new gate selected itself and ran:

| Observation | Value |
| --- | --- |
| run | **`38145306304`**, event `pull_request`, `completed/success` |
| head | `a91d8e4da19d2ecf727c3f72fc3c61b1d7ca1b8a` |
| job | `console-contract` -> `success` |
| step "Verify the console contract guards" | `184 passed in 4.83s` |
| step "Console-contract CI-wiring guard" | `21 passed in 3.57s` |
| all check-runs on that commit | 8, every one `success` |
| PR #435 state | `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN` |

Both steps report an explicit pass count, so this is **not** the "green job that
executed zero tests" class: the numbers are the same 184 and 21 measured locally, and a
zero-collection run would print `no tests ran`.

Still outstanding for full closure: `workflow_dispatch` at `ref=main` after merge. That
cannot be performed by this pass (it requires the gate on the default branch) and is the
next action after human merge.

## 7. Limitations and next action

- Before this pass, the gate was a **repository-source** claim; §6 now records its first
  execution. `workflow_dispatch` at `ref=main` remains unproven until after merge.
- `sg-02-fe-2-v.yml`'s `continue-on-error: true` suite step is **recorded debt**, not
  repaired here (separate workstream, and it belongs to the CP10 gate's owner).
- The guard does not attempt to prove the 12 guards *pass* — it proves they are
  *executed*. Passing is the gate's job at run time.
- No production observation is made or claimed. Production acceptance stays
  `NOT CLAIMED`.
