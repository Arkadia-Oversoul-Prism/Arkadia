"""Authenticated API surface for the bounded Canonical Workload."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth import require_auth
from solspire.workspace_manager import get_workspace_manager
from solspire.workload_manager import get_workload_manager

router = APIRouter(
    prefix="/workloads",
    tags=["SolSpire Workloads"],
    dependencies=[Depends(require_auth)],
)


@router.post("")
async def create_canonical_workload(user: dict = Depends(require_auth)) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    try:
        workload = get_workload_manager().create_canonical_barnabas(
            subject_ref=user["uid"], workspace_ref=workspace.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "workload": workload.to_dict()}


@router.get("")
async def get_canonical_workload(user: dict = Depends(require_auth)) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    workload = get_workload_manager().get_for_subject(user["uid"], workspace.id)
    if workload is None:
        raise HTTPException(status_code=404, detail="Canonical workload not found")
    return {"workload": workload.to_dict()}


__all__ = ["router"]
