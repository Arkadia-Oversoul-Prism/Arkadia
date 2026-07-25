# 03 — Scope
> Rewritten every session. This is the session scratchpad.
> Current session: B1.1 — SQLite Schema

---

## Today's Objective

**Implement the SQLite schema for the runtime database.**

Nothing else. Do not optimize. Do not refactor. Do not rename. Do not improve documentation outside this file. Do not explore. Stop immediately after tests pass.

---

## Source of Truth
`docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` → "Schema" section.
Read that file for the DDL. Do not invent columns.

## Files to Read (and only these)
```
docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md    — schema spec (required)
kernel/jobs.py                             — existing field names (read-only, for alignment)
```

## Files to Create (and only these)
```
kernel/storage/__init__.py    — empty package init
kernel/storage/schema.py      — DDL constants + create_tables(db_path: str) -> None
tests/test_sqlite_schema.py   — verifies tables and columns exist after create_tables()
```

## Implementation Constraints
- Use `CREATE TABLE IF NOT EXISTS` — `create_tables()` must be idempotent
- Enable WAL mode: `PRAGMA journal_mode=WAL`
- Database path for tests: `data/test_runtime.db` (not the production path)
- Production path: `data/runtime.db`
- Do not add `data/runtime.db` to the repository — it is runtime state

## Files Forbidden This Session
```
kernel/jobs.py          — integration is B1.2, not now
kernel/goals.py         — integration is B1.2, not now
kernel/worker.py        — integration is B1.3, not now
kernel/execution.py     — not in scope
kernel/planner.py       — not in scope
api/                    — not in scope
providers/              — not in scope
web/                    — not in scope
tests/architecture/     — not in scope
LAYER_MAP.py            — not in scope (never in Build mode)
Any ADR or governance doc — not in scope (check 02_DECISIONS.md instead)
```

## Stop Condition
`pytest tests/test_sqlite_schema.py` passes.
`pytest tests/architecture/ -v` is still 10/10.
`01_STATE.md` updated to reflect B1.1 complete, B1.2 ready.
`04_SUCCESS.md` updated.
`NEXT_AGENT.md` rewritten for B1.2.
