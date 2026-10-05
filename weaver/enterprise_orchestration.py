"""ARK-WEAVER-01 — Canonical Enterprise Orchestration Spine.

Enterprise operational records are distinct from SolSpire WorkEvents and from
the Weaver K15 -> K3 repository mutation path.

Core rule: no transition borrows standing from the next transition.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

VERIFICATION_VERDICTS = {"VERIFIED", "INSUFFICIENT", "CONTRADICTED"}
# Proposal lifecycle, reconstructed from the operating loop (GATE-09). The base
# set is the operational branch used by the store today; the declared set adds
# the pre-proposal and terminal states the loop requires. The union is exposed
# so consumers validate against one vocabulary.
PROPOSAL_STATUS_BASE = {"PROPOSED", "AWAITING_AUTHORITY", "AUTHORIZED", "EXECUTION_READY", "COMPLETED", "REJECTED"}
PROPOSAL_STATUS_DECLARED = {"DRAFT", "EXPIRED", "SUPERSEDED"}
PROPOSAL_STATUSES = PROPOSAL_STATUS_BASE | PROPOSAL_STATUS_DECLARED
EXECUTION_STATUSES = {"PREPARED", "ATTEMPTED", "SUCCEEDED", "FAILED", "BLOCKED"}
# Canonical operational transition vocabulary (GATE-05). Every operational event
# must name itself from this set so an observer can reconstruct what happened
# without hidden model reasoning. SUPPLIER_SIGNAL_INGESTED is retained because
# existing Eden ingestion already emits it; it is a named alias of capture, not
# a second vocabulary.
OPERATIONAL_EVENT_TYPES = frozenset({
    "INPUT_RECEIVED", "SOURCE_ATTRIBUTED", "CANONICALIZED", "KNOWLEDGE_UPDATED",
    "ENTITY_LINKED", "UNCERTAINTY_DETECTED", "TOOL_SELECTED", "TOOL_EXECUTED",
    "RESULT_RECEIVED", "PROPOSAL_GENERATED", "AUTHORIZATION_REQUIRED", "AUTHORIZED",
    "EXECUTION_PREPARED", "EXECUTED", "EVIDENCE_RECEIVED", "VERIFIED", "RECALIBRATED",
    "SUPPLIER_SIGNAL_INGESTED",
})


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
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS ew_canonical_records (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, source_channel TEXT NOT NULL,
        raw_payload TEXT, payload_hash TEXT NOT NULL, received_at REAL NOT NULL,
        ingested_by TEXT NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_authority_events (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, actor TEXT NOT NULL,
        authority_context TEXT NOT NULL, action TEXT NOT NULL,
        previous_state TEXT NOT NULL, new_state TEXT NOT NULL, timestamp REAL NOT NULL,
        origin TEXT NOT NULL, authentication_context TEXT NOT NULL,
        correlation_id TEXT NOT NULL, evidence_refs TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_interpretations (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, canonical_record_id TEXT NOT NULL,
        interpreter TEXT NOT NULL, interpretation TEXT NOT NULL, confidence REAL,
        derived_at REAL NOT NULL, correlation_id TEXT NOT NULL,
        FOREIGN KEY(canonical_record_id) REFERENCES ew_canonical_records(id)
    );
    CREATE TABLE IF NOT EXISTS ew_knowledge_mutations (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, previous_knowledge_refs TEXT NOT NULL,
        new_knowledge_refs TEXT NOT NULL, mutation_type TEXT NOT NULL,
        caused_by_kind TEXT NOT NULL, caused_by_id TEXT NOT NULL,
        timestamp REAL NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_operational_events (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, enterprise_id TEXT NOT NULL,
        workload_id TEXT, workstream_id TEXT, event_type TEXT NOT NULL,
        payload TEXT NOT NULL, timestamp REAL NOT NULL, caused_by_kind TEXT,
        caused_by_id TEXT, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_proposals (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, enterprise_id TEXT NOT NULL,
        objective TEXT NOT NULL, rationale TEXT NOT NULL,
        recommended_actions TEXT NOT NULL, required_authority TEXT NOT NULL,
        tool_selections TEXT NOT NULL, status TEXT NOT NULL,
        created_at REAL NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_authorizations (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, proposal_id TEXT NOT NULL,
        authority_event_id TEXT NOT NULL, acceptance_id TEXT, scope TEXT NOT NULL, constraints TEXT NOT NULL,
        expires_at REAL, granted_at REAL NOT NULL, correlation_id TEXT NOT NULL,
        FOREIGN KEY(proposal_id) REFERENCES ew_proposals(id),
        FOREIGN KEY(authority_event_id) REFERENCES ew_authority_events(id)
    );
    CREATE TABLE IF NOT EXISTS ew_execution_attempts (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, authorization_id TEXT NOT NULL,
        tool_channel TEXT NOT NULL, request_payload TEXT NOT NULL,
        attempted_at REAL NOT NULL, result_status TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        FOREIGN KEY(authorization_id) REFERENCES ew_authorizations(id)
    );
    CREATE TABLE IF NOT EXISTS ew_evidence (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, execution_attempt_id TEXT,
        source_ref TEXT, evidence_type TEXT NOT NULL, content_or_ref TEXT NOT NULL,
        captured_at REAL NOT NULL, correlation_id TEXT NOT NULL,
        FOREIGN KEY(execution_attempt_id) REFERENCES ew_execution_attempts(id)
    );
    CREATE TABLE IF NOT EXISTS ew_verifications (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, claim TEXT NOT NULL,
        evidence_refs TEXT NOT NULL, verdict TEXT NOT NULL, verified_at REAL NOT NULL,
        verifier TEXT NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_ew_ops_stream ON ew_operational_events(subject, enterprise_id, timestamp);
    CREATE TABLE IF NOT EXISTS ew_acceptances (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, verification_id TEXT NOT NULL,
        accepted_result_ref TEXT NOT NULL, accepting_authority TEXT NOT NULL,
        authorization_scope TEXT NOT NULL, context_ref TEXT NOT NULL,
        accepted_at REAL NOT NULL, status TEXT NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_reviews (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, work_event_id TEXT NOT NULL,
        reviewer TEXT NOT NULL, verdict TEXT NOT NULL, findings TEXT NOT NULL,
        reviewed_at REAL NOT NULL, amendment_of TEXT, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_completions (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, work_event_id TEXT NOT NULL,
        review_id TEXT NOT NULL, condition TEXT NOT NULL,
        supporting_evidence_refs TEXT NOT NULL, completed_at REAL NOT NULL,
        status TEXT NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ew_production_acceptances (
        id TEXT PRIMARY KEY, subject TEXT NOT NULL, completion_id TEXT NOT NULL,
        accepting_authority TEXT NOT NULL, context_ref TEXT NOT NULL,
        accepted_at REAL NOT NULL, status TEXT NOT NULL, correlation_id TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_ew_verifications_subject ON ew_verifications(subject, verified_at);
    CREATE INDEX IF NOT EXISTS idx_ew_acceptances_subject ON ew_acceptances(subject, accepted_at);
    CREATE INDEX IF NOT EXISTS idx_ew_reviews_work_event ON ew_reviews(work_event_id, reviewed_at);
    CREATE INDEX IF NOT EXISTS idx_ew_completions_work_event ON ew_completions(work_event_id, completed_at);
    CREATE INDEX IF NOT EXISTS idx_ew_prod_acceptances_completion ON ew_production_acceptances(completion_id, accepted_at);
    """)
    auth_columns = {row["name"] for row in conn.execute("PRAGMA table_info(ew_authorizations)").fetchall()}
    if "acceptance_id" not in auth_columns:
        conn.execute("ALTER TABLE ew_authorizations ADD COLUMN acceptance_id TEXT")
    conn.commit()
    return conn

@dataclass(frozen=True)
class CanonicalRecord:
    id: str
    subject: str
    source_channel: str
    raw_payload: Any
    payload_hash: str
    received_at: float
    ingested_by: str
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class HumanAuthorityEvent:
    id: str
    subject: str
    actor: str
    authority_context: str
    action: str
    previous_state: Any
    new_state: Any
    timestamp: float
    origin: str
    authentication_context: str
    correlation_id: str
    evidence_refs: list[str]
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class InterpretationRecord:
    id: str
    subject: str
    canonical_record_id: str
    interpreter: str
    interpretation: Any
    confidence: float | None
    derived_at: float
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class KnowledgeMutation:
    id: str
    subject: str
    previous_knowledge_refs: list[str]
    new_knowledge_refs: list[str]
    mutation_type: str
    caused_by_kind: str
    caused_by_id: str
    timestamp: float
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class OperationalEvent:
    id: str
    subject: str
    enterprise_id: str
    workload_id: str | None
    workstream_id: str | None
    event_type: str
    payload: Any
    timestamp: float
    caused_by_kind: str | None
    caused_by_id: str | None
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class Proposal:
    id: str
    subject: str
    enterprise_id: str
    objective: str
    rationale: str
    recommended_actions: list[Any]
    required_authority: str
    tool_selections: list[Any]
    status: str
    created_at: float
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class Authorization:
    id: str
    subject: str
    proposal_id: str
    authority_event_id: str
    acceptance_id: str | None
    scope: Any
    constraints: Any
    expires_at: float | None
    granted_at: float
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class ExecutionAttempt:
    id: str
    subject: str
    authorization_id: str
    tool_channel: str
    request_payload: Any
    attempted_at: float
    result_status: str
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    subject: str
    execution_attempt_id: str | None
    source_ref: str | None
    evidence_type: str
    content_or_ref: Any
    captured_at: float
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class AcceptanceRecord:
    id: str
    subject: str
    verification_id: str
    accepted_result_ref: str
    accepting_authority: str
    authorization_scope: Any
    context_ref: str
    accepted_at: float
    status: str
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class ReviewRecord:
    id: str
    subject: str
    work_event_id: str
    reviewer: str
    verdict: str
    findings: Any
    reviewed_at: float
    amendment_of: str | None
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class CompletionRecord:
    id: str
    subject: str
    work_event_id: str
    review_id: str
    condition: str
    supporting_evidence_refs: list[str]
    completed_at: float
    status: str
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class ProductionAcceptanceRecord:
    id: str
    subject: str
    completion_id: str
    accepting_authority: str
    context_ref: str
    accepted_at: float
    status: str
    correlation_id: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class VerificationRecord:
    id: str
    subject: str
    claim: str
    evidence_refs: list[str]
    verdict: str
    verified_at: float
    verifier: str
    correlation_id: str
    def to_dict(self): return asdict(self)

class EnterpriseOrchestrationStore:
    """Append-only canonical operational store with explicit transition gates."""

    def canonical_record(self, *, subject: str, source_channel: str, raw_payload: Any,
                         ingested_by: str, correlation_id: str | None = None) -> CanonicalRecord:
        cid = correlation_id or _id("corr")
        rid = _id("cr")
        payload_hash = hashlib.sha256(_json(raw_payload).encode()).hexdigest()
        record = CanonicalRecord(rid, subject, source_channel, raw_payload, payload_hash, _now(), ingested_by, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_canonical_records VALUES (?,?,?,?,?,?,?,?)",
                      (rid, subject, source_channel, _json(raw_payload), payload_hash, record.received_at, ingested_by, cid))
        return record

    def interpretation(self, *, subject: str, canonical_record_id: str, interpreter: str,
                        interpretation: Any, confidence: float | None = None,
                        correlation_id: str | None = None) -> InterpretationRecord:
        cid = correlation_id or self._correlation_for("ew_canonical_records", canonical_record_id)
        if not self._exists("ew_canonical_records", canonical_record_id):
            raise ValueError("canonical record required before interpretation")
        rid = _id("ir"); now = _now()
        row = InterpretationRecord(rid, subject, canonical_record_id, interpreter, interpretation, confidence, now, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_interpretations VALUES (?,?,?,?,?,?,?,?)",
                      (rid, subject, canonical_record_id, interpreter, _json(interpretation), confidence, now, cid))
        return row

    def knowledge_mutation(self, *, subject: str, previous_knowledge_refs: list[str],
                           new_knowledge_refs: list[str], mutation_type: str,
                           caused_by_kind: str, caused_by_id: str,
                           correlation_id: str | None = None) -> KnowledgeMutation:
        if caused_by_kind not in {"INTERPRETATION", "AUTHORITY"}:
            raise ValueError("knowledge mutation must be caused by INTERPRETATION or AUTHORITY")
        table = "ew_interpretations" if caused_by_kind == "INTERPRETATION" else "ew_authority_events"
        if not self._exists(table, caused_by_id):
            raise ValueError(f"{caused_by_kind} cause does not exist")
        cid = correlation_id or self._correlation_for(table, caused_by_id)
        rid = _id("km"); now = _now()
        row = KnowledgeMutation(rid, subject, previous_knowledge_refs, new_knowledge_refs, mutation_type, caused_by_kind, caused_by_id, now, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_knowledge_mutations VALUES (?,?,?,?,?,?,?,?,?)",
                      (rid, subject, _json(previous_knowledge_refs), _json(new_knowledge_refs), mutation_type, caused_by_kind, caused_by_id, now, cid))
        return row

    def operational_event(self, *, subject: str, enterprise_id: str, event_type: str,
                          payload: Any, workload_id: str | None = None,
                          workstream_id: str | None = None, caused_by_kind: str | None = None,
                          caused_by_id: str | None = None, correlation_id: str | None = None) -> OperationalEvent:
        event_type = str(event_type).upper()
        if event_type not in OPERATIONAL_EVENT_TYPES:
            raise ValueError(f"unsupported operational event type: {event_type}")
        cid = correlation_id or self._correlation_for_any(caused_by_kind, caused_by_id)
        eid = _id("oe"); now = _now()
        row = OperationalEvent(eid, subject, enterprise_id, workload_id, workstream_id, event_type, payload, now, caused_by_kind, caused_by_id, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_operational_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (eid, subject, enterprise_id, workload_id, workstream_id, event_type, _json(payload), now, caused_by_kind, caused_by_id, cid))
        return row

    def proposal(self, *, subject: str, enterprise_id: str, objective: str, rationale: str,
                 recommended_actions: list[Any], required_authority: str,
                 tool_selections: list[Any], correlation_id: str | None = None) -> Proposal:
        rid = _id("prop"); cid = correlation_id or _id("corr"); now = _now()
        row = Proposal(rid, subject, enterprise_id, objective, rationale, recommended_actions,
                       required_authority, tool_selections, "PROPOSED", now, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_proposals VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (rid, subject, enterprise_id, objective, rationale, _json(recommended_actions),
                       required_authority, _json(tool_selections), "PROPOSED", now, cid))
        return row

    def authority_event(self, *, subject: str, actor: str, authority_context: str,
                        action: str, previous_state: Any, new_state: Any,
                        origin: str, authentication_context: str,
                        evidence_refs: list[str] | None = None,
                        correlation_id: str | None = None) -> HumanAuthorityEvent:
        rid = _id("hae"); cid = correlation_id or _id("corr"); now = _now()
        row = HumanAuthorityEvent(rid, subject, actor, authority_context, action,
                                  previous_state, new_state, now, origin,
                                  authentication_context, cid, list(evidence_refs or []))
        with _db() as c:
            c.execute("INSERT INTO ew_authority_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (rid, subject, actor, authority_context, action, _json(previous_state),
                       _json(new_state), now, origin, authentication_context, cid, _json(evidence_refs or [])))
        return row

    def authorize(self, *, subject: str, proposal_id: str, authority_event_id: str,
                  scope: Any, constraints: Any, expires_at: float | None = None,
                  acceptance_id: str | None = None,
                  correlation_id: str | None = None) -> Authorization:
        proposal = self._row("ew_proposals", proposal_id)
        authority = self._row("ew_authority_events", authority_event_id)
        if not proposal or not authority:
            raise ValueError("proposal and human authority event are required")
        if proposal["subject"] != subject or authority["subject"] != subject:
            raise ValueError("subject mismatch")
        if str(authority["action"]).upper() not in {"AUTHORIZE", "APPROVE_PROPOSAL"}:
            raise ValueError("authority event does not authorize proposal")
        if authority["correlation_id"] != proposal["correlation_id"]:
            raise ValueError("authority event is not causally bound to proposal")
        if acceptance_id:
            acceptance = self._row("ew_acceptances", acceptance_id)
            if not acceptance or acceptance["subject"] != subject:
                raise ValueError("matching acceptance required")
            if acceptance["verification_id"] == "":
                raise ValueError("acceptance verification reference required")
            if acceptance["correlation_id"] != proposal["correlation_id"]:
                raise ValueError("acceptance is not causally bound to proposal")
        cid = correlation_id or proposal["correlation_id"]
        rid = _id("auth"); now = _now()
        row = Authorization(rid, subject, proposal_id, authority_event_id, acceptance_id, scope, constraints, expires_at, now, cid)
        with _db() as c:
            c.execute("""INSERT INTO ew_authorizations
                         (id, subject, proposal_id, authority_event_id, acceptance_id,
                          scope, constraints, expires_at, granted_at, correlation_id)
                         VALUES (?,?,?,?,?,?,?,?,?,?)""",
                      (rid, subject, proposal_id, authority_event_id, acceptance_id,
                       _json(scope), _json(constraints), expires_at, now, cid))
            c.execute("UPDATE ew_proposals SET status='AUTHORIZED' WHERE id=?", (proposal_id,))
        return row

    def authorization(self, *, subject: str, authorization_id: str) -> Authorization:
        row = self._row("ew_authorizations", authorization_id)
        if not row or row["subject"] != subject:
            raise ValueError("valid matching authorization required")
        return Authorization(
            row["id"], row["subject"], row["proposal_id"], row["authority_event_id"],
            row["acceptance_id"], json.loads(row["scope"]), json.loads(row["constraints"]), row["expires_at"],
            row["granted_at"], row["correlation_id"],
        )

    def complete_execution_attempt(self, *, subject: str, execution_attempt_id: str,
                                   result_status: str) -> ExecutionAttempt:
        status = str(result_status).upper()
        if status not in {"SUCCEEDED", "FAILED", "BLOCKED"}:
            raise ValueError(f"unsupported terminal execution status: {status}")
        row = self._row("ew_execution_attempts", execution_attempt_id)
        if not row or row["subject"] != subject:
            raise ValueError("matching execution attempt required")
        with _db() as c:
            c.execute("UPDATE ew_execution_attempts SET result_status=? WHERE id=?",
                      (status, execution_attempt_id))
        row = self._row("ew_execution_attempts", execution_attempt_id)
        attempt = ExecutionAttempt(
            row["id"], row["subject"], row["authorization_id"], row["tool_channel"],
            json.loads(row["request_payload"]), row["attempted_at"], row["result_status"],
            row["correlation_id"],
        )

        # Terminal Weaver lifecycle transition automatically records the causal
        # SolSpire WorkEvent. The bridge is observational only: it grants no
        # authority and does not imply review, completion, or production acceptance.
        authorization = self._row("ew_authorizations", row["authorization_id"])
        proposal = self._row("ew_proposals", authorization["proposal_id"]) if authorization else None
        if not proposal or proposal["subject"] != subject:
            raise ValueError("matching proposal required to resolve WorkEvent workspace")
        from weaver.execution_workevent_bridge import capture_execution_workevent
        capture_execution_workevent(
            store=self,
            subject=subject,
            execution_attempt_id=attempt.id,
            workspace_ref=proposal["enterprise_id"],
        )
        return attempt

    def execution_attempt(self, *, subject: str, authorization_id: str, tool_channel: str,
                          request_payload: Any, result_status: str = "ATTEMPTED",
                          correlation_id: str | None = None) -> ExecutionAttempt:
        auth = self._row("ew_authorizations", authorization_id)
        if not auth or auth["subject"] != subject:
            raise ValueError("valid matching authorization required before execution")
        if auth["expires_at"] is not None and float(auth["expires_at"]) < _now():
            raise ValueError("authorization has expired")
        status = result_status.upper()
        if status not in EXECUTION_STATUSES:
            raise ValueError(f"unsupported execution status: {status}")
        if status == "SUCCEEDED":
            raise ValueError("execution success requires EvidenceRecord; create attempt first")
        rid = _id("exec"); now = _now(); cid = correlation_id or auth["correlation_id"]
        row = ExecutionAttempt(rid, subject, authorization_id, tool_channel, request_payload, now, status, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_execution_attempts VALUES (?,?,?,?,?,?,?,?)",
                      (rid, subject, authorization_id, tool_channel, _json(request_payload), now, status, cid))
        return row

    def evidence(self, *, subject: str, evidence_type: str, content_or_ref: Any,
                 execution_attempt_id: str | None = None, source_ref: str | None = None,
                 correlation_id: str | None = None) -> EvidenceRecord:
        if not execution_attempt_id and not source_ref:
            raise ValueError("evidence requires execution_attempt_id or source_ref")
        if execution_attempt_id:
            attempt = self._row("ew_execution_attempts", execution_attempt_id)
            if not attempt or attempt["subject"] != subject:
                raise ValueError("matching execution attempt required")
        rid = _id("ev"); now = _now()
        cid = correlation_id or (self._correlation_for("ew_execution_attempts", execution_attempt_id) if execution_attempt_id else _id("corr"))
        row = EvidenceRecord(rid, subject, execution_attempt_id, source_ref, evidence_type, content_or_ref, now, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_evidence VALUES (?,?,?,?,?,?,?,?)",
                      (rid, subject, execution_attempt_id, source_ref, evidence_type, _json(content_or_ref), now, cid))
            if execution_attempt_id:
                c.execute("UPDATE ew_execution_attempts SET result_status='SUCCEEDED' WHERE id=?", (execution_attempt_id,))
        return row

    def verify(self, *, subject: str, claim: str, evidence_refs: list[str],
               verifier: str, verdict: str, correlation_id: str | None = None) -> VerificationRecord:
        verdict = verdict.upper()
        if verdict not in VERIFICATION_VERDICTS:
            raise ValueError(f"unsupported verification verdict: {verdict}")
        if not evidence_refs:
            raise ValueError("verification requires evidence references")
        missing = [ref for ref in evidence_refs if not self._exists("ew_evidence", ref)]
        if missing:
            raise ValueError(f"verification evidence missing: {missing}")
        with _db() as c:
            rows = c.execute(
                "SELECT id, subject FROM ew_evidence WHERE id IN (%s)" % ",".join("?" for _ in evidence_refs),
                tuple(evidence_refs),
            ).fetchall()
        foreign = [row["id"] for row in rows if row["subject"] != subject]
        if foreign:
            raise ValueError(f"verification evidence subject mismatch: {foreign}")
        rid = _id("vr"); now = _now()
        cid = correlation_id or self._correlation_for("ew_evidence", evidence_refs[0])
        row = VerificationRecord(rid, subject, claim, evidence_refs, verdict, now, verifier, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_verifications VALUES (?,?,?,?,?,?,?,?)",
                      (rid, subject, claim, _json(evidence_refs), verdict, now, verifier, cid))
        return row

    def acceptance(self, *, subject: str, verification_id: str, accepted_result_ref: str,
                    accepting_authority: str, authorization_scope: Any,
                    context_ref: str, correlation_id: str | None = None) -> AcceptanceRecord:
        verification = self._row("ew_verifications", verification_id)
        if not verification or verification["subject"] != subject:
            raise ValueError("matching verification required before acceptance")
        if str(verification["verdict"]).upper() != "VERIFIED":
            raise ValueError("only VERIFIED results may be accepted")
        if not accepting_authority.strip():
            raise ValueError("acceptance requires explicit accepting authority")
        if not context_ref.strip():
            raise ValueError("acceptance requires explicit context")
        if not authorization_scope:
            raise ValueError("acceptance requires explicit bounded scope")
        cid = correlation_id or verification["correlation_id"]
        rid = _id("accept"); now = _now()
        row = AcceptanceRecord(rid, subject, verification_id, accepted_result_ref,
                               accepting_authority, authorization_scope, context_ref,
                               now, "ACCEPTED", cid)
        with _db() as c:
            c.execute("INSERT INTO ew_acceptances VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (rid, subject, verification_id, accepted_result_ref,
                       accepting_authority, _json(authorization_scope), context_ref,
                       now, "ACCEPTED", cid))
        return row

    def review(self, *, subject: str, work_event_id: str, reviewer: str,
               verdict: str, findings: Any, amendment_of: str | None = None,
               correlation_id: str | None = None) -> ReviewRecord:
        verdict = str(verdict).upper()
        if verdict not in {"ACCEPTED", "REJECTED", "CLARIFIED"}:
            raise ValueError("unsupported review verdict")
        if not reviewer.strip():
            raise ValueError("review requires explicit reviewer")
        if not work_event_id.strip():
            raise ValueError("review requires WorkEvent reference")
        from solspire.workevent_manager import get_workevent_manager
        if get_workevent_manager().get(work_event_id, subject) is None:
            raise ValueError("matching WorkEvent required before review")
        cid = correlation_id or _id("corr")
        rid = _id("review"); now = _now()
        row = ReviewRecord(rid, subject, work_event_id, reviewer, verdict, findings,
                           now, amendment_of, cid)
        with _db() as c:
            c.execute("INSERT INTO ew_reviews VALUES (?,?,?,?,?,?,?,?,?)",
                      (rid, subject, work_event_id, reviewer, verdict, _json(findings),
                       now, amendment_of, cid))
        return row

    def completion(self, *, subject: str, work_event_id: str, review_id: str,
                   condition: str, supporting_evidence_refs: list[str],
                   correlation_id: str | None = None) -> CompletionRecord:
        review = self._row("ew_reviews", review_id)
        if not review or review["subject"] != subject:
            raise ValueError("matching review required before completion")
        if review["work_event_id"] != work_event_id:
            raise ValueError("review and WorkEvent mismatch")
        if str(review["verdict"]).upper() != "ACCEPTED":
            raise ValueError("completion requires an ACCEPTED review")
        if not condition.strip():
            raise ValueError("completion requires an explicit condition")
        if not supporting_evidence_refs:
            raise ValueError("completion requires supporting evidence")
        cid = correlation_id or review["correlation_id"]
        rid = _id("complete"); now = _now()
        row = CompletionRecord(rid, subject, work_event_id, review_id, condition,
                               list(supporting_evidence_refs), now, "COMPLETED", cid)
        with _db() as c:
            c.execute("INSERT INTO ew_completions VALUES (?,?,?,?,?,?,?,?,?)",
                      (rid, subject, work_event_id, review_id, condition,
                       _json(supporting_evidence_refs), now, "COMPLETED", cid))
        return row

    def production_acceptance(self, *, subject: str, completion_id: str,
                              accepting_authority: str, context_ref: str,
                              correlation_id: str | None = None) -> ProductionAcceptanceRecord:
        completion = self._row("ew_completions", completion_id)
        if not completion or completion["subject"] != subject:
            raise ValueError("matching completion required before production acceptance")
        if str(completion["status"]).upper() != "COMPLETED":
            raise ValueError("production acceptance requires COMPLETED result")
        if not accepting_authority.strip():
            raise ValueError("production acceptance requires explicit authority")
        if not context_ref.strip():
            raise ValueError("production acceptance requires explicit context")
        cid = correlation_id or completion["correlation_id"]
        rid = _id("prodaccept"); now = _now()
        row = ProductionAcceptanceRecord(rid, subject, completion_id,
                                         accepting_authority, context_ref, now,
                                         "ACCEPTED", cid)
        with _db() as c:
            c.execute("INSERT INTO ew_production_acceptances VALUES (?,?,?,?,?,?,?,?)",
                      (rid, subject, completion_id, accepting_authority, context_ref,
                       now, "ACCEPTED", cid))
        return row

    def stream(self, *, subject: str, enterprise_id: str, limit: int = 100) -> list[OperationalEvent]:
        limit = max(1, min(int(limit), 500))
        with _db() as c:
            rows = c.execute(
                "SELECT * FROM ew_operational_events WHERE subject=? AND enterprise_id=? ORDER BY timestamp ASC LIMIT ?",
                (subject, enterprise_id, limit),
            ).fetchall()
        return [OperationalEvent(
            r["id"], r["subject"], r["enterprise_id"], r["workload_id"], r["workstream_id"],
            r["event_type"], json.loads(r["payload"]), r["timestamp"], r["caused_by_kind"],
            r["caused_by_id"], r["correlation_id"]
        ) for r in rows]

    def operational_state(self, *, subject: str, enterprise_id: str) -> dict[str, Any]:
        """GATE-07: derive the explicit operational state of a loop.

        A read-only projection over the append-only records, not a store of its
        own. Each stage is reported independently: a PROPOSED proposal is never
        reported as AUTHORIZED, and an execution is never reported as VERIFIED
        unless a verification record exists. Missing evidence stays UNKNOWN.
        """
        stream = self.stream(subject=subject, enterprise_id=enterprise_id, limit=500)
        with _db() as c:
            proposals = c.execute(
                "SELECT id, objective, status FROM ew_proposals WHERE subject=? AND enterprise_id=?",
                (subject, enterprise_id),
            ).fetchall()
            attempts = c.execute(
                """SELECT a.id, a.result_status FROM ew_execution_attempts a
                   JOIN ew_authorizations z ON a.authorization_id = z.id
                   JOIN ew_proposals p ON z.proposal_id = p.id
                   WHERE a.subject=? AND p.enterprise_id=?""",
                (subject, enterprise_id),
            ).fetchall()
            verifications = c.execute(
                "SELECT id, claim, verdict FROM ew_verifications WHERE subject=?",
                (subject,),
            ).fetchall()
        unknowns = [
            e.payload for e in stream if e.event_type == "UNCERTAINTY_DETECTED"
        ]
        event_types = [e.event_type for e in stream]
        return {
            "subject": subject,
            "enterprise_id": enterprise_id,
            "observed": bool(stream),
            "event_count": len(stream),
            "last_event": event_types[-1] if event_types else None,
            "event_types": event_types,
            "proposals": {p["id"]: p["status"] for p in proposals},
            "awaiting_authority": [
                p["id"] for p in proposals if p["status"] in {"PROPOSED", "AWAITING_AUTHORITY"}
            ],
            "authorized": [p["id"] for p in proposals if p["status"] == "AUTHORIZED"],
            "executions": {a["id"]: a["result_status"] for a in attempts},
            "verified_claims": [
                {"id": v["id"], "claim": v["claim"], "verdict": v["verdict"]}
                for v in verifications if v["verdict"] == "VERIFIED"
            ],
            "unknowns": unknowns,
        }

    def reverse_walk(self, *, subject: str, kind: str, record_id: str) -> dict[str, Any]:
        """Return the inspectable ancestry of a claim/record; never infers missing links."""
        kind = kind.upper()
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        def visit(k: str, rid: str | None):
            if not rid or (k, rid) in seen:
                return
            seen.add((k, rid))
            table = {
                "CANONICAL_RECORD": "ew_canonical_records", "AUTHORITY_EVENT": "ew_authority_events",
                "INTERPRETATION": "ew_interpretations", "KNOWLEDGE_MUTATION": "ew_knowledge_mutations",
                "OPERATIONAL_EVENT": "ew_operational_events", "PROPOSAL": "ew_proposals",
                "AUTHORIZATION": "ew_authorizations", "EXECUTION_ATTEMPT": "ew_execution_attempts",
                "EVIDENCE": "ew_evidence", "VERIFICATION": "ew_verifications",
            }.get(k)
            if not table:
                raise ValueError(f"unsupported record kind: {k}")
            row = self._row(table, rid)
            if not row or row["subject"] != subject:
                return
            data = dict(row)
            rows.append({"kind": k, "id": rid, "record": data})
            if k == "VERIFICATION":
                for ref in json.loads(row["evidence_refs"]):
                    visit("EVIDENCE", ref)
            elif k == "EVIDENCE":
                if row["execution_attempt_id"]:
                    visit("EXECUTION_ATTEMPT", row["execution_attempt_id"])
                elif row["source_ref"]:
                    visit("CANONICAL_RECORD", row["source_ref"])
            elif k == "EXECUTION_ATTEMPT":
                visit("AUTHORIZATION", row["authorization_id"])
            elif k == "AUTHORIZATION":
                visit("PROPOSAL", row["proposal_id"]); visit("AUTHORITY_EVENT", row["authority_event_id"])
            elif k == "INTERPRETATION":
                visit("CANONICAL_RECORD", row["canonical_record_id"])
            elif k == "KNOWLEDGE_MUTATION":
                visit(row["caused_by_kind"], row["caused_by_id"])
            elif k == "OPERATIONAL_EVENT":
                visit(row["caused_by_kind"], row["caused_by_id"])
        visit(kind, record_id)
        root_kinds = {"CANONICAL_RECORD", "AUTHORITY_EVENT"}
        roots = [r for r in rows if r["kind"] in root_kinds]
        return {"subject": subject, "claim_kind": kind, "claim_id": record_id,
                "complete": bool(roots), "records": rows}

    def forward_walk(self, *, subject: str, kind: str, record_id: str) -> dict[str, Any]:
        """Trace forward from a root (source or authority) to its consequences.

        Complement to reverse_walk: given a canonical record or authority event,
        return every record derived from it by following stored foreign keys.
        Never invents a link — a record absent from the store is not traversed.
        """
        kind = kind.upper()
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def record(k: str, rid: str | None) -> dict[str, Any] | None:
            table = {
                "CANONICAL_RECORD": "ew_canonical_records", "AUTHORITY_EVENT": "ew_authority_events",
                "INTERPRETATION": "ew_interpretations", "KNOWLEDGE_MUTATION": "ew_knowledge_mutations",
                "OPERATIONAL_EVENT": "ew_operational_events", "PROPOSAL": "ew_proposals",
                "AUTHORIZATION": "ew_authorizations", "EXECUTION_ATTEMPT": "ew_execution_attempts",
                "EVIDENCE": "ew_evidence", "VERIFICATION": "ew_verifications",
            }.get(k)
            if not table or not rid:
                return None
            row = self._row(table, rid)
            if not row or row["subject"] != subject:
                return None
            return dict(row)

        def visit(k: str, rid: str | None):
            key = (k, rid)
            if not rid or key in seen:
                return
            row = record(k, rid)
            if row is None:
                return
            seen.add(key)
            rows.append({"kind": k, "id": rid, "record": row})
            if k == "CANONICAL_RECORD":
                for r in self._rows_where("ew_interpretations", "canonical_record_id", rid, subject):
                    visit("INTERPRETATION", r["id"])
                for r in self._rows_where("ew_evidence", "source_ref", rid, subject):
                    visit("EVIDENCE", r["id"])
                for r in self._rows_where("ew_operational_events", "caused_by_id", rid, subject):
                    visit("OPERATIONAL_EVENT", r["id"])
            elif k == "AUTHORITY_EVENT":
                for r in self._rows_where("ew_authorizations", "authority_event_id", rid, subject):
                    visit("AUTHORIZATION", r["id"])
                for r in self._rows_where("ew_knowledge_mutations", "caused_by_id", rid, subject):
                    visit("KNOWLEDGE_MUTATION", r["id"])
            elif k == "INTERPRETATION":
                for r in self._rows_where("ew_knowledge_mutations", "caused_by_id", rid, subject):
                    visit("KNOWLEDGE_MUTATION", r["id"])
                for r in self._rows_where("ew_operational_events", "caused_by_id", rid, subject):
                    visit("OPERATIONAL_EVENT", r["id"])
            elif k == "PROPOSAL":
                for r in self._rows_where("ew_authorizations", "proposal_id", rid, subject):
                    visit("AUTHORIZATION", r["id"])
                for r in self._rows_where("ew_operational_events", "caused_by_id", rid, subject):
                    visit("OPERATIONAL_EVENT", r["id"])
            elif k == "AUTHORIZATION":
                for r in self._rows_where("ew_execution_attempts", "authorization_id", rid, subject):
                    visit("EXECUTION_ATTEMPT", r["id"])
            elif k == "EXECUTION_ATTEMPT":
                for r in self._rows_where("ew_evidence", "execution_attempt_id", rid, subject):
                    visit("EVIDENCE", r["id"])
                for r in self._rows_where("ew_operational_events", "caused_by_id", rid, subject):
                    visit("OPERATIONAL_EVENT", r["id"])
            elif k == "EVIDENCE":
                for v in self._all_rows("ew_verifications", subject):
                    if rid in json.loads(v["evidence_refs"]):
                        visit("VERIFICATION", v["id"])
                for r in self._rows_where("ew_operational_events", "caused_by_id", rid, subject):
                    visit("OPERATIONAL_EVENT", r["id"])

        visit(kind, record_id)
        return {"subject": subject, "root_kind": kind, "root_id": record_id,
                "records": rows}

    def explain_execution(self, *, subject: str, execution_attempt_id: str) -> dict[str, Any]:
        """GATE-08: assemble the inspectable operational rationale for an attempt.

        Reports what happened (attempt), under what authority (authorization and
        its human authority event), for what objective/tool (proposal), and what
        evidence resulted (evidence). Read-only projection over records that
        already exist — it introduces no new mutation path.
        """
        attempt = self._row("ew_execution_attempts", execution_attempt_id)
        if not attempt or attempt["subject"] != subject:
            return {"subject": subject, "execution_attempt_id": execution_attempt_id,
                    "complete": False, "reason": "UNKNOWN"}
        auth = self._row("ew_authorizations", attempt["authorization_id"])
        proposal = self._row("ew_proposals", auth["proposal_id"]) if auth else None
        authority = self._row("ew_authority_events", auth["authority_event_id"]) if auth else None
        evidence = self._rows_where("ew_evidence", "execution_attempt_id", execution_attempt_id, subject)
        return {
            "subject": subject,
            "execution_attempt_id": execution_attempt_id,
            "complete": bool(auth),
            "objective": proposal["objective"] if proposal else None,
            "proposed_tool_selections": json.loads(proposal["tool_selections"]) if proposal else [],
            "required_authority": proposal["required_authority"] if proposal else None,
            "tool_channel": attempt["tool_channel"],
            "result_status": attempt["result_status"],
            "authorization": None if not auth else {
                "id": auth["id"], "scope": json.loads(auth["scope"]),
                "constraints": json.loads(auth["constraints"]),
            },
            "authority_event": None if not authority else {
                "id": authority["id"], "actor": authority["actor"], "action": authority["action"],
                "origin": authority["origin"],
            },
            "evidence_refs": [e["id"] for e in evidence],
        }

    def _rows_where(self, table: str, column: str, value: Any, subject: str) -> list[Any]:
        with _db() as c:
            return c.execute(
                f"SELECT * FROM {table} WHERE {column}=? AND subject=?", (value, subject)
            ).fetchall()

    def _all_rows(self, table: str, subject: str) -> list[Any]:
        with _db() as c:
            return c.execute(f"SELECT * FROM {table} WHERE subject=?", (subject,)).fetchall()

    def _row(self, table: str, rid: str | None):
        if not rid:
            return None
        with _db() as c:
            return c.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()

    def _exists(self, table: str, rid: str | None) -> bool:
        return self._row(table, rid) is not None

    def _correlation_for(self, table: str, rid: str | None) -> str:
        row = self._row(table, rid)
        if not row:
            raise ValueError("referenced record does not exist")
        return row["correlation_id"]

    def _correlation_for_any(self, kind: str | None, rid: str | None) -> str:
        if kind and rid:
            table = {
                "CANONICAL_RECORD": "ew_canonical_records", "AUTHORITY_EVENT": "ew_authority_events",
                "INTERPRETATION": "ew_interpretations", "KNOWLEDGE_MUTATION": "ew_knowledge_mutations",
                "OPERATIONAL_EVENT": "ew_operational_events", "PROPOSAL": "ew_proposals",
            }.get(kind.upper())
            if table:
                return self._correlation_for(table, rid)
        return _id("corr")

def simulate_eden_supplier_path(store: EnterpriseOrchestrationStore, *, subject: str,
                                enterprise_id: str, interpreter: str = "arkana-test") -> dict[str, Any]:
    """Deterministic simulated supplier path for ARK-WEAVER-01 acceptance testing."""
    canonical = store.canonical_record(
        subject=subject, source_channel="simulated_supplier_message",
        raw_payload={"message": "Supplier A says potatoes are available tomorrow; price not confirmed."},
        ingested_by="test",
    )
    interpretation = store.interpretation(
        subject=subject, canonical_record_id=canonical.id, interpreter=interpreter,
        interpretation={"availability": "APPEARS_AVAILABLE", "price": "UNKNOWN"}, confidence=0.71,
    )
    mutation = store.knowledge_mutation(
        subject=subject, previous_knowledge_refs=[],
        new_knowledge_refs=["eden:supplier:A:availability=appears_available"],
        mutation_type="SUPPLIER_AVAILABILITY_UPDATED",
        caused_by_kind="INTERPRETATION", caused_by_id=interpretation.id,
    )
    store.operational_event(
        subject=subject, enterprise_id=enterprise_id, workload_id="EDEN-PILOT-CYCLE-01",
        event_type="INPUT_RECEIVED", payload={"canonical_record_id": canonical.id},
        caused_by_kind="CANONICAL_RECORD", caused_by_id=canonical.id, correlation_id=canonical.correlation_id,
    )
    store.operational_event(
        subject=subject, enterprise_id=enterprise_id, workload_id="EDEN-PILOT-CYCLE-01",
        event_type="UNCERTAINTY_DETECTED", payload={"field": "price", "value": "UNKNOWN"},
        caused_by_kind="INTERPRETATION", caused_by_id=interpretation.id, correlation_id=interpretation.correlation_id,
    )
    proposal = store.proposal(
        subject=subject, enterprise_id=enterprise_id,
        objective="Resolve potato supplier price",
        rationale="Availability is indicated but price remains UNKNOWN.",
        recommended_actions=["verify supplier price", "do not commit funds"],
        required_authority="human",
        tool_selections=["supplier_verification"],
    )
    authority = store.authority_event(
        subject=subject, actor=subject, authority_context="Eden Cycle 01",
        action="APPROVE_PROPOSAL", previous_state="AWAITING_AUTHORITY",
        new_state="AUTHORIZED_FOR_PRICE_VERIFICATION", origin="human",
        authentication_context="authenticated_subject",
        correlation_id=proposal.correlation_id,
    )
    authorization = store.authorize(
        subject=subject, proposal_id=proposal.id, authority_event_id=authority.id,
        scope={"enterprise_id": enterprise_id, "objective": proposal.objective},
        constraints={"funds_commitment": False},
    )
    attempt = store.execution_attempt(
        subject=subject, authorization_id=authorization.id,
        tool_channel="simulated_supplier_verification",
        request_payload={"supplier": "A", "field": "price"},
    )
    evidence = store.evidence(
        subject=subject, execution_attempt_id=attempt.id, evidence_type="simulated_supplier_response",
        content_or_ref={"supplier": "A", "price_ngn_per_kg": 1200, "received": True},
    )
    verification = store.verify(
        subject=subject,
        claim="Supplier A price is ₦1,200/kg for the simulated verification.",
        evidence_refs=[evidence.id], verifier="test-verifier", verdict="VERIFIED",
    )
    return {"canonical": canonical, "interpretation": interpretation, "knowledge_mutation": mutation,
            "proposal": proposal, "authority_event": authority, "authorization": authorization,
            "execution_attempt": attempt, "evidence": evidence, "verification": verification}

__all__ = [
    "CanonicalRecord", "HumanAuthorityEvent", "InterpretationRecord", "KnowledgeMutation",
    "OperationalEvent", "Proposal", "Authorization", "ExecutionAttempt", "EvidenceRecord",
    "VerificationRecord", "EnterpriseOrchestrationStore", "simulate_eden_supplier_path",
]
