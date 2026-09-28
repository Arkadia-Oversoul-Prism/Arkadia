# EDEN-OPS-02 — Implementation Baseline

**Status:** IMPLEMENTATION on `feat/eden-ops-02-team-cockpit`
**Base:** EDEN-OPS-01 head `aef3a283a9901b74590b45c9aae930c900a72fcd`
**Specification:** AUTHORIZED 2026-09-28

## Included
- UID-backed membership via `eden_role_bindings` (placeholders grant nothing)
- Handle → UID resolution (api.auth primitives; injectable in tests)
- Shared `enterprise_tasks` table + Week-1 seed
- Evidence-required DONE/BLOCKED
- Control-room six-zone projection
- HTTP routes on enterprise_router (members, tasks, control-room)
- EnterpriseConsole control room UI replacing JSON dump

## Boundaries preserved
No K15/K3, WorkEvent schema, LAYER_MAP, Eden scaffold, or second mutation path.
