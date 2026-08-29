# WEAVER-W4 — Operator Validation + SolSpire Project Intelligence

## Principle

Project access ≠ PassSpec ≠ PatchApproval ≠ K15/K3 execution.

## Delivered

- `weaver/capabilities.py` — discovery registry (not authority)
- `weaver/operator_validation.py` — explicit read-only scenarios
- `solspire/weaver_bridge.py` — project-scoped analyze context
- SolSpire routes under `/solspire/projects/{id}/weaver/*`
- ProjectDashboard **Weaver** tab (read-only)
- Cockpit `/api/capabilities` and `/api/validation`

## Not introduced

- Second memory / graph / embedding store
- Second mutation path
- K17 patch fidelity
- Autonomous loops
