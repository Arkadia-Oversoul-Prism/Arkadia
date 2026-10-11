# EVIDENCE — prism-console-contract-domain-derivation-01

Bounded objective: repair the **measured** `console-contract` gate defect. PR #435
gave the console-contract guards an executing gate, but its gate carried a **fixed**
inventory while the wiring judge **derived** its own. The two drifted when new guards
landed, so `_complete_gates()` returned `[]` — the whole console contract had no
complete gate again, silently. This pass makes both sides derive from one source of
truth and adds the regression that fails when a guard is added but not executed.

Authority: read-only reconstruction, repository mutation on a dedicated branch, PR.
No merge, no deployment, no production acceptance. `main` is untouched.

## 0. Superseding measurement — a competing fix landed first

While this pass ran, `main` advanced and a **competing bounded fix** merged:
`b8869c04 gate10: complete console-contract gate coverage`. It repaired the same
instance by **extending the fixed list** from twelve to sixteen (adding the three new
guards to both `paths` filters and to the executing step).

| Fact | Value |
| --- | --- |
| `main` at first observation | `17988afdde8460cfcaf778258bc43aed1fc9d21f` (red: 21 nodes) |
| competing fix | `b8869c04` (extends the fixed list) |
| `main` after rebase (this pass's base) | `7b67215735945584e89fec50f97fe74dddfcbf28` (green: 19 nodes) |

The two fixes overlap but are **not** equivalent:

- `b8869c04` repairs the **instance** — the next console guard to arrive re-opens the
  same hole.
- this pass removes the **class** — the gate derives its inventory, so a new guard is
  executed without editing the gate, and `tests/test_prism_console_ci_wiring.py` fails
  if the gate ever goes back to a fixed inventory.

This branch is therefore rebased onto `7b672157` and the sections below are
**re-measured at that base**, not at the superseded `17988afd`.

## 1. Reconstruction — the PR to repair is already merged

| Fact | Value |
| --- | --- |
| `main` (first observation 2026-10-11T14:4xZ) | `17988afdde8460cfcaf778258bc43aed1fc9d21f` |
| PR #435 | `state=closed`, `merged=true` at `2026-10-11T14:17:29Z` |
| PR #435 merge commit | `18a450d0e4a07db4e6ce20af51bd6582481680b9` |
| PR #435 head | `b16d066506fe70dfbb6bf5743364f7e7f8bb815b` |

The branch named in the request (`gate10/prism-console-contract-ci-gating-01`) is the
merged #435 branch. Per the merge policy a merged PR is not a PR to update, so this
repair lands on a **new** branch `gate10/prism-console-contract-domain-derivation-01`
and a new PR.

## 2. The measured defect (at `main` `17988afd`, before `b8869c04`)

The gate's executing step named a **fixed list of twelve** guards. The wiring judge
(`tests/test_prism_console_ci_wiring.py::_console_domain`) **derived** its domain from
`git ls-files` at test time. After #435 merged, three new console guards arrived:

```
tests/test_knowledge_projects_boundary.py    (PR #431)
tests/test_knowledge_timeline_boundary.py    (PR #431)
tests/test_prism_opportunity_entry_flow.py   (PR #430)
```

Measured in a worktree at `17988afd`:

```
python scripts/console_contract_domain.py | wc -l         # 16  (derived domain)
# gate executes a fixed 12 -> 13 with the wiring guard itself
DOMAIN on main: 16
WORKFLOW executes: 13
MISSING (derived but unexecuted):
  tests/test_knowledge_projects_boundary.py
  tests/test_knowledge_timeline_boundary.py
  tests/test_prism_opportunity_entry_flow.py
COMPLETE GATES: []
```

```
python -m pytest tests/test_prism_console_ci_wiring.py -q -rEf
# 2 failed, 17 passed, 2 skipped
#   FAILED test_a_workflow_executes_the_whole_console_contract
#   FAILED test_wiring_workflow_is_a_complete_gate_that_selects_itself
```

So the guard *did* detect the drift — and reddened `main` itself. The fix is not to
teach the judge to tolerate a fixed list; it is to make the gate derive its executed
inventory so the two cannot disagree.

## 3. Change

| Path | Change |
| --- | --- |
| `scripts/console_contract_domain.py` | **new** single source of truth: `DOMAIN_NEEDLES`, `SURFACES`, `derive_domain()`, CLI (one path per line / `--json`). Read-only; fails closed (exit 2) on an empty domain. |
| `.github/workflows/prism-console-contract.yml` | executing step is now `python -m pytest -q $(python scripts/console_contract_domain.py)`; `paths` filter selects `tests/**` (so a newly added guard triggers the very judge that reports it unexecuted) plus the script and itself; `permissions: contents: read`; no `continue-on-error`. |
| `tests/test_prism_console_ci_wiring.py` | imports `derive_domain` from the shared script; recognises the **derived** inventory (`$(python scripts/console_contract_domain.py)`) as executing the whole domain; adds the drift regression + controls (30 tests, was 21). |
| `docs/control-plane/evidence/prism-console-contract-domain-derivation-01/EVIDENCE.md` | this record |

`api/main.py` is untouched; `python -m py_compile api/main.py` → OK (budget unaffected).

## 4. Invariants

Unchanged in substance from #435, with the derivation contract added:

1. At least one workflow executes the **whole derived domain**. A *derived* inventory
   (`$(python scripts/console_contract_domain.py)`) executes the whole domain by
   construction, including a guard that did not exist when the gate was written.
2. A complete gate is selected by `web/arkadia_console/**`, `api/frontend_routes.py`,
   every derived guard, and its own file.
3. A complete gate is dispatchable (`workflow_dispatch`).
4. A complete gate's executing steps can fail the run (no step/job
   `continue-on-error`, no step/job `if: false`).

Invariant 4 stays scoped to the *complete* gate(s): `sg-02-fe-2-v.yml`'s
`continue-on-error: true` suite step is recorded pre-existing debt owned by another
workstream. Recorded, not repaired.

## 5. Proof (all re-measured at `main` `7b672157` / branch `bdea8891`)

### 5.1 Wiring guard

```
python -m pytest tests/test_prism_console_ci_wiring.py -q -rEf
# 30 passed in 4.00s
```

### 5.2 The domain guards execute

```
python -m pytest $(python scripts/console_contract_domain.py) -q
# 310 passed in 11.64s     (16 guards, whole derived domain)
```

### 5.3 Live negative controls (real workflow file, restored byte-identically)

Each mutation applied to `.github/workflows/prism-console-contract.yml`, the guard run,
then the file restored from a copy and verified with `sha256sum -c`
(`854c46393690ccab43f974bfafddb280692e3fbf4ca94fb044f2518d2c246400`):

| Mutation | Guard result |
| --- | --- |
| executing step → fixed 15-guard list (the `b8869c04` shape) | `1 failed, 29 passed` |
| job-level `continue-on-error: true` on the real gate | `2 failed, 26 passed, 2 skipped` |
| `tests/**` filter narrowed to a single guard | `3 failed, 99 passed` |
| restore | `.github/workflows/prism-console-contract.yml: OK` |

The fixed-list mutation reddens `test_real_gate_inventory_is_derived_not_fixed` — the
invariant reports the missing derivation directly. The narrowed filter reddens
`test_complete_gate_is_selected_by_everything_it_judges`,
`test_real_gate_selects_a_guard_added_after_the_gate`, **and**
`tests/test_ci_gate_trigger_coverage.py::test_push_and_pull_request_filters_are_identical`,
confirming the broadened filter is still judged for symmetry.

### 5.4 Drift regression (the requested tests)

A `_grown_domain` fixture simulates a console guard added to the corpus after the gate
was written:

| Test | Property |
| --- | --- |
| `test_derived_inventory_executes_a_guard_added_after_the_gate` | a **derived** inventory follows the corpus; the new guard is executed |
| `test_fixed_inventory_omits_a_guard_added_after_the_gate` | **negative control**: a fixed list leaves the new guard unexecuted |
| `test_real_gate_inventory_is_derived_not_fixed` | the shipped gate derives, or the drift regression is not actually held |
| `test_real_gate_selects_a_guard_added_after_the_gate` | a new guard changes `tests/**`, which selects the judge that reports it unexecuted |
| `test_derived_inventory_is_recognised_as_executing_the_run` + 4 rejections | `$(python …)` counts; `echo $(python …)`, a comment, a quoted form, and a bare script run do not |

### 5.5 Protected surfaces

```
python -m pytest tests/architecture -q      # 11 passed
python -m py_compile api/main.py            # OK
printf '<changed paths>' | python scripts/cp10_mutation_boundary_policy.py --judge
# Mutation boundary PASS (M02A legitimate-surface + constitutional denylist); exit 0
```

`scripts/` and `tests/` are admitted by the existing CP10 rules; no allowlist edit was
needed.

### 5.6 Regression — failing/error node SET

Both trees measured **in this same environment** with
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`:

| Tree | Result | Failing/error nodes |
| --- | --- | --- |
| `main` `7b672157` (baseline) | `18 failed, 2605 passed, 17 skipped, 1 error` | 19 |
| branch `bdea8891` | `18 failed, 2614 passed, 17 skipped, 1 error` | 19 |

```
comm -3 /tmp/main2-nodes.txt /tmp/branch2-nodes.txt     # empty
sha256(main2-nodes.txt)   == 716df34bc5a6ad51dd122ffb09175f1be7883f85a5f4bc07dc12831109b0a45e
sha256(branch2-nodes.txt) == 716df34bc5a6ad51dd122ffb09175f1be7883f85a5f4bc07dc12831109b0a45e
```

Zero new failures, zero repaired — because `b8869c04` already cleared the two drift
nodes on `main`, and this pass adds no failing node. (The superseded `17988afd` delta
was `21 → 19`, `comm -3` carrying exactly those two nodes.)

The `+9 passed` is attributed by `--collect-only`, not inferred:

| File | `main` `7b672157` | branch `bdea8891` |
| --- | --- | --- |
| `tests/test_prism_console_ci_wiring.py` | 21 | 30 |
| whole suite (collected) | 2639 | 2648 |

+9 collected is exactly the new wiring nodes.

## 6. Limitations and next action

- No production observation is made. Production acceptance stays **NOT CLAIMED**.
- `workflow_dispatch` at `ref=main` remains unproven until the gate is on the default
  branch; that is the next action after human merge.
- `sg-02-fe-2-v.yml`'s `continue-on-error: true` suite step remains recorded debt.
- This pass does not prove the console guards *pass* — the wiring guard proves they are
  *executed*; passing is the gate's job at run time.
