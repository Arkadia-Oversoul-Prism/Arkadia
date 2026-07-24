# Session Handoff
> Copy this entire file as the opening message to the next agent session.
> This file is rewritten at the end of every session.

---

## Completed This Session
- B1.1 — SQLite Schema
  - `kernel/storage/__init__.py` created
  - `kernel/storage/schema.py` created — DDL + `create_tables(db_path)` function
  - `tests/test_sqlite_schema.py` created — 11 tests, all passing
  - Architecture fitness: 10/10 (unchanged)

## Not Started
- B1.2 — SQLiteJobStore (`kernel/storage/sqlite_job_store.py`, `kernel/storage/sqlite_goal_store.py`)

---

## Your Startup (follow exactly, in order)

1. Read `BOOTSTRAP.md`
2. Read `CURRENT_STATE.md`
3. Read `ACTIVE_CONTEXT.md`
4. Run `python3 -m pytest tests/architecture/ -v` — confirm 10/10
5. Implement the objective in `ACTIVE_CONTEXT.md`
6. Run verification once (see ACTIVE_CONTEXT.md stop condition)
7. Update `CURRENT_STATE.md` and `NEXT_AGENT.md`
8. Stop

## Do NOT Reopen
- ENGINEERING_PRINCIPLES.md
- ROADMAP.md
- ARCHITECTURE_MAP.md
- PHASE_GATES.md
- Any ADR (ADR-010 through ADR-015)
- CONTINUATION_LEDGER.md (except to update it at session end)

## Begin In
`kernel/storage/` — create `sqlite_job_store.py` and `sqlite_goal_store.py`.

Read `kernel/jobs.py` and `kernel/goals.py` to match the public API exactly.
Import `create_tables` from `kernel.storage.schema` — do not duplicate DDL.

## Stop When
`pytest tests/test_sqlite_job_store.py` passes.
`pytest tests/test_sqlite_goal_store.py` passes.
`pytest tests/architecture/` is 10/10.
`CURRENT_STATE.md` is updated.
This file (`NEXT_AGENT.md`) is rewritten for the B1.3 session.
