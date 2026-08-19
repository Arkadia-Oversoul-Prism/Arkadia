"""
Arkadia Knowledge OS — Timeline Engine
=======================================
Immutable append-only event log. Every event is permanent.
Replay entire projects from this log.
LAW I: One capability. One implementation. One canonical home.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from knowledge.db import execute, execute_one, last_insert_id

EVENT_TYPES = {
    "conversation",
    "prompt",
    "response",
    "knowledge_created",
    "knowledge_modified",
    "review",
    "decision",
    "sync",
    "error",
    "pipeline_run",
    "embed_complete",
    "graph_link",
    "search_query",
    "provider_call",
}


def record(
    event_type: str,
    payload: dict,
    note_id: Optional[int] = None,
    project_id: Optional[int] = None,
    provider: Optional[str] = None,
    persona: Optional[str] = None,
    user_id: Optional[str] = None,
) -> int:
    """Append immutable timeline event. Stamp user_id when known."""
    if event_type not in EVENT_TYPES:
        pass
    uid = (user_id or "").strip() or None
    if uid is None and note_id is not None:
        row = execute_one("SELECT user_id FROM notes WHERE id = ?", (note_id,))
        if row and row.get("user_id"):
            uid = row["user_id"]
    if uid is None and project_id is not None:
        row = execute_one("SELECT user_id FROM projects WHERE id = ?", (project_id,))
        if row and row.get("user_id"):
            uid = row["user_id"]
    now = datetime.now(timezone.utc).isoformat()
    execute(
        """
        INSERT INTO timeline (event_type, payload, note_id, project_id, provider, persona, user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_type, json.dumps(payload), note_id, project_id, provider, persona, uid, now),
    )
    return last_insert_id()


def get_event(event_id: int) -> Optional[dict]:
    row = execute_one("SELECT * FROM timeline WHERE id = ?", (event_id,))
    if row:
        row["payload"] = json.loads(row["payload"])
    return row


def _timeline_owner_clause(user_id: Optional[str]) -> tuple[str, list]:
    if user_id:
        return "user_id = ?", [user_id]
    return "1 = 0", []


def query(
    event_type: Optional[str] = None,
    project_id: Optional[int] = None,
    note_id: Optional[int] = None,
    provider: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[str] = None,
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    oc, op = _timeline_owner_clause(user_id)
    conditions.append(oc)
    params.extend(op)
    if event_type:
        conditions.append("event_type = ?"); params.append(event_type)
    if project_id is not None:
        conditions.append("project_id = ?"); params.append(project_id)
    if note_id is not None:
        conditions.append("note_id = ?"); params.append(note_id)
    if provider:
        conditions.append("provider = ?"); params.append(provider)
    if since:
        conditions.append("created_at >= ?"); params.append(since)
    if until:
        conditions.append("created_at <= ?"); params.append(until)
    where = f"WHERE {' AND '.join(conditions)}"
    params += [limit, offset]
    rows = execute(
        f"SELECT * FROM timeline {where} ORDER BY id ASC LIMIT ? OFFSET ?",
        tuple(params),
    )
    for r in rows:
        try:
            r["payload"] = json.loads(r["payload"])
        except (TypeError, json.JSONDecodeError):
            pass
    return rows


def replay_project(project_id: int, user_id: Optional[str] = None) -> list[dict]:
    return query(project_id=project_id, limit=10000, user_id=user_id)


def recent(limit: int = 20, user_id: Optional[str] = None) -> list[dict]:
    oc, op = _timeline_owner_clause(user_id)
    rows = execute(
        f"SELECT * FROM timeline WHERE {oc} ORDER BY id DESC LIMIT ?",
        tuple(op + [limit]),
    )
    for r in rows:
        try:
            r["payload"] = json.loads(r["payload"])
        except (TypeError, json.JSONDecodeError):
            pass
    return list(reversed(rows))
