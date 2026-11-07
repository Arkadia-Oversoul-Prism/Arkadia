# Lane 1 — repair the vacuous negative controls in the unified-interface guard

Pass: 2026-11-07. Base: `origin/main` `482a4ba09d3a63c76781d149d474de51b0c33f72`.
Branch: `feat/prism-l1-vacuous-control-integrity-02`. Lane: 1.

## 1. What was measured

`tests/test_console_unified_interface_contract.py` (added by `b9297ab9`, AO-002 / PR #630)
carried **six** `test_negative_control_*` nodes. A negative control exists to prove the
*detector* it protects can fail. All six restated their detector inline instead of calling
it, so they could not fail for any edit to the live assertion — the same defect class that
`b2d33c80` (#631) repaired in two sibling Lane-1 guards
(`test_console_surface_error_boundary.py`, `test_console_shell_nav_contract.py`).

The file's own header claims each detector "carries a negative control so it cannot be
disarmed by editing the console source alone". Measured at `482a4ba0`, that claim was false
for every control in the file.

## 2. The proof (pre-repair vs. repaired)

Method: neuter the *live* test's own detector expression (scoped by AST to that function's
source span) on the pre-repair file, and the *shared helper body* on the repaired file; run
the live node and its control node separately.

```
detector             | PRE live PRE ctrl pre verdict         | REP live REP ctrl rep verdict
--------------------------------------------------------------------------------------------
grouped-nav          | FAIL     pass     VACUOUS (ctrl green)| FAIL     FAIL     both redden
duplicated-ledger    | FAIL     pass     VACUOUS (ctrl green)| FAIL     FAIL     both redden
second-nav-renderer  | FAIL     pass     VACUOUS (ctrl green)| FAIL     FAIL     both redden
fabricated-roster    | n/a      pass     ORPHANED (see §3)   | FAIL     FAIL     both redden
remembered-selection | FAIL     pass     VACUOUS (ctrl green)| FAIL     FAIL     both redden
undeclared-polling   | pass     pass     VACUOUS (ctrl green)| FAIL     FAIL     both redden
```

Pre-repair: the live assertion reddens while its "control" stays green — the control proves
nothing. Repaired: both redden, because both call the same module-level function.

## 3. The fabricated-worker control was orphaned, not merely vacuous

`test_negative_control_a_fabricated_worker_list_would_be_detected` asserted
`"const WORKERS" not in weaver` and `"const WORKERS" in fabricated`. Neither the string
`WORKERS` nor any fabricated-worker detector appears in the live test it is named after
(`test_weaver_composes_real_read_models_and_declares_the_gaps` guards `EventSource` /
`setInterval`, not a roster). Measured: on the pre-repair file, neutering the live test's own
detectors left **both** the live node and the control green. The control was attached to no
live assertion at all.

The repair adds `_fabricated_worker_rosters()`, which the live assertion and the control both
call. It encodes the component's own stated doctrine — "It refuses to invent workers,
progress percentages, retry counters or live telemetry" — so the roster it names is the one
the surface documents as forbidden.

## 4. Change

One file, `tests/test_console_unified_interface_contract.py`. Six detectors move to
module-level functions that the live assertion and its control both call:

| helper | live node | control node |
|---|---|---|
| `_groups_from_the_declared_table` | `test_shell_derives_grouped_navigation_from_the_surface_table` | `…a_second_group_list_would_be_detected` |
| `_second_system_definitions` | `test_workspace_does_not_introduce_a_second_approval_or_session_system` | `…a_duplicated_ledger_would_be_detected` |
| `_navigation_renderers` | `test_exactly_one_file_renders_the_primary_navigation` | `…a_second_nav_renderer_is_detected` |
| `_fabricated_worker_rosters` | `test_weaver_composes_real_read_models_and_declares_the_gaps` | `…a_fabricated_worker_list_would_be_detected` |
| `_missing_remembered_selection_markers` | `test_project_selection_is_remembered_and_revalidated` | `…a_state_only_selection_would_be_detected` |
| `_undeclared_polling_offenders` | `test_no_undeclared_polling_anywhere_in_the_weaver_composition` | `…polling_in_a_composed_component_is_detected` |

Each control now calls the same function the live assertion does, and each asserts the
*repaired* input is not reported as well as the mutated one is — the positive/negative pair
the sibling guards use. No detector's live semantics changed: every live node passed before
and after.

**Node count is unchanged at 24.** This strengthens existing controls; it adds no nodes
(`--collect-only` → 24 on both trees).

## 5. Verification

- `pytest tests/test_console_unified_interface_contract.py -q` → **24 passed** (was 24 passed).
- `pytest tests/architecture -q` → **11 passed**.
- `pytest tests/test_prism_console_ci_wiring.py -q` → **31 passed**.
- `pytest $(python scripts/console_contract_domain.py) -q` → **1123 passed, 10 failed**. The
  ten failures are `test_mission_lifecycle_adapter_contract.py`, all from the same cause —
  `web/arkadia_console/node_modules/typescript/lib/typescript.js` is absent in this sandbox.
  This is a missing toolchain, not repository debt, and it matches the measured baseline
  recorded by #633 (`1133 passed` with `node_modules` installed, `10 failed` without it).
  Both trees agree.
- `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q`
  → **67 passed**.
- `scripts/lane_state.py --check` → exit 0; `--check --verify-live` → exit 0.
- The gate that executes this guard is `prism-console-contract.yml`, which runs the *derived*
  domain (`scripts/console_contract_domain.py`) rather than a fixed list, so no workflow edit
  is needed — the file was already in the domain and is executed.

## 6. Boundaries observed

No console source, backend contract, shared endpoint/type registry, authority surface, or
deployment configuration is touched. The changed file is a **shared shell/navigation
contract test**, which `SHARED-CONTRACTS.md` §1 assigns to workstream 1 (Lane 1: "shared
shell/endpoint contract tests"). No other lane's files are edited.

No merge, deployment, or acceptance claim. This session is
`IMPLEMENTATION_AGENT := OPENHANDS`, which holds no merge authority under GOV-01 §9 /
`AGENTS.md`. The PR stays **draft**.

*This record was created by an AI agent (OpenHands) on behalf of the user.*
