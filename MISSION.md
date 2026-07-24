# Arkadia — Mission
> One page. Never grow this file. Update at the end of every session.
> Start here. Then read BOOTSTRAP.md and CURRENT_STATE.md. Nothing else is mandatory.

---

## Current Phase
Phase 1 — Runtime Stabilization

## Current Workstream
B — Runtime Durability

## Current Checkpoint
**B1.3 — Worker Integration**

## Today's Goal
Wire `kernel/jobs.py` and `kernel/goals.py` to use the SQLite stores.
Add JSON→SQLite migration. Verify restart and concurrency on the live path.

## Stop Condition
`pytest tests/test_jobs_migration.py` passes.
`pytest tests/architecture/` is 10/10.
`kernel/jobs.py` and `kernel/goals.py` use SQLite backends.
Repository is deployable.

## Success Criteria
- [ ] `kernel/jobs.py` → imports SQLiteJobStore as JobStore
- [ ] `kernel/goals.py` → imports SQLiteGoalStore as GoalStore
- [ ] Migration: JSON→SQLite import on first startup if `data/runtime.db` absent
- [ ] `tests/test_jobs_migration.py` — JSON import integrity verified
- [ ] Restart simulation: RUNNING → PENDING on re-init
- [ ] Concurrency: two workers, no double-claim on live path
- [ ] Architecture fitness: 10/10
- [ ] `docs/checkpoints/B1.3.md` written
- [ ] `CURRENT_STATE.md` updated to B1.4 ready
