# Active Context — B1.1: SQLite Schema
> Delete and rewrite this file at the start of every session.
> This is the engineer's scratchpad. It is not a governance document.

---

## Today's Objective
Create the SQLite schema for the runtime database.

This is the only thing that should happen this session.

## Source of Truth for Schema
`docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` → "Schema" section.
Read that file when writing the DDL. Do not invent columns.

## Files to Create (and only these)
```
kernel/storage/__init__.py          — empty or minimal; makes storage a package
kernel/storage/schema.py            — DDL constants + create_tables(db_path) function
tests/test_sqlite_schema.py         — verifies tables and columns exist
```

## Files to Read (and only these)
```
docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md   — schema spec
kernel/jobs.py                            — to understand existing field names (read-only)
```

## Do Not Touch
```
kernel/jobs.py          (integration is B1.2)
kernel/goals.py         (integration is B1.2)
kernel/worker.py        (integration is B1.3)
kernel/execution.py     (not in scope)
kernel/planner.py       (not in scope)
api/                    (not in scope)
tests/architecture/     (not in scope)
LAYER_MAP.py            (not in scope)
Any ADR or governance doc
```

## Stop Condition
`pytest tests/test_sqlite_schema.py` passes.
`pytest tests/architecture/` is still 10/10.
`CURRENT_STATE.md` is updated to reflect B1.1 complete, B1.2 ready.
`NEXT_AGENT.md` is written.

## Known Constraints
- Database path: `data/runtime.db` (separate from `knowledge/arkadia.db`)
- Use WAL mode: `PRAGMA journal_mode=WAL`
- `create_tables()` must be idempotent — `CREATE TABLE IF NOT EXISTS`
- No migration of existing data in B1.1; that is B1.3
