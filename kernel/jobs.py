"""SolSpire Phase 5 — Job Orchestration Layer.

Decouples execution from response. Phase 4's `execute_intent` is
synchronous: caller waits for plan→execute→verify to complete before
seeing anything. That blocks on slow APIs, image batches, and any
multi-step workflow.

Phase 5 wraps that kernel call in a job:

    user → create_job(intent) → returns job_id immediately
                ↓
          worker pool picks it up
                ↓
          execute_intent runs in background
                ↓
          state updated, result stored
                ↓
          user polls /api/job/{id} or gets notified

This file owns:
  • The in-memory JobStore (thread-safe, with optional JSON snapshots)
  • The pending-job queue
  • The Job dict shape

The worker loop itself lives in kernel/worker.py so this module stays
free of execution concerns and testable in isolation.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
from typing import Any

# ── Job lifecycle states ────────────────────────────────────────────────────
PENDING   = "pending"
RUNNING   = "running"
COMPLETED = "completed"
FAILED    = "failed"

VALID_STATUSES = {PENDING, RUNNING, COMPLETED, FAILED}

MAX_RETRIES = 3

_DATA_DIR = os.environ.get("SOLSPIRE_DATA_DIR", "data")
_SNAPSHOT_PATH = os.path.join(_DATA_DIR, "job_store.json")


# ── Job store ───────────────────────────────────────────────────────────────

class JobStore:
    """Thread-safe in-memory job dictionary with an optional JSON
    snapshot to disk so jobs survive a soft restart. The store and the
    pending queue are separate concerns:
      • store  → full lookup table by job_id
      • queue  → FIFO of job_ids waiting for a worker
    """

    def __init__(self, snapshot_path: str = _SNAPSHOT_PATH) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._queue: queue.Queue[str] = queue.Queue()
        self._snapshot_path = snapshot_path
        self._load_snapshot()

    # ── persistence ─────────────────────────────────────────────────────────
    def _load_snapshot(self) -> None:
        if not os.path.exists(self._snapshot_path):
            return
        try:
            with open(self._snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, dict):
            return
        for job_id, job in data.items():
            if isinstance(job, dict) and "job_id" in job:
                self._jobs[job_id] = job
                # Re-enqueue any work that was unfinished when we shut down.
                if job.get("status") in (PENDING, RUNNING):
                    job["status"] = PENDING
                    self._queue.put(job_id)

    def _persist(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._snapshot_path), exist_ok=True)
            tmp = self._snapshot_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._jobs, f, indent=2, ensure_ascii=False, default=str)
            os.replace(tmp, self._snapshot_path)
        except OSError:
            pass  # best-effort; never crash a worker on snapshot failure

    # ── core API ────────────────────────────────────────────────────────────
    def create(self, intent: dict[str, Any], *, source: str = "api") -> dict[str, Any]:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = time.time()
        job: dict[str, Any] = {
            "job_id":     job_id,
            "status":     PENDING,
            "intent":     intent if isinstance(intent, dict) else {},
            "result":     None,
            "error":      None,
            "retries":    0,
            "source":     source,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "ended_at":   None,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._persist()
        self._queue.put(job_id)
        return job

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            j = self._jobs.get(job_id)
            return dict(j) if j else None

    def list(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        jobs.sort(key=lambda j: j.get("created_at", 0), reverse=True)
        return [dict(j) for j in jobs[:limit]]

    def update(self, job_id: str, **fields: Any) -> dict[str, Any] | None:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return None
            for k, v in fields.items():
                j[k] = v
            j["updated_at"] = time.time()
            self._persist()
            return dict(j)

    def mark_running(self, job_id: str) -> dict[str, Any] | None:
        return self.update(job_id, status=RUNNING, started_at=time.time())

    def mark_completed(self, job_id: str, result: Any) -> dict[str, Any] | None:
        return self.update(
            job_id, status=COMPLETED, result=result,
            ended_at=time.time(), error=None,
        )

    def mark_failed(self, job_id: str, error: str) -> dict[str, Any] | None:
        return self.update(
            job_id, status=FAILED, error=error, ended_at=time.time(),
        )

    def requeue_for_retry(self, job_id: str, error: str) -> dict[str, Any] | None:
        """Per spec: bump retry count, reset to pending, re-enqueue.
        After MAX_RETRIES, the worker should call mark_failed instead.
        """
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return None
            j["retries"]    = int(j.get("retries", 0)) + 1
            j["status"]     = PENDING
            j["error"]      = error
            j["updated_at"] = time.time()
            self._persist()
            snapshot = dict(j)
        self._queue.put(job_id)
        return snapshot

    # ── queue accessors (used by worker.py) ─────────────────────────────────
    def next_job_id(self, timeout: float = 1.0) -> str | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def task_done(self) -> None:
        try:
            self._queue.task_done()
        except ValueError:
            pass

    def stats(self) -> dict[str, int]:
        with self._lock:
            counts = {s: 0 for s in VALID_STATUSES}
            for j in self._jobs.values():
                s = j.get("status")
                if s in counts:
                    counts[s] += 1
            counts["total"] = len(self._jobs)
            counts["queue_depth"] = self._queue.qsize()
            return counts

    def reset(self) -> None:
        """Test-only: nuke all jobs. Does not drain in-flight work."""
        with self._lock:
            self._jobs.clear()
            self._persist()
        # Drain the queue
        try:
            while True:
                self._queue.get_nowait()
                self._queue.task_done()
        except queue.Empty:
            pass


# ── module-level singleton ──────────────────────────────────────────────────
_store: JobStore | None = None
_store_lock = threading.Lock()


def get_store() -> JobStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = JobStore()
    return _store


__all__ = [
    "JobStore", "get_store",
    "PENDING", "RUNNING", "COMPLETED", "FAILED",
    "VALID_STATUSES", "MAX_RETRIES",
]
