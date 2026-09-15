"""Bounded Weekly Synthesis persistence for SolSpire.

The synthesis can reveal the shape of the week. It cannot become the authority
over what happens next. Move 6 provisions a descriptive aggregation record only.
It does not create identity, authority, provenance, authorization, execution,
memory authority, or an alternate K15 -> K3 mutation path.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)
_ALLOWED_STATUS = {
    "DRAFT",
    "RECORDED",
    "REVIEWED",
    "SUPERSEDED",
    "DISPUTED",
    "UNKNOWN",
}


@dataclass(frozen=True)
class WeeklySynthesis:
    synthesis_id: str
    version: int
    period_start: str
    period_end: str
    subject_ref: str
    workspace_ref: str
    workload_ref: str | None
    source_pulse_refs: list[str]
    source_event_refs: list[str]
    evidence_refs: list[str]
    summary: str
    changes: list[str]
    patterns: list[str]
    contradictions: list[str]
    unknowns: list[str]
    risks: list[str]
    blockers: list[str]
    decisions_pending: list[str]
    candidate_directions: list[str]
    proposal_refs: list[str]
    feedback_refs: list[str]
    status: str
    supersedes_ref: str | None
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
        CREATE TABLE IF NOT EXISTS weekly_syntheses (
            synthesis_id TEXT PRIMARY KEY,
            version INTEGER NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            workload_ref TEXT,
            source_pulse_refs TEXT NOT NULL,
            source_event_refs TEXT NOT NULL,
            evidence_refs TEXT NOT NULL,
            summary TEXT NOT NULL,
            changes TEXT NOT NULL,
            patterns TEXT NOT NULL,
            contradictions TEXT NOT NULL,
            unknowns TEXT NOT NULL,
            risks TEXT NOT NULL,
            blockers TEXT NOT NULL,
            decisions_pending TEXT NOT NULL,
            candidate_directions TEXT NOT NULL,
            proposal_refs TEXT NOT NULL,
            feedback_refs TEXT NOT NULL,
            status TEXT NOT NULL,
            supersedes_ref TEXT,
            integrity_ref TEXT,
            created_by_event TEXT,
            schema_version TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(subject_ref, workspace_ref, period_start, period_end)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_weekly_syntheses_subject_ws "
        "ON weekly_syntheses(subject_ref, workspace_ref)"
    )
    conn.commit()
    return conn


def _loads_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _row_to_synthesis(row: sqlite3.Row) -> WeeklySynthesis:
    return WeeklySynthesis(
        synthesis_id=row["synthesis_id"],
        version=int(row["version"]),
        period_start=row["period_start"],
        period_end=row["period_end"],
        subject_ref=row["subject_ref"],
        workspace_ref=row["workspace_ref"],
        workload_ref=row["workload_ref"],
        source_pulse_refs=_loads_list(row["source_pulse_refs"]),
        source_event_refs=_loads_list(row["source_event_refs"]),
        evidence_refs=_loads_list(row["evidence_refs"]),
        summary=row["summary"] or "",
        changes=_loads_list(row["changes"]),
        patterns=_loads_list(row["patterns"]),
        contradictions=_loads_list(row["contradictions"]),
        unknowns=_loads_list(row["unknowns"]),
        risks=_loads_list(row["risks"]),
        blockers=_loads_list(row["blockers"]),
        decisions_pending=_loads_list(row["decisions_pending"]),
        candidate_directions=_loads_list(row["candidate_directions"]),
        proposal_refs=_loads_list(row["proposal_refs"]),
        feedback_refs=_loads_list(row["feedback_refs"]),
        status=row["status"],
        supersedes_ref=row["supersedes_ref"],
        integrity_ref=row["integrity_ref"],
        created_by_event=row["created_by_event"],
        schema_version=row["schema_version"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


def current_week_bounds(now: datetime | None = None) -> tuple[str, str]:
    """ISO dates for Monday–Sunday of the UTC week containing `now`."""
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    moment = moment.astimezone(timezone.utc)
    start = moment.date() - timedelta(days=moment.weekday())
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


class SynthesisManager:
    """Subject/workspace-scoped weekly synthesis records."""

    def create_or_get_current_week(
        self,
        *,
        subject_ref: str,
        workspace_ref: str,
        workload_ref: str | None = None,
        summary: str = "",
        source_pulse_refs: list[str] | None = None,
        source_event_refs: list[str] | None = None,
    ) -> WeeklySynthesis:
        subject = (subject_ref or "").strip()
        workspace = (workspace_ref or "").strip()
        if not subject:
            raise ValueError("subject_ref is required")
        if not workspace:
            raise ValueError("workspace_ref is required")

        period_start, period_end = current_week_bounds()
        existing = self.get_for_period(subject, workspace, period_start, period_end)
        if existing is not None:
            return existing

        now = time.time()
        synthesis = WeeklySynthesis(
            synthesis_id=str(uuid.uuid4()),
            version=1,
            period_start=period_start,
            period_end=period_end,
            subject_ref=subject,
            workspace_ref=workspace,
            workload_ref=(workload_ref or None),
            source_pulse_refs=list(source_pulse_refs or []),
            source_event_refs=list(source_event_refs or []),
            evidence_refs=[],
            summary=summary or "",
            changes=[],
            patterns=[],
            contradictions=[],
            unknowns=[],
            risks=[],
            blockers=[],
            decisions_pending=[],
            candidate_directions=[],
            proposal_refs=[],
            feedback_refs=[],
            status="RECORDED",
            supersedes_ref=None,
            integrity_ref=None,
            created_by_event=None,
            schema_version="1",
            created_at=now,
            updated_at=now,
        )
        if synthesis.status not in _ALLOWED_STATUS:
            raise ValueError("invalid synthesis status")

        conn = _db()
        try:
            conn.execute(
                """
                INSERT INTO weekly_syntheses (
                    synthesis_id, version, period_start, period_end, subject_ref,
                    workspace_ref, workload_ref, source_pulse_refs, source_event_refs,
                    evidence_refs, summary, changes, patterns, contradictions,
                    unknowns, risks, blockers, decisions_pending, candidate_directions,
                    proposal_refs, feedback_refs, status, supersedes_ref, integrity_ref,
                    created_by_event, schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    synthesis.synthesis_id,
                    synthesis.version,
                    synthesis.period_start,
                    synthesis.period_end,
                    synthesis.subject_ref,
                    synthesis.workspace_ref,
                    synthesis.workload_ref,
                    json.dumps(synthesis.source_pulse_refs),
                    json.dumps(synthesis.source_event_refs),
                    json.dumps(synthesis.evidence_refs),
                    synthesis.summary,
                    json.dumps(synthesis.changes),
                    json.dumps(synthesis.patterns),
                    json.dumps(synthesis.contradictions),
                    json.dumps(synthesis.unknowns),
                    json.dumps(synthesis.risks),
                    json.dumps(synthesis.blockers),
                    json.dumps(synthesis.decisions_pending),
                    json.dumps(synthesis.candidate_directions),
                    json.dumps(synthesis.proposal_refs),
                    json.dumps(synthesis.feedback_refs),
                    synthesis.status,
                    synthesis.supersedes_ref,
                    synthesis.integrity_ref,
                    synthesis.created_by_event,
                    synthesis.schema_version,
                    synthesis.created_at,
                    synthesis.updated_at,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Concurrent create for same period: return existing.
            recovered = self.get_for_period(subject, workspace, period_start, period_end)
            if recovered is not None:
                return recovered
            raise
        finally:
            conn.close()
        return synthesis

    def get_for_period(
        self,
        subject_ref: str,
        workspace_ref: str,
        period_start: str,
        period_end: str,
    ) -> WeeklySynthesis | None:
        conn = _db()
        try:
            row = conn.execute(
                """
                SELECT * FROM weekly_syntheses
                WHERE subject_ref = ? AND workspace_ref = ?
                  AND period_start = ? AND period_end = ?
                """,
                (subject_ref, workspace_ref, period_start, period_end),
            ).fetchone()
        finally:
            conn.close()
        return _row_to_synthesis(row) if row else None

    def get_current_week(self, subject_ref: str, workspace_ref: str) -> WeeklySynthesis | None:
        start, end = current_week_bounds()
        return self.get_for_period(subject_ref, workspace_ref, start, end)

    def list_for_subject(
        self, subject_ref: str, workspace_ref: str, limit: int = 20
    ) -> list[WeeklySynthesis]:
        conn = _db()
        try:
            rows = conn.execute(
                """
                SELECT * FROM weekly_syntheses
                WHERE subject_ref = ? AND workspace_ref = ?
                ORDER BY period_start DESC
                LIMIT ?
                """,
                (subject_ref, workspace_ref, limit),
            ).fetchall()
        finally:
            conn.close()
        return [_row_to_synthesis(row) for row in rows]


_MANAGER: SynthesisManager | None = None


def get_synthesis_manager() -> SynthesisManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = SynthesisManager()
    return _MANAGER


__all__ = [
    "WeeklySynthesis",
    "SynthesisManager",
    "get_synthesis_manager",
    "current_week_bounds",
]
