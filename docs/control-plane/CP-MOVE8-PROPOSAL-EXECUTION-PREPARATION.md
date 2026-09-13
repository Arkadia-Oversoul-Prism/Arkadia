# CP-MOVE8 — Proposal Execution Preparation

**STATUS:** DESIGN + IMPLEMENTATION BOUNDARY  
**MODE:** Bounded preparation only — not K15/K3 execution  
**PRECEDES:** Any recursive loop or repository mutation under K3  

> **ACCEPTED ≠ AUTHORIZED ≠ EXECUTED.**  
> Move 8 prepares a reviewable authorization package. It does not execute.

## Purpose

Close the gap between:

```
PROPOSAL → FEEDBACK → ACCEPTED (human decision on content)
```

and:

```
AUTHORIZATION → PASS SPEC → K15 → K3 (governed mutation)
```

without collapsing those layers.

## Distinctions

| Claim | Rule |
|-------|------|
| ACCEPTED ≠ AUTHORIZED | Human acceptance of proposal content does not authorize mutation |
| AUTHORIZED ≠ EXECUTED | Even a future authorization event is not K3 execution |
| PREPARATION ≠ EXECUTION | Move 8 packages intent; it does not mutate product code |
| PACKAGE ≠ PASS SPEC | Package may *reference* intended scope; it does not become PassSpec authority |
| FEEDBACK ≠ ACCEPTANCE | Only an explicit human decision endpoint may set ACCEPTED/DECLINED |
| CONSENSUS ≠ AUTHORIZATION | Unanimous feedback cannot create an authorization package that executes |

## Human decision (content)

Explicit authenticated action may set proposal status to:

- `ACCEPTED` — human accepts the proposal content for later consideration
- `DECLINED` — human declines
- `WITHDRAWN` — human withdraws

These actions set `decision_ref` to a decision record id. They **must not** set `authorization_ref` by themselves.

## Authorization package (preparation)

An authorization package may be created **only** for a proposal already `ACCEPTED`.

Hard markers on every package:

```text
execution_authorized = false
auto_execute = false
k15_invoked = false
k3_invoked = false
merge_authorized = false
deploy_authorized = false
```

Any client attempt to set `execution_authorized=true` is **refused**.

Package states:

`PREPARED` | `REFUSED` | `SUPERSEDED` | `UNKNOWN`

`PREPARED` means: ready for a **future** human authorization of execution under a separate gate — not that execution is allowed now.

## Linkage

When a package is prepared, the proposal may store `authorization_ref = package_id` as a **pointer to the prep record**, not as proof of executable authority. Runtime consumers must treat package fields as authoritative for whether execution is allowed (always false under Move 8).

## Non-goals

- No K15 transaction
- No K3 plan/implement/verify
- No git commit/push from this surface
- No PassSpec minting that grants write scope
- No automatic promotion of ACCEPTED to AUTHORIZED
- No Barnabas live data ingestion
- No provenance frontier closure

## Implementation gate

Requires Moves 0–7 closed as applicable, explicit human authorization for Move 8, and runtime probes proving:

1. unauth → 401  
2. feedback cannot ACCEPTED  
3. human decision can ACCEPTED without authorization_ref  
4. prep refused unless ACCEPTED  
5. package always `execution_authorized=false`  
6. isolation  
7. prior surfaces intact  

## Closure criterion

Move 8 is CLOSED only when production probes confirm preparation without execution.

`HUMAN DECISION → PREP PACKAGE → (future) EXPLICIT EXECUTION AUTHORIZATION → K15 → K3`
