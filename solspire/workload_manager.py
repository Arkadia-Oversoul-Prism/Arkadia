"""Bounded Canonical Workload persistence for SolSpire.

The workload is a governed object of work. It does not create identity,
authority, provenance, authorization, execution, memory authority, or an
alternate K15 -> K3 mutation path. Move 4 provisions only the canonical
Barnabas workload structure; no live project data is stored.
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
_ALLOWED_STATUS = {
    "PROPOSED", "OPEN", "ACTIVE", "ON_HOLD", "COMPLETED", "CLOSED",
    "SUPERSEDED", "DISPUTED", "UNKNOWN",
}
_CANONICAL_TITLE = "Barnabas / Eden Food Systems — Plateau Food Market Intelligence"
_CANONICAL_OBJECTIVE = (
    "Market reconnaissance, evidence collection, commodity and corridor "
    "intelligence, synthesis, and defined deliverables."
)


@dataclass(frozen=True)
class CanonicalWorkload:
    workload_id: str
    workload_type: str
    canonical_subject_ref: str
    workspace_ref: str
    display_name: str
    title: str
    objective: str
    scope_ref: str | None
    market_intelligence_scope_ref: str | None
    principal_ref: str | None
    owner_ref: str | None
    participant_refs: list[str]
    phase: str
    status: str
    deliverable_refs: list[str]
    artifact_refs: list[str]
    evidence_refs: list[str]
    work_event_refs: list[str]
    decision_refs: list[str]
    provenance_refs: list[str]
    authorization_refs: list[str]
    approval_refs: list[str]
    created_by_event: str | None
    effective_from: float | None
    effective_until: float | None
    supersedes_ref: str | None
    closure_ref: str | None
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
        CREATE TABLE IF NOT EXISTS canonical_workloads (
            workload_id TEXT PRIMARY KEY,
            workload_type TEXT NOT NULL,
            canonical_subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            display_name TEXT NOT NULL,
            title TEXT NOT NULL,
            objective TEXT NOT NULL,
            scope_ref TEXT,
            market_intelligence_scope_ref TEXT,
            principal_ref TEXT,
            owner_ref TEXT,
            participant_refs TEXT NOT NULL DEFAULT '[]',
            phase TEXT NOT NULL,
            status TEXT NOT NULL,
            deliverable_refs TEXT NOT NULL DEFAULT '[]',
            artifact_refs TEXT NOT NULL DEFAULT '[]',
            evidence_refs TEXT NOT NULL DEFAULT '[]',
            work_event_refs TEXT NOT NULL DEFAULT '[]',
            decision_refs TEXT NOT NULL DEFAULT '[]',
            provenance_refs TEXT NOT NULL DEFAULT '[]',
            authorization_refs TEXT NOT NULL DEFAULT '[]',
            approval_refs TEXT NOT NULL DEFAULT '[]',
            created_by_event TEXT,
            effective_from REAL,
            effective_until REAL,
            supersedes_ref TEXT,
            closure_ref TEXT,
            schema_version TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(canonical_subject_ref, workspace_ref)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_workloads_subject ON canonical_workloads(canonical_subject_ref, created_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_workloads_workspace ON canonical_workloads(workspace_ref, created_at)"
    )
    conn.commit()
    return conn


class CanonicalWorkloadManager:
    def create_canonical_barnabas(self, *, subject_ref: str, workspace_ref: str) -> CanonicalWorkload:
        subject_ref = (subject_ref or "").strip()
        workspace_ref = (workspace_ref or "").strip()
        if not subject_ref:
            raise ValueError("Canonical subject reference must not be empty")
        if not workspace_ref:
            raise ValueError("Workspace reference must not be empty")

        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM canonical_workloads WHERE canonical_subject_ref=? AND workspace_ref=?",
                (subject_ref, workspace_ref),
            ).fetchone()
            if row:
                return self._from_row(row)

            now = time.time()
            workload = CanonicalWorkload(
                workload_id=str(uuid.uuid4()),
                workload_type="canonical_workload",
                canonical_subject_ref=subject_ref,
                workspace_ref=workspace_ref,
                display_name="Barnabas Canonical Workload",
                title=_CANONICAL_TITLE,
                objective=_CANONICAL_OBJECTIVE,
                scope_ref="barnabas-reference-scope",
                market_intelligence_scope_ref="bounded-market-intelligence-reference",
                principal_ref=subject_ref,
                owner_ref=subject_ref,
                participant_refs=[],
                phase="STRUCTURE_PROVISIONED",
                status="PROPOSED",
                deliverable_refs=[],
                artifact_refs=[],
                evidence_refs=[],
                work_event_refs=[],
                decision_refs=[],
                provenance_refs=[],
                authorization_refs=[],
                approval_refs=[],
                created_by_event=None,
                effective_from=None,
                effective_until=None,
                supersedes_ref=None,
                closure_ref=None,
                schema_version="1",
                created_at=now,
                updated_at=now,
            )
            conn.execute(
                """
                INSERT INTO canonical_workloads (
                    workload_id, workload_type, canonical_subject_ref, workspace_ref,
                    display_name, title, objective, scope_ref, market_intelligence_scope_ref,
                    principal_ref, owner_ref, participant_refs, phase, status,
                    deliverable_refs, artifact_refs, evidence_refs, work_event_refs,
                    decision_refs, provenance_refs, authorization_refs, approval_refs,
                    created_by_event, effective_from, effective_until, supersedes_ref,
                    closure_ref, schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workload.workload_id, workload.workload_type, workload.canonical_subject_ref,
                    workload.workspace_ref, workload.display_name, workload.title,
                    workload.objective, workload.scope_ref, workload.market_intelligence_scope_ref,
                    workload.principal_ref, workload.owner_ref, json.dumps(workload.participant_refs),
                    workload.phase, workload.status, json.dumps(workload.deliverable_refs),
                    json.dumps(workload.artifact_refs), json.dumps(workload.evidence_refs),
                    json.dumps(workload.work_event_refs), json.dumps(workload.decision_refs),
                    json.dumps(workload.provenance_refs), json.dumps(workload.authorization_refs),
                    json.dumps(workload.approval_refs), workload.created_by_event,
                    workload.effective_from, workload.effective_until, workload.supersedes_ref,
                    workload.closure_ref, workload.schema_version, workload.created_at,
                    workload.updated_at,
                ),
            )
            return workload

    def get_for_subject(self, subject_ref: str, workspace_ref: str) -> CanonicalWorkload | None:
        subject_ref = (subject_ref or "").strip()
        workspace_ref = (workspace_ref or "").strip()
        if not subject_ref or not workspace_ref:
            return None
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM canonical_workloads WHERE canonical_subject_ref=? AND workspace_ref=?",
                (subject_ref, workspace_ref),
            ).fetchone()
        return self._from_row(row) if row else None

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CanonicalWorkload:
        def arr(name: str) -> list[str]:
            return json.loads(row[name])
        return CanonicalWorkload(
            workload_id=row["workload_id"], workload_type=row["workload_type"],
            canonical_subject_ref=row["canonical_subject_ref"], workspace_ref=row["workspace_ref"],
            display_name=row["display_name"], title=row["title"], objective=row["objective"],
            scope_ref=row["scope_ref"], market_intelligence_scope_ref=row["market_intelligence_scope_ref"],
            principal_ref=row["principal_ref"], owner_ref=row["owner_ref"],
            participant_refs=arr("participant_refs"), phase=row["phase"], status=row["status"],
            deliverable_refs=arr("deliverable_refs"), artifact_refs=arr("artifact_refs"),
            evidence_refs=arr("evidence_refs"), work_event_refs=arr("work_event_refs"),
            decision_refs=arr("decision_refs"), provenance_refs=arr("provenance_refs"),
            authorization_refs=arr("authorization_refs"), approval_refs=arr("approval_refs"),
            created_by_event=row["created_by_event"], effective_from=row["effective_from"],
            effective_until=row["effective_until"], supersedes_ref=row["supersedes_ref"],
            closure_ref=row["closure_ref"], schema_version=row["schema_version"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )


_GLOBAL_CWM = CanonicalWorkloadManager()


def get_workload_manager() -> CanonicalWorkloadManager:
    return _GLOBAL_CWM


__all__ = ["CanonicalWorkload", "CanonicalWorkloadManager", "get_workload_manager"]
