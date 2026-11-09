# Lane 3 — knowledge status-read control binding (2026-11-09)

**Lane:** 3 (Solariun + Knowledge OS)
**Branch:** `feat/prism-l3-knowledge-status-control-binding-03`
**Base main:** `9ba62a011cf2a1a1eba6fbdcd3feadaf9a84cec7`
**Scope:** `tests/test_knowledge_status_read_boundary.py` (one file, test-side only)

## Defect

`tests/test_knowledge_status_read_boundary.py` carried three `test_negative_control_*` nodes.
None called a module-level detector, so none shared a predicate with a live assertion:

| Control | Shape before |
|---|---|
| `test_negative_control_the_naive_reader_dereferences_the_error_envelope` | asserted a probe value (`contract_probe["naive_reader_on_error_envelope"]`) it had just built |
| `test_negative_control_the_status_surface_routes_through_the_shared_reader` | asserted substrings of `readStatus` inline; **orphaned** — no live assertion in the file asserted the same seam |
| `test_negative_control_the_reader_is_not_a_blanket_refusal` | asserted `"return payload;" in source` inline |

A control that shares no predicate with a live assertion cannot fail when that predicate is
edited, so "the oracle can bite" was carried by inline expressions and by the node's name.

## Measured vacuity at base `9ba62a01`

AST-scoped mutation of the **live** expression (scoped to that function's own span):

```
baseline:                                            14 passed
live `requireKnowledgeStatusReading(` check neutered -> 14 passed   <- vacuity
restored:                                            14 passed
```

## Repair

Four module-level detectors now hold the predicates, and the live assertions **and** their
controls both call them:

| Detector | Predicate | Live assertion |
|---|---|---|
| `_contract_refusal_defects(probe)` | the 200 `status:error` envelope / a missing block / a non-object body is refused | `test_the_contract_module_refuses_every_failure_shape` |
| `_reader_wiring_defects(body)` | `readStatus` validates through the shared reader and is not an unvalidated typed read | `test_the_status_surface_routes_through_the_shared_reader` |
| `_blanket_refusal_defects(source)` | the reader returns a validated reading | `test_the_reader_is_not_a_blanket_refusal` |
| `_naive_reader_defects(probe)` | a body-shape-blind reader crashes on the envelope | `test_a_body_shape_blind_reader_crashes_on_the_failure_envelope` |

Each control feeds its detector the pre-repair shape and asserts it is reported, **and** feeds
it the live input and asserts it is *not* reported, so a detector that reports unconditionally
cannot pass either. Node count 14 → 19 (+4 live assertions giving the orphaned predicate a live
partner, +1 control).

## Post-repair mutation matrix (file restored byte-identically after each)

```
== never-report (detector body -> return []) ==
  _reader_wiring_defects:     live passed | ctrl FAILED
  _contract_refusal_defects:  live passed | ctrl FAILED
  _blanket_refusal_defects:   live passed | ctrl FAILED
  _naive_reader_defects:      live passed | ctrl FAILED
== always-report (detector body -> return ['forced']) ==
  _reader_wiring_defects:     live FAILED | ctrl FAILED
  _contract_refusal_defects:  live FAILED | ctrl FAILED
  _blanket_refusal_defects:   live FAILED | ctrl FAILED
  _naive_reader_defects:      live FAILED | ctrl FAILED
restored: identical = True
```

The never-report row is the binding: `assert defects == []` is satisfied by `return []`, so the
control's own positive half is what catches it. The always-report row shows the live assertion
and its control redden together, so neither can be satisfied unconditionally.

## Verification (at this head)

- `python -m pytest tests/test_knowledge_status_read_boundary.py -q -rEf` → **19 passed** (`--collect-only` → 19)
- `python -m pytest tests/architecture -q` → **11 passed**
- `python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` → **67 passed**
- Derived console-contract domain (`python -m pytest $(python scripts/console_contract_domain.py)`) → **1130 passed / 10 failed** — the 10 are the documented missing-`node_modules` baseline, all `test_mission_lifecycle_adapter_contract.py`; this file is absent from the failing set
- `python scripts/lane_state.py --check` → exit 0
- `python -m py_compile api/main.py` → OK (untouched)

## Scope / ownership

Lane 3 bounded slice under `SHARED-CONTRACTS.md` §11 (N1–N8). Changed paths:
`tests/test_knowledge_status_read_boundary.py`, the lane-3 instruction doc, the re-derived
`lane-state.json`, and this evidence record. No console source, backend contract, registry,
authority surface or other lane's file is touched. The guard is executed by the derived
console-contract domain, so no workflow edit is needed.

## Status

Draft. Merge, deployment and acceptance remain human-only.
