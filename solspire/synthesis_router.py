"""Authenticated API surface for the bounded Weekly Synthesis."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.synthesis_manager import get_synthesis_manager
from solspire.workspace_manager import get_workspace_manager

router = APIRouter(
    prefix="/syntheses",
    tags=["SolSpire Weekly Syntheses"],
    dependencies=[Depends(require_auth)],
)


class CreateSynthesisRequest(BaseModel):
    summary: str = ""
    workload_ref: str | None = None
    source_pulse_refs: list[str] = Field(default_factory=list)
    source_event_refs: list[str] = Field(default_factory=list)


@router.post("")
async def create_weekly_synthesis(
    body: CreateSynthesisRequest | None = None,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    payload = body or CreateSynthesisRequest()
    try:
        synthesis = get_synthesis_manager().create_or_get_current_week(
            subject_ref=user["uid"],
            workspace_ref=workspace.id,
            workload_ref=payload.workload_ref,
            summary=payload.summary,
            source_pulse_refs=payload.source_pulse_refs,
            source_event_refs=payload.source_event_refs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "synthesis": synthesis.to_dict()}


@router.get("")
async def list_weekly_syntheses(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    items = get_synthesis_manager().list_for_subject(user["uid"], workspace.id, limit)
    return {"syntheses": [item.to_dict() for item in items], "count": len(items)}


@router.get("/current")
async def get_current_week_synthesis(user: dict = Depends(require_auth)) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    synthesis = get_synthesis_manager().get_current_week(user["uid"], workspace.id)
    if synthesis is None:
        raise HTTPException(status_code=404, detail="Current weekly synthesis not found")
    return {"synthesis": synthesis.to_dict()}


__all__ = ["router"]
