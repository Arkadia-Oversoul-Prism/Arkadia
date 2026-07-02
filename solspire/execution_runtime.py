"""SolSpire Console — ExecutionRuntime (Milestone 1).

Manages the lifecycle of plan executions: execute, pause, resume, cancel.
In-process for Milestone 1; Phase 2 swaps to a durable queue.

Contract:
    runtime = ExecutionRuntime()
    execution = runtime.execute(plan)
    runtime.pause(execution.id)
    runtime.resume(execution.id)
    runtime.cancel(execution.id)
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("solspire.execution_runtime")


class ExecutionStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    PAUSED    = "paused"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


@dataclass
class Plan:
    id: str
    request: str
    intent: str
    steps: list[dict[str, Any]]
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "request": self.request,
            "intent": self.intent,
            "steps": self.steps,
            "created_at": self.created_at,
        }


@dataclass
class Execution:
    id: str
    plan: Plan
    status: ExecutionStatus
    started_at: float
    completed_at: float | None
    results: list[dict[str, Any]]
    error: str | None
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan.id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "results": self.results,
            "error": self.error,
            "retries": self.retries,
        }


_MAX_RETRIES = 2
_STEP_TIMEOUT = 30.0


class ExecutionRuntime:
    def __init__(self) -> None:
        self._executions: dict[str, Execution] = {}
        self._pause_events: dict[str, threading.Event] = {}
        self._cancel_flags: dict[str, bool] = {}
        self._lock = threading.Lock()

    def execute(self, plan: Plan) -> Execution:
        exec_id = str(uuid.uuid4())
        execution = Execution(
            id=exec_id,
            plan=plan,
            status=ExecutionStatus.RUNNING,
            started_at=time.time(),
            completed_at=None,
            results=[],
            error=None,
        )
        pause_event = threading.Event()
        pause_event.set()  # not paused initially

        with self._lock:
            self._executions[exec_id] = execution
            self._pause_events[exec_id] = pause_event
            self._cancel_flags[exec_id] = False

        logger.info("ExecutionRuntime: starting execution %s (plan=%s, steps=%d)",
                    exec_id, plan.id, len(plan.steps))

        thread = threading.Thread(target=self._run, args=(exec_id,), daemon=True)
        thread.start()

        # Wait briefly so the caller gets a running execution
        time.sleep(0.05)
        return self._executions[exec_id]

    def pause(self, execution_id: str) -> None:
        with self._lock:
            ev = self._pause_events.get(execution_id)
            ex = self._executions.get(execution_id)
        if not ev or not ex:
            raise KeyError(f"Execution '{execution_id}' not found")
        if ex.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot pause execution in state '{ex.status}'")
        ev.clear()
        ex.status = ExecutionStatus.PAUSED
        logger.info("ExecutionRuntime: paused %s", execution_id)

    def resume(self, execution_id: str) -> None:
        with self._lock:
            ev = self._pause_events.get(execution_id)
            ex = self._executions.get(execution_id)
        if not ev or not ex:
            raise KeyError(f"Execution '{execution_id}' not found")
        if ex.status != ExecutionStatus.PAUSED:
            raise ValueError(f"Cannot resume execution in state '{ex.status}'")
        ex.status = ExecutionStatus.RUNNING
        ev.set()
        logger.info("ExecutionRuntime: resumed %s", execution_id)

    def cancel(self, execution_id: str) -> None:
        with self._lock:
            ex = self._executions.get(execution_id)
            if not ex:
                raise KeyError(f"Execution '{execution_id}' not found")
            self._cancel_flags[execution_id] = True
            ev = self._pause_events.get(execution_id)
            if ev:
                ev.set()  # unblock if paused
        ex.status = ExecutionStatus.CANCELLED
        logger.info("ExecutionRuntime: cancelled %s", execution_id)

    def get(self, execution_id: str) -> Execution | None:
        return self._executions.get(execution_id)

    def list_executions(self) -> list[dict[str, Any]]:
        with self._lock:
            return [ex.to_dict() for ex in self._executions.values()]

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for ex in self._executions.values()
                       if ex.status in (ExecutionStatus.RUNNING, ExecutionStatus.PAUSED))

    def _run(self, exec_id: str) -> None:
        ex = self._executions[exec_id]
        ev = self._pause_events[exec_id]

        try:
            for i, step in enumerate(ex.plan.steps):
                # Pause checkpoint
                ev.wait(timeout=_STEP_TIMEOUT)
                if self._cancel_flags.get(exec_id):
                    ex.status = ExecutionStatus.CANCELLED
                    return

                step_result = self._execute_step(step, ex, i)
                ex.results.append(step_result)

                if not step_result.get("ok", True):
                    ex.retries += 1
                    if ex.retries >= _MAX_RETRIES:
                        ex.status = ExecutionStatus.FAILED
                        ex.error = f"Step {i} failed after {_MAX_RETRIES} retries: {step_result.get('error')}"
                        return

            ex.status = ExecutionStatus.COMPLETED
        except Exception as exc:
            ex.status = ExecutionStatus.FAILED
            ex.error = str(exc)
            logger.error("ExecutionRuntime: execution %s failed: %s", exec_id, exc)
        finally:
            ex.completed_at = time.time()

    def _execute_step(self, step: dict[str, Any], ex: Execution, idx: int) -> dict[str, Any]:
        tool = step.get("tool", "llm")
        payload = step.get("payload", {})
        logger.debug("ExecutionRuntime: step %d tool=%s", idx, tool)

        try:
            match tool:
                case "fs_read":
                    from solspire.tools_fs import read_file
                    return {"step": idx, "tool": tool, **read_file(payload.get("path", ""))}
                case "fs_write":
                    from solspire.tools_fs import write_file
                    return {"step": idx, "tool": tool, **write_file(payload.get("path", ""), payload.get("content", ""))}
                case "fs_list":
                    from solspire.tools_fs import list_directory
                    return {"step": idx, "tool": tool, **list_directory(payload.get("path", "."))}
                case "github_repos":
                    from solspire.tools_github import list_repos
                    return {"step": idx, "tool": tool, **list_repos(payload.get("owner", ""))}
                case "github_tree":
                    from solspire.tools_github import get_tree
                    return {"step": idx, "tool": tool, **get_tree(payload.get("owner", ""), payload.get("repo", ""))}
                case "github_read":
                    from solspire.tools_github import read_file as gh_read
                    return {"step": idx, "tool": tool, **gh_read(payload.get("owner", ""), payload.get("repo", ""), payload.get("path", ""))}
                case "project_create":
                    from solspire.project_manager import get_project_manager
                    p = get_project_manager().create(payload.get("name", "Unnamed"))
                    return {"step": idx, "tool": tool, "ok": True, "project": p.to_dict()}
                case "llm" | _:
                    from solspire.provider_manager import get_manager
                    result = get_manager().invoke_model(
                        payload.get("prompt", step.get("description", "Complete this step.")),
                        payload.get("context", {}),
                    )
                    return {"step": idx, "tool": "llm", "ok": True, "result": result}
        except Exception as exc:
            logger.error("ExecutionRuntime: step %d error: %s", idx, exc)
            return {"step": idx, "tool": tool, "ok": False, "error": str(exc)}


_GLOBAL_RUNTIME = ExecutionRuntime()


def get_runtime() -> ExecutionRuntime:
    return _GLOBAL_RUNTIME


__all__ = ["Plan", "Execution", "ExecutionStatus", "ExecutionRuntime", "get_runtime"]
