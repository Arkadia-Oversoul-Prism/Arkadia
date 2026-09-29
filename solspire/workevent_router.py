"""Authenticated API surface for the bounded SolSpire WorkEvent Spine."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.workspace_manager import get_workspace_manager
from solspire.workevent_manager import get_workevent_manager

router = APIRouter(
    prefix="/workevents",
    tags=["SolSpire WorkEvents"],
    dependencies=[Depends(require_auth)],
)


class CreateWorkEventRequest(BaseModel):
    work_event_id: str | None = None
    event_type: str
    occurred_at: float
    event_version: int = Field(default=1, ge=1)
    effective_from: float | None = None
    effective_until: float | None = None
    work_ref: str | None = None
    parent_event_ref: str | None = None
    sequence_ref: str | None = None
    scope_ref: str | None = None
    actor_ref: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    state_before_ref: str | None = None
    state_after_ref: str | None = None
    decision_ref: str | None = None
    witness_ref: str | None = None
    status: str = "RECORDED"
    supersedes_ref: str | None = None
    reversal_of_ref: str | None = None
    created_by_event: str | None = None
    schema_version: str = "1"


@router.post("")
async def create_workevent(body: CreateWorkEventRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    try:
        event = get_workevent_manager().create(
            subject_ref=user["uid"],
            workspace_ref=workspace.id,
            **body.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "work_event": event.to_dict()}


@router.get("")
async def list_workevents(
    workspace_ref: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    if workspace_ref and workspace_ref != workspace.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    events = get_workevent_manager().list(user["uid"], workspace.id, limit)
    return {"work_events": [event.to_dict() for event in events], "count": len(events)}


@router.get("/{work_event_id}")
async def get_workevent(work_event_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    event = get_workevent_manager().get(work_event_id, user["uid"])
    if event is None:
        raise HTTPException(status_code=404, detail="WorkEvent not found")
    return {"work_event": event.to_dict()}


# Workload and Daily Pulse routers are include_router'd from console_router
# at /solspire so they resolve as /solspire/workloads and /solspire/pulses
# (not nested under /workevents).


__all__ = ["router"]
