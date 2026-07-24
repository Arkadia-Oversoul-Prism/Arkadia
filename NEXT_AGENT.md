# Session Handoff
> Copy this entire file as the opening message to the next agent session.
> This file is rewritten at the end of every session.

---

## Completed This Session
- B0.5 — Baseline Integrity (fitness test direction fix, debt registration, registry rename)
- Governance infrastructure: BOOTSTRAP.md, CURRENT_STATE.md, ACTIVE_CONTEXT.md, DECISION_CACHE.md, PROJECT_INDEX.md, NEXT_AGENT.md created

## Not Started
- B1.1 — SQLite Schema (`kernel/storage/schema.py`, `tests/test_sqlite_schema.py`)

---

## Your Startup (follow exactly, in order)

1. Read `BOOTSTRAP.md`
2. Read `CURRENT_STATE.md`
3. Read `ACTIVE_CONTEXT.md`
4. Run `pytest tests/architecture/ -v` — confirm 10/10
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
`kernel/storage/` — create the directory and schema file.
Schema spec: `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md`

## Stop When
`pytest tests/test_sqlite_schema.py` passes.
`pytest tests/architecture/` is 10/10.
`CURRENT_STATE.md` is updated.
This file (`NEXT_AGENT.md`) is rewritten for the B1.2 session.
