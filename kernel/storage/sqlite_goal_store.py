"""SQLiteGoalStore — durable replacement for the in-memory GoalStore.

Drop-in replacement for ``kernel.goals.GoalStore``.  Public API is
identical; callers require zero changes.

History is stored as a JSON array in the ``history`` TEXT column, capped
at ``HISTORY_CAP`` entries.  The hourly-cap calculation is a pure
function copied from ``kernel/goals.py`` with no logic changes.
"""
from __future__ import annotations

import json
import sqlite3
import time
import threading
import uuid
from typing import Any

from kernel.storage.schema import create_tables

# ── Constants (mirror kernel.goals so importers need not change) ─────────────
ACTIVE    = "active"
PAUSED    = "paused"
COMPLETED = "completed"

VALID_STATUSES = {ACTIVE, PAUSED, COMPLETED}

MIN_CADENCE_SECONDS    = 30
MAX_RUNS_PER_HOUR_HARD = 60
DEFAULT_MAX_PER_HOUR   = 6
HISTORY_CAP            = 50


# ── helpers ──────────────────────────────────────────────────────────────────

def _encode_history(history: list) -> str:
    return json.dumps(history, default=str)


def _decode_history(text: str | None) -> list:
    if not text:
        return []
    try:
        v = json.loads(text)
        return v if isinstance(v, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _row_to_goal(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "goal_id":           row["goal_id"],
        "description":       row["description"],
        "status":            row["status"],
        "cadence_seconds":   row["cadence_seconds"],
        "max_runs_per_hour": row["max_runs_per_hour"],
        "next_run":          row["next_run"],
        "last_run":          row["last_run"],
        "run_count":         row["run_count"],
        "history":           _decode_history(row["history"]),
        "created_at":        row["created_at"],
        "updated_at":        row["updated_at"],
    }


def _under_hourly_cap(goal: dict[str, Any], now: float) -> bool:
    """Pure function — logic identical to kernel/goals.py._under_hourly_cap."""
    cap     = int(goal.get("max_runs_per_hour", DEFAULT_MAX_PER_HOUR))
    cadence = float(goal.get("cadence_seconds", MIN_CADENCE_SECONDS))
    if cadence * cap >= 3600:
        return True
    last = goal.get("last_run")
    if last is None:
        return True
    min_gap = 3600.0 / cap
    return (now - float(last)) >= min_gap


# ── store ────────────────────────────────────────────────────────────────────

class SQLiteGoalStore:
    """Thread-safe, crash-safe goal store backed by SQLite WAL."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path: str = create_tables(db_path=db_path)
        self._local   = threading.local()

    # ── connection management ────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
        return self._local.conn

    # ── core API ─────────────────────────────────────────────────────────────

    def create(self, description: str, *,
               cadence_seconds: float = 300.0,
               max_runs_per_hour: int = DEFAULT_MAX_PER_HOUR,
               start_now: bool = True) -> dict[str, Any]:
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Goal description is required.")

        cadence = max(MIN_CADENCE_SECONDS, float(cadence_seconds))
        cap     = max(1, min(MAX_RUNS_PER_HOUR_HARD, int(max_runs_per_hour)))
        now     = time.time()
        goal_id = f"goal_{uuid.uuid4().hex[:12]}"

        conn = self._conn()
        conn.execute(
            """
            INSERT INTO goals
                (goal_id, description, status, cadence_seconds, max_runs_per_hour,
                 next_run, last_run, run_count, history, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL, 0, ?, ?, ?)
            """,
            (goal_id, description.strip(), ACTIVE, cadence, cap,
             now if start_now else now + cadence,
             _encode_history([]), now, now),
        )
        conn.commit()
        return self.get(goal_id)  # type: ignore[return-value]

    def get(self, goal_id: str) -> dict[str, Any] | None:
        row = self._conn().execute(
            "SELECT * FROM goals WHERE goal_id = ?", (goal_id,)
        ).fetchone()
        return _row_to_goal(row) if row else None

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            rows = self._conn().execute(
                "SELECT * FROM goals WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM goals ORDER BY created_at DESC"
            ).fetchall()
        return [_row_to_goal(r) for r in rows]

    def update(self, goal_id: str, **fields: Any) -> dict[str, Any] | None:
        if not fields:
            return self.get(goal_id)

        # Validate and clamp fields that have hard constraints
        if "status" in fields and fields["status"] not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        if "cadence_seconds" in fields:
            fields["cadence_seconds"] = max(
                MIN_CADENCE_SECONDS, float(fields["cadence_seconds"])
            )
        if "max_runs_per_hour" in fields:
            fields["max_runs_per_hour"] = max(
                1, min(MAX_RUNS_PER_HOUR_HARD, int(fields["max_runs_per_hour"]))
            )
        if "history" in fields:
            fields["history"] = _encode_history(fields["history"])

        now = time.time()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [now, goal_id]
        conn = self._conn()
        conn.execute(
            f"UPDATE goals SET {set_clause}, updated_at = ? WHERE goal_id = ?",
            values,
        )
        conn.commit()
        return self.get(goal_id)

    def delete(self, goal_id: str) -> bool:
        conn = self._conn()
        cursor = conn.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
        conn.commit()
        return cursor.rowcount > 0

    def record_run(self, goal_id: str, *, job_id: str | None,
                   ts: float | None = None) -> dict[str, Any] | None:
        """Mark a goal as just-fired: bump counters, advance next_run."""
        ts = ts if ts is not None else time.time()
        conn = self._conn()

        row = conn.execute(
            "SELECT cadence_seconds, history FROM goals WHERE goal_id = ?",
            (goal_id,),
        ).fetchone()
        if row is None:
            return None

        cadence = float(row["cadence_seconds"])
        history = _decode_history(row["history"])
        if job_id:
            history.append(job_id)
            history = history[-HISTORY_CAP:]

        conn.execute(
            """
            UPDATE goals
               SET last_run   = ?,
                   next_run   = ?,
                   run_count  = run_count + 1,
                   history    = ?,
                   updated_at = ?
             WHERE goal_id = ?
            """,
            (ts, ts + cadence, _encode_history(history), ts, goal_id),
        )
        conn.commit()
        return self.get(goal_id)

    def due_goals(self, *, now: float | None = None) -> list[dict[str, Any]]:
        """Return active goals past their next_run and under their hourly cap."""
        now = now if now is not None else time.time()
        rows = self._conn().execute(
            """
            SELECT * FROM goals
             WHERE status  = ?
               AND (next_run IS NULL OR next_run <= ?)
            """,
            (ACTIVE, now),
        ).fetchall()
        out = []
        for row in rows:
            goal = _row_to_goal(row)
            if _under_hourly_cap(goal, now):
                out.append(goal)
        return out

    def reset(self) -> None:
        """Test-only: delete all goals."""
        conn = self._conn()
        conn.execute("DELETE FROM goals")
        conn.commit()


__all__ = [
    "SQLiteGoalStore",
    "ACTIVE", "PAUSED", "COMPLETED", "VALID_STATUSES",
    "MIN_CADENCE_SECONDS", "MAX_RUNS_PER_HOUR_HARD",
    "DEFAULT_MAX_PER_HOUR", "HISTORY_CAP",
]
