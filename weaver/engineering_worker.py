"""Bounded worker session: WAKE → … → STOP at review."""
from __future__ import annotations

from typing import Any

from weaver.engineering_router import EngineeringRouter
from weaver.execution_adapter import ExecutionAdapter, ExecutionRequest, NullExecutionAdapter


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
        route = self.router.run()
        if route.get("status") in ("FAILED", "NO_LEGAL_MOVE", "BLOCKED"):
            return {**route, "worker": "STOPPED", "merge": False, "deploy": False}

        move = route.get("next_move") or {}
        plan = route.get("plan") or {}
        exec_result = self.adapter.execute(
            ExecutionRequest(
                move_id=str(move.get("id") or ""),
                plan=plan,
                dry_run=self.dry_run,
                repo_root=str(self.router.repo_root),
            )
        )
        # Hard stop: never merge/deploy
        return {
            **route,
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
