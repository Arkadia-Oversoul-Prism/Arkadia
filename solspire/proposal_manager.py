"""Bounded Proposal Feedback Loop persistence for SolSpire.

Feedback can change a proposal. It cannot become the authority to execute the
proposal. Move 7 provisions descriptive proposal and feedback records only.
It does not create identity, authority, provenance, authorization, execution,
memory authority, or an alternate K15 -> K3 mutation path.

ACCEPTED ≠ AUTHORIZED. DECISION_PENDING ≠ DECISION MADE.
PREPARATION ≠ PASS SPEC ≠ K15 ≠ K3. execution_authorized is always false in Move 8.
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
_ALLOWED_PROPOSAL_STATUS = {
    "DRAFT",
    "PRESENTED",
    "UNDER_REVIEW",
    "REVISION_REQUESTED",
    "REVISED",
    "DECISION_PENDING",
    "ACCEPTED",
    "DECLINED",
    "WITHDRAWN",
    "SUPERSEDED",
    "DISPUTED",
    "UNKNOWN",
}
_ALLOWED_FEEDBACK_STATUS = {
    "SUBMITTED",
    "ACKNOWLEDGED",
    "ADDRESSED",
    "WITHDRAWN",
    "DISPUTED",
    "UNKNOWN",
}


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    proposal_version: int
    subject_ref: str
    workspace_ref: str
    workload_ref: str | None
    objective: str
    scope: str
    assumptions: list[str]
    alternatives: list[str]
    requested_decision: str
    proposal_status: str
    feedback_refs: list[str]
    revision_refs: list[str]
    decision_ref: str | None
    provenance_ref: str | None
    authorization_ref: str | None
    evidence_refs: list[str]
    work_event_refs: list[str]
    supersedes_ref: str | None
    effective_from: float | None
    effective_until: float | None
    closure_ref: str | None
    integrity_ref: str | None
    created_by_event: str | None
    schema_version: str
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProposalFeedback:
    feedback_id: str
    proposal_id: str
    subject_ref: str
    workspace_ref: str
    feedback_type: str
    observation: str
    recommendation: str
    evidence_refs: list[str]
    status: str
    created_by_event: str | None
    schema_version: str
    created_at: float

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
        CREATE TABLE IF NOT EXISTS proposals (
            proposal_id TEXT PRIMARY KEY,
            proposal_version INTEGER NOT NULL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            workload_ref TEXT,
            objective TEXT NOT NULL,
            scope TEXT NOT NULL,
            assumptions TEXT NOT NULL,
            alternatives TEXT NOT NULL,
            requested_decision TEXT NOT NULL,
            proposal_status TEXT NOT NULL,
            feedback_refs TEXT NOT NULL,
            revision_refs TEXT NOT NULL,
            decision_ref TEXT,
            provenance_ref TEXT,
            authorization_ref TEXT,
            evidence_refs TEXT NOT NULL,
            work_event_refs TEXT NOT NULL,
            supersedes_ref TEXT,
            effective_from REAL,
            effective_until REAL,
            closure_ref TEXT,
            integrity_ref TEXT,
            created_by_event TEXT,
            schema_version TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_feedback (
            feedback_id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            feedback_type TEXT NOT NULL,
            observation TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            evidence_refs TEXT NOT NULL,
            status TEXT NOT NULL,
            created_by_event TEXT,
            schema_version TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_proposals_subject_ws "
        "ON proposals(subject_ref, workspace_ref)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_proposal "
        "ON proposal_feedback(proposal_id, subject_ref)"
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


def _row_to_proposal(row: sqlite3.Row) -> Proposal:
    return Proposal(
        proposal_id=row["proposal_id"],
        proposal_version=int(row["proposal_version"]),
        subject_ref=row["subject_ref"],
        workspace_ref=row["workspace_ref"],
        workload_ref=row["workload_ref"],
        objective=row["objective"] or "",
        scope=row["scope"] or "",
        assumptions=_loads_list(row["assumptions"]),
        alternatives=_loads_list(row["alternatives"]),
        requested_decision=row["requested_decision"] or "",
        proposal_status=row["proposal_status"],
        feedback_refs=_loads_list(row["feedback_refs"]),
        revision_refs=_loads_list(row["revision_refs"]),
        decision_ref=row["decision_ref"],
        provenance_ref=row["provenance_ref"],
        authorization_ref=row["authorization_ref"],
        evidence_refs=_loads_list(row["evidence_refs"]),
        work_event_refs=_loads_list(row["work_event_refs"]),
        supersedes_ref=row["supersedes_ref"],
        effective_from=row["effective_from"],
        effective_until=row["effective_until"],
        closure_ref=row["closure_ref"],
        integrity_ref=row["integrity_ref"],
        created_by_event=row["created_by_event"],
        schema_version=row["schema_version"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


def _row_to_feedback(row: sqlite3.Row) -> ProposalFeedback:
    return ProposalFeedback(
        feedback_id=row["feedback_id"],
        proposal_id=row["proposal_id"],
        subject_ref=row["subject_ref"],
        workspace_ref=row["workspace_ref"],
        feedback_type=row["feedback_type"],
        observation=row["observation"] or "",
        recommendation=row["recommendation"] or "",
        evidence_refs=_loads_list(row["evidence_refs"]),
        status=row["status"],
        created_by_event=row["created_by_event"],
        schema_version=row["schema_version"],
        created_at=float(row["created_at"]),
    )


class ProposalManager:
    """Subject/workspace-scoped proposal and feedback records."""

    def create_proposal(
        self,
        *,
        subject_ref: str,
        workspace_ref: str,
        objective: str = "",
        scope: str = "",
        requested_decision: str = "",
        workload_ref: str | None = None,
        assumptions: list[str] | None = None,
        alternatives: list[str] | None = None,
    ) -> Proposal:
        subject = (subject_ref or "").strip()
        workspace = (workspace_ref or "").strip()
        if not subject:
            raise ValueError("subject_ref is required")
        if not workspace:
            raise ValueError("workspace_ref is required")

        now = time.time()
        proposal = Proposal(
            proposal_id=str(uuid.uuid4()),
            proposal_version=1,
            subject_ref=subject,
            workspace_ref=workspace,
            workload_ref=(workload_ref or None),
            objective=objective or "",
            scope=scope or "",
            assumptions=list(assumptions or []),
            alternatives=list(alternatives or []),
            requested_decision=requested_decision or "",
            proposal_status="PRESENTED",
            feedback_refs=[],
            revision_refs=[],
            decision_ref=None,
            provenance_ref=None,
            authorization_ref=None,
            evidence_refs=[],
            work_event_refs=[],
            supersedes_ref=None,
            effective_from=None,
            effective_until=None,
            closure_ref=None,
            integrity_ref=None,
            created_by_event=None,
            schema_version="1",
            created_at=now,
            updated_at=now,
        )
        if proposal.proposal_status not in _ALLOWED_PROPOSAL_STATUS:
            raise ValueError("invalid proposal status")

        conn = _db()
        try:
            conn.execute(
                """
                INSERT INTO proposals (
                    proposal_id, proposal_version, subject_ref, workspace_ref,
                    workload_ref, objective, scope, assumptions, alternatives,
                    requested_decision, proposal_status, feedback_refs, revision_refs,
                    decision_ref, provenance_ref, authorization_ref, evidence_refs,
                    work_event_refs, supersedes_ref, effective_from, effective_until,
                    closure_ref, integrity_ref, created_by_event, schema_version,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.proposal_id,
                    proposal.proposal_version,
                    proposal.subject_ref,
                    proposal.workspace_ref,
                    proposal.workload_ref,
                    proposal.objective,
                    proposal.scope,
                    json.dumps(proposal.assumptions),
                    json.dumps(proposal.alternatives),
                    proposal.requested_decision,
                    proposal.proposal_status,
                    json.dumps(proposal.feedback_refs),
                    json.dumps(proposal.revision_refs),
                    proposal.decision_ref,
                    proposal.provenance_ref,
                    proposal.authorization_ref,
                    json.dumps(proposal.evidence_refs),
                    json.dumps(proposal.work_event_refs),
                    proposal.supersedes_ref,
                    proposal.effective_from,
                    proposal.effective_until,
                    proposal.closure_ref,
                    proposal.integrity_ref,
                    proposal.created_by_event,
                    proposal.schema_version,
                    proposal.created_at,
                    proposal.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return proposal

    def get_proposal(self, proposal_id: str, subject_ref: str) -> Proposal | None:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT * FROM proposals WHERE proposal_id = ? AND subject_ref = ?",
                (proposal_id, subject_ref),
            ).fetchone()
        finally:
            conn.close()
        return _row_to_proposal(row) if row else None

    def list_proposals(
        self, subject_ref: str, workspace_ref: str, limit: int = 50
    ) -> list[Proposal]:
        conn = _db()
        try:
            rows = conn.execute(
                """
                SELECT * FROM proposals
                WHERE subject_ref = ? AND workspace_ref = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (subject_ref, workspace_ref, limit),
            ).fetchall()
        finally:
            conn.close()
        return [_row_to_proposal(row) for row in rows]

    def add_feedback(
        self,
        *,
        proposal_id: str,
        subject_ref: str,
        workspace_ref: str,
        feedback_type: str = "observation",
        observation: str = "",
        recommendation: str = "",
        evidence_refs: list[str] | None = None,
    ) -> tuple[Proposal, ProposalFeedback]:
        subject = (subject_ref or "").strip()
        if not subject:
            raise ValueError("subject_ref is required")
        proposal = self.get_proposal(proposal_id, subject)
        if proposal is None:
            raise ValueError("proposal not found")
        if proposal.workspace_ref != workspace_ref:
            raise ValueError("workspace mismatch")

        now = time.time()
        feedback = ProposalFeedback(
            feedback_id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            subject_ref=subject,
            workspace_ref=workspace_ref,
            feedback_type=feedback_type or "observation",
            observation=observation or "",
            recommendation=recommendation or "",
            evidence_refs=list(evidence_refs or []),
            status="SUBMITTED",
            created_by_event=None,
            schema_version="1",
            created_at=now,
        )
        if feedback.status not in _ALLOWED_FEEDBACK_STATUS:
            raise ValueError("invalid feedback status")

        new_refs = list(proposal.feedback_refs) + [feedback.feedback_id]
        # Feedback may move presentation into review; never into AUTHORIZED.
        new_status = proposal.proposal_status
        if new_status in ("PRESENTED", "DRAFT", "REVISED"):
            new_status = "UNDER_REVIEW"

        conn = _db()
        try:
            conn.execute(
                """
                INSERT INTO proposal_feedback (
                    feedback_id, proposal_id, subject_ref, workspace_ref,
                    feedback_type, observation, recommendation, evidence_refs,
                    status, created_by_event, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.feedback_id,
                    feedback.proposal_id,
                    feedback.subject_ref,
                    feedback.workspace_ref,
                    feedback.feedback_type,
                    feedback.observation,
                    feedback.recommendation,
                    json.dumps(feedback.evidence_refs),
                    feedback.status,
                    feedback.created_by_event,
                    feedback.schema_version,
                    feedback.created_at,
                ),
            )
            conn.execute(
                """
                UPDATE proposals
                SET feedback_refs = ?, proposal_status = ?, updated_at = ?
                WHERE proposal_id = ? AND subject_ref = ?
                """,
                (
                    json.dumps(new_refs),
                    new_status,
                    now,
                    proposal_id,
                    subject,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        updated = self.get_proposal(proposal_id, subject)
        assert updated is not None
        # Boundary: feedback never writes authorization_ref or provenance_ref.
        assert updated.authorization_ref is None
        assert updated.provenance_ref is None
        return updated, feedback

    def list_feedback(self, proposal_id: str, subject_ref: str) -> list[ProposalFeedback]:
        conn = _db()
        try:
            rows = conn.execute(
                """
                SELECT * FROM proposal_feedback
                WHERE proposal_id = ? AND subject_ref = ?
                ORDER BY created_at ASC
                """,
                (proposal_id, subject_ref),
            ).fetchall()
        finally:
            conn.close()
        return [_row_to_feedback(row) for row in rows]

    def record_decision(
        self,
        *,
        proposal_id: str,
        subject_ref: str,
        decision: str,
    ) -> Proposal:
        """Record human ACCEPTED / DECLINED / WITHDRAWN. Never authorizes execution."""
        subject = (subject_ref or "").strip()
        if not subject:
            raise ValueError("subject_ref is required")
        decision_u = (decision or "").strip().upper()
        if decision_u not in {"ACCEPTED", "DECLINED", "WITHDRAWN"}:
            raise ValueError("decision must be ACCEPTED, DECLINED, or WITHDRAWN")

        proposal = self.get_proposal(proposal_id, subject)
        if proposal is None:
            raise ValueError("proposal not found")

        now = time.time()
        decision_id = str(uuid.uuid4())
        conn = _db()
        try:
            conn.execute(
                """
                UPDATE proposals
                SET proposal_status = ?, decision_ref = ?, updated_at = ?
                WHERE proposal_id = ? AND subject_ref = ?
                """,
                (decision_u, decision_id, now, proposal_id, subject),
            )
            # Boundary: never touch authorization_ref or provenance_ref on decision.
            conn.commit()
        finally:
            conn.close()

        updated = self.get_proposal(proposal_id, subject)
        assert updated is not None
        assert updated.authorization_ref is None
        assert updated.proposal_status == decision_u
        return updated

    def prepare_execution(
        self,
        *,
        proposal_id: str,
        subject_ref: str,
        workspace_ref: str,
        notes: str = "",
    ) -> tuple[Proposal, "ExecutionPreparation"]:
        """Create a locked preparation package. execution_authorized is always false."""
        subject = (subject_ref or "").strip()
        if not subject:
            raise ValueError("subject_ref is required")
        proposal = self.get_proposal(proposal_id, subject)
        if proposal is None:
            raise ValueError("proposal not found")
        if proposal.workspace_ref != workspace_ref:
            raise ValueError("workspace mismatch")
        if proposal.proposal_status != "ACCEPTED":
            raise ValueError("proposal must be ACCEPTED before execution preparation")

        now = time.time()
        prep = ExecutionPreparation(
            preparation_id=str(uuid.uuid4()),
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.proposal_version,
            subject_ref=subject,
            workspace_ref=workspace_ref,
            status="PREPARED",
            execution_authorized=False,
            auto_merge=False,
            auto_deploy=False,
            auto_execute=False,
            pass_spec_ref=None,
            k15_ref=None,
            k3_ref=None,
            notes=notes or "",
            schema_version="1",
            created_at=now,
        )

        conn = _db()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_preparations (
                    preparation_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    proposal_version INTEGER NOT NULL,
                    subject_ref TEXT NOT NULL,
                    workspace_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_authorized INTEGER NOT NULL,
                    auto_merge INTEGER NOT NULL,
                    auto_deploy INTEGER NOT NULL,
                    auto_execute INTEGER NOT NULL,
                    pass_spec_ref TEXT,
                    k15_ref TEXT,
                    k3_ref TEXT,
                    notes TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO execution_preparations (
                    preparation_id, proposal_id, proposal_version, subject_ref,
                    workspace_ref, status, execution_authorized, auto_merge,
                    auto_deploy, auto_execute, pass_spec_ref, k15_ref, k3_ref,
                    notes, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, NULL, NULL, NULL, ?, ?, ?)
                """,
                (
                    prep.preparation_id,
                    prep.proposal_id,
                    prep.proposal_version,
                    prep.subject_ref,
                    prep.workspace_ref,
                    prep.status,
                    prep.notes,
                    prep.schema_version,
                    prep.created_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        # Proposal remains ACCEPTED; still not authorized.
        assert proposal.authorization_ref is None
        assert prep.execution_authorized is False
        return proposal, prep

    def list_preparations(
        self, proposal_id: str, subject_ref: str
    ) -> list["ExecutionPreparation"]:
        conn = _db()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_preparations (
                    preparation_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    proposal_version INTEGER NOT NULL,
                    subject_ref TEXT NOT NULL,
                    workspace_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_authorized INTEGER NOT NULL,
                    auto_merge INTEGER NOT NULL,
                    auto_deploy INTEGER NOT NULL,
                    auto_execute INTEGER NOT NULL,
                    pass_spec_ref TEXT,
                    k15_ref TEXT,
                    k3_ref TEXT,
                    notes TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            rows = conn.execute(
                """
                SELECT * FROM execution_preparations
                WHERE proposal_id = ? AND subject_ref = ?
                ORDER BY created_at ASC
                """,
                (proposal_id, subject_ref),
            ).fetchall()
        finally:
            conn.close()
        out: list[ExecutionPreparation] = []
        for row in rows:
            out.append(
                ExecutionPreparation(
                    preparation_id=row["preparation_id"],
                    proposal_id=row["proposal_id"],
                    proposal_version=int(row["proposal_version"]),
                    subject_ref=row["subject_ref"],
                    workspace_ref=row["workspace_ref"],
                    status=row["status"],
                    execution_authorized=bool(row["execution_authorized"]),
                    auto_merge=bool(row["auto_merge"]),
                    auto_deploy=bool(row["auto_deploy"]),
                    auto_execute=bool(row["auto_execute"]),
                    pass_spec_ref=row["pass_spec_ref"],
                    k15_ref=row["k15_ref"],
                    k3_ref=row["k3_ref"],
                    notes=row["notes"] or "",
                    schema_version=row["schema_version"],
                    created_at=float(row["created_at"]),
                )
            )
        return out






@dataclass(frozen=True)
class ExecutionPreparation:
    """Dry-run preparation only. Never grants K15/K3 authority."""

    preparation_id: str
    proposal_id: str
    proposal_version: int
    subject_ref: str
    workspace_ref: str
    status: str
    execution_authorized: bool
    auto_merge: bool
    auto_deploy: bool
    auto_execute: bool
    pass_spec_ref: str | None
    k15_ref: str | None
    k3_ref: str | None
    notes: str
    schema_version: str
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_MANAGER: ProposalManager | None = None


def get_proposal_manager() -> ProposalManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = ProposalManager()
    return _MANAGER


__all__ = [
    "Proposal",
    "ProposalFeedback",
    "ExecutionPreparation",
    "ProposalManager",
    "get_proposal_manager",
]
