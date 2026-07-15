"""SolSpire Phase 3 — task / plan state store.

Process-local. Phase 4 swaps this for a persistent backend (Postgres /
Supabase) without changing the surface here.

Each PLAN owns N TASK STATE OBJECTS that match the spec:
    {
      "task_id": "...",
      "status":  "pending | running | complete | failed | skipped",
      "results": {},
      "history": []
    }
"""
from __future__ import annotations

import time
import uuid
from typing import Any

# plan_id → plan dict
_PLANS: dict[str, dict[str, Any]] = {}

VALID_STATUSES = {"pending", "running", "complete", "failed", "skipped"}


def _now() -> float:
    return time.time()


def new_plan_id() -> str:
    return f"plan_{uuid.uuid4().hex[:10]}"


def new_task_id(idx: int) -> str:
    return f"t_{idx + 1:02d}_{uuid.uuid4().hex[:6]}"


def save_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Persist a plan envelope. Returns the stored dict."""
    pid = plan.get("plan_id") or new_plan_id()
    plan["plan_id"] = pid
    plan.setdefault("created_at", _now())
    plan["updated_at"] = _now()
    _PLANS[pid] = plan
    return plan


def get_plan(plan_id: str) -> dict[str, Any] | None:
    return _PLANS.get(plan_id)


def list_plans() -> list[dict[str, Any]]:
    return list(_PLANS.values())


def update_task(plan_id: str, task_id: str, **fields: Any) -> dict[str, Any] | None:
    """Mutate a task in-place: status, results, history-append.

    `history` is special — pass `event=...` to append a structured entry
    instead of overwriting the list.
    """
    plan = _PLANS.get(plan_id)
    if not plan:
        return None
    for task in plan.get("tasks", []):
        if task.get("task_id") == task_id:
            event = fields.pop("event", None)
            for k, v in fields.items():
                if k == "status" and v not in VALID_STATUSES:
                    continue
                task[k] = v
            if event is not None:
                task.setdefault("history", []).append({
                    "at":    _now(),
                    "event": event,
                })
            plan["updated_at"] = _now()
            return task
    return None


def reset() -> None:
    """Test-only: clear all plans."""
    _PLANS.clear()


__all__ = [
    "new_plan_id", "new_task_id",
    "save_plan", "get_plan", "list_plans",
    "update_task", "reset",
    "VALID_STATUSES",
]
