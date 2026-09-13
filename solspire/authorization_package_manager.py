"""Move 8 — Authorization package preparation (non-executable).

PREPARED ≠ AUTHORIZED TO EXECUTE.
execution_authorized is always false under Move 8.
No K15/K3 invocation occurs here.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB", "data/solspire_projects.db")
_ALLOWED_STATUS = {"PREPARED", "REFUSED", "SUPERSEDED", "UNKNOWN"}


@dataclass(frozen=True)
class AuthorizationPackage:
    package_id: str
    proposal_id: str
    subject_ref: str
    workspace_ref: str
    status: str
    execution_authorized: bool
    auto_execute: bool
    k15_invoked: bool
    k3_invoked: bool
    merge_authorized: bool
    deploy_authorized: bool
    intended_scope: str
    notes: str
    schema_version: str
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS authorization_packages (
            package_id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_authorized INTEGER NOT NULL,
            auto_execute INTEGER NOT NULL,
            k15_invoked INTEGER NOT NULL,
            k3_invoked INTEGER NOT NULL,
            merge_authorized INTEGER NOT NULL,
            deploy_authorized INTEGER NOT NULL,
            intended_scope TEXT NOT NULL,
            notes TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_pkg_subject "
        "ON authorization_packages(subject_ref, proposal_id)"
    )
    conn.commit()
    return conn


def _row_to_package(row: sqlite3.Row) -> AuthorizationPackage:
    return AuthorizationPackage(
        package_id=row["package_id"],
        proposal_id=row["proposal_id"],
        subject_ref=row["subject_ref"],
        workspace_ref=row["workspace_ref"],
        status=row["status"],
        execution_authorized=bool(row["execution_authorized"]),
        auto_execute=bool(row["auto_execute"]),
        k15_invoked=bool(row["k15_invoked"]),
        k3_invoked=bool(row["k3_invoked"]),
        merge_authorized=bool(row["merge_authorized"]),
        deploy_authorized=bool(row["deploy_authorized"]),
        intended_scope=row["intended_scope"] or "",
        notes=row["notes"] or "",
        schema_version=row["schema_version"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


class AuthorizationPackageManager:
    def prepare(
        self,
        *,
        proposal_id: str,
        subject_ref: str,
        workspace_ref: str,
        intended_scope: str = "",
        notes: str = "",
        execution_authorized: bool | None = None,
    ) -> AuthorizationPackage:
        subject = (subject_ref or "").strip()
        if not subject:
            raise ValueError("subject_ref is required")
        if execution_authorized is True:
            raise ValueError(
                "execution_authorized must remain false; Move 8 refuses elevated packages"
            )

        now = time.time()
        package = AuthorizationPackage(
            package_id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            subject_ref=subject,
            workspace_ref=workspace_ref,
            status="PREPARED",
            execution_authorized=False,
            auto_execute=False,
            k15_invoked=False,
            k3_invoked=False,
            merge_authorized=False,
            deploy_authorized=False,
            intended_scope=intended_scope or "",
            notes=notes or "",
            schema_version="1",
            created_at=now,
            updated_at=now,
        )
        if package.status not in _ALLOWED_STATUS:
            raise ValueError("invalid package status")

        conn = _db()
        try:
            conn.execute(
                """
                INSERT INTO authorization_packages (
                    package_id, proposal_id, subject_ref, workspace_ref, status,
                    execution_authorized, auto_execute, k15_invoked, k3_invoked,
                    merge_authorized, deploy_authorized, intended_scope, notes,
                    schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    package.package_id,
                    package.proposal_id,
                    package.subject_ref,
                    package.workspace_ref,
                    package.status,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    package.intended_scope,
                    package.notes,
                    package.schema_version,
                    package.created_at,
                    package.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return package

    def get(self, package_id: str, subject_ref: str) -> AuthorizationPackage | None:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT * FROM authorization_packages WHERE package_id = ? AND subject_ref = ?",
                (package_id, subject_ref),
            ).fetchone()
        finally:
            conn.close()
        return _row_to_package(row) if row else None

    def list_for_proposal(
        self, proposal_id: str, subject_ref: str
    ) -> list[AuthorizationPackage]:
        conn = _db()
        try:
            rows = conn.execute(
                """
                SELECT * FROM authorization_packages
                WHERE proposal_id = ? AND subject_ref = ?
                ORDER BY created_at DESC
                """,
                (proposal_id, subject_ref),
            ).fetchall()
        finally:
            conn.close()
        return [_row_to_package(row) for row in rows]


_MANAGER: AuthorizationPackageManager | None = None


def get_authorization_package_manager() -> AuthorizationPackageManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = AuthorizationPackageManager()
    return _MANAGER


__all__ = [
    "AuthorizationPackage",
    "AuthorizationPackageManager",
    "get_authorization_package_manager",
]
