"""
Approval gate for sensitive tool calls.
Extracted from api/main.py (Phase 2 decomposition) — paths unchanged.

Pending approvals live in memory (good enough for single-instance use).
Both the /api/approvals endpoints and CEO chat (api/main.py) share this
module-level state.
"""
import logging
import threading
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("arkadia")

PENDING_APPROVALS: dict = {}
APPROVAL_LOCK = threading.Lock()

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def queue_approval(tool_name: str, payload: dict, description: str) -> str:
    """Create a pending approval entry; returns the approval_id."""
    approval_id = str(uuid.uuid4())[:12]
    with APPROVAL_LOCK:
        PENDING_APPROVALS[approval_id] = {
            "id": approval_id,
            "tool_name": tool_name,
            "payload": payload,
            "description": description,
            "status": "pending",
            "created_at": _now_iso(),
            "decided_at": None,
        }
    return approval_id


@router.post("/api/approvals/request")
async def api_request_approval(request: Request):
    """Queue a tool call for human approval. Returns approval_id."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    tool_name = body.get("tool_name", "")
    payload = body.get("payload", {})
    description = body.get("description", f"Run {tool_name}")
    approval_id = queue_approval(tool_name, payload, description)
    logger.info("[APPROVAL] created %s for tool=%s", approval_id, tool_name)
    return {"approval_id": approval_id, "status": "pending"}


@router.get("/api/approvals")
async def api_list_approvals(status: str | None = None):
    with APPROVAL_LOCK:
        items = list(PENDING_APPROVALS.values())
    if status:
        items = [a for a in items if a["status"] == status]
    return {"approvals": sorted(items, key=lambda a: a["created_at"], reverse=True)}


@router.post("/api/approvals/{approval_id}/approve")
async def api_approve(approval_id: str):
    with APPROVAL_LOCK:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        approval["status"] = "approved"
        approval["decided_at"] = _now_iso()
    # Execute the tool now
    from kernel.tools import get_tool
    tool = get_tool(approval["tool_name"])
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{approval['tool_name']}' not found")
    try:
        result = tool.run(approval["payload"])
        approval["result"] = result
        return {"approval_id": approval_id, "status": "approved", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")


@router.post("/api/approvals/{approval_id}/reject")
async def api_reject(approval_id: str):
    with APPROVAL_LOCK:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        approval["status"] = "rejected"
        approval["decided_at"] = _now_iso()
    return {"approval_id": approval_id, "status": "rejected"}
