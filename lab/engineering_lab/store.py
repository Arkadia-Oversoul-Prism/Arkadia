"""EL-01 / EL-03 — durable Engineering Lab store.

Persistence reuses the *canonical shared* SolSpire SQLite database
(``SOLSPIRE_PROJECTS_DB`` / ``data/solspire_projects.db``) exactly as every
other owned primitive does. This is deliberate: the directive forbids a second
database or a parallel persistence system.

Ownership is enforced in every read: rows are scoped by ``subject_ref`` (the
verified Firebase uid). A missing row for a different subject is reported as
absent, not as a leak.

Authority is never persisted as an implication: an authorization row records
what a *human* authorized; no row in this store can be created by the substrate
to grant itself authority.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from .contracts import assert_transition_allowed, utc_now

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        _migrate(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


_MIGRATION_LOCK = threading.Lock()


def _migrate(conn: sqlite3.Connection) -> None:
    with _MIGRATION_LOCK:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS el_agents (
                agent_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL,
                role TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_agents_subject
                ON el_agents (subject_ref);

            CREATE TABLE IF NOT EXISTS el_sessions (
                session_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL,
                workspace_ref TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                state TEXT NOT NULL,
                objective TEXT NOT NULL DEFAULT '',
                repository_ref TEXT,
                authorization_ref TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_sessions_subject
                ON el_sessions (subject_ref, updated_at);

            CREATE TABLE IF NOT EXISTS el_runs (
                run_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                subject_ref TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                state TEXT NOT NULL,
                result_state TEXT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_runs_session
                ON el_runs (session_id);

            CREATE TABLE IF NOT EXISTS el_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                subject_ref TEXT NOT NULL,
                run_id TEXT,
                event_type TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                payload TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_events_session
                ON el_events (session_id, sequence);

            CREATE TABLE IF NOT EXISTS el_artifacts (
                artifact_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL,
                session_id TEXT NOT NULL,
                run_id TEXT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_artifacts_session
                ON el_artifacts (session_id);

            CREATE TABLE IF NOT EXISTS el_evidence (
                evidence_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL,
                workspace_ref TEXT NOT NULL,
                run_ref TEXT NOT NULL,
                state TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_evidence_run
                ON el_evidence (run_ref);

            CREATE TABLE IF NOT EXISTS el_automations (
                automation_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_automations_subject
                ON el_automations (subject_ref);

            CREATE TABLE IF NOT EXISTS el_automation_runs (
                automation_run_id TEXT PRIMARY KEY,
                automation_id TEXT NOT NULL,
                subject_ref TEXT NOT NULL,
                state TEXT NOT NULL,
                session_id TEXT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS el_authorizations (
                authorization_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL,
                scope_ref TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_el_authorizations_scope
                ON el_authorizations (scope_ref);
            """
        )


class EngineeringLabStore:
    """Owned, append-oriented persistence for the Engineering Lab substrate."""

    # -- agents ---------------------------------------------------------------

    def save_agent(self, agent: Any) -> dict[str, Any]:
        payload = agent.to_dict() if hasattr(agent, "to_dict") else dict(agent)
        with _db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO el_agents"
                " (agent_id, subject_ref, role, payload, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    payload["agent_id"],
                    payload.get("subject_ref", ""),
                    payload["role"],
                    json.dumps(payload),
                    payload["created_at"],
                ),
            )
        return payload

    def list_agents(self, subject_ref: str) -> list[dict[str, Any]]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT payload FROM el_agents WHERE subject_ref = ?"
                " ORDER BY created_at DESC",
                (subject_ref,),
            ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # -- sessions -------------------------------------------------------------

    def create_session(self, session: Any) -> dict[str, Any]:
        payload = session.to_dict()
        self._require_state(payload["state"])
        with _db() as conn:
            conn.execute(
                "INSERT INTO el_sessions"
                " (session_id, subject_ref, workspace_ref, agent_id, state,"
                "  objective, repository_ref, authorization_ref, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload["session_id"],
                    payload["subject_ref"],
                    payload["workspace_ref"],
                    payload["agent_id"],
                    payload["state"],
                    payload.get("objective", ""),
                    payload.get("repository_ref"),
                    payload.get("authorization_ref"),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
        return payload

    def get_session(self, session_id: str, subject_ref: str) -> dict[str, Any] | None:
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM el_sessions WHERE session_id = ? AND subject_ref = ?",
                (session_id, subject_ref),
            ).fetchone()
        return dict(row) if row else None

    def list_sessions(self, subject_ref: str, limit: int = 50) -> list[dict[str, Any]]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM el_sessions WHERE subject_ref = ?"
                " ORDER BY updated_at DESC LIMIT ?",
                (subject_ref, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def transition_session(
        self, session_id: str, subject_ref: str, target: str
    ) -> dict[str, Any]:
        """Move a session to *target*, enforcing AEAS section 5 legal transitions."""
        current = self.get_session(session_id, subject_ref)
        if current is None:
            raise KeyError(f"session '{session_id}' not found for subject")
        assert_transition_allowed(current["state"], target)
        now = utc_now()
        with _db() as conn:
            conn.execute(
                "UPDATE el_sessions SET state = ?, updated_at = ?"
                " WHERE session_id = ? AND subject_ref = ?",
                (target, now, session_id, subject_ref),
            )
        updated = self.get_session(session_id, subject_ref)
        assert updated is not None
        return updated

    # -- runs -----------------------------------------------------------------

    def create_run(self, run: Any) -> dict[str, Any]:
        payload = run.to_dict()
        with _db() as conn:
            conn.execute(
                "INSERT INTO el_runs"
                " (run_id, session_id, subject_ref, agent_id, state, result_state,"
                "  payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload["run_id"],
                    payload["session_id"],
                    run.subject_ref,
                    payload["agent_id"],
                    payload["state"],
                    payload.get("result_state"),
                    json.dumps(payload),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
        return payload

    def update_run(self, run_id: str, subject_ref: str, **fields: Any) -> dict[str, Any]:
        with _db() as conn:
            row = conn.execute(
                "SELECT payload FROM el_runs WHERE run_id = ? AND subject_ref = ?",
                (run_id, subject_ref),
            ).fetchone()
            if row is None:
                raise KeyError(f"run '{run_id}' not found for subject")
            payload = json.loads(row["payload"])
            payload.update(fields)
            payload["updated_at"] = utc_now()
            conn.execute(
                "UPDATE el_runs SET state = ?, result_state = ?, payload = ?, updated_at = ?"
                " WHERE run_id = ? AND subject_ref = ?",
                (
                    payload.get("state"),
                    payload.get("result_state"),
                    json.dumps(payload),
                    payload["updated_at"],
                    run_id,
                    subject_ref,
                ),
            )
        return payload

    def list_runs(self, session_id: str, subject_ref: str) -> list[dict[str, Any]]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT payload FROM el_runs WHERE session_id = ? AND subject_ref = ?"
                " ORDER BY created_at ASC",
                (session_id, subject_ref),
            ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # -- events ---------------------------------------------------------------

    def append_event(self, record: dict[str, Any], subject_ref: str) -> None:
        with _db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO el_events"
                " (event_id, session_id, subject_ref, run_id, event_type,"
                "  sequence, payload, timestamp_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["event_id"],
                    record["session_id"],
                    subject_ref,
                    record.get("run_id"),
                    record["event_type"],
                    record.get("sequence", 0),
                    json.dumps(record.get("payload", {})),
                    record["timestamp_utc"],
                ),
            )

    def list_events(
        self, session_id: str, subject_ref: str, limit: int = 500
    ) -> list[dict[str, Any]]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM el_events WHERE session_id = ? AND subject_ref = ?"
                " ORDER BY sequence ASC LIMIT ?",
                (session_id, subject_ref, limit),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "event_id": r["event_id"],
                    "session_id": r["session_id"],
                    "run_id": r["run_id"],
                    "event_type": r["event_type"],
                    "sequence": r["sequence"],
                    "payload": json.loads(r["payload"]),
                    "timestamp_utc": r["timestamp_utc"],
                }
            )
        return out

    # -- artifacts ------------------------------------------------------------

    def save_artifact(self, artifact: dict[str, Any], subject_ref: str) -> dict[str, Any]:
        with _db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO el_artifacts"
                " (artifact_id, subject_ref, session_id, run_id, kind, title,"
                "  payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    artifact["artifact_id"],
                    subject_ref,
                    artifact["session_id"],
                    artifact.get("run_id"),
                    artifact["kind"],
                    artifact["title"],
                    json.dumps(artifact),
                    artifact["created_at"],
                ),
            )
        return artifact

    def get_artifact(self, artifact_id: str, subject_ref: str) -> dict[str, Any] | None:
        with _db() as conn:
            row = conn.execute(
                "SELECT payload FROM el_artifacts WHERE artifact_id = ? AND subject_ref = ?",
                (artifact_id, subject_ref),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_artifacts(
        self, subject_ref: str, session_id: str | None = None
    ) -> list[dict[str, Any]]:
        with _db() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT payload FROM el_artifacts WHERE subject_ref = ?"
                    " AND session_id = ? ORDER BY created_at ASC",
                    (subject_ref, session_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT payload FROM el_artifacts WHERE subject_ref = ?"
                    " ORDER BY created_at ASC",
                    (subject_ref,),
                ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # -- evidence -------------------------------------------------------------

    def save_evidence(self, record: Any) -> dict[str, Any]:
        payload = record.to_dict()
        with _db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO el_evidence"
                " (evidence_id, subject_ref, workspace_ref, run_ref, state,"
                "  summary, payload, timestamp_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload["evidence_id"],
                    payload["subject_ref"],
                    payload["workspace_ref"],
                    payload["run_ref"],
                    payload["state"],
                    payload["summary"],
                    json.dumps(payload),
                    payload["timestamp_utc"],
                ),
            )
        return payload

    def list_evidence(self, subject_ref: str, run_ref: str | None = None) -> list[dict[str, Any]]:
        with _db() as conn:
            if run_ref:
                rows = conn.execute(
                    "SELECT payload FROM el_evidence WHERE subject_ref = ? AND run_ref = ?"
                    " ORDER BY timestamp_utc ASC",
                    (subject_ref, run_ref),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT payload FROM el_evidence WHERE subject_ref = ?"
                    " ORDER BY timestamp_utc ASC",
                    (subject_ref,),
                ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # -- automations (EL-03) --------------------------------------------------

    def create_automation(self, automation: dict[str, Any], subject_ref: str) -> dict[str, Any]:
        now = utc_now()
        with _db() as conn:
            conn.execute(
                "INSERT INTO el_automations"
                " (automation_id, subject_ref, name, state, payload, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    automation["automation_id"],
                    subject_ref,
                    automation["name"],
                    automation["state"],
                    json.dumps(automation),
                    now,
                    now,
                ),
            )
        return automation

    def get_automation(self, automation_id: str, subject_ref: str) -> dict[str, Any] | None:
        with _db() as conn:
            row = conn.execute(
                "SELECT payload FROM el_automations WHERE automation_id = ? AND subject_ref = ?",
                (automation_id, subject_ref),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_automations(self, subject_ref: str) -> list[dict[str, Any]]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT payload FROM el_automations WHERE subject_ref = ?"
                " ORDER BY created_at DESC",
                (subject_ref,),
            ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def set_automation_state(
        self, automation_id: str, subject_ref: str, state: str
    ) -> dict[str, Any]:
        automation = self.get_automation(automation_id, subject_ref)
        if automation is None:
            raise KeyError(f"automation '{automation_id}' not found for subject")
        automation["state"] = state
        now = utc_now()
        with _db() as conn:
            conn.execute(
                "UPDATE el_automations SET state = ?, payload = ?, updated_at = ?"
                " WHERE automation_id = ? AND subject_ref = ?",
                (state, json.dumps(automation), now, automation_id, subject_ref),
            )
        return automation

    def record_automation_run(self, record: dict[str, Any], subject_ref: str) -> dict[str, Any]:
        record.setdefault("automation_run_id", f"EAR-{uuid.uuid4().hex[:12]}")
        record.setdefault("created_at", utc_now())
        with _db() as conn:
            conn.execute(
                "INSERT INTO el_automation_runs"
                " (automation_run_id, automation_id, subject_ref, state, session_id,"
                "  payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record["automation_run_id"],
                    record["automation_id"],
                    subject_ref,
                    record["state"],
                    record.get("session_id"),
                    json.dumps(record),
                    record["created_at"],
                ),
            )
        return record

    def list_automation_runs(
        self, automation_id: str, subject_ref: str
    ) -> list[dict[str, Any]]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT payload FROM el_automation_runs"
                " WHERE automation_id = ? AND subject_ref = ? ORDER BY created_at DESC",
                (automation_id, subject_ref),
            ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # -- authorizations -------------------------------------------------------

    def record_authorization(self, record: dict[str, Any], subject_ref: str) -> dict[str, Any]:
        """Record a *human-originated* authorization. Never self-created."""
        if record.get("originated_by") != "human":
            raise ValueError(
                "authorizations must be human-originated; the substrate may not "
                "originate authority"
            )
        with _db() as conn:
            conn.execute(
                "INSERT INTO el_authorizations"
                " (authorization_id, subject_ref, scope_ref, payload, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    record["authorization_id"],
                    subject_ref,
                    record["scope_ref"],
                    json.dumps(record),
                    record.get("created_at", utc_now()),
                ),
            )
        return record

    def get_authorization(self, authorization_id: str, subject_ref: str) -> dict[str, Any] | None:
        with _db() as conn:
            row = conn.execute(
                "SELECT payload FROM el_authorizations"
                " WHERE authorization_id = ? AND subject_ref = ?",
                (authorization_id, subject_ref),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def find_authorization_for_scope(
        self, scope_ref: str, subject_ref: str
    ) -> dict[str, Any] | None:
        with _db() as conn:
            row = conn.execute(
                "SELECT payload FROM el_authorizations"
                " WHERE scope_ref = ? AND subject_ref = ? ORDER BY created_at DESC LIMIT 1",
                (scope_ref, subject_ref),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    # -- helpers --------------------------------------------------------------

    @staticmethod
    def _require_state(state: str) -> None:
        from .contracts import CHECKPOINT_STATES

        if state not in CHECKPOINT_STATES:
            raise ValueError(f"unknown session state '{state}'")


_GLOBAL_STORE: EngineeringLabStore | None = None
_GLOBAL_STORE_LOCK = threading.Lock()


def get_store() -> EngineeringLabStore:
    global _GLOBAL_STORE
    with _GLOBAL_STORE_LOCK:
        if _GLOBAL_STORE is None:
            _GLOBAL_STORE = EngineeringLabStore()
        return _GLOBAL_STORE
