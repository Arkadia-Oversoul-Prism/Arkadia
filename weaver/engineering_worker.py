"""Bounded worker session aligned to M09 Worker Contract.

Lifecycle: WAKE → LOAD → VALIDATE → ROUTE → PLAN → EXECUTE →
CHECKPOINT → VERIFY → REPORT → TERMINATE (review boundary).

See docs/control-plane/WORKER_CONTRACT.md.
"""
from __future__ import annotations

from typing import Any

from weaver.engineering_router import EngineeringRouter
from weaver.execution_adapter import ExecutionAdapter, ExecutionRequest, NullExecutionAdapter

LIFECYCLE_PHASES = (
    "WAKE",
    "LOAD",
    "VALIDATE",
    "ROUTE",
    "PLAN",
    "EXECUTE",
    "CHECKPOINT",
    "VERIFY",
    "REPORT",
    "TERMINATE",
)

CONTRACT_ID = "ARKADIA-WORKER-CONTRACT-v1"


class EngineeringWorker:
    def __init__(
        self,
        repo_root: str = ".",
        session_id: str | None = None,
        dry_run: bool = True,
        adapter: ExecutionAdapter | None = None,
    ) -> None:
        self.router = EngineeringRouter(repo_root=repo_root, session_id=session_id, dry_run=dry_run)
        self.adapter = adapter or NullExecutionAdapter()
        self.dry_run = dry_run

    def run(self) -> dict[str, Any]:
        phases_completed: list[str] = ["WAKE", "LOAD", "VALIDATE"]
        route = self.router.run()
        phases_completed.append("ROUTE")
        phases_completed.append("PLAN")

        if route.get("status") in ("FAILED", "NO_LEGAL_MOVE", "BLOCKED"):
            phases_completed.extend(["REPORT", "TERMINATE"])
            return {
                **route,
                "contract_id": CONTRACT_ID,
                "lifecycle_phases": list(LIFECYCLE_PHASES),
                "phases_completed": phases_completed,
                "worker": "STOPPED",
                "merge": False,
                "deploy": False,
                "continues_to_next_move": False,
            }

        move = route.get("next_move") or {}
        plan = route.get("plan") or {}
        phases_completed.append("EXECUTE")
        exec_result = self.adapter.execute(
            ExecutionRequest(
                move_id=str(move.get("id") or ""),
                plan=plan,
                dry_run=self.dry_run,
                repo_root=str(self.router.repo_root),
            )
        )
        phases_completed.extend(["CHECKPOINT", "VERIFY", "REPORT", "TERMINATE"])
        return {
            **route,
            "contract_id": CONTRACT_ID,
            "lifecycle_phases": list(LIFECYCLE_PHASES),
            "phases_completed": phases_completed,
            "worker": "STOPPED_AT_REVIEW",
            "execution": {
                "ok": exec_result.ok,
                "message": exec_result.message,
                "files_changed": exec_result.files_changed,
                "provider": exec_result.provider,
            },
            "merge": False,
            "deploy": False,
            "continues_to_next_move": False,
        }
