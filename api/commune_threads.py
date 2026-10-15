"""First-class Arkana thread API over the canonical Knowledge OS threads table."""
from __future__ import annotations

import re
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


#: The Oracle spine's conversation notes carry both turns in one note.
_ORACLE_PROMPT = "## Prompt\n\n"
_ORACLE_RESPONSE = "\n\n## Response\n\n"

#: Project conversation notes carry one turn per note, headed `Role: <role>`.
_PROJECT_HEADER = re.compile(r"^Role:[ \t]*(\S+)", re.MULTILINE)

#: Roles that are an Arkana answer rather than a user turn, across producers.
_ASSISTANT_ROLES = frozenset({"arkana", "assistant", "model"})


def _turn_messages(content: str) -> list[tuple[str, str]]:
    """Every ``(role, content)`` turn a conversation note records.

    Two producers write ``note_type='conversation'`` notes into the same thread,
    each in its own shape, and both are canonical:

    * ``knowledge.pipeline.ingest_conversation`` writes the Oracle spine's pair in
      a single note — ``## Prompt`` then ``## Response`` — so one row is two turns.
    * ``solspire.conversation_bridge`` writes one turn per note, headed
      ``Role: <role>``, so one row is one turn.

    A note in neither shape is skipped rather than guessed at: an unknown body
    must never become a fabricated message.
    """
    if _ORACLE_PROMPT in content:
        prompt, _, rest = content.partition(_ORACLE_PROMPT)
        if _ORACLE_RESPONSE not in rest:
            # A half-written pair has no answer; report nothing rather than
            # inventing one.
            return []
        question, _, answer = rest.partition(_ORACLE_RESPONSE)
        return [("user", question), ("arkana", answer)]

    match = _PROJECT_HEADER.search(content)
    if not match:
        return []
    body = content[match.end():].strip("\n")
    role = "arkana" if match.group(1).lower() in _ASSISTANT_ROLES else "user"
    return [(role, body)] if body else []


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


@router.patch("/{thread_uuid}")
async def rename_arkana_thread(thread_uuid: str, request: Request) -> dict[str, Any]:
    """Rename a canonical Arkana thread. Titles are system-owned, not user-authored."""
    from knowledge.vault import get_thread
    from knowledge.db import execute
    uid = await _user_id(request)
    thread = get_thread(thread_uuid, user_id=uid)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    body = await request.json()
    title = str(body.get("title") or "").strip()[:120]
    if not title:
        raise HTTPException(status_code=400, detail="A semantic title is required")
    execute("UPDATE threads SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?", (title, thread["id"], uid))
    updated = get_thread(thread_uuid, user_id=uid)
    return {"thread": _public_thread(updated or thread)}


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
        created_at = row.get("created_at")
        for role, body in _turn_messages(row.get("content") or ""):
            messages.append({"role": role, "content": body, "created_at": created_at})
    return {"messages": messages}
