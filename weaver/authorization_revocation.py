"""Durable authorization revocation and the Weaver dispatch guard — Gate 1C.

This closes the identified hard blocker: `ew_authorizations.expires_at` existed
but was not enforced at the dispatch boundary, and the execution adapter had no
final revocation check. An authorization that had not expired was therefore
usable even after the delegation behind it was revoked.

Design constraints honoured here:
  * revocation is a durable, append-only record — not a deleted row, not a
    hidden UI button, not a JWT expiry
  * the check runs at the *last responsible boundary*, immediately before
    dispatch, not only when the authorization was created
  * a missing or unreadable revocation store denies (fail-closed)
  * this module adds no approval engine and no execution path; it only refuses
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)


def _now() -> float:
    return time.time()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ew_authorization_revocations (
            revocation_id TEXT PRIMARY KEY,
            authorization_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            delegation_id TEXT,
            reason TEXT NOT NULL,
            revoked_by TEXT NOT NULL,
            revoked_at REAL NOT NULL,
            correlation_id TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ew_auth_revocation_auth
            ON ew_authorization_revocations(authorization_id);
        CREATE INDEX IF NOT EXISTS idx_ew_auth_revocation_delegation
            ON ew_authorization_revocations(delegation_id);
        """
    )
    # Additive column: which delegation (if any) an authorization was issued
    # under. Existing rows keep NULL, which is correct — they predate the
    # executive delegation model and are not agent-associated.
    #
    # The table may not exist yet: this store can be opened before the
    # enterprise orchestration store has created its schema. In that case there
    # is nothing to migrate, and the column is added when the table appears.
    table_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ew_authorizations'"
    ).fetchone()
    if table_exists:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(ew_authorizations)").fetchall()}
        if "delegation_id" not in columns:
            conn.execute("ALTER TABLE ew_authorizations ADD COLUMN delegation_id TEXT")
    conn.commit()
    return conn


class AuthorizationRevoked(PermissionError):
    """Raised when an authorization is revoked, expired, or unverifiable."""


class AuthorizationRevocationStore:
    """Durable revocation ledger for enterprise Authorizations."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        if self._db_path:
            global _DB_PATH
            _DB_PATH = self._db_path
        return _db()

    def revoke(
        self,
        *,
        authorization_id: str,
        subject: str,
        reason: str,
        revoked_by: str,
        delegation_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        revocation_id = _id("ewrev")
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO ew_authorization_revocations
                   (revocation_id, authorization_id, subject, delegation_id,
                    reason, revoked_by, revoked_at, correlation_id)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    revocation_id,
                    authorization_id,
                    subject,
                    delegation_id,
                    reason,
                    revoked_by,
                    _now(),
                    correlation_id or _id("ewcid"),
                ),
            )
        return {
            "revocation_id": revocation_id,
            "authorization_id": authorization_id,
            "subject": subject,
            "delegation_id": delegation_id,
            "reason": reason,
            "revoked_by": revoked_by,
        }

    def is_revoked(self, authorization_id: str) -> bool:
        """True when a durable revocation exists. Unreadable store → deny."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT 1 FROM ew_authorization_revocations WHERE authorization_id=? LIMIT 1",
                    (authorization_id,),
                ).fetchone()
        except sqlite3.Error:
            return True
        return row is not None

    def revoke_for_delegation(self, *, delegation_id: str, reason: str, revoked_by: str) -> int:
        """Revoke every outstanding authorization issued under a delegation.

        Returns the number of authorizations newly revoked. Idempotent: an
        already-revoked authorization is not recorded twice.
        """
        with self._connect() as conn:
            # The enterprise schema may not exist yet (this store can be opened
            # first). No table means no outstanding authorizations to withdraw.
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ew_authorizations'"
            ).fetchone()
            if not table_exists:
                return 0
            rows = conn.execute(
                "SELECT id, subject FROM ew_authorizations WHERE delegation_id=?",
                (delegation_id,),
            ).fetchall()
            already = {
                row["authorization_id"]
                for row in conn.execute(
                    "SELECT authorization_id FROM ew_authorization_revocations WHERE delegation_id=?",
                    (delegation_id,),
                ).fetchall()
            }
            count = 0
            for row in rows:
                if row["id"] in already:
                    continue
                conn.execute(
                    """INSERT INTO ew_authorization_revocations
                       (revocation_id, authorization_id, subject, delegation_id,
                        reason, revoked_by, revoked_at, correlation_id)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        _id("ewrev"),
                        row["id"],
                        row["subject"],
                        delegation_id,
                        reason,
                        revoked_by,
                        _now(),
                        _id("ewcid"),
                    ),
                )
                count += 1
        return count

    def revocations(self, authorization_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ew_authorization_revocations WHERE authorization_id=? ORDER BY revoked_at",
                (authorization_id,),
            ).fetchall()
        return [dict(row) for row in rows]


def assert_dispatchable(
    *,
    authorization: Any,
    revocations: AuthorizationRevocationStore | None = None,
    now: float | None = None,
) -> None:
    """The final gate before a governed execution is dispatched.

    Raises AuthorizationRevoked (a PermissionError) on any failure. Called by
    the Weaver console adapter immediately before the sandbox runs, so an
    authorization cannot survive revocation merely because it has not expired.
    """
    if authorization is None:
        raise AuthorizationRevoked("authorization required before dispatch")

    expires_at = getattr(authorization, "expires_at", None)
    if expires_at is not None and float(expires_at) <= float(now if now is not None else _now()):
        raise AuthorizationRevoked("authorization has expired")

    store = revocations or AuthorizationRevocationStore()
    authorization_id = str(getattr(authorization, "id", "") or "")
    if not authorization_id:
        raise AuthorizationRevoked("authorization has no identifier")
    if store.is_revoked(authorization_id):
        raise AuthorizationRevoked("authorization has been revoked")


__all__ = [
    "AuthorizationRevoked",
    "AuthorizationRevocationStore",
    "assert_dispatchable",
]
