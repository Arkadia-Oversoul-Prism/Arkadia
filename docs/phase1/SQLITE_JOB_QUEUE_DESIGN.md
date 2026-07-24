# Phase 1 — SQLite Job Queue Design

**Status:** Design complete. Awaiting approval before implementation.  
**Date:** 2026-07-24  
**Workstream:** B — Runtime Durability

---

## Problem Statement

`kernel/jobs.py` uses `queue.Queue` (in-memory) as the pending-job queue and a dict as the job store. A JSON snapshot provides soft-restart recovery but:
- Jobs enqueued between the last snapshot and a crash are silently lost
- The JSON file is rewritten in full on every state change (O(N) writes)
- The queue and the store are two separate data structures that can diverge
- Multiple workers race on `queue.Queue.get()` — correct but opaque

**Target:** Replace with SQLite, keeping the existing `JobStore` public API unchanged.

---

## Design Principles

1. **SQLite IS the queue** — no separate in-memory structure. Workers query the database directly.
2. **WAL mode** — SQLite WAL (Write-Ahead Logging) enables concurrent readers + one writer. No corruption on crash.
3. **Atomic claim** — worker claims a job in a single `UPDATE ... WHERE status='pending' ... RETURNING` statement. No TOCTOU between "find pending job" and "mark it running".
4. **Backward-compatible API** — `JobStore.create()`, `.get()`, `.list()`, `.mark_running()`, `.mark_completed()`, `.mark_failed()`, `.requeue_for_retry()`, `.stats()` signatures unchanged. No changes to `worker.py`, `api/main.py`, or any route that calls the store.
5. **Firebase remains additive** — sync adapter fires after SQLite write, never blocks the store.
6. **Incremental migration** — JSON snapshot reader preserved as a one-time import on first startup.

---

## Schema

```sql
-- Single database: data/arkadia.db (or ARKADIA_DB_PATH env override)
-- Shared with knowledge/arkadia.db if the Knowledge OS path matches;
-- otherwise a separate file at data/runtime.db to avoid coupling.
-- Recommendation: data/runtime.db (keeps runtime state separate from knowledge)

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── jobs ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,
    status      TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    intent      TEXT NOT NULL DEFAULT '{}',   -- JSON blob
    result      TEXT,                          -- JSON blob, nullable
    error       TEXT,
    trace       TEXT,                          -- JSON blob, nullable (Phase 8 trace)
    retries     INTEGER NOT NULL DEFAULT 0,
    source      TEXT NOT NULL DEFAULT 'api',
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    started_at  REAL,
    ended_at    REAL
);

-- Indexes to support common query patterns
CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_source     ON jobs (source);

-- ── goals ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS goals (
    goal_id           TEXT PRIMARY KEY,
    description       TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'paused', 'completed')),
    cadence_seconds   REAL NOT NULL DEFAULT 300.0,
    max_runs_per_hour INTEGER NOT NULL DEFAULT 6,
    next_run          REAL,
    last_run          REAL,
    run_count         INTEGER NOT NULL DEFAULT 0,
    history           TEXT NOT NULL DEFAULT '[]',  -- JSON array of job_ids, capped at 50
    created_at        REAL NOT NULL,
    updated_at        REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_goals_status   ON goals (status);
CREATE INDEX IF NOT EXISTS idx_goals_next_run ON goals (next_run);
```

---

## Worker Claim Protocol (Atomic)

Current (race-prone conceptually, safe only because Python GIL + queue.Queue):
```python
job_id = store.next_job_id(timeout=1.0)  # blocks on queue.Queue.get()
job = store.get(job_id)
store.mark_running(job_id)
```

SQLite replacement (truly atomic across processes and threads):
```sql
-- Worker N executes this as a single transaction:
BEGIN IMMEDIATE;
    SELECT job_id FROM jobs
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT 1;

    UPDATE jobs
    SET status = 'running', started_at = ?, updated_at = ?
    WHERE job_id = ?;
COMMIT;
```

`BEGIN IMMEDIATE` acquires a write lock before the SELECT, so two workers cannot claim the same job. If no pending job exists, the worker sleeps for 0.5–1s and retries (replacing the blocking `queue.Queue.get(timeout=1.0)` behaviour).

---

## Migration Strategy

### Step 1: Parallel write (no disruption)

On startup, if `data/runtime.db` does not exist:
1. Create and schema the SQLite database
2. If `data/job_store.json` exists, read it and INSERT all jobs into SQLite
3. If `data/goal_store.json` exists, read it and INSERT all goals into SQLite
4. Log the import counts

The old JSON files are left in place as a read-only backup. They are not written after migration.

### Step 2: Switch JobStore backend

Replace the `dict + queue.Queue` implementation in `kernel/jobs.py` with `kernel/storage/sqlite_job_store.py`. The class exposes the identical public API.

The existing `JobStore` class becomes an alias:
```python
# kernel/jobs.py (after migration)
from kernel.storage.sqlite_job_store import SQLiteJobStore as JobStore
```

All callers continue unchanged.

### Step 3: Switch GoalStore backend

Same pattern: `kernel/storage/sqlite_goal_store.py`, same public API.

### Step 4: Remove JSON snapshot code

After two weeks of stable production operation with SQLite, remove `_persist()` / `_load_snapshot()` from the old implementation.

---

## Rollback Plan

If SQLite introduces a regression:
1. Rename `data/runtime.db` → `data/runtime.db.broken`
2. Restore the previous `kernel/jobs.py` from git (one-file revert)
3. JSON snapshots are still present and will be loaded on next start
4. Zero data loss for completed/failed jobs (JSON has them); in-flight jobs re-run

The rollback is a single `git revert` of the migration commit. The constraint: **every commit must leave the repository deployable** (per Phase 1 engineering rules).

---

## Concurrency Model

| Scenario | Current (queue.Queue) | SQLite |
|---|---|---|
| 2 workers, same job | Cannot happen (queue.Queue dequeues atomically) | Cannot happen (BEGIN IMMEDIATE) |
| Job created during worker poll | Added to queue immediately | SELECT finds it on next poll cycle |
| Process crash mid-job | RUNNING job reset to PENDING on next start | Same (UPDATE status on startup) |
| Read-only query (GET /api/job/{id}) | Lock-free (dict read under RLock) | WAL reader — no blocking write lock needed |
| High write throughput | Unbounded (in-memory) | SQLite WAL handles ~10K writes/sec on SSD |

---

## What This Does NOT Do

- Does not introduce Redis, Kafka, or any external queue. SQLite is sufficient.
- Does not change the job schema (all existing fields preserved).
- Does not change the Firebase sync behaviour — it remains an optional additive mirror.
- Does not affect the Knowledge OS SQLite database (separate file).

---

## File Plan

```
kernel/
  storage/
    __init__.py
    base.py              ← StorageBackend abstract base
    sqlite_job_store.py  ← SQLiteJobStore (new)
    sqlite_goal_store.py ← SQLiteGoalStore (new)
    json_job_store.py    ← extracted from current jobs.py (deprecated, for rollback)
  jobs.py                ← imports SQLiteJobStore as JobStore (API unchanged)
  goals.py               ← imports SQLiteGoalStore as GoalStore (API unchanged)

data/
  runtime.db             ← new SQLite database
  job_store.json         ← preserved read-only (migration source)
  goal_store.json        ← preserved read-only (migration source)

tests/
  test_sqlite_job_store.py   ← new
  test_sqlite_goal_store.py  ← new
  test_jobs_migration.py     ← verifies JSON→SQLite import integrity
```

---

## Tests Required Before Implementation Is Complete

1. `create()` + `get()` round-trip
2. Two concurrent workers claim different jobs (no double-claim)
3. Process crash simulation: RUNNING job resets to PENDING on restart
4. JSON snapshot migration: all jobs imported with correct field values
5. `stats()` returns correct counts
6. `requeue_for_retry()` respects `MAX_RETRIES`
7. Goal `due_goals()` returns only active goals past `next_run`

---

*Next document: PLUGIN_REGISTRY_SPEC.md*
