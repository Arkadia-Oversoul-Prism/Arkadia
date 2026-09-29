# M09 — Worker Contract — Acceptance-Readiness Verification

**Move:** M09 — worker-contract  
**HEAD inspected:** `566df75c90c688c967bd92692e16f83bba86de03`  
**Verdict:** `READY_FOR_REVIEW`

> Does **not** accept M09. No ACCEPT.json in this pass.

## Merge evidence
- PR #47 / `7fcb9a1`

## Spec alignment
| Criterion | Result |
|-----------|--------|
| WORKER_CONTRACT.md + schema + instance | PASS |
| Lifecycle WAKE→TERMINATE | PASS |
| merge/deploy human_only | PASS |
| EngineeringWorker stops at review | PASS |
| Focused tests | PASS — `tests/test_m09_worker_contract.py` |
