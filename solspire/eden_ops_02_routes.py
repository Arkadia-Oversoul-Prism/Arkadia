"""EDEN-OPS-02 FastAPI route handlers for enterprise_router inclusion."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import require_auth
from solspire import eden_ops_02 as e02
from solspire.enterprise_router import _MANAGER


def _owner_uid(enterprise_id: str) -> str | None:
    return e02.owner_uid_for_enterprise(enterprise_id=enterprise_id)


def _require_access(enterprise_id: str, caller_uid: str) -> str:
    owner = _owner_uid(enterprise_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Enterprise not found")
    if not e02.can_access_enterprise(
        enterprise_id=enterprise_id, caller_uid=caller_uid, owner_uid=owner
    ):
        raise HTTPException(status_code=404, detail="Enterprise not found")
    return owner


def register_eden_ops_02_routes(router: APIRouter) -> None:
    @router.post("/workspaces/{enterprise_id}/members")
    async def add_member(
        enterprise_id: str, body: dict[str, Any], user: dict = Depends(require_auth)
    ):
        owner = _require_access(enterprise_id, user["uid"])
        if user["uid"] != owner:
            raise HTTPException(status_code=403, detail="Owner only")
        try:
            pub = e02.add_member_by_handle(
                enterprise_id=enterprise_id,
                owner_uid=owner,
                caller_uid=user["uid"],
                handle=str(body.get("handle") or ""),
                desk=str(body.get("desk") or ""),
                human_name=body.get("human_name"),
            )
        except ValueError as ex:
            raise HTTPException(status_code=400, detail=str(ex))
        except LookupError as ex:
            raise HTTPException(status_code=404, detail=str(ex))
        except PermissionError as ex:
            raise HTTPException(status_code=403, detail=str(ex))
        return {"member": pub.to_dict()}

    @router.delete("/workspaces/{enterprise_id}/members/{handle}/desks/{desk}")
    async def remove_member(
        enterprise_id: str, handle: str, desk: str, user: dict = Depends(require_auth)
    ):
        owner = _require_access(enterprise_id, user["uid"])
        if user["uid"] != owner:
            raise HTTPException(status_code=403, detail="Owner only")
        try:
            e02.remove_member_desk(
                enterprise_id=enterprise_id,
                owner_uid=owner,
                caller_uid=user["uid"],
                handle=handle,
                desk=desk,
            )
        except ValueError as ex:
            raise HTTPException(status_code=400, detail=str(ex))
        except LookupError as ex:
            raise HTTPException(status_code=404, detail=str(ex))
        except PermissionError as ex:
            raise HTTPException(status_code=403, detail=str(ex))
        return {"ok": True}

    @router.get("/workspaces/{enterprise_id}/tasks")
    async def get_tasks(
        enterprise_id: str,
        desk: str | None = Query(None),
        user: dict = Depends(require_auth),
    ):
        _require_access(enterprise_id, user["uid"])
        e02.seed_tasks(enterprise_id=enterprise_id)
        tasks = e02.list_tasks(enterprise_id=enterprise_id, desk=desk)
        return {"tasks": [t.to_public_dict() for t in tasks]}

    @router.patch("/workspaces/{enterprise_id}/tasks/{task_id}")
    async def patch_task(
        enterprise_id: str,
        task_id: str,
        body: dict[str, Any],
        user: dict = Depends(require_auth),
    ):
        owner = _require_access(enterprise_id, user["uid"])
        try:
            task = e02.update_task(
                enterprise_id=enterprise_id,
                task_id=task_id,
                caller_uid=user["uid"],
                owner_uid=owner,
                status=body.get("status"),
                evidence_note=body.get("evidence_note"),
                title=body.get("title"),
            )
        except LookupError as ex:
            raise HTTPException(status_code=404, detail=str(ex))
        except PermissionError as ex:
            raise HTTPException(status_code=403, detail=str(ex))
        except ValueError as ex:
            raise HTTPException(status_code=400, detail=str(ex))
        return {"task": task.to_public_dict()}

    @router.get("/workspaces/{enterprise_id}/control-room")
    async def get_control_room(
        enterprise_id: str, user: dict = Depends(require_auth)
    ):
        _require_access(enterprise_id, user["uid"])
        e02.seed_tasks(enterprise_id=enterprise_id)
        return e02.control_room(
            enterprise_id=enterprise_id, subject_for_projection=user["uid"]
        )
