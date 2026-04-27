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

logger = logging.getLogger("arkadia.worker")

_workers: list[threading.Thread] = []
_started = False
_lock = threading.Lock()
_shutdown = threading.Event()


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
    global _started
    _started = False


def worker_count() -> int:
    return sum(1 for t in _workers if t.is_alive())


__all__ = ["start_workers", "stop_workers", "worker_count"]
