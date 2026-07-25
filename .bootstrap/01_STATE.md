# 01 — Current State
> Updated at the end of every session. Source of truth for what's next.

---

## Mode
BUILD

## Phase
Phase 1 — Runtime Stabilization

## Workstream
B — Durable Persistence

## Checkpoint
**B1.1 — SQLite Schema** (READY TO BEGIN)

## Current Goal
Create the SQLite schema for the runtime database (`data/runtime.db`).
This is the foundation for all durable job and goal persistence.

## Last Commit
B0.5 complete — baseline integrity: fitness test direction fixed, debt registered, registry renamed ALLOWED_VIOLATIONS → REGISTERED_ARCHITECTURAL_DEBT.

## Repository Health
- Architecture fitness tests: **10/10**
- Registered layer violations: 10 (LAYER_MAP.py — do not touch)
- Registered circular imports: 3 (LAYER_MAP.py — do not touch)
- Workflows: failing (pre-existing — missing secrets, not a B1 blocker)

## Blocked By
Nothing.

## Known Debt
See `REPOSITORY_SNAPSHOT.md` → Debt Registry section. All 13 entries assigned to Workstream A, Gate E. Do not touch in B1.

## Next Checkpoints (implement only when current is done)
- B1.2 — SQLiteJobStore
- B1.3 — Worker Integration
- B1.4 — Cleanup / Gate B close
