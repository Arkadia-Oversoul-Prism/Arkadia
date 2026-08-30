# R4 — SolSpire `/run` Orchestration Reconciliation

**Scope:** collapse duplicated global/project `/run` orchestration without changing execution authority.

## Decision

Both `/solspire/run` and `/solspire/projects/{project_id}/run` now delegate to one canonical `_execute_run()` pipeline:

`provider selection → intent classification → plan creation → plan validation → ExecutionRuntime → bounded wait → response`

The project route remains a contextual wrapper. It enforces project ownership, delegates the complete run to `_execute_run()`, then records the existing `workflow_run` activity event.

## Preserved boundaries

- Project ownership remains enforced by `require_project_owner`.
- Execution ownership continues to use the authenticated Firebase UID.
- ExecutionRuntime remains the R3 general workflow substrate and does not gain mutation authority.
- Weaver/K15/K3 governance remains outside this `/run` workflow.
- No second authorization authority is introduced.

## R4 invariant

> There is exactly one SolSpire intent → plan → validate → execute implementation; project context adds observability, not a second orchestration path.
