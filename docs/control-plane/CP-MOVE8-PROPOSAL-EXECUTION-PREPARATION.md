# CP-MOVE8 — Proposal Execution Preparation

**STATUS:** DESIGN + IMPLEMENTATION BOUNDARY
**MODE:** Bounded preparation only, not K15/K3 execution
**CANONICAL SURFACE:** `solspire.proposal_manager` + `solspire.proposal_router`

> **ACCEPTED ≠ AUTHORIZED ≠ EXECUTED.**

Move 8 closes the distinction between a human content decision and a future governed execution step without creating a second authorization or execution subsystem.

## Boundary

The canonical implementation on `main` provides:

- `POST /proposals/{proposal_id}/decision` for an explicit human content decision.
- `POST /proposals/{proposal_id}/prepare-execution` for bounded preparation.
- `GET /proposals/{proposal_id}/preparations` for subject-bound inspection.

A human decision may set `ACCEPTED`, `DECLINED`, or `WITHDRAWN`. It does not authorize execution and does not mutate `authorization_ref`.

Execution preparation is only available for an `ACCEPTED` proposal. Preparation records remain non-executable and carry no PassSpec, K15, or K3 authority.

## Hard boundary markers

```text
execution_authorized = false
auto_merge = false
auto_deploy = false
auto_execute = false
pass_spec_ref = null
k15_ref = null
k3_ref = null
```

The preparation surface does not invoke K15 or K3, does not create a git commit or push, and does not grant merge or production authority.

## Architectural reconciliation

The original Move 8 branch introduced a separate `authorization_package_manager` and `authorization_packages` table. Current `main` already contains the canonical bounded execution-preparation substrate in `proposal_manager.py`. The reconciled branch therefore removes the duplicate persistence layer and keeps Move 8 on the existing proposal/workspace/API boundary.

This preserves:

- existing proposal persistence;
- existing subject/workspace isolation;
- existing canonical API routing;
- existing human decision semantics;
- existing K15/K3 boundary;
- human merge and production authority.

## Verification gate

Move 8 remains open until runtime evidence proves, at minimum:

1. unauthenticated access is rejected;
2. feedback cannot create `ACCEPTED`;
3. explicit human decision can create `ACCEPTED` without execution authority;
4. preparation requires `ACCEPTED`;
5. preparation remains non-executable;
6. subject/workspace isolation holds;
7. prior canonical surfaces remain intact.

Preview/build success is not production verification. No merge or production deployment is authorized by this document.

## Closure

```text
HUMAN DECISION
    ↓
PREPARATION
    ↓
FUTURE EXPLICIT EXECUTION AUTHORIZATION
    ↓
K15
    ↓
K3
```

Only the human authorization gate can move the system beyond preparation.
