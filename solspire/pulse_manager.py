"""Bounded Daily Pulse persistence for SolSpire.

The pulse describes the day. It does not become the authority over the work.
Move 5 provisions a descriptive pulse record only. It does not create identity,
authority, provenance, authorization, execution, memory authority, or an
alternate K15 -> K3 mutation path.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB", "data/solspire_projects.db")
_ALLOWED_STATUS = {
    "DRAFT",
    "RECORDED",
    "REVIEWED",
    "SUPERSEDED",
    "DISPUTED",
    "UNKNOWN",
}


@dataclass(frozen=True)
class DailyPulse:
    pulse_id: str
    version: int
    date: str
    subject_ref: str
    workspace_ref: str
    workload_ref: str | None
    previous_pulse_ref: str | None
    period: str
    state_summary: str
    changes: list[str]
    work_event_refs: list[str]
    evidence_refs: list[str]
    decision_refs: list[str]
    blockers: list[str]
    proposal_refs: list[str]
    feedback_refs: list[str]
    human_attention_refs: list[str]
    status: str
    integrity_ref: str | None
    created_by_event: str | None
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
        CREATE TABLE IF NOT EXISTS daily_pulses (
            pulse_id TEXT PRIMARY KEY,
            version INTEGER NOT NULL,
            date TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            workload_ref TEXT,
            previous_pulse_ref TEXT,
            period TEXT NOT NULL,
            state_summary TEXT NOT NULL,
            changes TEXT NOT NULL,
            work_event_refs TEXT NOT NULL,
            evidence_refs TEXT NOT NULL,
            decision_refs TEXT NOT NULL,
            blockers TEXT NOT NULL,
            proposal_refs TEXT NOT NULL,
            feedback_refs TEXT NOT NULL,
            human_attention_refs TEXT NOT NULL,
            status TEXT NOT NULL,
            integrity_ref TEXT,
            created_by_event TEXT,
            schema_version TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(subject_ref, workspace_ref, date)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_daily_pulses_subject_ws "
        "ON daily_pulses(subject_ref, workspace_ref)"
    )
    conn.commit()
    return conn


def _row_to_pulse(row: sqlite3.Row) -> DailyPulse:
    return DailyPulse(
        pulse_id=row["pulse_id"],
        version=int(row["version"]),
        date=row["date"],
        subject_ref=row["subject_ref"],
        workspace_ref=row["workspace_ref"],
        workload_ref=row["workload_ref"],
        previous_pulse_ref=row["previous_pulse_ref"],
        period=row["period"],
        state_summary=row["state_summary"],
        changes=json.loads(row["changes"] or "[]"),
        work_event_refs=json.loads(row["work_event_refs"] or "[]"),
        evidence_refs=json.loads(row["evidence_refs"] or "[]"),
        decision_refs=json.loads(row["decision_refs"] or "[]"),
        blockers=json.loads(row["blockers"] or "[]"),
        proposal_refs=json.loads(row["proposal_refs"] or "[]"),
        feedback_refs=json.loads(row["feedback_refs"] or "[]"),
        human_attention_refs=json.loads(row["human_attention_refs"] or "[]"),
        status=row["status"],
        integrity_ref=row["integrity_ref"],
        created_by_event=row["created_by_event"],
        schema_version=row["schema_version"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


class PulseManager:
    """Subject- and workspace-scoped Daily Pulse store."""

    def create_or_get_today(
        self,
        *,
        subject_ref: str,
        workspace_ref: str,
        workload_ref: str | None = None,
        state_summary: str = "",
        period: str = "day",
    ) -> DailyPulse:
        if not subject_ref or not str(subject_ref).strip():
            raise ValueError("subject_ref is required")
        if not workspace_ref or not str(workspace_ref).strip():
            raise ValueError("workspace_ref is required")

        subject_ref = str(subject_ref).strip()
        workspace_ref = str(workspace_ref).strip()
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now = time.time()

        with _db() as conn:
            existing = conn.execute(
                """
                SELECT * FROM daily_pulses
                WHERE subject_ref = ? AND workspace_ref = ? AND date = ?
                """,
                (subject_ref, workspace_ref, date),
            ).fetchone()
            if existing is not None:
                return _row_to_pulse(existing)

            prev = conn.execute(
                """
                SELECT pulse_id FROM daily_pulses
                WHERE subject_ref = ? AND workspace_ref = ?
                ORDER BY date DESC, created_at DESC
                LIMIT 1
                """,
                (subject_ref, workspace_ref),
            ).fetchone()
            previous_pulse_ref = prev["pulse_id"] if prev else None

            pulse = DailyPulse(
                pulse_id=str(uuid.uuid4()),
                version=1,
                date=date,
                subject_ref=subject_ref,
                workspace_ref=workspace_ref,
                workload_ref=workload_ref,
                previous_pulse_ref=previous_pulse_ref,
                period=period or "day",
                state_summary=state_summary or "",
                changes=[],
                work_event_refs=[],
                evidence_refs=[],
                decision_refs=[],
                blockers=[],
                proposal_refs=[],
                feedback_refs=[],
                human_attention_refs=[],
                status="RECORDED",
                integrity_ref=None,
                created_by_event=None,
                schema_version="1",
                created_at=now,
                updated_at=now,
            )
            if pulse.status not in _ALLOWED_STATUS:
                raise ValueError("invalid pulse status")
            conn.execute(
                """
                INSERT INTO daily_pulses (
                    pulse_id, version, date, subject_ref, workspace_ref, workload_ref,
                    previous_pulse_ref, period, state_summary, changes, work_event_refs,
                    evidence_refs, decision_refs, blockers, proposal_refs, feedback_refs,
                    human_attention_refs, status, integrity_ref, created_by_event,
                    schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pulse.pulse_id,
                    pulse.version,
                    pulse.date,
                    pulse.subject_ref,
                    pulse.workspace_ref,
                    pulse.workload_ref,
                    pulse.previous_pulse_ref,
                    pulse.period,
                    pulse.state_summary,
                    json.dumps(pulse.changes),
                    json.dumps(pulse.work_event_refs),
                    json.dumps(pulse.evidence_refs),
                    json.dumps(pulse.decision_refs),
                    json.dumps(pulse.blockers),
                    json.dumps(pulse.proposal_refs),
                    json.dumps(pulse.feedback_refs),
                    json.dumps(pulse.human_attention_refs),
                    pulse.status,
                    pulse.integrity_ref,
                    pulse.created_by_event,
                    pulse.schema_version,
                    pulse.created_at,
                    pulse.updated_at,
                ),
            )
            return pulse

    def get_for_subject_date(
        self, subject_ref: str, workspace_ref: str, date: str
    ) -> DailyPulse | None:
        with _db() as conn:
            row = conn.execute(
                """
                SELECT * FROM daily_pulses
                WHERE subject_ref = ? AND workspace_ref = ? AND date = ?
                """,
                (subject_ref, workspace_ref, date),
            ).fetchone()
            return _row_to_pulse(row) if row else None

    def list_for_subject(
        self, subject_ref: str, workspace_ref: str, limit: int = 30
    ) -> list[DailyPulse]:
        with _db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM daily_pulses
                WHERE subject_ref = ? AND workspace_ref = ?
                ORDER BY date DESC, created_at DESC
                LIMIT ?
                """,
                (subject_ref, workspace_ref, limit),
            ).fetchall()
            return [_row_to_pulse(r) for r in rows]


_manager: PulseManager | None = None


def get_pulse_manager() -> PulseManager:
    global _manager
    if _manager is None:
        _manager = PulseManager()
    return _manager


__all__ = ["DailyPulse", "PulseManager", "get_pulse_manager"]
