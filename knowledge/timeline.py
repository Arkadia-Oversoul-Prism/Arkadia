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
) -> int:
    """
    Append an immutable event to the timeline.
    Returns the new event id.
    NEVER update or delete timeline rows — the timeline is sacred.
    """
    if event_type not in EVENT_TYPES:
        # Allow unknown types (extensible), but log a warning
        pass

    now = datetime.now(timezone.utc).isoformat()
    execute(
        """
        INSERT INTO timeline (event_type, payload, note_id, project_id, provider, persona, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (event_type, json.dumps(payload), note_id, project_id, provider, persona, now),
    )
    return last_insert_id()


def get_event(event_id: int) -> Optional[dict]:
    row = execute_one("SELECT * FROM timeline WHERE id = ?", (event_id,))
    if row:
        row["payload"] = json.loads(row["payload"])
    return row


def query(
    event_type: Optional[str] = None,
    project_id: Optional[int] = None,
    note_id: Optional[int] = None,
    provider: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    conditions: list[str] = []
    params: list = []

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

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
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


def replay_project(project_id: int) -> list[dict]:
    """Return the full ordered event stream for a project — the complete replay."""
    return query(project_id=project_id, limit=10000)


def recent(limit: int = 20) -> list[dict]:
    """Most recent events across all projects."""
    rows = execute(
        "SELECT * FROM timeline ORDER BY id DESC LIMIT ?", (limit,)
    )
    for r in rows:
        try:
            r["payload"] = json.loads(r["payload"])
        except (TypeError, json.JSONDecodeError):
            pass
    return list(reversed(rows))
