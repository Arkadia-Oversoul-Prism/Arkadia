"""Canonical SolSpire workspace persistence.

A workspace is the bounded container above projects. Identity is derived from
and bound to the verified Firebase uid supplied by the authenticated API
boundary. This module does not create authority, identity, provenance, memory,
or an alternate execution path.
"""
from __future__ import annotations

import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB", "data/solspire_projects.db")


@dataclass(frozen=True)
class Workspace:
    id: str
    workspace_type: str
    canonical_subject_ref: str
    display_name: str
    lifecycle: str
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            workspace_type TEXT NOT NULL,
            canonical_subject_ref TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            lifecycle TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


class WorkspaceManager:
    def get_or_create(self, subject_uid: str, display_name: str = "SolSpire Workspace") -> Workspace:
        subject_uid = (subject_uid or "").strip()
        if not subject_uid:
            raise ValueError("Canonical subject reference must not be empty")

        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM workspaces WHERE canonical_subject_ref=?",
                (subject_uid,),
            ).fetchone()
            if row:
                return self._from_row(row)

            now = time.time()
            workspace = Workspace(
                id=str(uuid.uuid4()),
                workspace_type="canonical_solspire",
                canonical_subject_ref=subject_uid,
                display_name=display_name.strip() or "SolSpire Workspace",
                lifecycle="active",
                created_at=now,
                updated_at=now,
            )
            conn.execute(
                """
                INSERT INTO workspaces
                    (id, workspace_type, canonical_subject_ref, display_name, lifecycle, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workspace.id,
                    workspace.workspace_type,
                    workspace.canonical_subject_ref,
                    workspace.display_name,
                    workspace.lifecycle,
                    workspace.created_at,
                    workspace.updated_at,
                ),
            )
            return workspace

    def get_for_subject(self, subject_uid: str) -> Workspace | None:
        subject_uid = (subject_uid or "").strip()
        if not subject_uid:
            return None
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM workspaces WHERE canonical_subject_ref=?",
                (subject_uid,),
            ).fetchone()
        return self._from_row(row) if row else None

    def count_for_subject(self, subject_uid: str) -> int:
        with _db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM workspaces WHERE canonical_subject_ref=?",
                ((subject_uid or "").strip(),),
            ).fetchone()
        return int(row["count"])

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Workspace:
        return Workspace(
            id=row["id"],
            workspace_type=row["workspace_type"],
            canonical_subject_ref=row["canonical_subject_ref"],
            display_name=row["display_name"],
            lifecycle=row["lifecycle"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


_GLOBAL_WM = WorkspaceManager()


def get_workspace_manager() -> WorkspaceManager:
    return _GLOBAL_WM


__all__ = ["Workspace", "WorkspaceManager", "get_workspace_manager"]
