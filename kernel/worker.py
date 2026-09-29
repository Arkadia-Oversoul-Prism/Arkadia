"""SolSpire background worker pool with Phase 6 durable execution."""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from kernel.execution import execute_intent
from kernel.jobs import COMPLETED, FAILED, HEARTBEAT_SECONDS, MAX_RETRIES, get_store
from kernel.goals import get_store as get_goal_store

logger = logging.getLogger("arkadia.worker")
_workers: list[threading.Thread] = []
_started = False
_lock = threading.Lock()
_shutdown = threading.Event()
_GOAL_TICK_SECONDS = float(os.environ.get("SOLSPIRE_GOAL_TICK_SECONDS", "15"))
_GOAL_THREAD: threading.Thread | None = None


def _backoff_seconds(retry_count: int) -> float:
    return min(2.0, 0.5 * (2 ** max(0, retry_count - 1)))


def _heartbeat_loop(job_id: str, worker_id: str, stop: threading.Event) -> None:
    store = get_store()
    while not stop.wait(HEARTBEAT_SECONDS):
        if not store.heartbeat(job_id, worker_id):
            logger.warning("job %s heartbeat lost for worker %s", job_id, worker_id)
            return


def _process_job(job: dict[str, Any], worker_id: str | None = None) -> None:
    store = get_store()
    job_id = job["job_id"]
    worker_id = worker_id or f"worker-{threading.get_ident()}"

    if not store.acquire_lease(job_id, worker_id):
        logger.info("job %s skipped: lease unavailable", job_id)
        return

    heartbeat_stop = threading.Event()
    heartbeat = threading.Thread(
        target=_heartbeat_loop,
        args=(job_id, worker_id, heartbeat_stop),
        name=f"heartbeat-{job_id}",
        daemon=True,
    )
    heartbeat.start()

    try:
        current = store.get(job_id) or job
        execution = current.get("execution") or {}
        last = execution.get("checkpoints") or []
        resume_from = last[-1]["name"] if last else None
        store.checkpoint(job_id, "execution.started", {"resume_from": resume_from}, state="ANALYSING")
        logger.info("job %s running (retry=%d resume_from=%s)", job_id, current.get("retries", 0), resume_from)

        intent = dict(current.get("intent") or {})
        payload = dict(intent.get("payload") or {})
        if resume_from:
            payload.setdefault("_execution", {})["resume_from"] = resume_from
            intent["payload"] = payload

        result = execute_intent(intent)
        if isinstance(result, dict) and result.get("handled") and not result.get("success"):
            _handle_failure(job_id, f"kernel verify failed: {result.get('summary', 'no summary')}", result)
            return

        store.checkpoint(job_id, "execution.completed", {"success": bool(result.get("success")) if isinstance(result, dict) else True}, state="LEARNED")
        store.mark_completed(job_id, result)
        store.update(job_id, execution={**(store.get(job_id) or {}).get("execution", {}), "state": "COMPLETE", "lease": None})
        logger.info("job %s completed", job_id)
        _record_job_trace(job_id, intent, result)
    except Exception as e:  # noqa: BLE001
        logger.exception("job %s raised", job_id)
        _handle_failure(job_id, repr(e))
    finally:
        heartbeat_stop.set()
        heartbeat.join(timeout=max(1.0, HEARTBEAT_SECONDS))
        store.release_lease(job_id, worker_id)


def _handle_failure(job_id: str, error: str, partial_result: Any | None = None) -> None:
    store = get_store()
    current = store.get(job_id) or {}
    retries = int(current.get("retries", 0))
    if retries < MAX_RETRIES:
        backoff = _backoff_seconds(retries + 1)
        logger.warning("job %s failed (retry %d/%d in %.1fs): %s", job_id, retries + 1, MAX_RETRIES, backoff, error)
        time.sleep(backoff)
        store.requeue_for_retry(job_id, error=error)
    else:
        logger.error("job %s exhausted retries: %s", job_id, error)
        store.mark_failed(job_id, error=error)
        if partial_result is not None:
            store.update(job_id, result=partial_result)


def _record_job_trace(job_id: str, intent: dict[str, Any], result: dict[str, Any] | None) -> None:
    if not isinstance(result, dict):
        return
    payload = (intent or {}).get("payload") or {}
    execution = result.get("execution") or {}
    steps = execution.get("steps") if isinstance(execution, dict) else result.get("steps") or []
    trace = {
        "job_id": job_id,
        "intent_type": (intent or {}).get("type"),
        "input": payload.get("input") or payload.get("message") or payload,
        "plan": result.get("plan"),
        "plan_source": result.get("plan_source"),
        "context": (execution or {}).get("context") if isinstance(execution, dict) else None,
        "steps": [
            {
                "step_id": s.get("step_id"), "tool": s.get("tool"), "input": s.get("input"),
                "duration_ms": s.get("duration_ms"),
                "success": bool((s.get("envelope") or {}).get("success")),
                "summary": (s.get("envelope") or {}).get("summary"),
            }
            for s in (steps or []) if isinstance(s, dict)
        ],
        "success": bool(result.get("success")),
        "summary": result.get("summary"),
    }
    try:
        get_store().update(job_id, trace=trace)
    except Exception:  # noqa: BLE001
        logger.exception("failed to persist trace for %s", job_id)


def _worker_loop(worker_id: int) -> None:
    store = get_store()
    worker_name = f"worker-{worker_id}"
    logger.info("%s online", worker_name)
    while not _shutdown.is_set():
        store.recover_expired_leases()
        job_id = store.next_job_id(timeout=1.0)
        if job_id is None:
            continue
        try:
            job = store.get(job_id)
            if job is None:
                continue
            if job.get("status") in (COMPLETED, FAILED):
                continue
            _process_job(job, worker_name)
        finally:
            store.task_done()
    logger.info("%s offline", worker_name)


def start_workers(n: int | None = None) -> int:
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
            t = threading.Thread(target=_worker_loop, args=(i,), name=f"solspire-worker-{i}", daemon=True)
            t.start()
            _workers.append(t)
        _started = True
        logger.info("started %d background worker(s)", n)
        return n


def stop_workers(timeout: float = 5.0) -> None:
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


def _goal_scheduler_loop() -> None:
    from kernel import metrics
    job_store = get_store()
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
                intent = {"type": "__plan__", "payload": {"input": description, "goal_id": goal_id}, "source": "goal"}
                job = job_store.create(intent, source="goal")
                goal_store.record_run(goal_id, job_id=job["job_id"])
                metrics.record_goal_run(success=True)
                logger.info("goal %s → enqueued job %s", goal_id, job["job_id"])
            except Exception:  # noqa: BLE001
                logger.exception("goal %s scheduling failed", goal_id)
                metrics.record_goal_run(success=False)
        slept = 0.0
        while slept < _GOAL_TICK_SECONDS and not _shutdown.is_set():
            time.sleep(0.5)
            slept += 0.5
    logger.info("goal scheduler offline")


def start_goal_scheduler() -> bool:
    global _GOAL_THREAD
    with _lock:
        if _GOAL_THREAD is not None and _GOAL_THREAD.is_alive():
            return False
        _shutdown.clear()
        t = threading.Thread(target=_goal_scheduler_loop, name="solspire-goal-scheduler", daemon=True)
        t.start()
        _GOAL_THREAD = t
        return True


def goal_scheduler_alive() -> bool:
    return _GOAL_THREAD is not None and _GOAL_THREAD.is_alive()


__all__ = ["start_workers", "stop_workers", "worker_count", "start_goal_scheduler", "goal_scheduler_alive"]
