# WEAVER-K5 — Governed Proposal Engine

**PROPOSAL ≠ AUTHORIZATION**

## Module

`weaver/proposal.py`

## States

PROPOSED | APPROVED | REJECTED | EXPIRED | INVALID

## Flow

Objective → deterministic/LLM-assisted findings → normalize/validate → human approve → `proposal_to_plan` → K3 `run_transaction`

## Non-goals

No autonomous execution, no scope expansion, no second write path.
