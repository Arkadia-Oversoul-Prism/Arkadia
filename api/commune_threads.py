"""First-class Arkana thread API over the canonical Knowledge OS threads table."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/commune/threads", tags=["arkana-threads"])


async def _user_id(request: Request) -> str:
    from api.auth import get_current_user
    user = await get_current_user(request)
    uid = (user or {}).get("uid") if user else None
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required")
    return uid


def _public_thread(row: dict) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "uuid": row.get("uuid"),
        "title": row.get("title"),
        "project_id": row.get("project_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


@router.get("")
async def list_arkana_threads(request: Request, project_id: int | None = None) -> dict[str, Any]:
    from knowledge.vault import list_threads
    uid = await _user_id(request)
    return {"threads": [_public_thread(x) for x in list_threads(uid, project_id=project_id)]}


@router.post("")
async def create_arkana_thread(request: Request) -> dict[str, Any]:
    from knowledge.vault import create_thread
    uid = await _user_id(request)
    body = await request.json()
    title = str(body.get("title") or "New conversation").strip()[:200]
    project_id = body.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="project_id must be an integer")
        from knowledge.db import execute_one
        project = execute_one("SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, uid))
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    return _public_thread(create_thread(title=title, user_id=uid, project_id=project_id))


@router.get("/{thread_uuid}")
async def get_arkana_thread(thread_uuid: str, request: Request) -> dict[str, Any]:
    from knowledge.vault import get_thread
    uid = await _user_id(request)
    row = get_thread(thread_uuid, user_id=uid)
    if not row:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"thread": _public_thread(row)}


@router.get("/{thread_uuid}/messages")
async def list_arkana_thread_messages(thread_uuid: str, request: Request) -> dict[str, Any]:
    from knowledge.vault import get_thread
    from knowledge.db import execute
    uid = await _user_id(request)
    thread = get_thread(thread_uuid, user_id=uid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    rows = execute(
        "SELECT content, created_at FROM notes WHERE thread_id = ? AND note_type = 'conversation' AND user_id = ? ORDER BY created_at ASC, id ASC",
        (thread["id"], uid),
    ) or []
    messages: list[dict[str, Any]] = []
    for row in rows:
        content = row.get("content") or ""
        prompt = content.split("## Prompt\n\n", 1)[1] if "## Prompt\\n\\n" in content else ""
        response = prompt.split("\n\n## Response\n\n", 1) if prompt else []
        if response:
            prompt, answer = response[0], response[1]
            messages.extend([
                {"role": "user", "content": prompt, "created_at": row.get("created_at")},
                {"role": "arkana", "content": answer, "created_at": row.get("created_at")},
            ])
    return {"messages": messages}
