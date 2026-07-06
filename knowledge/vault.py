"""
Arkadia Knowledge OS — Knowledge Vault
======================================
Canonical CRUD for notes. Every note is Markdown on disk + a SQLite record.
LAW III: Markdown is the human format. SQLite is the machine format.
"""

import hashlib
import json
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from knowledge.db import execute, execute_one, last_insert_id

VAULT_ROOT = Path("vault")

NoteType = Literal[
    "note", "conversation", "research", "book", "person", "idea", "decision", "daily"
]

# Maps note_type → vault subdirectory
TYPE_TO_DIR: dict[str, str] = {
    "note":         "Ideas",
    "conversation": "Projects",
    "research":     "Research",
    "book":         "Books",
    "person":       "People",
    "idea":         "Ideas",
    "decision":     "Projects",
    "daily":        "Daily",
}

RELATIONSHIP_TYPES = [
    "references", "extends", "contradicts", "summarizes",
    "implements", "belongs_to", "generated_by", "reviewed_by", "derived_from",
]


# ─────────────────────────────────────────────────────────────────────────────
# Note metadata header (YAML-like, written into every Markdown file)
# ─────────────────────────────────────────────────────────────────────────────

def _build_frontmatter(note: dict) -> str:
    return f"""---
id: {note['uuid']}
title: {note['title']}
created: {note['created_at']}
updated: {note['updated_at']}
type: {note['note_type']}
project: {note.get('project_uuid', '')}
thread: {note.get('thread_uuid', '')}
participants: {note['participants']}
tags: {note['tags']}
links: {note['links']}
embedding_status: {note['embedding_status']}
source_provider: {note.get('source_provider', '')}
---

"""


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Returns (metadata_dict, body_content)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end]
    body = text[end + 5:]
    meta: dict = {}
    for line in fm_block.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body


def _checksum(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def create_note(
    title: str,
    content: str,
    note_type: NoteType = "note",
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    participants: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    links: Optional[list[str]] = None,
    source_provider: Optional[str] = None,
) -> dict:
    """Create a note: write Markdown to vault, insert SQLite record."""
    now = datetime.now(timezone.utc).isoformat()
    note_uuid = str(_uuid.uuid4())
    participants_json = json.dumps(participants or [])
    tags_json = json.dumps(tags or [])
    links_json = json.dumps(links or [])

    # Resolve vault path
    subdir = TYPE_TO_DIR.get(note_type, "Ideas")
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:64]
    filename = f"{now[:10]}_{safe_title}_{note_uuid[:8]}.md"
    vault_path = f"{subdir}/{filename}"
    abs_path = VAULT_ROOT / vault_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    note_row = {
        "uuid": note_uuid,
        "title": title,
        "content": content,
        "vault_path": vault_path,
        "note_type": note_type,
        "project_id": project_id,
        "thread_id": thread_id,
        "participants": participants_json,
        "tags": tags_json,
        "links": links_json,
        "embedding_status": "pending",
        "graph_nodes": "[]",
        "checksum": _checksum(content),
        "source_provider": source_provider,
        "created_at": now,
        "updated_at": now,
        # helpers for frontmatter (not stored in db directly)
        "project_uuid": "",
        "thread_uuid": "",
    }

    # Write Markdown
    md = _build_frontmatter(note_row) + content
    abs_path.write_text(md, encoding="utf-8")

    # Insert SQLite record
    execute(
        """
        INSERT INTO notes
            (uuid, title, content, vault_path, note_type, project_id, thread_id,
             participants, tags, links, embedding_status, graph_nodes, checksum,
             source_provider, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            note_uuid, title, content, vault_path, note_type,
            project_id, thread_id,
            participants_json, tags_json, links_json,
            "pending", "[]", note_row["checksum"],
            source_provider, now, now,
        ),
    )

    note_row["id"] = last_insert_id()
    return note_row


def get_note(note_uuid: str) -> Optional[dict]:
    return execute_one("SELECT * FROM notes WHERE uuid = ?", (note_uuid,))


def get_note_by_id(note_id: int) -> Optional[dict]:
    return execute_one("SELECT * FROM notes WHERE id = ?", (note_id,))


def update_note(
    note_uuid: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[list[str]] = None,
    links: Optional[list[str]] = None,
    embedding_status: Optional[str] = None,
) -> Optional[dict]:
    note = get_note(note_uuid)
    if not note:
        return None

    now = datetime.now(timezone.utc).isoformat()
    updates: list[str] = ["updated_at = ?"]
    params: list = [now]

    if title is not None:
        updates.append("title = ?"); params.append(title)
    if content is not None:
        updates.append("content = ?"); params.append(content)
        updates.append("checksum = ?"); params.append(_checksum(content))
        updates.append("embedding_status = ?"); params.append("pending")
    if tags is not None:
        updates.append("tags = ?"); params.append(json.dumps(tags))
    if links is not None:
        updates.append("links = ?"); params.append(json.dumps(links))
    if embedding_status is not None:
        updates.append("embedding_status = ?"); params.append(embedding_status)

    params.append(note_uuid)
    execute(f"UPDATE notes SET {', '.join(updates)} WHERE uuid = ?", tuple(params))

    # Re-write Markdown on disk
    updated = get_note(note_uuid)
    if updated and (content is not None or title is not None):
        abs_path = VAULT_ROOT / updated["vault_path"]
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        md = _build_frontmatter({**updated, "project_uuid": "", "thread_uuid": ""}) + (
            content or updated["content"]
        )
        abs_path.write_text(md, encoding="utf-8")

    return get_note(note_uuid)


def list_notes(
    note_type: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conditions = []
    params: list = []
    if note_type:
        conditions.append("note_type = ?"); params.append(note_type)
    if project_id:
        conditions.append("project_id = ?"); params.append(project_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params += [limit, offset]
    return execute(
        f"SELECT * FROM notes {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params),
    )


def add_graph_edge(source_id: int, target_id: int, relationship: str, weight: float = 1.0) -> None:
    """
    Canonical graph edge write — delegates to knowledge.graph.add_edge.
    LAW I: One implementation. No duplicate logic.
    """
    from knowledge.graph import add_edge
    add_edge(source_id, target_id, relationship, weight)


def get_graph_neighbours(note_id: int, max_depth: int = 2) -> list[dict]:
    """BFS traversal — delegates to knowledge.graph.traverse."""
    from knowledge.graph import traverse
    result = traverse(note_id, max_depth=max_depth)
    return result["nodes"]


# ─────────────────────────────────────────────────────────────────────────────
# Project helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_project(name: str, description: str = "", tags: Optional[list[str]] = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    proj_uuid = str(_uuid.uuid4())
    tags_json = json.dumps(tags or [])
    execute(
        "INSERT INTO projects (uuid, name, description, tags, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (proj_uuid, name, description, tags_json, now, now),
    )
    return {"uuid": proj_uuid, "name": name, "description": description, "id": last_insert_id()}


def get_project(name_or_uuid: str) -> Optional[dict]:
    return execute_one(
        "SELECT * FROM projects WHERE uuid = ? OR name = ?",
        (name_or_uuid, name_or_uuid),
    )
