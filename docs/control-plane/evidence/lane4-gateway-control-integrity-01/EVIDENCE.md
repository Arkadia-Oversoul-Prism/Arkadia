# Lane 4 — model-gateway negative-control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `feat/prism-w4-gateway-control-integrity-01`
**Base `main`:** `14aa82e01f64531f97620f854e12c0885c76c9d0`
**Scope:** two Lane-4-owned test files. No console source, backend contract, registry, authority
surface, or other lane's file is touched.

## 1. Defect — five vacuous negative controls

Both model-gateway guards carried `test_negative_control_*` nodes whose body **restated the
detector inline** instead of calling the code the live assertion uses. A control that restates its
detector cannot fail for any edit to the live assertion it protects, so the detector could be
disarmed with no red test.

Measured on the real file with AST-scoped mutation (neuter the *live* detector's own expression,
scoped to that function's span, then run the live node **and** its control):

| live node | control | neutered live detector | result |
|---|---|---|---|
| `test_projection_config_classes_equal_the_handler_s_classes` | `test_negative_control_class_detector_sees_a_divergent_value` | `True or projected == handler_classes` | `2 passed` |
| `test_projection_is_pure` | `test_negative_control_purity_detector_sees_an_import` | `True or not re.search(...)` | `2 passed` |
| `test_surface_is_wired_to_the_declared_registry_entry` | `test_negative_control_wiring_detector_sees_an_inlined_path` | `True or "endpoints.labGateway" in source` | `2 passed` |
| `test_handler_returns_a_description_not_an_authority` | `test_negative_control_the_side_effect_detector_sees_one` | control parsed its own snippet | control never touched the live detector |
| `test_config_class_vocabulary_is_the_gateway_s_own` (`test_prism_w4_model_gateway.py`) | `test_negative_control_class_detector_sees_a_divergent_value` | `True or projected == declared_classes` | `2 passed` |

The live node reddening while the control stays green is the signature: the control is bound to
nothing. The fourth control parsed a synthetic snippet and asserted on *that snippet*, never on the
shipped `describe_gateway`.

This is the defect class Lane 1 repaired in #631 (`b2d33c80`) and #634 (`f495e1b6`), Lane 2 in
#635 (`20150343`), and Lane 3 in #638 (`14aa82e0`). Those passes each repaired the guards they
owned; the two Lane-4 model-gateway guards were not reached.

## 2. Repair

Each detector moves to a module-level function the live assertion **and** its control both call:

| helper | file | replaces |
|---|---|---|
| `_wiring_violations` | `test_lab_model_gateway_contract.py` | inline `"endpoints.labGateway" in source` + path check |
| `_purity_violations` | `test_lab_model_gateway_contract.py` | inline import regex + token loop |
| `_projected_classes` | both files | inline `CONFIG_CLASSES` extraction |
| `_side_effects_in_function` | `test_lab_model_gateway_contract.py` | inline `ast.unparse` side-effect scan |

Each control now also asserts the **repaired** input is not reported (a control that only proves
the mutated case is a control that may have swallowed the live one).

No detector's live semantics changed: every live node passed before and after, and the node count
is unchanged at **43** — this strengthens controls, it adds none.

## 3. Proof of the repair (live mutation, both polarities)

Post-repair, neutering the **shared helper** body (AST-scoped to the helper's own span) reddens the
control in every case:

```
_wiring_violations          -> always-clean  live=pass control=FAIL
_wiring_violations          -> always-dirty  live=FAIL control=FAIL
_purity_violations          -> always-clean  live=pass control=FAIL
_purity_violations          -> always-dirty  live=FAIL control=FAIL
_projected_classes          -> always-clean  live=FAIL control=FAIL
_projected_classes          -> always-dirty  live=FAIL control=FAIL
_side_effects_in_function   -> always-clean  live=pass control=FAIL
_side_effects_in_function   -> always-dirty  live=FAIL control=FAIL
_projected_classes (w4)     -> always-clean  live=FAIL control=FAIL
_projected_classes (w4)     -> always-dirty  live=FAIL control=FAIL
```

The discriminating property is `control=FAIL`: pre-repair the same mutation of the live detector
left the control green. The files were restored byte-identically after every control run
(asserted in the harness).

## 4. Verification

| command | result |
|---|---|
| `pytest tests/test_lab_model_gateway_contract.py tests/test_prism_w4_model_gateway.py -q -rEf` | **43 passed** |
| `pytest $(python scripts/console_contract_domain.py) -q -rEf` | **1123 passed, 10 failed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | **67 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest --collect-only` (both files) | **43** collected (unchanged) |

The 10 console-domain failures are **all** `tests/test_mission_lifecycle_adapter_contract.py`, the
documented missing-`node_modules` TypeScript toolchain
(`web/arkadia_console/node_modules/typescript/lib/typescript.js` absent locally); they match the
baseline recorded by #633/#634 and pass in CI. Neither changed file appears in the failing set.

## 5. Boundaries

- Files touched: two Lane-4-owned test files, this evidence doc, `AGENT-04-ARKANA-WEAVER-LAB.md`
  (Lane 4's own instruction), and `lane-state.json` (refreshed in the same change — see §6).
- No console source, backend contract, registry entry, authority surface, or other lane's file.
- The PR stays **draft**. Merge, production deployment, and acceptance remain human-only.

## 6. Lane-doc currency

The slice edits `AGENT-04-ARKANA-WEAVER-LAB.md`, a guarded lane doc.
`scripts/lane_state.py::_freshness_findings` treats a commit after the newest snapshot commit that
touches a guarded lane doc as staleness, so merging as-is would redden `lane-doc-currency` on
`main` the instant the merge lands. The snapshot is re-derived with
`scripts/lane_state_refresh.py --write --base-main <fresh main>` in the same change, matching the
convention #614/#619/#633 set.
