"""Bounded WorkEvent persistence for the SolSpire continuity spine.

WorkEvents are inspectable continuity records bound to the authenticated
subject and that subject's canonical SolSpire workspace. They do not create
identity, authority, provenance, authorization, execution, memory authority,
or an alternate K15 -> K3 mutation path.
"""
from __future__ import annotations

import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

_ALLOWED_STATUS = {
    "PROPOSED", "OBSERVED", "RECORDED", "VERIFIED",
    "SUPERSEDED", "REVERSED", "DISPUTED", "UNKNOWN",
}


@dataclass(frozen=True)
class WorkEvent:
    work_event_id: str
    event_type: str
    event_version: int
    occurred_at: float
    recorded_at: float
    effective_from: float | None
    effective_until: float | None
    subject_ref: str
    workspace_ref: str
    work_ref: str | None
    parent_event_ref: str | None
    sequence_ref: str | None
    scope_ref: str | None
    actor_ref: str | None
    artifact_refs: list[str]
    state_before_ref: str | None
    state_after_ref: str | None
    decision_ref: str | None
    witness_ref: str | None
    status: str
    supersedes_ref: str | None
    reversal_of_ref: str | None
    created_by_event: str | None
    schema_version: str

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
        CREATE TABLE IF NOT EXISTS work_events (
            work_event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            event_version INTEGER NOT NULL,
            occurred_at REAL NOT NULL,
            recorded_at REAL NOT NULL,
            effective_from REAL,
            effective_until REAL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            work_ref TEXT,
            parent_event_ref TEXT,
            sequence_ref TEXT,
            scope_ref TEXT,
            actor_ref TEXT,
            artifact_refs TEXT NOT NULL DEFAULT '[]',
            state_before_ref TEXT,
            state_after_ref TEXT,
            decision_ref TEXT,
            witness_ref TEXT,
            status TEXT NOT NULL,
            supersedes_ref TEXT,
            reversal_of_ref TEXT,
            created_by_event TEXT,
            schema_version TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_events_subject ON work_events(subject_ref, recorded_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_work_events_workspace ON work_events(workspace_ref, recorded_at)"
    )
    conn.commit()
    return conn


class WorkEventManager:
    def create(
        self,
        *,
        subject_ref: str,
        workspace_ref: str,
        event_type: str,
        occurred_at: float,
        work_event_id: str | None = None,
        event_version: int = 1,
        effective_from: float | None = None,
        effective_until: float | None = None,
        work_ref: str | None = None,
        parent_event_ref: str | None = None,
        sequence_ref: str | None = None,
        scope_ref: str | None = None,
        actor_ref: str | None = None,
        artifact_refs: list[str] | None = None,
        state_before_ref: str | None = None,
        state_after_ref: str | None = None,
        decision_ref: str | None = None,
        witness_ref: str | None = None,
        status: str = "RECORDED",
        supersedes_ref: str | None = None,
        reversal_of_ref: str | None = None,
        created_by_event: str | None = None,
        schema_version: str = "1",
    ) -> WorkEvent:
        subject_ref = (subject_ref or "").strip()
        workspace_ref = (workspace_ref or "").strip()
        event_type = (event_type or "").strip()
        status = (status or "").strip().upper()
        if not subject_ref:
            raise ValueError("Subject reference must not be empty")
        if not workspace_ref:
            raise ValueError("Workspace reference must not be empty")
        if not event_type:
            raise ValueError("Event type must not be empty")
        if event_version < 1:
            raise ValueError("Event version must be positive")
        if status not in _ALLOWED_STATUS:
            raise ValueError(f"Unsupported WorkEvent status: {status}")
        if effective_from is not None and effective_until is not None and effective_from > effective_until:
            raise ValueError("effective_from must not be later than effective_until")
        if not isinstance(artifact_refs or [], list):
            raise ValueError("artifact_refs must be a list")

        event_id = (work_event_id or str(uuid.uuid4())).strip()
        if not event_id:
            raise ValueError("WorkEvent identity must not be empty")
        recorded_at = time.time()
        event = WorkEvent(
            work_event_id=event_id,
            event_type=event_type,
            event_version=event_version,
            occurred_at=float(occurred_at),
            recorded_at=recorded_at,
            effective_from=effective_from,
            effective_until=effective_until,
            subject_ref=subject_ref,
            workspace_ref=workspace_ref,
            work_ref=(work_ref or None),
            parent_event_ref=(parent_event_ref or None),
            sequence_ref=(sequence_ref or None),
            scope_ref=(scope_ref or None),
            actor_ref=(actor_ref or None),
            artifact_refs=list(artifact_refs or []),
            state_before_ref=(state_before_ref or None),
            state_after_ref=(state_after_ref or None),
            decision_ref=(decision_ref or None),
            witness_ref=(witness_ref or None),
            status=status,
            supersedes_ref=(supersedes_ref or None),
            reversal_of_ref=(reversal_of_ref or None),
            created_by_event=(created_by_event or None),
            schema_version=(schema_version or "1"),
        )
        import json
        with _db() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO work_events (
                        work_event_id, event_type, event_version, occurred_at, recorded_at,
                        effective_from, effective_until, subject_ref, workspace_ref, work_ref,
                        parent_event_ref, sequence_ref, scope_ref, actor_ref, artifact_refs,
                        state_before_ref, state_after_ref, decision_ref, witness_ref, status,
                        supersedes_ref, reversal_of_ref, created_by_event, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.work_event_id, event.event_type, event.event_version,
                        event.occurred_at, event.recorded_at, event.effective_from,
                        event.effective_until, event.subject_ref, event.workspace_ref,
                        event.work_ref, event.parent_event_ref, event.sequence_ref,
                        event.scope_ref, event.actor_ref, json.dumps(event.artifact_refs),
                        event.state_before_ref, event.state_after_ref, event.decision_ref,
                        event.witness_ref, event.status, event.supersedes_ref,
                        event.reversal_of_ref, event.created_by_event, event.schema_version,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("WorkEvent identity already exists") from exc
        return event

    def get(self, work_event_id: str, subject_ref: str) -> WorkEvent | None:
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM work_events WHERE work_event_id=? AND subject_ref=?",
                ((work_event_id or "").strip(), (subject_ref or "").strip()),
            ).fetchone()
        return self._from_row(row) if row else None

    def list(self, subject_ref: str, workspace_ref: str | None = None, limit: int = 100) -> list[WorkEvent]:
        subject_ref = (subject_ref or "").strip()
        if not subject_ref:
            return []
        limit = max(1, min(int(limit), 500))
        with _db() as conn:
            if workspace_ref:
                rows = conn.execute(
                    "SELECT * FROM work_events WHERE subject_ref=? AND workspace_ref=? ORDER BY recorded_at ASC LIMIT ?",
                    (subject_ref, workspace_ref.strip(), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM work_events WHERE subject_ref=? ORDER BY recorded_at ASC LIMIT ?",
                    (subject_ref, limit),
                ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> WorkEvent:
        import json
        return WorkEvent(
            work_event_id=row["work_event_id"],
            event_type=row["event_type"],
            event_version=row["event_version"],
            occurred_at=row["occurred_at"],
            recorded_at=row["recorded_at"],
            effective_from=row["effective_from"],
            effective_until=row["effective_until"],
            subject_ref=row["subject_ref"],
            workspace_ref=row["workspace_ref"],
            work_ref=row["work_ref"],
            parent_event_ref=row["parent_event_ref"],
            sequence_ref=row["sequence_ref"],
            scope_ref=row["scope_ref"],
            actor_ref=row["actor_ref"],
            artifact_refs=json.loads(row["artifact_refs"]),
            state_before_ref=row["state_before_ref"],
            state_after_ref=row["state_after_ref"],
            decision_ref=row["decision_ref"],
            witness_ref=row["witness_ref"],
            status=row["status"],
            supersedes_ref=row["supersedes_ref"],
            reversal_of_ref=row["reversal_of_ref"],
            created_by_event=row["created_by_event"],
            schema_version=row["schema_version"],
        )


_GLOBAL_WEM = WorkEventManager()


def get_workevent_manager() -> WorkEventManager:
    return _GLOBAL_WEM


__all__ = ["WorkEvent", "WorkEventManager", "get_workevent_manager"]
