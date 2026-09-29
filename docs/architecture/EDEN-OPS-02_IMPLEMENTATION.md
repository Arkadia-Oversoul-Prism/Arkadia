# EDEN-OPS-02 — Implementation Baseline

**Status:** RECOVERED / IMPLEMENTED on `gate-00-closure-eden-ops-02-recovery` (not yet VERIFIED, not yet in `main`)
**Base:** EDEN-OPS-01 head `aef3a283a9901b74590b45c9aae930c900a72fcd`
**Specification:** AUTHORIZED 2026-09-28

## Canonical recovery record (GATE-00 closure)

The historical implementation lived on `feat/eden-ops-02-team-cockpit`. PR #89 was
recorded as merged, but it merged into `feat/eden-ops-01-live-cockpit`, which had
already been merged to `main` at `3858af8`. Merge commit `0e71508` is therefore
**not an ancestor of `main`**, and no EDEN-OPS-02 artifact ever reached `main`.
Historical state: **CONTRADICTED** (merged record, absent from canonical base).

Orphaned commits are preserved unchanged as evidence:

- `evidence/eden-ops-02-orphan-tip`   → `239887c3ca994a56386bcc7152636190d9790fea`
- `evidence/eden-ops-02-orphan-merge` → `0e715086dab61694b7bb5db3ae64ef251854d92f`

This branch recovers the intended capability onto `main @ 0b1ee72` and repairs
only the four demonstrated defects:

1. `public_enterprise_payload` — was referenced by `enterprise_router` and its own
   test but never defined (`AttributeError`).
2. `owner_uid_for_enterprise` — was referenced by `eden_ops_02_routes` and
   `enterprise_router` but never defined (`AttributeError`).
3. Invalid-handle `LookupError` → `ValueError` — an unparseable handle was reported
   as "unknown handle" instead of a format error.
4. Seed/desk mismatch — the Week-1 seed contained no `Logistics` row although
   `EDEN_DESKS` and `week-1-monday.md` (16:00 Logistics + Quality) define it. The
   two sheet-specified Logistics tasks were restored and the stale magic-number
   count assertion was replaced with seed-derived, uniqueness and desk-validity
   assertions.

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
