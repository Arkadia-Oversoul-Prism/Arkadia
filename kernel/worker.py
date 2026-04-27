"""SolSpire Phase 5 — Background worker pool.

Daemon threads pull job_ids from the JobStore queue, run the Phase 4
kernel against the job's intent, and write the result back. Failures
are retried up to MAX_RETRIES with exponential backoff before the job
is marked failed.

  • Started by api.main on FastAPI startup
  • Daemon threads → die with the process, no shutdown handshake needed
  • Idempotent start: calling start_workers() twice is safe

Number of workers is set by the SOLSPIRE_WORKERS env var (default 2).
"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from kernel.execution import execute_intent
from kernel.jobs import (
    COMPLETED, FAILED, MAX_RETRIES, RUNNING,
    get_store,
)
from kernel.goals import get_store as get_goal_store

logger = logging.getLogger("arkadia.worker")

_workers: list[threading.Thread] = []
_started = False
_lock = threading.Lock()
_shutdown = threading.Event()

# ── Goal scheduler config ───────────────────────────────────────────────────
_GOAL_TICK_SECONDS = float(os.environ.get("SOLSPIRE_GOAL_TICK_SECONDS", "15"))
_GOAL_THREAD: threading.Thread | None = None


def _backoff_seconds(retry_count: int) -> float:
    # 0.5s, 1s, 2s — bounded so a busy retry loop can't starve other work.
    return min(2.0, 0.5 * (2 ** max(0, retry_count - 1)))


def _process_job(job: dict[str, Any]) -> None:
    store = get_store()
    job_id = job["job_id"]
    intent = job.get("intent") or {}

    store.mark_running(job_id)
    logger.info("job %s running (retry=%d)", job_id, job.get("retries", 0))

    try:
        result = execute_intent(intent)
    except Exception as e:  # noqa: BLE001 — worker must never die from job code
        logger.exception("job %s raised", job_id)
        _handle_failure(job_id, repr(e))
        return

    # The kernel itself can return success=False without raising. Treat that
    # as a soft failure for retry purposes — the spec considers `failed` as
    # any non-success terminal state.
    if isinstance(result, dict) and result.get("handled") and not result.get("success"):
        _handle_failure(
            job_id,
            error=f"kernel verify failed: {result.get('summary', 'no summary')}",
            partial_result=result,
        )
        return

    store.mark_completed(job_id, result)
    logger.info("job %s completed", job_id)

    # Phase 8: persist a focused trace for this job alongside the result.
    _record_job_trace(job_id, intent, result)


def _handle_failure(job_id: str, error: str,
                    partial_result: Any | None = None) -> None:
    """Spec step 4: bump retries, requeue if under cap, else mark failed."""
    store = get_store()
    current = store.get(job_id) or {}
    retries = int(current.get("retries", 0))

    if retries < MAX_RETRIES:
        backoff = _backoff_seconds(retries + 1)
        logger.warning(
            "job %s failed (retry %d/%d in %.1fs): %s",
            job_id, retries + 1, MAX_RETRIES, backoff, error,
        )
        time.sleep(backoff)
        store.requeue_for_retry(job_id, error=error)
    else:
        logger.error("job %s exhausted retries: %s", job_id, error)
        store.mark_failed(job_id, error=error)
        if partial_result is not None:
            store.update(job_id, result=partial_result)


def _record_job_trace(job_id: str, intent: dict[str, Any],
                      result: dict[str, Any] | None) -> None:
    """Phase 8 trace projection. Stores a compact, focused breakdown of the
    job — input, plan, per-step outputs, final summary — on the job record
    itself so /api/job/{id}/trace can serve it without recomputing."""
    if not isinstance(result, dict):
        return
    payload = (intent or {}).get("payload") or {}
    execution = result.get("execution") or {}
    steps = execution.get("steps") if isinstance(execution, dict) else result.get("steps") or []
    trace = {
        "job_id":     job_id,
        "intent_type": (intent or {}).get("type"),
        "input":      payload.get("input") or payload.get("message") or payload,
        "plan":       result.get("plan"),
        "plan_source": result.get("plan_source"),
        "context":    (execution or {}).get("context") if isinstance(execution, dict) else None,
        "steps": [
            {
                "step_id":     s.get("step_id"),
                "tool":        s.get("tool"),
                "input":       s.get("input"),
                "duration_ms": s.get("duration_ms"),
                "success":     bool((s.get("envelope") or {}).get("success")),
                "summary":     (s.get("envelope") or {}).get("summary"),
            }
            for s in (steps or []) if isinstance(s, dict)
        ],
        "success":    bool(result.get("success")),
        "summary":    result.get("summary"),
    }
    try:
        get_store().update(job_id, trace=trace)
    except Exception:  # noqa: BLE001 — trace is best-effort
        logger.exception("failed to persist trace for %s", job_id)


def _worker_loop(worker_id: int) -> None:
    store = get_store()
    logger.info("worker-%d online", worker_id)
    while not _shutdown.is_set():
        job_id = store.next_job_id(timeout=1.0)
        if job_id is None:
            continue
        try:
            job = store.get(job_id)
            if job is None:
                continue
            # If a snapshot reload re-enqueued a job that was already
            # completed/failed, skip it.
            if job.get("status") in (COMPLETED, FAILED):
                continue
            _process_job(job)
        finally:
            store.task_done()
    logger.info("worker-%d offline", worker_id)


# ── public API ─────────────────────────────────────────────────────────────

def start_workers(n: int | None = None) -> int:
    """Spin up N daemon worker threads. Idempotent. Returns worker count."""
    global _started
    with _lock:
        if _started:
            return len(_workers)
        if n is None:
            try:
                n = int(os.environ.get("SOLSPIRE_WORKERS", "2"))
            except ValueError:
                n = 2
        n = max(1, min(n, 16))
        _shutdown.clear()
        for i in range(n):
            t = threading.Thread(
                target=_worker_loop, args=(i,),
                name=f"solspire-worker-{i}", daemon=True,
            )
            t.start()
            _workers.append(t)
        _started = True
        logger.info("started %d background worker(s)", n)
        return n


def stop_workers(timeout: float = 5.0) -> None:
    """Best-effort shutdown. Workers exit on the next 1s queue poll."""
    _shutdown.set()
    for t in _workers:
        t.join(timeout=timeout)
    _workers.clear()
    global _started, _GOAL_THREAD
    _started = False
    if _GOAL_THREAD is not None:
        _GOAL_THREAD.join(timeout=timeout)
        _GOAL_THREAD = None


def worker_count() -> int:
    return sum(1 for t in _workers if t.is_alive())


# ── Phase 8: goal scheduler ─────────────────────────────────────────────────

def _goal_scheduler_loop() -> None:
    """Periodically check the GoalStore for due goals and enqueue each as
    a __plan__ job. The scheduler never executes a goal in its own thread —
    it only enqueues, so retries / persistence / observability all flow
    through the existing job machinery.
    """
    from kernel import metrics

    job_store  = get_store()
    goal_store = get_goal_store()
    logger.info("goal scheduler online (tick=%.1fs)", _GOAL_TICK_SECONDS)

    while not _shutdown.is_set():
        try:
            due = goal_store.due_goals()
        except Exception:  # noqa: BLE001
            logger.exception("goal scheduler: due_goals failed")
            due = []

        for goal in due:
            goal_id = goal.get("goal_id")
            description = goal.get("description") or ""
            try:
                intent = {
                    "type":    "__plan__",
                    "payload": {"input": description, "goal_id": goal_id},
                    "source":  "goal",
                }
                job = job_store.create(intent, source="goal")
                goal_store.record_run(goal_id, job_id=job["job_id"])
                metrics.record_goal_run(success=True)
                logger.info("goal %s → enqueued job %s", goal_id, job["job_id"])
            except Exception as e:  # noqa: BLE001
                logger.exception("goal %s scheduling failed", goal_id)
                metrics.record_goal_run(success=False)

        # Sleep in small slices so shutdown is responsive.
        slept = 0.0
        while slept < _GOAL_TICK_SECONDS and not _shutdown.is_set():
            time.sleep(0.5)
            slept += 0.5

    logger.info("goal scheduler offline")


def start_goal_scheduler() -> bool:
    """Spin up the goal scheduler thread. Idempotent. Returns True if
    started this call (vs already running)."""
    global _GOAL_THREAD
    with _lock:
        if _GOAL_THREAD is not None and _GOAL_THREAD.is_alive():
            return False
        _shutdown.clear()
        t = threading.Thread(
            target=_goal_scheduler_loop,
            name="solspire-goal-scheduler",
            daemon=True,
        )
        t.start()
        _GOAL_THREAD = t
        return True


def goal_scheduler_alive() -> bool:
    return _GOAL_THREAD is not None and _GOAL_THREAD.is_alive()


__all__ = [
    "start_workers", "stop_workers", "worker_count",
    "start_goal_scheduler", "goal_scheduler_alive",
]
