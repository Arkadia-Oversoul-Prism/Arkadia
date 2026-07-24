"""SQLiteJobStore — durable replacement for the in-memory JobStore.

Drop-in replacement for ``kernel.jobs.JobStore``.  Public API is
identical; callers require zero changes.

Design decisions (see DECISION_CACHE.md and SQLITE_JOB_QUEUE_DESIGN.md):
- WAL mode: set by ``create_tables()``; no separate pragma needed here.
- Atomic claim: ``BEGIN IMMEDIATE`` acquires a write-lock before the
  SELECT so two workers cannot claim the same job.
- Crash recovery: any job left in ``running`` status on startup is reset
  to ``pending`` and re-queued.
- ``next_job_id(timeout)`` polls the database instead of blocking on a
  ``queue.Queue``; semantics are identical from the caller's perspective.
- All JSON blobs (intent, result, trace) are stored as TEXT; ``None``
  serialises to SQL NULL.
"""
from __future__ import annotations

import json
import sqlite3
import time
import threading
import uuid
from typing import Any

from kernel.storage.schema import create_tables

# ── Constants (mirror kernel.jobs so importers need not change) ──────────────
PENDING   = "pending"
RUNNING   = "running"
COMPLETED = "completed"
FAILED    = "failed"

VALID_STATUSES = {PENDING, RUNNING, COMPLETED, FAILED}
MAX_RETRIES    = 3

_POLL_INTERVAL = 0.5   # seconds between empty-queue polls


# ── helpers ──────────────────────────────────────────────────────────────────

def _encode(value: Any) -> str | None:
    """Serialise a Python value to a JSON string for TEXT columns."""
    if value is None:
        return None
    return json.dumps(value, default=str)


def _decode(text: str | None) -> Any:
    """Deserialise a JSON TEXT column back to a Python object."""
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "job_id":     row["job_id"],
        "status":     row["status"],
        "intent":     _decode(row["intent"]),
        "result":     _decode(row["result"]),
        "error":      row["error"],
        "trace":      _decode(row["trace"]),
        "retries":    row["retries"],
        "source":     row["source"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "started_at": row["started_at"],
        "ended_at":   row["ended_at"],
    }


# ── store ────────────────────────────────────────────────────────────────────

class SQLiteJobStore:
    """Thread-safe, crash-safe job store backed by SQLite WAL.

    Parameters
    ----------
    db_path:
        Path to the SQLite file.  Passed to ``create_tables()`` which
        creates the file and schema if absent.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path: str = create_tables(db_path=db_path)
        self._local   = threading.local()   # per-thread connection
        self._recover_running_jobs()

    # ── connection management ────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        """Return a per-thread SQLite connection (created on first access)."""
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
        return self._local.conn

    # ── crash recovery ───────────────────────────────────────────────────────

    def _recover_running_jobs(self) -> None:
        """Reset jobs that were RUNNING when the process last died."""
        conn = self._conn()
        now = time.time()
        conn.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE status = ?",
            (PENDING, now, RUNNING),
        )
        conn.commit()

    # ── core API (identical signatures to JobStore) ──────────────────────────

    def create(self, intent: dict[str, Any], *, source: str = "api") -> dict[str, Any]:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = time.time()
        conn = self._conn()
        conn.execute(
            """
            INSERT INTO jobs
                (job_id, status, intent, result, error, trace,
                 retries, source, created_at, updated_at, started_at, ended_at)
            VALUES (?, ?, ?, NULL, NULL, NULL, 0, ?, ?, ?, NULL, NULL)
            """,
            (job_id, PENDING, _encode(intent if isinstance(intent, dict) else {}),
             source, now, now),
        )
        conn.commit()
        return self.get(job_id)  # type: ignore[return-value]

    def get(self, job_id: str) -> dict[str, Any] | None:
        row = self._conn().execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        return _row_to_job(row) if row else None

    def list(self, *, limit: int = 100,
             status: str | None = None) -> list[dict[str, Any]]:
        if status:
            rows = self._conn().execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [_row_to_job(r) for r in rows]

    def update(self, job_id: str, **fields: Any) -> dict[str, Any] | None:
        if not fields:
            return self.get(job_id)
        now = time.time()
        # Serialise JSON columns
        for col in ("intent", "result", "trace"):
            if col in fields:
                fields[col] = _encode(fields[col])
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [now, job_id]
        conn = self._conn()
        conn.execute(
            f"UPDATE jobs SET {set_clause}, updated_at = ? WHERE job_id = ?",
            values,
        )
        conn.commit()
        return self.get(job_id)

    def mark_running(self, job_id: str) -> dict[str, Any] | None:
        return self.update(job_id, status=RUNNING, started_at=time.time())

    def mark_completed(self, job_id: str,
                       result: Any) -> dict[str, Any] | None:
        return self.update(
            job_id, status=COMPLETED,
            result=result, ended_at=time.time(), error=None,
        )

    def mark_failed(self, job_id: str, error: str) -> dict[str, Any] | None:
        return self.update(job_id, status=FAILED,
                           error=error, ended_at=time.time())

    def requeue_for_retry(self, job_id: str,
                          error: str) -> dict[str, Any] | None:
        """Bump retry count, reset to pending.  Caller must check MAX_RETRIES."""
        conn = self._conn()
        now = time.time()
        conn.execute(
            """
            UPDATE jobs
               SET status     = ?,
                   retries    = retries + 1,
                   error      = ?,
                   updated_at = ?
             WHERE job_id = ?
            """,
            (PENDING, error, now, job_id),
        )
        conn.commit()
        return self.get(job_id)

    # ── queue accessors (used by kernel/worker.py) ───────────────────────────

    def next_job_id(self, timeout: float = 1.0) -> str | None:
        """Block until a pending job is available or *timeout* expires.

        Uses ``BEGIN IMMEDIATE`` to atomically claim the job so two
        workers cannot race on the same row.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job_id = self._claim_one()
            if job_id:
                return job_id
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(_POLL_INTERVAL, remaining))
        return None

    def _claim_one(self) -> str | None:
        """Atomically claim the oldest pending job. Returns job_id or None."""
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT job_id FROM jobs WHERE status = ? ORDER BY created_at ASC LIMIT 1",
                (PENDING,),
            ).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                return None
            job_id = row["job_id"]
            now = time.time()
            conn.execute(
                "UPDATE jobs SET status = ?, started_at = ?, updated_at = ? WHERE job_id = ?",
                (RUNNING, now, now, job_id),
            )
            conn.execute("COMMIT")
            return job_id
        except sqlite3.OperationalError:
            # Another writer holds the lock; back off and retry
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            return None

    def task_done(self) -> None:
        """No-op: SQLite has no queue to acknowledge. Preserved for API parity."""

    def stats(self) -> dict[str, int]:
        rows = self._conn().execute(
            "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"
        ).fetchall()
        counts: dict[str, int] = {s: 0 for s in VALID_STATUSES}
        for row in rows:
            if row["status"] in counts:
                counts[row["status"]] = row["n"]
        counts["total"] = sum(counts.values())
        # queue_depth = pending jobs not yet claimed
        counts["queue_depth"] = counts[PENDING]
        return counts

    def reset(self) -> None:
        """Test-only: delete all jobs."""
        conn = self._conn()
        conn.execute("DELETE FROM jobs")
        conn.commit()


__all__ = [
    "SQLiteJobStore",
    "PENDING", "RUNNING", "COMPLETED", "FAILED",
    "VALID_STATUSES", "MAX_RETRIES",
]
