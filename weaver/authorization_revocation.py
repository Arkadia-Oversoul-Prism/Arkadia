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


def _delegation_denial_reason(delegation: Any, *, authorization: Any, at: float) -> str | None:
    """Why a linked delegation forbids dispatch, or None when it permits it.

    This is deliberately independent of the revocation ledger. The cascade in
    `executive_office.revocation` revokes the delegation first and then writes
    authorization revocations; if that second write fails, the ledger has no
    record and the authorization would otherwise look clean. Re-reading the
    delegation here closes that window: the delegation's own status, expiry and
    credential epoch are authoritative.
    """
    status = str(getattr(delegation, "status", "") or "").upper()
    if status != "ACTIVE":
        return f"delegation is {status.lower() or 'unavailable'}"

    delegation_expires = getattr(delegation, "expires_at", None)
    if delegation_expires is not None and float(delegation_expires) <= at:
        return "delegation has expired"

    effective_from = getattr(delegation, "effective_from", None)
    if effective_from is not None and float(effective_from) > at:
        return "delegation is not yet effective"

    # Credential epoch supersession: a suspend/revoke bumps the delegation's
    # epoch. An authorization stamped with an older epoch is dead even if its
    # own expires_at has not passed.
    #
    # A NULL issued epoch is NOT "no restriction". An authorization that names a
    # delegation but carries no epoch cannot prove which credential generation
    # it was issued under, so it must be treated as superseded. Without this,
    # any row written before the column existed — or written by a caller that
    # bypassed the auto-stamp — would silently skip the check entirely.
    issued_epoch = getattr(authorization, "delegation_epoch", None)
    current_epoch = getattr(delegation, "credential_epoch", None)
    if issued_epoch is None:
        return "delegation credential epoch missing on authorization"
    if current_epoch is not None and int(issued_epoch) != int(current_epoch):
        return "delegation credential epoch superseded"

    return None


def assert_dispatchable(
    *,
    authorization: Any,
    revocations: AuthorizationRevocationStore | None = None,
    registry: Any | None = None,
    now: float | None = None,
) -> None:
    """The final gate before a governed execution is dispatched.

    Raises AuthorizationRevoked (a PermissionError) on any failure. Called by
    the Weaver console adapter immediately before the sandbox runs, so an
    authorization cannot survive revocation merely because it has not expired.

    Three independent checks, all fail-closed:

      1. the authorization's own expiry;
      2. a durable authorization revocation record;
      3. for an authorization linked to an executive delegation, the
         delegation's *current* status, expiry and credential epoch, re-read
         from the registry at dispatch time.

    Check 3 exists because the revocation cascade can partially fail: the
    delegation is committed to REVOKED before the authorization revocations are
    written, so a failure in between leaves no ledger record. Re-reading the
    delegation makes that window harmless.
    """
    if authorization is None:
        raise AuthorizationRevoked("authorization required before dispatch")

    at = float(now if now is not None else _now())

    expires_at = getattr(authorization, "expires_at", None)
    if expires_at is not None and float(expires_at) <= at:
        raise AuthorizationRevoked("authorization has expired")

    store = revocations or AuthorizationRevocationStore()
    authorization_id = str(getattr(authorization, "id", "") or "")
    if not authorization_id:
        raise AuthorizationRevoked("authorization has no identifier")
    if store.is_revoked(authorization_id):
        raise AuthorizationRevoked("authorization has been revoked")

    # ── Delegation re-read (independent of the revocation ledger) ────────────
    delegation_id = getattr(authorization, "delegation_id", None)
    if not delegation_id:
        # Not agent-associated: the two checks above are the whole contract.
        return

    if registry is None:
        # Imported lazily so this module stays importable without the executive
        # package, and so a missing registry is a denial rather than a crash.
        from executive_office.registry import DelegationRegistry

        registry = DelegationRegistry()

    try:
        delegation = registry.get(str(delegation_id))
    except Exception as exc:  # noqa: BLE001 - any read failure must deny
        # Unknown delegation, unreadable store, corrupt row: all deny. A
        # missing record is not "no restriction", it is "cannot prove the
        # authority still exists".
        raise AuthorizationRevoked(
            f"delegation could not be verified: {type(exc).__name__}"
        ) from exc

    if delegation is None:
        raise AuthorizationRevoked("delegation record is missing")

    reason = _delegation_denial_reason(delegation, authorization=authorization, at=at)
    if reason:
        raise AuthorizationRevoked(reason)


__all__ = [
    "AuthorizationRevoked",
    "AuthorizationRevocationStore",
    "assert_dispatchable",
]
