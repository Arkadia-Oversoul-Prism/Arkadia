# Arkadia — Current State
> Updated at the end of every session. The next agent reads this before anything else.
> If this file and another document disagree, verify the code. Update this file. (Principle 11)

---

## Phase
Phase 1 — Runtime Stabilization

## Checkpoint
**B1.3 — Worker Integration** (READY TO BEGIN)

## Mode
BUILD

## Objective
Wire `kernel/jobs.py` to use `SQLiteJobStore` and `kernel/goals.py` to use `SQLiteGoalStore`.
Run the JSON→SQLite migration on first startup. Add restart and concurrency tests on the live path.

## Scope (this checkpoint only)
- Edit `kernel/jobs.py`: import `SQLiteJobStore as JobStore` from `kernel.storage.sqlite_job_store`
- Edit `kernel/goals.py`: import `SQLiteGoalStore as GoalStore` from `kernel.storage.sqlite_goal_store`
- Add migration: on first startup, if `data/runtime.db` does not exist, import `data/job_store.json` and `data/goal_store.json`
- Write `tests/test_jobs_migration.py` — verifies JSON→SQLite import integrity
- Run restart simulation test (RUNNING → PENDING recovery on new store init)
- Run concurrency test on the wired-up path

## Stop When
All tests pass. `kernel/jobs.py` and `kernel/goals.py` use SQLite. JSON files preserved read-only. Architecture fitness 10/10.

## Do Not Touch
- `kernel/worker.py` (unchanged — it calls jobs.get_store() which will now return SQLiteJobStore)
- `api/` (any file)
- Fitness tests / LAYER_MAP.py
- ADRs / Governance docs

## Blocked By
Nothing.

## Repository Health
- Branch: `main`
- Architecture fitness: 10/10 passing
- Schema tests: 11/11 passing (B1.1)
- Job store tests: 21/21 passing (B1.2)
- Goal store tests: 26/26 passing (B1.2)
- Total: 68/68 passing
- Workflows: failing (pre-existing — missing secrets, not a B1 blocker)

## Success Criteria (B1.3)
- [ ] `kernel/jobs.py` uses SQLiteJobStore
- [ ] `kernel/goals.py` uses SQLiteGoalStore
- [ ] JSON→SQLite migration runs on first startup
- [ ] `pytest tests/test_jobs_migration.py` passes
- [ ] Restart simulation passes
- [ ] Concurrency test passes
- [ ] `pytest tests/architecture/` still 10/10
- [ ] Repository deployable
- [ ] Continuation Ledger updated

## Last Session
B1.2 — SQLiteJobStore + SQLiteGoalStore complete.
- Created `kernel/storage/sqlite_job_store.py` (SQLiteJobStore, 21 tests all passing)
- Created `kernel/storage/sqlite_goal_store.py` (SQLiteGoalStore, 26 tests all passing)
- Created `MISSION.md` (one-page session orientation)
- Architecture fitness: 10/10 (unchanged)

## Next Checkpoints (do not implement yet)
- B1.4 — Cleanup / Gate B close
