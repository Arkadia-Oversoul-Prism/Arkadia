# Phase 9 — Opening Record

**Status:** OPEN  
**Opened:** 2026-09-10  
**Prior phase:** Phase 8 — SEALED  
**Prior closure:** `docs/verification/PHASE8_GATE_CLOSURE.md`  
**Merge commit (Phase 8):** `6bf382c03cc6e95ee7a2d01e14a4a83c89a4cb46`

## Authorization

Human authorization received to close Phase 8 and authorize Phase 9.

## Scope

**Human Decision Queue** over Phase 8 opportunities:

- Input: Opportunity records (Phase 8)
- Output: Decision records — `APPROVE` / `REJECT` / `DEFER`
- Every decision carries rationale and opportunity provenance binding
- Default without explicit policy: **DEFER**
- Explicit APPROVE still sets `execution_authorized=false`, `auto_build=false`, `auto_merge=false`

## Forbidden

- Auto-execute, auto-build, auto-merge, deploy
- Treating decision APPROVE as K15/K3 authorization
- Parallel verification spine
- Track 2 / sovereign work
- Authority above Level 2

## Gate

Deterministic tests in `tests/test_phase9_decision_queue.py`, wired into CP10 as `phase9_decision` (mirrors phase8_possibility).

## Boundary

Phase 9 records **human decisions**. It does not execute them. Phase 10 remains locked until Phase 9 closure.
