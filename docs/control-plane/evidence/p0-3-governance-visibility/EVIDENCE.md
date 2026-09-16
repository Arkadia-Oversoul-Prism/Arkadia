# P0.3 — Governance Visibility — Evidence

**Packet:** SOLSPIRE-P0-EXECUTION-01  
**Base:** `dcda7efa...`

## Scope
Display existing readiness/auth stages as:
Proposal ≠ Approval ≠ Execution ≠ Verified
UI does not authorize K15; backend remains authoritative.

## Acceptance
- [x] Stages visible in Weaver panel
- [x] lock_reasons path preserved
- [x] No PassSpec/K15 semantic change
- [x] No UI-as-authority

## Tests
`tests/test_solspire_p0_execution_01.py` · test_p0_3_*
