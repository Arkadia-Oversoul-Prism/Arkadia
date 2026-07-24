# Session Handoff
> Copy this entire file as the opening message to the next agent session.
> This file is rewritten at the end of every session.

---

## Completed This Session
- B1.2 — SQLiteJobStore + SQLiteGoalStore
  - `kernel/storage/sqlite_job_store.py` — 21 tests passing
  - `kernel/storage/sqlite_goal_store.py` — 26 tests passing
  - `MISSION.md` created (one-page session orientation)
  - Total: 68/68 tests passing; architecture fitness 10/10

## Not Started
- B1.3 — Worker Integration

---

## Your Startup (maximum 3 minutes, follow exactly)

1. Read `MISSION.md`
2. Read `BOOTSTRAP.md`
3. Read `CURRENT_STATE.md`
4. Run `python3 -m pytest tests/architecture/ -q` — confirm 10/10
5. Implement the objective in `CURRENT_STATE.md`
6. Run verification once
7. Update `MISSION.md`, `CURRENT_STATE.md`, `NEXT_AGENT.md`
8. Stop

## Do NOT Reopen
- ENGINEERING_PRINCIPLES.md, ROADMAP.md, ARCHITECTURE_MAP.md, PHASE_GATES.md
- Any ADR (ADR-010 through ADR-015)
- CONTINUATION_LEDGER.md (except to update at session end)
- ACTIVE_CONTEXT.md (superseded by MISSION.md)
- DECISION_CACHE.md (unless blocked by a design question)

## Key Files for B1.3
- `kernel/jobs.py` — replace JobStore backend (read it first; match existing module-level API)
- `kernel/goals.py` — replace GoalStore backend (read it first)
- `kernel/storage/sqlite_job_store.py` — already done; import from here
- `kernel/storage/sqlite_goal_store.py` — already done; import from here
- `data/job_store.json` / `data/goal_store.json` — migration source; preserve read-only

## Stop When
`pytest tests/test_jobs_migration.py` passes.
`pytest tests/architecture/` is 10/10.
`MISSION.md` updated to B1.4.
`CURRENT_STATE.md` updated to B1.4 ready.
This file rewritten for the B1.4 session.
