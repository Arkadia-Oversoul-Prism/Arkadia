# Proposal P-010 — Steward Filter

## Purpose
Introduce a decision-hygiene filter enforcing sustainability, exit-logic, and action compression.

## Scope
- Single module: weaver/filters/steward.py
- Non-autonomous
- Proposal-only logic

## Files
- weaver/filters/steward.py

## Guarantees
- Blocks identity inflation
- Blocks symbolic drift without action
- Forces action-oriented output
- Sustainable continuity only

## Design Rules
- No narrative generation beyond proposals
- No memory accumulation
- Exit-as-success is valid condition
- Sustainability check on all outputs

## Risk Surface
None — filtering layer only.

## Rollback
Remove steward filter
