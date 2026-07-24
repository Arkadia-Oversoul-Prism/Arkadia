# Phase 1 — Runtime State Diagram

**Status:** Analysis complete. No implementation until deliverables are approved.  
**Date:** 2026-07-24  
**Workstream:** B — Runtime Durability

---

## Current Runtime Architecture

```
Process startup (FastAPI lifespan)
        │
        ├── JobStore()        ← singleton, lazy-init via get_store()
        │     ├── _jobs: dict[str, Job]        IN MEMORY
        │     ├── _queue: queue.Queue[job_id]  IN MEMORY
        │     └── _load_snapshot()
        │           ├── reads data/job_store.json  (if exists)
        │           └── fallback: reads Firestore   (if Firebase configured)
        │
        ├── GoalStore()       ← singleton, lazy-init via get_store()
        │     ├── _goals: dict[str, Goal]      IN MEMORY
        │     └── _load()
        │           ├── reads data/goal_store.json  (if exists)
        │           └── fallback: reads Firestore
        │
        ├── start_workers(n)  ← n daemon threads (default 2, via SOLSPIRE_WORKERS)
        │     └── _worker_loop(i) × n
        │           └── loop: store.next_job_id(timeout=1.0) → _process_job()
        │
        └── start_goal_scheduler()
              └── _goal_scheduler_loop()
                    └── every SOLSPIRE_GOAL_TICK_SECONDS (default 15):
                          due_goals() → create job per goal → enqueue
```

---

## Job Lifecycle State Machine

```
                    ┌─────────┐
         create()   │         │
         ──────────►│ PENDING │
                    │         │
                    └────┬────┘
                         │ worker picks up
                         │ mark_running()
                         ▼
                    ┌─────────┐
                    │         │
                    │ RUNNING │
                    │         │
                    └────┬────┘
                         │
                ┌────────┴────────┐
                │                 │
          success=True      success=False / exception
                │                 │
                ▼                 ▼
          ┌──────────┐     retries < MAX_RETRIES (3)?
          │          │           │
          │COMPLETED │    YES ───┘──► requeue_for_retry() → PENDING
          │          │    NO ───────► mark_failed() → FAILED
          └──────────┘                     │
                                      ┌────┴─────┐
                                      │          │
                                      │  FAILED  │
                                      │          │
                                      └──────────┘
```

---

## Persistence Reality (Current)

### What survives a soft restart (process killed, re-started):

```
✅ Persisted (JSON snapshot)
   - All job records (status, result, error, timestamps)
   - In-flight jobs (RUNNING) are reset to PENDING on reload
   - Goal records

✅ Persisted (Firestore, when configured)
   - Same as above, mirrored to cloud

❌ NOT persisted
   - The in-memory queue.Queue contents (job_ids waiting to run)
   - Jobs enqueued AFTER last _persist() call and BEFORE crash
   - Goal scheduler position (re-derives from next_run timestamps — acceptable)
```

### Critical gap: the queue is not the store

`JobStore._queue` (a `queue.Queue`) and `JobStore._jobs` (a dict) are separate.
A job can be:
- In `_jobs` as PENDING but NOT in `_queue` (if snapshot was loaded mid-flight and the job was already dequeued when the snapshot was taken)
- In `_queue` but already COMPLETED (worker checks status before processing — safe)

On restart, `_load_snapshot()` re-enqueues any job with status PENDING or RUNNING.
This is correct but relies on the JSON snapshot being atomic — which it is (via `os.replace`).

### Race condition window (low risk, documented):

```
T1: create() → adds to _jobs → _persist() → adds to _queue
T2: worker picks up from _queue → mark_running() → _persist()
T3: CRASH (after T2 persist writes RUNNING, before completion)
T4: Restart → loads RUNNING job → resets to PENDING → re-enqueues
→  Job re-runs. Idempotency of job execution is NOT enforced.
   (Acceptable for current capabilities; must be addressed before
    financial or external-side-effect operations run autonomously.)
```

---

## Worker Thread Model

```
Main thread (FastAPI event loop — asyncio)
    │
    ├── Worker-0 (daemon thread — blocking, synchronous)
    │     └── execute_intent() — synchronous Gemini calls, file I/O
    │
    ├── Worker-1 (daemon thread — same)
    │     └── execute_intent()
    │
    └── Goal Scheduler (daemon thread)
          └── due_goals() + job_store.create() × N goals
```

**Threading model observations:**
- Workers are daemon threads → die with the process (no graceful drain on shutdown)
- `stop_workers()` sends `_shutdown` event and joins with timeout — best-effort
- In-flight jobs at shutdown time: marked RUNNING in snapshot, will re-run on restart
- `execute_intent` is blocking and synchronous inside a daemon thread — correct for current scale
- Concurrency limit: `SOLSPIRE_WORKERS` threads × 1 job each = bounded parallelism

---

## Durability Gap Summary

| Gap | Severity | Phase 1 target |
|---|---|---|
| In-memory `queue.Queue` loses pending jobs on crash | HIGH | YES — SQLite queue |
| No job idempotency guarantee | MEDIUM | Design note in SQLite design |
| Daemon threads have no graceful drain | LOW | Acceptable until job volume grows |
| Firestore sync is best-effort (silent failure) | MEDIUM | Acceptable; log failures |
| GoalStore and JobStore duplicate persistence pattern | MEDIUM | YES — shared StorageBackend |
| JSON snapshot: every `_persist()` rewrites entire file | LOW | SQLite eliminates this |
| `os.replace()` atomicity: works on Linux; not guaranteed on NFS | LOW | Document; not a current risk |

---

## Target Runtime Architecture (Phase 1)

```
Process startup
        │
        ├── SQLiteJobStore()     ← replaces in-memory JobStore
        │     ├── SQLite WAL mode (crash-safe)
        │     ├── No in-memory dict — SQLite IS the store
        │     └── Queue: SELECT ... WHERE status='pending' ORDER BY created_at
        │
        ├── SQLiteGoalStore()    ← replaces GoalStore
        │     └── Same SQLite database (separate table)
        │
        └── Workers poll SQLite queue instead of queue.Queue
              └── UPDATE job SET status='running' WHERE status='pending' LIMIT 1
                  (atomic; safe under multiple workers)
```

Firebase remains additive: a sync adapter that mirrors SQLite rows to Firestore
on write — not embedded in the store itself.

---

*Next document: SQLITE_JOB_QUEUE_DESIGN.md*
