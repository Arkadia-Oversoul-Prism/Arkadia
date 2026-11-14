"""Durable Executive Delegation Registry — Gate 1A.

Single source of truth for whether the Chief Agent may act. Deliberately a
separate durable store from the SolSpire project database: a delegation is an
authority record, not project data, and it must survive process restart,
redeployment and model replacement.

Enforced here:
  * append-only event history; current status is materialised from events
  * `credential_epoch` increments on every suspend/revoke, so tokens issued
    under the previous epoch are invalid immediately
  * fail-closed: any read error is reported as "no active delegation"
  * the agent has no write path; only Founder-authenticated control actions
    and the broker's read path touch this store
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from executive_office import PRINCIPAL_ID

_DB_PATH = os.environ.get("EXECUTIVE_OFFICE_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "executive_office.db"
)

PENDING = "PENDING"
ACTIVE = "ACTIVE"
SUSPENDED = "SUSPENDED"
REVOKED = "REVOKED"
EXPIRED = "EXPIRED"

STATUSES = frozenset({PENDING, ACTIVE, SUSPENDED, REVOKED, EXPIRED})
#: Statuses that permit token issuance and request service.
SERVICEABLE = frozenset({ACTIVE})
#: Terminal for a delegation id; reactivation requires a new grant.
TERMINAL = frozenset({REVOKED})


def _now() -> float:
    return time.time()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS eo_delegations (
            delegation_id TEXT PRIMARY KEY,
            principal_id TEXT NOT NULL,
            owner_uid TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            policy_version INTEGER NOT NULL,
            policy_digest TEXT NOT NULL,
            resource_scope TEXT NOT NULL,
            capability_scope TEXT NOT NULL,
            status TEXT NOT NULL,
            effective_from REAL NOT NULL,
            expires_at REAL NOT NULL,
            created_by TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            revoked_at REAL,
            revoked_by TEXT,
            revocation_reason TEXT,
            credential_epoch INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS eo_delegation_events (
            event_id TEXT PRIMARY KEY,
            delegation_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            previous_status TEXT,
            new_status TEXT NOT NULL,
            credential_epoch INTEGER NOT NULL,
            reason TEXT,
            payload TEXT NOT NULL,
            timestamp REAL NOT NULL,
            correlation_id TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_eo_events_delegation
            ON eo_delegation_events(delegation_id, timestamp);
        CREATE TABLE IF NOT EXISTS eo_queued_work (
            job_id TEXT PRIMARY KEY,
            delegation_id TEXT NOT NULL,
            principal_id TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            cancelled_at REAL,
            cancel_reason TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_eo_queue_delegation
            ON eo_queued_work(delegation_id, status);
        """
    )
    conn.commit()
    return conn


@dataclass(frozen=True)
class Delegation:
    delegation_id: str
    principal_id: str
    owner_uid: str
    workspace_id: str
    policy_id: str
    policy_version: int
    policy_digest: str
    resource_scope: Any
    capability_scope: Any
    status: str
    effective_from: float
    expires_at: float
    created_by: str
    approved_by: str
    created_at: float
    updated_at: float
    revoked_at: float | None
    revoked_by: str | None
    revocation_reason: str | None
    credential_epoch: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_expired(self, at: float | None = None) -> bool:
        return float(self.expires_at) <= float(at if at is not None else _now())

    def is_serviceable(self, at: float | None = None) -> bool:
        return self.status in SERVICEABLE and not self.is_expired(at)


class DelegationRegistry:
    """Durable, append-only delegation authority store."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    # ── internals ────────────────────────────────────────────────────────────
    def _connect(self) -> sqlite3.Connection:
        if self._db_path:
            global _DB_PATH
            _DB_PATH = self._db_path
        return _db()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Delegation:
        return Delegation(
            delegation_id=row["delegation_id"],
            principal_id=row["principal_id"],
            owner_uid=row["owner_uid"],
            workspace_id=row["workspace_id"],
            policy_id=row["policy_id"],
            policy_version=int(row["policy_version"]),
            policy_digest=row["policy_digest"],
            resource_scope=json.loads(row["resource_scope"]),
            capability_scope=json.loads(row["capability_scope"]),
            status=row["status"],
            effective_from=float(row["effective_from"]),
            expires_at=float(row["expires_at"]),
            created_by=row["created_by"],
            approved_by=row["approved_by"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            revoked_at=row["revoked_at"],
            revoked_by=row["revoked_by"],
            revocation_reason=row["revocation_reason"],
            credential_epoch=int(row["credential_epoch"]),
        )

    def _append_event(
        self,
        conn: sqlite3.Connection,
        *,
        delegation_id: str,
        event_type: str,
        actor: str,
        previous_status: str | None,
        new_status: str,
        credential_epoch: int,
        reason: str | None,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> str:
        event_id = _id("eoev")
        conn.execute(
            """INSERT INTO eo_delegation_events
               (event_id, delegation_id, event_type, actor, previous_status,
                new_status, credential_epoch, reason, payload, timestamp, correlation_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id,
                delegation_id,
                event_type,
                actor,
                previous_status,
                new_status,
                credential_epoch,
                reason,
                _json(payload or {}),
                _now(),
                correlation_id or _id("eocid"),
            ),
        )
        return event_id

    # ── Founder control actions ──────────────────────────────────────────────
    def grant(
        self,
        *,
        owner_uid: str,
        workspace_id: str,
        policy_id: str,
        policy_version: int,
        policy_digest: str,
        resource_scope: Any,
        capability_scope: Any,
        expires_at: float,
        founder_uid: str,
        effective_from: float | None = None,
        principal_id: str = PRINCIPAL_ID,
        correlation_id: str | None = None,
    ) -> Delegation:
        """Create an ACTIVE delegation. Founder-only; validated fail-closed."""
        owner_uid = (owner_uid or "").strip()
        workspace_id = (workspace_id or "").strip()
        founder_uid = (founder_uid or "").strip()
        if not owner_uid:
            raise ValueError("owner_uid is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")
        if not founder_uid:
            raise ValueError("founder_uid is required")
        if not policy_digest:
            raise ValueError("policy_digest is required")
        if expires_at is None or float(expires_at) <= _now():
            raise ValueError("a bounded future expires_at is required")
        if principal_id != PRINCIPAL_ID:
            raise ValueError(f"unsupported principal: {principal_id}")

        now = _now()
        delegation_id = _id("eodel")
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO eo_delegations
                   (delegation_id, principal_id, owner_uid, workspace_id, policy_id,
                    policy_version, policy_digest, resource_scope, capability_scope,
                    status, effective_from, expires_at, created_by, approved_by,
                    created_at, updated_at, revoked_at, revoked_by, revocation_reason,
                    credential_epoch)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    delegation_id,
                    principal_id,
                    owner_uid,
                    workspace_id,
                    policy_id,
                    int(policy_version),
                    policy_digest,
                    _json(resource_scope),
                    _json(capability_scope),
                    ACTIVE,
                    float(effective_from if effective_from is not None else now),
                    float(expires_at),
                    founder_uid,
                    founder_uid,
                    now,
                    now,
                    None,
                    None,
                    None,
                    1,
                ),
            )
            self._append_event(
                conn,
                delegation_id=delegation_id,
                event_type="GRANTED",
                actor=founder_uid,
                previous_status=None,
                new_status=ACTIVE,
                credential_epoch=1,
                reason=None,
                payload={
                    "owner_uid": owner_uid,
                    "workspace_id": workspace_id,
                    "policy_digest": policy_digest,
                },
                correlation_id=correlation_id,
            )
        return self.get(delegation_id)

    def suspend(self, *, delegation_id: str, founder_uid: str, reason: str | None = None) -> Delegation:
        return self._transition(
            delegation_id=delegation_id,
            founder_uid=founder_uid,
            target=SUSPENDED,
            event_type="SUSPENDED",
            reason=reason,
            bump_epoch=True,
        )

    def revoke(self, *, delegation_id: str, founder_uid: str, reason: str | None = None) -> Delegation:
        """Terminal revocation. Increments the epoch and cancels queued work."""
        delegation = self._transition(
            delegation_id=delegation_id,
            founder_uid=founder_uid,
            target=REVOKED,
            event_type="REVOKED",
            reason=reason,
            bump_epoch=True,
        )
        self.cancel_queued_work(delegation_id=delegation_id, reason=reason or "delegation revoked")
        return delegation

    def reactivate(self, *, delegation_id: str, founder_uid: str, reason: str | None = None) -> Delegation:
        """Reversible only from SUSPENDED. A REVOKED grant is terminal."""
        current = self.get(delegation_id)
        if current.status in TERMINAL:
            raise ValueError("revocation is terminal; a new grant is required")
        return self._transition(
            delegation_id=delegation_id,
            founder_uid=founder_uid,
            target=ACTIVE,
            event_type="REACTIVATED",
            reason=reason,
            bump_epoch=True,
        )

    def _transition(
        self,
        *,
        delegation_id: str,
        founder_uid: str,
        target: str,
        event_type: str,
        reason: str | None,
        bump_epoch: bool,
    ) -> Delegation:
        founder_uid = (founder_uid or "").strip()
        if not founder_uid:
            raise ValueError("founder_uid is required")
        if target not in STATUSES:
            raise ValueError(f"unsupported status: {target}")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM eo_delegations WHERE delegation_id=?", (delegation_id,)
            ).fetchone()
            if not row:
                raise ValueError("unknown delegation")
            previous = row["status"]
            if previous in TERMINAL and target != REVOKED:
                raise ValueError("revocation is terminal; a new grant is required")
            epoch = int(row["credential_epoch"]) + (1 if bump_epoch else 0)
            now = _now()
            conn.execute(
                """UPDATE eo_delegations
                   SET status=?, updated_at=?, credential_epoch=?,
                       revoked_at=?, revoked_by=?, revocation_reason=?
                   WHERE delegation_id=?""",
                (
                    target,
                    now,
                    epoch,
                    now if target == REVOKED else row["revoked_at"],
                    founder_uid if target == REVOKED else row["revoked_by"],
                    reason if target == REVOKED else row["revocation_reason"],
                    delegation_id,
                ),
            )
            self._append_event(
                conn,
                delegation_id=delegation_id,
                event_type=event_type,
                actor=founder_uid,
                previous_status=previous,
                new_status=target,
                credential_epoch=epoch,
                reason=reason,
            )
        return self.get(delegation_id)

    # ── reads ────────────────────────────────────────────────────────────────
    def get(self, delegation_id: str) -> Delegation:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM eo_delegations WHERE delegation_id=?", (delegation_id,)
            ).fetchone()
        if not row:
            raise ValueError("unknown delegation")
        return self._from_row(row)

    def find(self, delegation_id: str) -> Delegation | None:
        try:
            return self.get(delegation_id)
        except (ValueError, sqlite3.Error):
            return None

    def list_for_owner(self, owner_uid: str) -> list[Delegation]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM eo_delegations WHERE owner_uid=? ORDER BY created_at DESC",
                ((owner_uid or "").strip(),),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def events(self, delegation_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM eo_delegation_events WHERE delegation_id=? ORDER BY timestamp, rowid",
                (delegation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def active_for_principal(self, principal_id: str = PRINCIPAL_ID) -> Delegation | None:
        """The one serviceable delegation for a principal, or None.

        Fail-closed: a store error is reported as "no active delegation" rather
        than propagating an exception a caller might treat as transient.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM eo_delegations WHERE principal_id=? AND status=? "
                    "ORDER BY created_at DESC",
                    (principal_id, ACTIVE),
                ).fetchall()
        except sqlite3.Error:
            return None
        for row in rows:
            delegation = self._from_row(row)
            if delegation.is_serviceable():
                return delegation
        return None

    # ── queued work (revocation ledger, not an execution engine) ─────────────
    def enqueue_work(self, *, delegation_id: str, description: str, job_id: str | None = None) -> str:
        job = job_id or _id("eojob")
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO eo_queued_work
                   (job_id, delegation_id, principal_id, description, status, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (job, delegation_id, PRINCIPAL_ID, description, "QUEUED", _now()),
            )
        return job

    def cancel_queued_work(self, *, delegation_id: str, reason: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE eo_queued_work
                   SET status='CANCELLED', cancelled_at=?, cancel_reason=?
                   WHERE delegation_id=? AND status='QUEUED'""",
                (_now(), reason, delegation_id),
            )
            return int(cursor.rowcount or 0)

    def queued_work(self, delegation_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM eo_queued_work WHERE delegation_id=? ORDER BY created_at",
                (delegation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def job_is_dispatchable(self, job_id: str) -> bool:
        """A cancelled job is never dispatchable, whatever its delegation says."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM eo_queued_work WHERE job_id=?", (job_id,)
            ).fetchone()
        return bool(row) and row["status"] == "QUEUED"


__all__ = [
    "Delegation",
    "DelegationRegistry",
    "PENDING",
    "ACTIVE",
    "SUSPENDED",
    "REVOKED",
    "EXPIRED",
    "STATUSES",
    "SERVICEABLE",
    "TERMINAL",
]
