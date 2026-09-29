# M01 — Persistence Architecture

Status: PENDING

## Objective
Make the Solariun workspace truthfully persistent without creating a parallel filesystem or Knowledge OS.

## Required discovery
Inspect the existing project, file, conversation, task, memory, and Knowledge OS paths before choosing implementation details.

Determine:
- browser-local ownership
- server-side durable ownership
- synchronization direction
- offline behavior
- deployment survival
- logout/login recovery
- device restoration
- conflict handling
- identity and project scoping

## Implementation rule
Choose the smallest architecture compatible with the existing stack. Prefer an authenticated local-first workspace store synchronized with the existing durable corpus rather than replacing the existing backend model.

Do not introduce a second database or parallel project model.

## Acceptance
A created project and representative project data remain available after refresh, frontend redeploy, backend redeploy, logout/login, and normal session interruption.

The implementation must preserve user/project ownership boundaries and existing Knowledge OS relationships.

## Verification
- inspect storage model
- run existing backend/frontend tests
- add focused persistence tests where missing
- verify recovery behavior
- inspect final diff for parallel storage systems

## Stop condition
Stop at review. Do not advance to M02 until M01 is accepted.
