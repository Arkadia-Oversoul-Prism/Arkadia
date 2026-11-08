# Lane 2 — opportunity control integrity: bind three vacuous negative controls

**Pass:** `lane2-opportunity-control-integrity-02`
**Lane:** 2 — NovaNet + project Opportunity Radar
**Base `main`:** `e14fd5d7d4129bfc8699cd5dca064f4af66559f6` (PR #639 merge)
**Branch:** `feat/prism-l2-opportunity-control-integrity-02`
**Disposition:** DRAFT — merge, production deployment and acceptance remain human-only.

## 1. The defect

`tests/test_prism_opportunity_entry_flow.py` carried three `test_negative_control_*` nodes that
did not call the detector they claim to prove. Each is a different shape of the same defect:

| control | why it was vacuous |
|---|---|
| `test_negative_control_the_probe_detects_a_wrong_body_builder` | built its own `wrong` dict and asserted `"buyer_price" in wrong` — a fact about a literal written two lines above it, not about the live assertion's detector |
| `test_negative_control_the_authority_pins_are_not_vacuous` | asserted its hand-written `injected` string contained the forbidden tokens **and** that those tokens were absent from the real surfaces. Neither half ran a detector, so the live assertion's own token tuples could be emptied silently |
| `test_negative_control_the_snapping_seed_would_have_rewritten_the_status` | reconstructed the pre-repair *body* from the Node probe and compared dicts; it never ran the source-level pin the live `test_the_frontend_seed_no_longer_snaps_an_unknown_status` depends on |

A control that cannot fail for any edit to the detector it protects is vacuous: the detector can
be disarmed with no red test.

This is the defect class Lane 1 repaired in #631 (`b2d33c80`), #634 (`f495e1b6`), #636
(`35e03fcb`) and #637 (`03220c95`); Lane 2 in #635 (`20150343`); Lane 3 in #638 (`14aa82e0`);
Lane 4 in #639 (`e14fd5d7`). #635 bound two controls in this lane's guards; these three nodes in
the same file were not reached.

## 2. Measurement — pre-repair (the vacuity)

Method: neuter the **live detector's own expression**, AST-scoped to that function's span, then
run the live node **and** its control.

| live node | neutered expression | result |
|---|---|---|
| `test_executed_contract_minimal_create_asserts_no_commercial_fact` | `for field in (...)` → `for field in ()` | `live=pass control=pass` |
| `test_surface_and_form_invent_no_authority_and_no_transport` | `for forbidden in (...)` → `for forbidden in ()` | `live=pass control=pass` |
| `test_the_frontend_seed_no_longer_snaps_an_unknown_status` | the `not in contract` pin → `assert True` | `live=pass control=pass` |

Nothing reddened. The live detector could be emptied and no test in the file would notice.

## 3. The repair

Each predicate moves to a module-level helper the live assertion **and** its control both call,
with the data it scans hoisted to named constants so the control can feed the detector the shape
it must reject:

| helper | replaces | feeds the control |
|---|---|---|
| `_asserted_facts(body)` | the inline `for field in (...)` loop | `COMMERCIAL_OMITTED_FIELDS`, `UNASSERTED_BODY_FIELDS` |
| `_transport_defects(code)` / `_invented_authority_defects(code)` | the two inline `for ... in (...)` loops | `TRANSPORT_TOKENS`, `INVENTED_AUTHORITY_TOKENS` |
| `_snapping_seed_defects(contract_code)` | the inline `not in contract` pin | `SNAPPING_SEED_EXPRESSION`, `VERBATIM_SEED_EXPRESSION` |

Each control also asserts the **repaired** input is *not* reported, so a detector that matches
everything cannot pass either. No live semantics changed and the node count is unchanged at
**88** — this strengthens controls, it adds none.

## 4. Proof of the repair — discriminating A/B on the real file

**On the pre-repair blob**, neutering the live detector's own expression left both nodes green
(`live=pass control=pass`) — the vacuity in §2.

**On the repaired file**, neutering the **shared helper body** reddens the control in both
polarities:

| helper | mutation | live | control |
|---|---|---|---|
| `_asserted_facts` | `return ["forced"]` (always-dirty) | FAIL | **FAIL** |
| `_asserted_facts` | `return []` (always-clean) | pass | **FAIL** |
| `_transport_defects` | always-dirty / always-clean | FAIL / pass | **FAIL / FAIL** |
| `_snapping_seed_defects` | always-dirty / always-clean | FAIL / pass | **FAIL / FAIL** |

The discriminating property is `control=FAIL` in both directions. `always-clean` is the sharper
half: the live assertion asserts the report is *empty*, so a detector that reports nothing
satisfies it — only the control, which asserts the report is *non-empty*, can catch that. Pre-
repair the same mutation of the live detector left the control green.

The file was restored byte-identically after every mutation (asserted in the harness, not
asserted by inspection).

## 5. Verification

| check | result |
|---|---|
| `pytest tests/test_prism_opportunity_entry_flow.py -q -rEf` | **88 passed** (node count unchanged) |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q -rEf` | **67 passed** |
| `pytest $(python scripts/console_contract_domain.py) -q` | **10 failed, 1123 passed** |
| `python scripts/lane_state.py --check` | exit **0** |

The 10 domain failures are **all** in `tests/test_mission_lifecycle_adapter_contract.py` and are
the documented missing-`node_modules` TypeScript-toolchain baseline (this sandbox has no
`web/arkadia_console/node_modules`); they are identical to `main` and are not attributable to
this change. Attribution is by failing-node **identity**, never by count.

No workflow edit is needed: `scripts/console_contract_domain.py` derives its domain at test time
and already lists `tests/test_prism_opportunity_entry_flow.py` (line 49), so the console-contract
gate executes this guard.

## 6. Scope

Bounded to `tests/test_prism_opportunity_entry_flow.py` plus this lane's own instruction doc and
the derived lane-state snapshot. No console source, backend contract, registry, authority
surface, deployment configuration or other lane's file is touched.

## 7. What this does not claim

This is a repository-source claim about test-control binding. It is not a production
observation, not a deployment claim, and not acceptance. Merge remains human-only.
