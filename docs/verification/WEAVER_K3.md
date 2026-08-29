# WEAVER-K3 — Plan → Implement → Verify Transaction

## Principle

**PLAN ≠ AUTHORIZATION.** PassSpec remains the human authorization envelope.

## Modules

- `weaver/plan.py` — Plan structure, scope gate, approve_plan
- `weaver/transaction.py` — run_transaction lifecycle

## Lifecycle

PassSpec → preflight → plan → approval boundary → run_authorized (K0.1/K2) → tests → diff → commit → push (if required) → remote verify → checkpoint

## Next action

Awaiting human authorization. No K4 auto-start.
