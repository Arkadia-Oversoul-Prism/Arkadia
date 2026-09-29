"""Phase 6 — durable execution record schema.

The record is intentionally storage-agnostic. ``kernel.jobs.JobStore`` remains
responsible for persistence; this module defines the shape of the durable
execution state that survives worker restart.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EXECUTION_STATES = {
    "CREATED",
    "QUEUED",
    "ANALYSING",
    "EXECUTING",
    "CHECKPOINTED",
    "RESUMING",
    "LEARNED",
    "COMPLETE",
    "FAILED",
}


@dataclass
class ExecutionRecord:
    """Serializable execution state carried by a JobStore record."""

    task_id: str
    state: str = "CREATED"
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    lease: dict[str, Any] | None = None
    heartbeat: float | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in EXECUTION_STATES:
            raise ValueError(f"invalid execution state: {self.state}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "state": self.state,
            "checkpoints": list(self.checkpoints),
            "lease": dict(self.lease) if self.lease else None,
            "heartbeat": self.heartbeat,
            "artifacts": list(self.artifacts),
            "events": list(self.events),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ExecutionRecord":
        return cls(
            task_id=str(value["task_id"]),
            state=str(value.get("state", "CREATED")),
            checkpoints=list(value.get("checkpoints") or []),
            lease=dict(value["lease"]) if value.get("lease") else None,
            heartbeat=value.get("heartbeat"),
            artifacts=list(value.get("artifacts") or []),
            events=list(value.get("events") or []),
        )

    @property
    def last_checkpoint(self) -> dict[str, Any] | None:
        return self.checkpoints[-1] if self.checkpoints else None


__all__ = ["EXECUTION_STATES", "ExecutionRecord"]
