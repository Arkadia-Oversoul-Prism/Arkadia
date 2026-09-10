"""SolSpire job orchestration and Phase 6 persistent execution state."""
from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
from typing import Any

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
VALID_STATUSES = {PENDING, RUNNING, COMPLETED, FAILED}
MAX_RETRIES = 3

LEASE_SECONDS = float(os.environ.get("SOLSPIRE_LEASE_SECONDS", "30"))
HEARTBEAT_SECONDS = float(os.environ.get("SOLSPIRE_HEARTBEAT_SECONDS", "5"))

_DATA_DIR = os.environ.get("SOLSPIRE_DATA_DIR", "data")
_SNAPSHOT_PATH = os.path.join(_DATA_DIR, "job_store.json")


def _execution(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "state": "QUEUED",
        "checkpoints": [],
        "lease": None,
        "heartbeat": None,
        "artifacts": [],
        "events": [],
    }


class JobStore:
    """Thread-safe job table plus durable execution metadata.

    The public Phase 5 API is preserved. Phase 6 adds checkpoints, leases,
    heartbeats and recovery without introducing another queue abstraction.
    """

    def __init__(self, snapshot_path: str = _SNAPSHOT_PATH) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._queue: queue.Queue[str] = queue.Queue()
        self._snapshot_path = snapshot_path
        self._load_snapshot()

    def _load_snapshot(self) -> None:
        loaded_from_disk = False
        if os.path.exists(self._snapshot_path):
            try:
                with open(self._snapshot_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for job_id, job in data.items():
                        if isinstance(job, dict) and "job_id" in job:
                            self._jobs[job_id] = job
                            if job.get("status") in (PENDING, RUNNING):
                                # A worker process may have died while holding
                                # the lease. Requeue it and preserve its last
                                # checkpoint rather than restarting the record.
                                job["status"] = PENDING
                                execution = job.setdefault("execution", _execution(job_id))
                                execution["state"] = "RESUMING" if execution.get("checkpoints") else "QUEUED"
                                execution["lease"] = None
                                self._queue.put(job_id)
                    loaded_from_disk = bool(self._jobs)
            except (json.JSONDecodeError, OSError):
                pass

        if not loaded_from_disk:
            try:
                from api.firebase_store import fb_load_jobs
                fb_jobs = fb_load_jobs()
                for job_id, job in fb_jobs.items():
                    if isinstance(job, dict) and "job_id" in job:
                        self._jobs[job_id] = job
                        if job.get("status") in (PENDING, RUNNING):
                            job["status"] = PENDING
                            execution = job.setdefault("execution", _execution(job_id))
                            execution["state"] = "RESUMING" if execution.get("checkpoints") else "QUEUED"
                            execution["lease"] = None
                            self._queue.put(job_id)
                if fb_jobs:
                    import logging
                    logging.getLogger("arkadia.jobs").info("[JOBS] Restored %d jobs from Firestore", len(fb_jobs))
            except Exception:
                pass

    def _persist(self) -> None:
        try:
            directory = os.path.dirname(self._snapshot_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            tmp = self._snapshot_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._jobs, f, indent=2, ensure_ascii=False, default=str)
            os.replace(tmp, self._snapshot_path)
        except OSError:
            pass
        try:
            from api.firebase_store import fb_sync_jobs
            fb_sync_jobs(self._jobs)
        except Exception:
            pass

    def create(self, intent: dict[str, Any], *, source: str = "api") -> dict[str, Any]:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = time.time()
        task_id = str(intent.get("proposal_id") or intent.get("task_id") or job_id) if isinstance(intent, dict) else job_id
        job: dict[str, Any] = {
            "job_id": job_id,
            "status": PENDING,
            "intent": intent if isinstance(intent, dict) else {},
            "result": None,
            "error": None,
            "retries": 0,
            "source": source,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "ended_at": None,
            "execution": _execution(task_id),
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
        now = time.time()
        return self.update(job_id, status=COMPLETED, result=result, ended_at=now, error=None)

    def mark_failed(self, job_id: str, error: str) -> dict[str, Any] | None:
        return self.update(job_id, status=FAILED, error=error, ended_at=time.time())

    def requeue_for_retry(self, job_id: str, error: str) -> dict[str, Any] | None:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return None
            j["retries"] = int(j.get("retries", 0)) + 1
            j["status"] = PENDING
            j["error"] = error
            execution = j.setdefault("execution", _execution(job_id))
            execution["state"] = "RESUMING" if execution.get("checkpoints") else "QUEUED"
            execution["lease"] = None
            j["updated_at"] = time.time()
            self._persist()
            snapshot = dict(j)
        self._queue.put(job_id)
        return snapshot

    def acquire_lease(self, job_id: str, worker_id: str, *, lease_seconds: float = LEASE_SECONDS) -> bool:
        now = time.time()
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.get("status") in (COMPLETED, FAILED):
                return False
            execution = job.setdefault("execution", _execution(job_id))
            lease = execution.get("lease")
            if lease and float(lease.get("expires_at", 0)) > now and lease.get("worker_id") != worker_id:
                return False
            recovering = bool(lease and float(lease.get("expires_at", 0)) <= now)
            execution["lease"] = {
                "worker_id": worker_id,
                "acquired_at": now,
                "expires_at": now + lease_seconds,
            }
            execution["heartbeat"] = now
            execution["state"] = "RESUMING" if recovering or execution.get("checkpoints") else "EXECUTING"
            execution.setdefault("events", []).append({"event": "lease.acquired", "worker_id": worker_id, "at": now, "recovered": recovering})
            job["status"] = RUNNING
            job["started_at"] = job.get("started_at") or now
            job["updated_at"] = now
            self._persist()
            return True

    def heartbeat(self, job_id: str, worker_id: str, *, lease_seconds: float = LEASE_SECONDS) -> bool:
        now = time.time()
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            execution = job.setdefault("execution", _execution(job_id))
            lease = execution.get("lease")
            if not lease or lease.get("worker_id") != worker_id:
                return False
            if float(lease.get("expires_at", 0)) <= now:
                return False
            lease["expires_at"] = now + lease_seconds
            execution["heartbeat"] = now
            job["updated_at"] = now
            self._persist()
            return True

    def release_lease(self, job_id: str, worker_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            execution = job.setdefault("execution", _execution(job_id))
            lease = execution.get("lease")
            if not lease or lease.get("worker_id") != worker_id:
                return False
            execution["lease"] = None
            self._persist()
            return True

    def checkpoint(self, job_id: str, name: str, data: Any = None, *, state: str = "CHECKPOINTED") -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            execution = job.setdefault("execution", _execution(job_id))
            checkpoint = {
                "index": len(execution.get("checkpoints") or []),
                "name": name,
                "data": data,
                "at": now,
            }
            execution.setdefault("checkpoints", []).append(checkpoint)
            execution["state"] = state
            execution.setdefault("events", []).append({"event": "checkpoint", "name": name, "index": checkpoint["index"], "at": now})
            job["updated_at"] = now
            self._persist()
            return dict(checkpoint)

    def recover_expired_leases(self) -> int:
        now = time.time()
        recovered = 0
        with self._lock:
            for job in self._jobs.values():
                execution = job.get("execution") or {}
                lease = execution.get("lease")
                if job.get("status") == RUNNING and lease and float(lease.get("expires_at", 0)) <= now:
                    execution["lease"] = None
                    execution["state"] = "RESUMING" if execution.get("checkpoints") else "QUEUED"
                    job["status"] = PENDING
                    job["updated_at"] = now
                    self._queue.put(job["job_id"])
                    recovered += 1
            if recovered:
                self._persist()
        return recovered

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
        with self._lock:
            self._jobs.clear()
            self._persist()
        try:
            while True:
                self._queue.get_nowait()
                self._queue.task_done()
        except queue.Empty:
            pass


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
    "JobStore", "get_store", "PENDING", "RUNNING", "COMPLETED", "FAILED",
    "VALID_STATUSES", "MAX_RETRIES", "LEASE_SECONDS", "HEARTBEAT_SECONDS",
]
