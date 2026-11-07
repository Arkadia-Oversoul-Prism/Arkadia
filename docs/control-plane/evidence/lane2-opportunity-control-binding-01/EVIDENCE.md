# Lane 2 — two vacuous opportunity negative controls bound to their detectors

**Branch:** `feat/prism-l2-opportunity-control-binding-01`
**Base:** `main` @ `482a4ba09d3a63c76781d149d474de51b0c33f72`
**Head:** `2069fca0` (the evidence commit; the guard change is `a01a5485`)
**Owner:** Lane 2 (SHARED-CONTRACTS.md §1 — "opportunity tests/evidence")
**Scope:** two Lane-2 opportunity guards, no production code, no other lane's paths.

## Defect (measured at `482a4ba0`)

Two `test_negative_control_*` nodes restate the live detector inline instead of
calling it. A control that restates its detector cannot fail for any edit to the
live assertion it protects, so the detector can be disarmed with no red test.

This is the same class `b2d33c80` (#631) repaired in two Lane-1 console guards and
#634 (`cbf50989`, open) repaired in a third. Neither reached Lane 2.

| guard | control | live node it claims to protect |
|---|---|---|
| `tests/test_prism_opportunity_entry_flow.py` | `test_negative_control_the_settable_detector_flags_the_full_vocabulary` | `test_the_form_offers_only_settable_statuses` |
| `tests/test_prism_opportunity_radar_module.py` | `test_negative_control_the_mount_pins_are_not_vacuous` | `test_projects_surface_mounts_the_opportunity_radar_section` |

## Proof (pre-repair vs. repaired)

Method: mutate the **console source** the detector reads to reintroduce the defect
the guard exists to catch, then run the live node and its control separately. On the
pre-repair blobs the live node reddens and the "control" stays green — it proves
nothing. On the repaired blobs both redden, because both call the same module-level
function.

| tree | mutation | live | control | verdict |
|---|---|---|---|---|
| pre-repair `482a4ba0` | `ProspectEntryForm.tsx`: `SETTABLE_STATUSES.map((status)` -> `BUYER_RECON_STATUSES.map((status)` | FAIL | **PASS** | **VACUOUS** |
| pre-repair `482a4ba0` | `SolSpirePage.tsx`: mount `<OpportunityRadarSection ... />` deleted | FAIL | **PASS** | **VACUOUS** |
| repaired head | neuter `_status_option_violations` | FAIL | FAIL | bound |
| repaired head | neuter `_unmounted_page_violations` | FAIL | FAIL | bound |

Both console sources were restored byte-identically after each mutation.

## Change

Two detectors move to module-level functions the live assertion and its control both
call; each control also asserts the repaired input is *not* reported.

| helper | live node | control node |
|---|---|---|
| `_status_option_violations` | `test_the_form_offers_only_settable_statuses` | `test_negative_control_the_settable_detector_flags_the_full_vocabulary` |
| `_unmounted_page_violations` | `test_projects_surface_mounts_the_opportunity_radar_section` | `test_negative_control_the_mount_pins_are_not_vacuous` |

No detector's live semantics changed: every live node passed before and after.
**Node count is unchanged at 113** (`--collect-only` -> 113 on both trees) — this
strengthens controls, it adds none.

## Verification (measured at `482a4ba0`)

| Check | Command | Result |
|---|---|---|
| repaired guards | `pytest tests/test_prism_opportunity_entry_flow.py tests/test_prism_opportunity_radar_module.py -q` | **113 passed** (was 113 passed) |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| console-contract gate | `pytest $(python scripts/console_contract_domain.py) -q` | **1123 passed, 10 failed** |
| console CI wiring | `pytest tests/test_prism_console_ci_wiring.py -q` | **31 passed** |
| lane currency | `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | **67 passed** |
| lane snapshot | `scripts/lane_state.py --check --verify-live` | exit **0** |
| mutation boundary | `cp10_mutation_boundary_policy.py --judge` on both paths | PASS |

The ten failures are all `test_mission_lifecycle_adapter_contract.py`, from one cause:
`web/arkadia_console/node_modules/typescript/lib/typescript.js` is absent in this
sandbox. That is a missing toolchain, not repository debt, and matches the recorded
baseline (`1133 passed` with `node_modules`, `10 failed` without). Neither tree
touches those nodes.

## Boundaries

No console source, backend contract, shared endpoint/type registry, authority surface,
or deployment configuration is touched. Neither file is a guarded lane doc, so no
`lane-state.json` refresh is required in this change (measured: the diff touches no
path under `docs/control-plane/parallel-ui/`).

Reconciliation was exhausted before this PR was opened: #634 is Lane 1's open PR and
lanes 2, 3 and 4 held no open PR. N1–N8 are satisfied for Lane 2.

Merge, production deployment and acceptance remain human-only. This PR stays **draft** —
`IMPLEMENTATION_AGENT := OPENHANDS` holds no merge authority under GOV-01 §9.
