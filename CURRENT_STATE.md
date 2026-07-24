# Arkadia — Current State
> Updated at the end of every session. The next agent reads this before anything else.
> If this file and another document disagree, verify the code. Update this file. (Principle 11)

---

## Phase
Phase 1 — Runtime Stabilization

## Checkpoint
**B1.2 — SQLiteJobStore** (READY TO BEGIN)

## Mode
BUILD

## Objective
Implement `kernel/storage/sqlite_job_store.py` and `kernel/storage/sqlite_goal_store.py`.
The public API of `kernel/jobs.py` (JobStore class) must be preserved exactly.
`kernel/jobs.py` itself is NOT changed in this checkpoint — that is B1.3.

## Scope (this checkpoint only)
- Create `kernel/storage/sqlite_job_store.py` — `SQLiteJobStore` class
- Create `kernel/storage/sqlite_goal_store.py` — `SQLiteGoalStore` class
- Write `tests/test_sqlite_job_store.py` — full lifecycle + concurrency + retry tests
- Write `tests/test_sqlite_goal_store.py` — due_goals, run tracking tests

## Stop When
All unit tests pass. `kernel/jobs.py` still uses the old in-memory store. Architecture fitness still 10/10.

## Do Not Touch
- `kernel/jobs.py` (B1.3)
- `kernel/goals.py` (B1.3)
- `kernel/worker.py` (B1.3)
- `api/` (any file)
- Fitness tests / LAYER_MAP.py
- ADRs / Governance docs

## Blocked By
Nothing.

## Repository Health
- Branch: `main`
- Fitness tests: 10/10 passing
- Schema tests: 11/11 passing (new — B1.1)
- Registered debt: 10 layer violations + 3 circular imports (all in LAYER_MAP.py — do not touch)
- Workflows: failing (pre-existing — missing secrets, not a B1 blocker)

## Success Criteria (B1.2)
- [ ] `kernel/storage/sqlite_job_store.py` exists and passes all tests
- [ ] `kernel/storage/sqlite_goal_store.py` exists and passes all tests
- [ ] Atomic claim test passes (two workers, no double-claim)
- [ ] Crash recovery test passes (RUNNING → PENDING on startup)
- [ ] `pytest tests/architecture/` still 10/10
- [ ] Repository deployable (no import errors introduced)
- [ ] Continuation Ledger updated

## Last Session
B1.1 — SQLite Schema complete.
- Created `kernel/storage/__init__.py`
- Created `kernel/storage/schema.py` (DDL + `create_tables()`)
- Created `tests/test_sqlite_schema.py` (11 tests — all passing)
- Architecture fitness: 10/10 (unchanged)

## Next Checkpoints (do not implement yet)
- B1.3 — Worker Integration (replace in-memory queue in kernel/jobs.py)
- B1.4 — Cleanup / Gate B close
