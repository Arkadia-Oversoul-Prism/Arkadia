from __future__ import annotations

from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALXAI_VERSION = "04.1"


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canon(value).encode()).hexdigest()


class ObservationMode(str, Enum):
    DIRECT_API = "DIRECT_API"
    DIRECT_UI = "DIRECT_UI"
    DIRECT_FILE = "DIRECT_FILE"
    DIRECT_RUNTIME = "DIRECT_RUNTIME"
    DIRECT_DATABASE = "DIRECT_DATABASE"
    DIRECT_HUMAN_REPORT = "DIRECT_HUMAN_REPORT"
    INHERITED_PACKET = "INHERITED_PACKET"
    INHERITED_STATE = "INHERITED_STATE"
    RELAYED_EVIDENCE = "RELAYED_EVIDENCE"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    HYPOTHESIZED = "HYPOTHESIZED"
    UNKNOWN = "UNKNOWN"


class EpistemicClass(str, Enum):
    OBSERVED_FACT = "OBSERVED_FACT"
    REPORTED_FACT = "REPORTED_FACT"
    DERIVED_FACT = "DERIVED_FACT"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    DECISION = "DECISION"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"


class Status(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"


class ALXModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class Evidence(ALXModel):
    evidence_id: str
    source_id: str
    source_authority: str
    observation_mode: ObservationMode
    observed_at: datetime | None = None
    event_at: datetime | None = None
    locator: str | None = None
    content_digest: str | None = None
    supports: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)
    collector_node: str
    integrity_status: Literal["VALID", "INVALID", "UNKNOWN"] = "UNKNOWN"


class Claim(ALXModel):
    claim_id: str
    subject: str
    predicate: str
    object: Any
    scope: str = "global"
    status: Status = Status.ACTIVE
    source_authority: str = "UNKNOWN"
    observation_mode: ObservationMode = ObservationMode.UNKNOWN
    epistemic_class: EpistemicClass = EpistemicClass.UNKNOWN
    observed_at: datetime | None = None
    event_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    supports: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    refines: list[str] = Field(default_factory=list)
    derived_from: list[str] = Field(default_factory=list)

    @field_validator("claim_id")
    @classmethod
    def stable_id(cls, v: str) -> str:
        if not v or v.strip() != v:
            raise ValueError("claim_id must be non-empty and canonical")
        return v


class Event(ALXModel):
    event_id: str
    event_type: str
    actor: str
    subject: str
    occurred_at: datetime | None = None
    observed_at: datetime | None = None
    authorization_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    previous_state: str | None = None
    resulting_state: str | None = None
    status: str = "UNKNOWN"


class Decision(ALXModel):
    decision_id: str
    decision_maker: str
    decision_scope: str
    question: str
    decision: str
    evidence_refs: list[str] = Field(default_factory=list)
    authorized_actions: list[str] = Field(default_factory=list)
    decided_at: datetime | None = None
    status: str = "UNKNOWN"


class Capability(ALXModel):
    operation: str
    status: Literal["AVAILABLE", "UNAVAILABLE", "UNAUTHORIZED", "UNKNOWN"]
    scope: str = "global"


class Source(ALXModel):
    source_id: str
    domain: str
    authority_scope: list[str] = Field(default_factory=list)
    access_status: str = "UNKNOWN"
    freshness: str = "UNKNOWN"
    observation_methods: list[ObservationMode] = Field(default_factory=list)


class State(ALXModel):
    state_id: str
    parent_state_id: str | None = None
    protocol_version: str = ALXAI_VERSION
    created_at: datetime
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    source_registry: list[Source] = Field(default_factory=list)
    state_digest: str | None = None

    def canonical_payload(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude={"state_digest"})
        return data

    def with_root(self) -> "State":
        raw = self.model_copy(update={"state_digest": None})
        return raw.model_copy(update={"state_digest": digest(raw.canonical_payload())})


class Delta(ALXModel):
    delta_id: str
    parent_state_id: str
    resulting_state_id: str
    created_at: datetime
    contributor_node: str
    claims_added: list[Claim] = Field(default_factory=list)
    claims_updated: list[Claim] = Field(default_factory=list)
    claims_superseded: list[str] = Field(default_factory=list)
    evidence_added: list[Evidence] = Field(default_factory=list)
    events_added: list[Event] = Field(default_factory=list)
    decisions_added: list[Decision] = Field(default_factory=list)
    conflicts_added: list[str] = Field(default_factory=list)
    unknowns_added: list[str] = Field(default_factory=list)
    capability_changes: list[Capability] = Field(default_factory=list)
    source_observations: list[str] = Field(default_factory=list)
    integrity_digest: str | None = None

    def canonical_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"integrity_digest"})

    def with_digest(self) -> "Delta":
        raw = self.model_copy(update={"integrity_digest": None})
        return raw.model_copy(update={"integrity_digest": digest(raw.canonical_payload())})


def create_state(*, parent_state_id: str | None, created_at: datetime, **kwargs: Any) -> State:
    return State(parent_state_id=parent_state_id, created_at=created_at, **kwargs).with_root()


def create_delta(*, parent: State, contributor_node: str, created_at: datetime, resulting_state: State, **kwargs: Any) -> Delta:
    if resulting_state.parent_state_id != parent.state_id:
        raise ValueError("resulting state must point to parent state")
    delta_id = kwargs.pop("delta_id", f"DELTA-{resulting_state.state_id}")
    return Delta(
        delta_id=delta_id,
        parent_state_id=parent.state_id,
        resulting_state_id=resulting_state.state_id,
        created_at=created_at,
        contributor_node=contributor_node,
        **kwargs,
    ).with_digest()


def apply_delta(parent: State, delta: Delta) -> State:
    if delta.parent_state_id != parent.state_id:
        raise ValueError("delta parent does not match supplied state")
    if delta.integrity_digest != digest(delta.canonical_payload()):
        raise ValueError("delta integrity digest mismatch")
    claims = {c.claim_id: c for c in parent.claims}
    for c in delta.claims_added + delta.claims_updated:
        claims[c.claim_id] = c
    for cid in delta.claims_superseded:
        if cid in claims:
            claims[cid] = claims[cid].model_copy(update={"status": Status.SUPERSEDED})
    evidence = {e.evidence_id: e for e in parent.evidence}
    evidence.update({e.evidence_id: e for e in delta.evidence_added})
    events = {e.event_id: e for e in parent.events}
    events.update({e.event_id: e for e in delta.events_added})
    decisions = {d.decision_id: d for d in parent.decisions}
    decisions.update({d.decision_id: d for d in delta.decisions_added})
    result = State(
        state_id=delta.resulting_state_id,
        parent_state_id=parent.state_id,
        protocol_version=parent.protocol_version,
        created_at=delta.created_at,
        claims=list(claims.values()), evidence=list(evidence.values()),
        events=list(events.values()), decisions=list(decisions.values()),
        conflicts=parent.conflicts + delta.conflicts_added,
        unknowns=parent.unknowns + delta.unknowns_added,
        capabilities=delta.capability_changes or parent.capabilities,
        source_registry=parent.source_registry,
    )
    return result.with_root()


def _claim_key(c: Claim) -> tuple[str, str, str, str]:
    return (c.subject, c.predicate, _canon(c.object), c.scope)


def validate_packet(packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        state = State.model_validate(packet.get("state"))
    except Exception as exc:
        return {"status": "INVALID", "errors": [f"state: {exc}"], "warnings": []}
    if state.state_digest != digest(state.canonical_payload()):
        errors.append("state integrity digest mismatch")
    claim_ids = [c.claim_id for c in state.claims]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("duplicate claim_id")
    evidence_ids = {e.evidence_id for e in state.evidence}
    for c in state.claims:
        missing = set(c.evidence_refs) - evidence_ids
        if missing:
            errors.append(f"claim {c.claim_id} references missing evidence: {sorted(missing)}")
        if c.observation_mode in {ObservationMode.INFERRED, ObservationMode.HYPOTHESIZED} and c.epistemic_class == EpistemicClass.OBSERVED_FACT:
            errors.append(f"claim {c.claim_id}: inference/hypothesis cannot be OBSERVED_FACT")
    # Packet-level future metadata is a warning/error boundary, not a rewrite of source timestamps.
    packet_created = packet.get("created_at")
    if packet_created:
        try:
            pdt = datetime.fromisoformat(packet_created.replace("Z", "+00:00"))
            if pdt > datetime.now(pdt.tzinfo):
                errors.append("packet metadata created_at is in the future")
        except ValueError:
            errors.append("packet created_at is not ISO-8601")
    keys: dict[tuple[str,str,str,str], list[Claim]] = {}
    for c in state.claims:
        keys.setdefault(_claim_key(c), []).append(c)
    for key, claims in keys.items():
        direct = [c for c in claims if c.observation_mode in {ObservationMode.DIRECT_API, ObservationMode.DIRECT_UI, ObservationMode.DIRECT_FILE, ObservationMode.DIRECT_RUNTIME, ObservationMode.DIRECT_DATABASE, ObservationMode.DIRECT_HUMAN_REPORT}]
        if len(direct) > 1 and len({c.object.__repr__() for c in direct}) > 1:
            errors.append(f"conflicting direct observations for {key}")
    if state.parent_state_id is None and state.state_id != "STATE-000":
        warnings.append("non-genesis state has no parent_state_id")
    return {"status": "INVALID" if errors else ("VALID_WITH_WARNINGS" if warnings else "VALID"), "errors": errors, "warnings": warnings}
