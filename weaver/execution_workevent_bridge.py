"""Explicit causal bridge: Weaver ExecutionAttempt -> SolSpire WorkEvent.

The bridge records an observed consequential transition. It does not grant
authority, prove correctness, mark completion, or perform production acceptance.
"""
from __future__ import annotations

from typing import Any

from solspire.workevent_manager import WorkEvent, get_workevent_manager
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore, ExecutionAttempt


_TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "BLOCKED"}


def capture_execution_workevent(
    *,
    store: EnterpriseOrchestrationStore,
    subject: str,
    execution_attempt_id: str,
    workspace_ref: str,
    actor_ref: str | None = None,
    state_before_ref: str = "AUTHORIZED",
) -> WorkEvent:
    """Create exactly one WorkEvent for a terminal Weaver execution attempt."""
    row = store._row("ew_execution_attempts", execution_attempt_id)
    if not row or row["subject"] != subject:
        raise ValueError("matching execution attempt required")
    status = str(row["result_status"]).upper()
    if status not in _TERMINAL_STATUSES:
        raise ValueError("WorkEvent capture requires terminal execution status")

    workevents = get_workevent_manager()
    existing = workevents.get_by_execution_attempt(execution_attempt_id, subject)
    if existing is not None:
        return existing

    execution = ExecutionAttempt(
        row["id"],
        row["subject"],
        row["authorization_id"],
        row["tool_channel"],
        __import__("json").loads(row["request_payload"]),
        row["attempted_at"],
        row["result_status"],
        row["correlation_id"],
    )
    event_type = f"EXECUTION_{status}"
    try:
        return workevents.create(
            subject_ref=subject,
        workspace_ref=workspace_ref,
        event_type=event_type,
        occurred_at=execution.attempted_at,
        work_ref=execution.id,
        execution_attempt_ref=execution.id,
        scope_ref=execution.authorization_id,
        actor_ref=actor_ref or subject,
        artifact_refs=[execution.id],
        state_before_ref=state_before_ref,
        state_after_ref=status,
        decision_ref=execution.authorization_id,
        witness_ref=execution.id,
            status="RECORDED",
        )
    except ValueError:
        # A concurrent retry may win the unique execution_attempt_ref insert.
        existing = workevents.get_by_execution_attempt(execution_attempt_id, subject)
        if existing is not None:
            return existing
        raise


__all__ = ["capture_execution_workevent"]
