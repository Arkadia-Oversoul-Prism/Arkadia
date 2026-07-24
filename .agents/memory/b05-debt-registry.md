---
name: B0.5 Baseline Integrity — Debt Registry and Measurement Fixes
description: What was found and fixed in Workstream B0.5; the full architectural debt registry as of baseline freeze.
---

# B0.5 — Baseline Integrity

**Completed:** ARK Y1 · D116 (2026-07-24)

## Measurement System Fix

`test_no_layer_inversions` in `tests/architecture/test_layer_boundaries.py` had an inverted condition.

**Wrong:** `if imported_layer > importer_layer:` — flagged permitted imports, missed real violations (61 false positives)  
**Correct:** `if imported_layer < importer_layer:` — flags when a more-stable (higher-numbered) layer imports a less-stable (lower-numbered) one

**Why:** LAYER_MAP numbering is 0=Presentation (least stable) → 5=Constitution (most stable). Permitted direction is lower-number → higher-number. A violation is a higher-numbered layer importing a lower-numbered one.

## Registry Variable Names (post-rename)

- `ALLOWED_VIOLATIONS` was renamed to `REGISTERED_ARCHITECTURAL_DEBT`
- `ALLOWED_CIRCULAR_IMPORTS` was renamed to `REGISTERED_CIRCULAR_DEBT`
- Both live in `tests/architecture/LAYER_MAP.py`
- Test functions also renamed: `test_allowed_violations_are_documented` → `test_registered_debt_is_documented`, etc.
- Freeze rule added to LAYER_MAP.py: registry edits only when adding new intentional debt or removing resolved debt.

## REGISTERED_CIRCULAR_DEBT Mechanism

Added to `LAYER_MAP.py` and `test_no_circular_imports_in_kernel` — a debt registry for circular import cycles analogous to ALLOWED_VIOLATIONS for layer inversions. Format: `(cycle_tuple, "owner — workstream — exit criterion")`.

## Full Debt Registry (as of B0.5 baseline)

All registered in `tests/architecture/LAYER_MAP.py`. All assigned to Workstream A, Phase 1 Gate E.

### Layer Violations (10 total — ALLOWED_VIOLATIONS)
- kernel/agents.py → api (generate_verse) — previously documented
- kernel/planner.py → api (key_manager) — previously documented
- kernel/tools_real.py → api (key_manager) — previously documented
- kernel/jobs.py → api (firebase_store) — previously documented
- kernel/goals.py → api (firebase_store) — previously documented
- kernel/tts.py → api (tts_key_manager) — **newly discovered in B0.5**
- api/nodes.py → kernel (kernel.tools) — **newly discovered; identity layer must be a leaf**
- api/main.py → solspire (console_router) — **newly discovered; api→presentation violation**
- providers/* → api (provider_key_store, key_manager) — **newly discovered; providers must receive keys via injection**
- providers/router.py → knowledge (knowledge.db) — **newly discovered; orthogonal violation**

### Circular Import Cycles (3 entries — ALLOWED_CIRCULAR_IMPORTS)
- kernel.execution → kernel.tools → kernel.execution
- kernel.execution → kernel.planner → kernel.execution
- kernel.execution → kernel.planner → kernel.tools → kernel.execution (three-node variant)

**Why:** DFS cycle detection is traversal-order dependent and may report the same underlying mutual-import cluster as multiple distinct cycles. Register all variants the detector reports.

## B0.5 Exit State

`pytest tests/architecture/ -v` → 10/10 passing.  
No implementation code changed. Baseline is frozen. B1 may begin.
