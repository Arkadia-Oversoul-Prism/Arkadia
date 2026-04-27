"""SolSpire Phase 8 — Persistent goal store + scheduler.

A "goal" is a long-horizon directive the system pursues over time —
distinct from a one-shot job. Each goal carries a description, a
cadence, and a per-hour cap so a runaway scheduler can never loop the
system into the ground.

When the goal scheduler thread wakes, it asks the store for goals
whose `next_run` has passed and who haven't exceeded their hourly cap,
then enqueues each one as a plan-job. The job system (Phase 5) then
handles execution, retries, and persistence — goals never run in the
scheduler's own thread.

Schema (data/goal_store.json):
    {
      "<goal_id>": {
        "goal_id":           str,
        "description":       str,
        "status":            "active" | "paused" | "completed",
        "cadence_seconds":   float,            # min seconds between runs
        "max_runs_per_hour": int,
        "next_run":          float | None,
        "last_run":          float | None,
        "run_count":         int,
        "history":           [job_id, ...]     # capped at HISTORY_CAP
        "created_at":        float,
        "updated_at":        float,
      }
    }
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import Any

ACTIVE    = "active"
PAUSED    = "paused"
COMPLETED = "completed"
VALID_STATUSES = {ACTIVE, PAUSED, COMPLETED}

# Hard safety floors — enforced regardless of what the user submits.
MIN_CADENCE_SECONDS    = 30
MAX_RUNS_PER_HOUR_HARD = 60     # ceiling the user cannot raise
DEFAULT_MAX_PER_HOUR   = 6
HISTORY_CAP            = 50

_DATA_DIR     = os.environ.get("SOLSPIRE_DATA_DIR", "data")
_STORE_PATH   = os.path.join(_DATA_DIR, "goal_store.json")


class GoalStore:
    def __init__(self, snapshot_path: str = _STORE_PATH) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._goals: dict[str, dict[str, Any]] = {}
        self._snapshot_path = snapshot_path
        self._load()

    # ── persistence ─────────────────────────────────────────────────────────
    def _load(self) -> None:
        if not os.path.exists(self._snapshot_path):
            return
        try:
            with open(self._snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(data, dict):
            for gid, g in data.items():
                if isinstance(g, dict) and g.get("goal_id"):
                    self._goals[gid] = g

    def _persist(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._snapshot_path), exist_ok=True)
            tmp = self._snapshot_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._goals, f, indent=2, ensure_ascii=False, default=str)
            os.replace(tmp, self._snapshot_path)
        except OSError:
            pass

    # ── core API ────────────────────────────────────────────────────────────
    def create(self, description: str, *,
               cadence_seconds: float = 300.0,
               max_runs_per_hour: int = DEFAULT_MAX_PER_HOUR,
               start_now: bool = True) -> dict[str, Any]:
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Goal description is required.")

        cadence = max(MIN_CADENCE_SECONDS, float(cadence_seconds))
        cap = max(1, min(MAX_RUNS_PER_HOUR_HARD, int(max_runs_per_hour)))
        now = time.time()
        goal_id = f"goal_{uuid.uuid4().hex[:12]}"
        goal: dict[str, Any] = {
            "goal_id":           goal_id,
            "description":       description.strip(),
            "status":            ACTIVE,
            "cadence_seconds":   cadence,
            "max_runs_per_hour": cap,
            "next_run":          now if start_now else now + cadence,
            "last_run":          None,
            "run_count":         0,
            "history":           [],
            "created_at":        now,
            "updated_at":        now,
        }
        with self._lock:
            self._goals[goal_id] = goal
            self._persist()
        return dict(goal)

    def get(self, goal_id: str) -> dict[str, Any] | None:
        with self._lock:
            g = self._goals.get(goal_id)
            return dict(g) if g else None

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            goals = list(self._goals.values())
        if status:
            goals = [g for g in goals if g.get("status") == status]
        goals.sort(key=lambda g: g.get("created_at", 0), reverse=True)
        return [dict(g) for g in goals]

    def update(self, goal_id: str, **fields: Any) -> dict[str, Any] | None:
        with self._lock:
            g = self._goals.get(goal_id)
            if g is None:
                return None
            if "status" in fields and fields["status"] not in VALID_STATUSES:
                raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
            if "cadence_seconds" in fields:
                fields["cadence_seconds"] = max(MIN_CADENCE_SECONDS, float(fields["cadence_seconds"]))
            if "max_runs_per_hour" in fields:
                fields["max_runs_per_hour"] = max(
                    1, min(MAX_RUNS_PER_HOUR_HARD, int(fields["max_runs_per_hour"]))
                )
            for k, v in fields.items():
                g[k] = v
            g["updated_at"] = time.time()
            self._persist()
            return dict(g)

    def delete(self, goal_id: str) -> bool:
        with self._lock:
            existed = goal_id in self._goals
            self._goals.pop(goal_id, None)
            if existed:
                self._persist()
            return existed

    def record_run(self, goal_id: str, *, job_id: str | None,
                   ts: float | None = None) -> dict[str, Any] | None:
        """Mark a goal as just-fired: bump counters, set next_run from cadence,
        append job_id to capped history. Called by the scheduler when it
        enqueues a job for the goal."""
        ts = ts if ts is not None else time.time()
        with self._lock:
            g = self._goals.get(goal_id)
            if g is None:
                return None
            g["last_run"]   = ts
            g["next_run"]   = ts + float(g.get("cadence_seconds", MIN_CADENCE_SECONDS))
            g["run_count"]  = int(g.get("run_count", 0)) + 1
            history = list(g.get("history") or [])
            if job_id:
                history.append(job_id)
                history = history[-HISTORY_CAP:]
            g["history"]    = history
            g["updated_at"] = ts
            self._persist()
            return dict(g)

    def due_goals(self, *, now: float | None = None) -> list[dict[str, Any]]:
        """Return active goals whose next_run has passed AND who are still
        under their per-hour cap."""
        now = now if now is not None else time.time()
        out: list[dict[str, Any]] = []
        with self._lock:
            for g in self._goals.values():
                if g.get("status") != ACTIVE:
                    continue
                if (g.get("next_run") or 0) > now:
                    continue
                if not _under_hourly_cap(g, now):
                    continue
                out.append(dict(g))
        return out

    def reset(self) -> None:
        with self._lock:
            self._goals.clear()
            self._persist()


def _under_hourly_cap(goal: dict[str, Any], now: float) -> bool:
    """A goal is under cap if it has fewer than max_runs_per_hour entries
    in its history within the last 3600 seconds. We approximate by
    counting recent history slots — exact wall-clock counting requires
    storing timestamps per run, which we avoid for storage discipline."""
    cap = int(goal.get("max_runs_per_hour", DEFAULT_MAX_PER_HOUR))
    cadence = float(goal.get("cadence_seconds", MIN_CADENCE_SECONDS))
    # If cadence × cap > 3600, the cadence already enforces the cap.
    if cadence * cap >= 3600:
        return True
    # Otherwise fall back to last_run gap: require at least 3600/cap seconds
    # since last_run on average — simple, effective, no extra storage.
    last = goal.get("last_run")
    if last is None:
        return True
    min_gap = 3600.0 / cap
    return (now - float(last)) >= min_gap


# ── module-level singleton (mirrors JobStore pattern) ───────────────────────
_store: GoalStore | None = None
_store_lock = threading.Lock()


def get_store() -> GoalStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = GoalStore()
    return _store


__all__ = [
    "GoalStore", "get_store",
    "ACTIVE", "PAUSED", "COMPLETED", "VALID_STATUSES",
    "MIN_CADENCE_SECONDS", "MAX_RUNS_PER_HOUR_HARD",
    "DEFAULT_MAX_PER_HOUR", "HISTORY_CAP",
]
