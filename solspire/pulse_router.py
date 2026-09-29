"""Authenticated API surface for the bounded Daily Pulse."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.pulse_manager import get_pulse_manager
from solspire.workspace_manager import get_workspace_manager

router = APIRouter(
    prefix="/pulses",
    tags=["SolSpire Daily Pulses"],
    dependencies=[Depends(require_auth)],
)


class CreatePulseRequest(BaseModel):
    state_summary: str = ""
    period: str = Field(default="day")
    workload_ref: str | None = None


@router.post("")
async def create_daily_pulse(
    body: CreatePulseRequest | None = None,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    payload = body or CreatePulseRequest()
    try:
        pulse = get_pulse_manager().create_or_get_today(
            subject_ref=user["uid"],
            workspace_ref=workspace.id,
            workload_ref=payload.workload_ref,
            state_summary=payload.state_summary,
            period=payload.period,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "pulse": pulse.to_dict()}


@router.get("")
async def list_daily_pulses(
    limit: int = Query(default=30, ge=1, le=100),
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    pulses = get_pulse_manager().list_for_subject(user["uid"], workspace.id, limit)
    return {"pulses": [p.to_dict() for p in pulses], "count": len(pulses)}


@router.get("/today")
async def get_today_pulse(user: dict = Depends(require_auth)) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    from datetime import datetime, timezone

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pulse = get_pulse_manager().get_for_subject_date(user["uid"], workspace.id, date)
    if pulse is None:
        raise HTTPException(status_code=404, detail="Daily pulse not found")
    return {"pulse": pulse.to_dict()}


__all__ = ["router"]
