# Active Context — B1.2: SQLiteJobStore + SQLiteGoalStore
> Delete and rewrite this file at the start of every session.
> This is the engineer's scratchpad. It is not a governance document.

---

## Today's Objective
Implement the two SQLite-backed store classes.
`kernel/jobs.py` is NOT changed yet — that is B1.3.

## Files to Create (and only these)
```
kernel/storage/sqlite_job_store.py    — SQLiteJobStore class
kernel/storage/sqlite_goal_store.py   — SQLiteGoalStore class
tests/test_sqlite_job_store.py        — lifecycle, concurrency, retry tests
tests/test_sqlite_goal_store.py       — due_goals, run tracking tests
```

## Files to Read (and only these)
```
kernel/jobs.py              — match the public API exactly (read-only)
kernel/goals.py             — match the public API exactly (read-only)
kernel/storage/schema.py    — already written; import create_tables() from here
```

## Public API to Preserve (from kernel/jobs.py)
```python
# JobStore methods
create(intent: dict, *, source: str = "api") -> dict
get(job_id: str) -> dict | None
list(*, limit: int = 100, status: str | None = None) -> list[dict]
update(job_id: str, **fields) -> dict | None
mark_running(job_id: str) -> dict | None
mark_completed(job_id: str, result: Any) -> dict | None
mark_failed(job_id: str, error: str) -> dict | None
requeue_for_retry(job_id: str, error: str) -> dict | None
next_job_id(timeout: float = 1.0) -> str | None    # blocking poll replacement
task_done() -> None
stats() -> dict[str, int]
reset() -> None    # test-only
```

## Do Not Touch
```
kernel/jobs.py          (integration is B1.3)
kernel/goals.py         (integration is B1.3)
kernel/worker.py        (integration is B1.3)
kernel/execution.py     (not in scope)
api/                    (not in scope)
tests/architecture/     (not in scope)
LAYER_MAP.py            (not in scope)
Any ADR or governance doc
```

## Stop Condition
`pytest tests/test_sqlite_job_store.py` passes.
`pytest tests/test_sqlite_goal_store.py` passes.
`pytest tests/architecture/` is still 10/10.
`CURRENT_STATE.md` is updated to reflect B1.2 complete, B1.3 ready.
`NEXT_AGENT.md` is rewritten.

## Key Implementation Notes
- Use `create_tables()` from `kernel.storage.schema` in `__init__` (ensures schema exists)
- Atomic claim: `BEGIN IMMEDIATE; SELECT … LIMIT 1; UPDATE … ; COMMIT` (see design doc)
- `next_job_id(timeout)` replaces `queue.Queue.get(timeout)` — poll loop with sleep
- WAL mode: set by `create_tables()`; do not re-set in store code
- `reset()` is test-only: DELETE FROM jobs; DELETE FROM goals
