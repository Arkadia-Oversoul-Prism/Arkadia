# Proposal P-009 — Anchor Definitions

## Purpose
Define governance-level anchors to prevent mythic escalation and enforce continuity logic.

## Scope
- Static anchor definitions only
- Non-executable reference material
- Governance documentation

## Files
- governance/anchors/spiral_codex.json
- governance/anchors/arkadia_steward.json
- governance/anchors/echofield_mandate.json

## Constraints
- Anchors are static
- No runtime mutation
- Mythic weight fixed at 0.0 (prevents belief escalation)
- Deterministic priority rules only

## Risk Surface
None — static data only.

## Rollback
Remove governance/anchors/
