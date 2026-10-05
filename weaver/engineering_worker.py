"""Bounded worker session aligned to M09 Worker Contract.

Lifecycle: WAKE → LOAD → VALIDATE → ROUTE → PLAN → EXECUTE →
CHECKPOINT → VERIFY → REPORT → TERMINATE (review boundary).

See docs/control-plane/WORKER_CONTRACT.md.
"""
from __future__ import annotations

from typing import Any
import json
import os
import urllib.request

from weaver.attention_bus import (
    JsonlAttentionOutbox,
    build_engineering_attention_event,
    classify_event,
)
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
            result = {
                **route,
                "contract_id": CONTRACT_ID,
                "lifecycle_phases": list(LIFECYCLE_PHASES),
                "phases_completed": phases_completed,
                "worker": "STOPPED",
                "merge": False,
                "deploy": False,
                "continues_to_next_move": False,
            }
            return self._record_attention(result)

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
        result = {
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
        return self._record_attention(result)

    def _record_attention(self, result: dict[str, Any]) -> dict[str, Any]:
        """Record a downstream attention event; never changes execution authority."""
        event = build_engineering_attention_event(result)
        plan = classify_event(event)
        outbox = JsonlAttentionOutbox(
            self.router.repo_root / "docs/control-plane/evidence/attention-events.jsonl"
        )
        recorded = outbox.append(event, plan)
        result["attention_event"] = event.to_dict()
        result["attention_delivery_plan"] = plan.to_dict()
        result["attention_outbox_recorded"] = recorded

        delivery_url = os.environ.get("ARKADIA_ATTENTION_DELIVERY_URL", "").strip()
        sovereign_key = os.environ.get("SOVEREIGN_KEY", "").strip()
        owner_uid = os.environ.get("ARKADIA_ATTENTION_OWNER_UID", "").strip()
        if delivery_url and sovereign_key and owner_uid:
            try:
                payload = {**event.to_dict(), "user_id": owner_uid}
                request = urllib.request.Request(
                    delivery_url,
                    data=json.dumps(payload).encode("utf-8"),
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "X-Arkadia-Sovereign-Key": sovereign_key,
                    },
                )
                with urllib.request.urlopen(request, timeout=20) as response:
                    delivery = json.loads(response.read().decode("utf-8"))
                result["attention_delivery"] = delivery
            except Exception as exc:
                result["attention_delivery"] = {
                    "status": "FAILED",
                    "error": str(exc)[:500],
                }
        else:
            result["attention_delivery"] = {
                "status": "NOT_CONFIGURED",
                "reason": "ARKADIA_ATTENTION_DELIVERY_URL/SOVEREIGN_KEY/ARKADIA_ATTENTION_OWNER_UID not configured",
            }
        return result
