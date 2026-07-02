"""SolSpire Console — ProjectManager (Milestone 1, SQLite-backed).

Contract:
    pm = ProjectManager()
    project = pm.create("Codex Editorial")
    project = pm.load(project_id)
    pm.archive(project_id)
    projects = pm.list_projects()
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("solspire.project_manager")

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB", "data/solspire_projects.db")


@dataclass
class Project:
    id: str
    name: str
    status: str
    created_at: float
    updated_at: float
    metadata: dict[str, Any] = field(default_factory=dict)
    conversations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'active',
            created_at   REAL NOT NULL,
            updated_at   REAL NOT NULL,
            metadata     TEXT NOT NULL DEFAULT '{}',
            conversations TEXT NOT NULL DEFAULT '[]'
        )
    """)
    conn.commit()
    return conn


class ProjectManager:
    def create(self, name: str, metadata: dict[str, Any] | None = None) -> Project:
        if not name or not name.strip():
            raise ValueError("Project name must not be empty")
        project = Project(
            id=str(uuid.uuid4()),
            name=name.strip(),
            status="active",
            created_at=time.time(),
            updated_at=time.time(),
            metadata=metadata or {},
            conversations=[],
        )
        with _db() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, status, created_at, updated_at, metadata, conversations) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project.id, project.name, project.status,
                 project.created_at, project.updated_at,
                 json.dumps(project.metadata), json.dumps(project.conversations)),
            )
        logger.info("ProjectManager: created project '%s' id=%s", project.name, project.id)
        return project

    def load(self, project_id: str) -> Project:
        with _db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise KeyError(f"Project '{project_id}' not found")
        return self._from_row(row)

    def archive(self, project_id: str) -> None:
        with _db() as conn:
            cur = conn.execute(
                "UPDATE projects SET status='archived', updated_at=? WHERE id=?",
                (time.time(), project_id),
            )
        if cur.rowcount == 0:
            raise KeyError(f"Project '{project_id}' not found")
        logger.info("ProjectManager: archived project id=%s", project_id)

    def list_projects(self, status: str | None = None) -> list[Project]:
        with _db() as conn:
            if status:
                rows = conn.execute("SELECT * FROM projects WHERE status=? ORDER BY updated_at DESC", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [self._from_row(r) for r in rows]

    def add_conversation(self, project_id: str, role: str, content: str) -> None:
        project = self.load(project_id)
        project.conversations.append({"role": role, "content": content, "ts": time.time()})
        with _db() as conn:
            conn.execute(
                "UPDATE projects SET conversations=?, updated_at=? WHERE id=?",
                (json.dumps(project.conversations), time.time(), project_id),
            )

    def _from_row(self, row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"] or "{}"),
            conversations=json.loads(row["conversations"] or "[]"),
        )


_GLOBAL_PM = ProjectManager()


def get_project_manager() -> ProjectManager:
    return _GLOBAL_PM


__all__ = ["Project", "ProjectManager", "get_project_manager"]
