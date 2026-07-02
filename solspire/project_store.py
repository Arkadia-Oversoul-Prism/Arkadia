"""SolSpire — Project Sub-Resource Store.

Adds per-project tables: files, repositories, tasks, memory, events, conversations.
All tables live in the same SQLite DB as projects (data/solspire_projects.db).
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import uuid
from typing import Any

logger = logging.getLogger("solspire.project_store")

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB", "data/solspire_projects.db")


# ── DB init ───────────────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _migrate(conn)
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_conversations (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            title       TEXT NOT NULL DEFAULT 'Untitled',
            status      TEXT NOT NULL DEFAULT 'active',
            messages    TEXT NOT NULL DEFAULT '[]',
            created_at  REAL NOT NULL,
            updated_at  REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_files (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            name        TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            mime_type   TEXT NOT NULL DEFAULT 'text/plain',
            created_at  REAL NOT NULL,
            updated_at  REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_repositories (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            owner       TEXT NOT NULL,
            repo        TEXT NOT NULL,
            branch      TEXT NOT NULL DEFAULT 'main',
            label       TEXT NOT NULL DEFAULT '',
            created_at  REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_tasks (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status      TEXT NOT NULL DEFAULT 'open',
            assigned_to TEXT NOT NULL DEFAULT '',
            priority    TEXT NOT NULL DEFAULT 'normal',
            created_at  REAL NOT NULL,
            updated_at  REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_memory (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            tags        TEXT NOT NULL DEFAULT '[]',
            created_at  REAL NOT NULL,
            updated_at  REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_events (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            summary     TEXT NOT NULL,
            data        TEXT NOT NULL DEFAULT '{}',
            created_at  REAL NOT NULL
        )
    """)


# ── Event helper ──────────────────────────────────────────────────────────────

def log_event(project_id: str, event_type: str, summary: str, data: dict | None = None) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT INTO project_events (id, project_id, event_type, summary, data, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), project_id, event_type, summary, json.dumps(data or {}), time.time()),
        )


# ── Conversations ─────────────────────────────────────────────────────────────

def list_conversations(project_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM project_conversations WHERE project_id=? ORDER BY updated_at DESC",
            (project_id,)
        ).fetchall()
    return [_conv_row(r) for r in rows]


def create_conversation(project_id: str, title: str) -> dict:
    cid = str(uuid.uuid4())
    now = time.time()
    with _db() as conn:
        conn.execute(
            "INSERT INTO project_conversations (id,project_id,title,status,messages,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (cid, project_id, title or "Untitled", "active", "[]", now, now)
        )
    log_event(project_id, "conversation_created", f"New conversation: {title}")
    return {"id": cid, "project_id": project_id, "title": title, "status": "active", "messages": [], "created_at": now, "updated_at": now}


def get_conversation(conv_id: str) -> dict | None:
    with _db() as conn:
        row = conn.execute("SELECT * FROM project_conversations WHERE id=?", (conv_id,)).fetchone()
    return _conv_row(row) if row else None


def append_message(conv_id: str, role: str, content: str) -> dict:
    with _db() as conn:
        row = conn.execute("SELECT * FROM project_conversations WHERE id=?", (conv_id,)).fetchone()
        if not row:
            raise KeyError(f"Conversation {conv_id} not found")
        msgs = json.loads(row["messages"] or "[]")
        msgs.append({"role": role, "content": content, "ts": time.time()})
        conn.execute("UPDATE project_conversations SET messages=?,updated_at=? WHERE id=?",
                     (json.dumps(msgs), time.time(), conv_id))
    return {"ok": True}


def archive_conversation(conv_id: str) -> None:
    with _db() as conn:
        conn.execute("UPDATE project_conversations SET status='archived',updated_at=? WHERE id=?",
                     (time.time(), conv_id))


def _conv_row(r) -> dict:
    return {"id": r["id"], "project_id": r["project_id"], "title": r["title"],
            "status": r["status"], "messages": json.loads(r["messages"] or "[]"),
            "created_at": r["created_at"], "updated_at": r["updated_at"]}


# ── Files ─────────────────────────────────────────────────────────────────────

def list_files(project_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT id,project_id,name,mime_type,length(content) as size,created_at,updated_at FROM project_files WHERE project_id=? ORDER BY updated_at DESC",
            (project_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def create_file(project_id: str, name: str, content: str, mime_type: str = "text/plain") -> dict:
    fid = str(uuid.uuid4())
    now = time.time()
    with _db() as conn:
        conn.execute(
            "INSERT INTO project_files (id,project_id,name,content,mime_type,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (fid, project_id, name, content, mime_type, now, now)
        )
    log_event(project_id, "file_created", f"New file: {name}")
    return {"id": fid, "project_id": project_id, "name": name, "size": len(content), "mime_type": mime_type, "created_at": now, "updated_at": now}


def get_file(file_id: str) -> dict | None:
    with _db() as conn:
        row = conn.execute("SELECT * FROM project_files WHERE id=?", (file_id,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "project_id": row["project_id"], "name": row["name"],
            "content": row["content"], "mime_type": row["mime_type"],
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def update_file(file_id: str, content: str, name: str | None = None) -> dict:
    with _db() as conn:
        if name:
            conn.execute("UPDATE project_files SET content=?,name=?,updated_at=? WHERE id=?",
                         (content, name, time.time(), file_id))
        else:
            conn.execute("UPDATE project_files SET content=?,updated_at=? WHERE id=?",
                         (content, time.time(), file_id))
    return {"ok": True}


def delete_file(file_id: str) -> bool:
    with _db() as conn:
        c = conn.execute("DELETE FROM project_files WHERE id=?", (file_id,))
    return c.rowcount > 0


# ── Repositories ──────────────────────────────────────────────────────────────

def list_repositories(project_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM project_repositories WHERE project_id=? ORDER BY created_at DESC",
            (project_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def link_repository(project_id: str, owner: str, repo: str, branch: str = "main", label: str = "") -> dict:
    rid = str(uuid.uuid4())
    now = time.time()
    with _db() as conn:
        conn.execute(
            "INSERT INTO project_repositories (id,project_id,owner,repo,branch,label,created_at) VALUES (?,?,?,?,?,?,?)",
            (rid, project_id, owner, repo, branch, label or f"{owner}/{repo}", now)
        )
    log_event(project_id, "repo_linked", f"Linked repo: {owner}/{repo}@{branch}")
    return {"id": rid, "project_id": project_id, "owner": owner, "repo": repo, "branch": branch, "label": label, "created_at": now}


def unlink_repository(repo_id: str) -> bool:
    with _db() as conn:
        c = conn.execute("DELETE FROM project_repositories WHERE id=?", (repo_id,))
    return c.rowcount > 0


# ── Tasks ─────────────────────────────────────────────────────────────────────

def list_tasks(project_id: str, status: str | None = None) -> list[dict]:
    with _db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM project_tasks WHERE project_id=? AND status=? ORDER BY created_at DESC",
                (project_id, status)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM project_tasks WHERE project_id=? ORDER BY created_at DESC",
                (project_id,)
            ).fetchall()
    return [dict(r) for r in rows]


def create_task(project_id: str, title: str, description: str = "",
                assigned_to: str = "", priority: str = "normal") -> dict:
    tid = str(uuid.uuid4())
    now = time.time()
    with _db() as conn:
        conn.execute(
            "INSERT INTO project_tasks (id,project_id,title,description,status,assigned_to,priority,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (tid, project_id, title, description, "open", assigned_to, priority, now, now)
        )
    log_event(project_id, "task_created", f"Task: {title}")
    return {"id": tid, "project_id": project_id, "title": title, "description": description,
            "status": "open", "assigned_to": assigned_to, "priority": priority,
            "created_at": now, "updated_at": now}


def update_task(task_id: str, **kwargs) -> dict:
    allowed = {"title", "description", "status", "assigned_to", "priority"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return {"ok": False, "error": "No valid fields"}
    fields["updated_at"] = time.time()
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [task_id]
    with _db() as conn:
        conn.execute(f"UPDATE project_tasks SET {sets} WHERE id=?", vals)
    return {"ok": True}


def delete_task(task_id: str) -> bool:
    with _db() as conn:
        c = conn.execute("DELETE FROM project_tasks WHERE id=?", (task_id,))
    return c.rowcount > 0


# ── Memory ────────────────────────────────────────────────────────────────────

def list_memory(project_id: str, q: str = "") -> list[dict]:
    with _db() as conn:
        if q:
            rows = conn.execute(
                "SELECT * FROM project_memory WHERE project_id=? AND (title LIKE ? OR content LIKE ?) ORDER BY updated_at DESC",
                (project_id, f"%{q}%", f"%{q}%")
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM project_memory WHERE project_id=? ORDER BY updated_at DESC",
                (project_id,)
            ).fetchall()
    return [_mem_row(r) for r in rows]


def add_memory(project_id: str, title: str, content: str, tags: list[str] | None = None) -> dict:
    mid = str(uuid.uuid4())
    now = time.time()
    with _db() as conn:
        conn.execute(
            "INSERT INTO project_memory (id,project_id,title,content,tags,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (mid, project_id, title, content, json.dumps(tags or []), now, now)
        )
    log_event(project_id, "memory_added", f"Memory: {title}")
    return {"id": mid, "project_id": project_id, "title": title, "content": content,
            "tags": tags or [], "created_at": now, "updated_at": now}


def update_memory(mem_id: str, title: str | None = None, content: str | None = None,
                  tags: list[str] | None = None) -> dict:
    with _db() as conn:
        row = conn.execute("SELECT * FROM project_memory WHERE id=?", (mem_id,)).fetchone()
        if not row:
            return {"ok": False}
        conn.execute(
            "UPDATE project_memory SET title=?,content=?,tags=?,updated_at=? WHERE id=?",
            (title or row["title"], content or row["content"],
             json.dumps(tags) if tags is not None else row["tags"], time.time(), mem_id)
        )
    return {"ok": True}


def delete_memory(mem_id: str) -> bool:
    with _db() as conn:
        c = conn.execute("DELETE FROM project_memory WHERE id=?", (mem_id,))
    return c.rowcount > 0


def _mem_row(r) -> dict:
    return {"id": r["id"], "project_id": r["project_id"], "title": r["title"],
            "content": r["content"], "tags": json.loads(r["tags"] or "[]"),
            "created_at": r["created_at"], "updated_at": r["updated_at"]}


# ── Events ────────────────────────────────────────────────────────────────────

def list_events(project_id: str, event_type: str | None = None, limit: int = 100) -> list[dict]:
    with _db() as conn:
        if event_type:
            rows = conn.execute(
                "SELECT * FROM project_events WHERE project_id=? AND event_type=? ORDER BY created_at DESC LIMIT ?",
                (project_id, event_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM project_events WHERE project_id=? ORDER BY created_at DESC LIMIT ?",
                (project_id, limit)
            ).fetchall()
    return [_evt_row(r) for r in rows]


def _evt_row(r) -> dict:
    return {"id": r["id"], "project_id": r["project_id"], "event_type": r["event_type"],
            "summary": r["summary"], "data": json.loads(r["data"] or "{}"),
            "created_at": r["created_at"]}


__all__ = [
    "log_event",
    "list_conversations", "create_conversation", "get_conversation", "append_message", "archive_conversation",
    "list_files", "create_file", "get_file", "update_file", "delete_file",
    "list_repositories", "link_repository", "unlink_repository",
    "list_tasks", "create_task", "update_task", "delete_task",
    "list_memory", "add_memory", "update_memory", "delete_memory",
    "list_events",
]
