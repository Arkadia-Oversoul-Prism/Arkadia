"""WEAVER-K6 — Governed human-in-the-loop session conductor.

Deterministic state machine. Continuity ≠ authorization.
Previous session never grants current execution authority.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .pass_spec import PassSpec, current_head
from .proposal import (
    Proposal,
    ProposalError,
    ProposalStatus,
    approve_proposal,
    build_deterministic_proposal,
    execute_approved_proposal,
    normalize_proposal,
    reject_proposal,
    validate_proposal_against_spec,
)
from .recon import build_context_packet, is_stale


class SessionState(str, Enum):
    CREATED = "CREATED"
    RECONSTRUCTED = "RECONSTRUCTED"
    PROPOSED = "PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    PLANNED = "PLANNED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    PENDING_PUBLICATION = "PENDING_PUBLICATION"
    NO_CHANGE = "NO_CHANGE"


@dataclass
class ApprovalBinding:
    proposal_id: str
    proposal_hash: str
    repository_head_sha: str
    approved_at: int = 0

    def matches(self, proposal: Proposal, head_sha: str) -> bool:
        return (
            self.proposal_id == proposal.proposal_id
            and self.proposal_hash == proposal_content_hash(proposal)
            and self.repository_head_sha == head_sha
        )


def proposal_content_hash(proposal: Proposal) -> str:
    payload = {
        "proposal_id": proposal.proposal_id,
        "objective": proposal.objective,
        "repository_anchor": proposal.repository_anchor,
        "affected_paths": proposal.affected_paths,
        "proposed_changes": proposal.proposed_changes,
        "required_tests": proposal.required_tests,
        "non_goals": proposal.non_goals,
    }
    blob = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass
class WeaverSession:
    session_id: str
    objective: str
    repository_anchor: str
    state: str = SessionState.CREATED.value
    recon: dict[str, Any] = field(default_factory=dict)
    proposal: dict[str, Any] | None = None
    approval: dict[str, Any] | None = None
    pass_spec: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None
    terminal_status: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _session_id(objective: str, anchor: str) -> str:
    h = hashlib.sha256(f"{anchor}:{objective}:{int(time.time())}".encode()).hexdigest()[:12]
    return f"sess-{h}"


def create_session(objective: str, *, repo_root: str = ".") -> WeaverSession:
    if not (objective or "").strip():
        raise ValueError("objective required")
    head = current_head(repo_root)
    return WeaverSession(
        session_id=_session_id(objective, head),
        objective=objective.strip(),
        repository_anchor=head,
        state=SessionState.CREATED.value,
    )


def run_recon(session: WeaverSession, *, repo_root: str = ".") -> WeaverSession:
    packet = build_context_packet(repo_root)
    session.recon = {
        "head_sha": packet.get("head_sha"),
        "origin_sha": packet.get("origin_sha"),
        "working_tree_clean": packet.get("working_tree_clean"),
        "architecture_status": (packet.get("architecture") or {}).get("status"),
        "stale": is_stale(packet, repo_root),
        "next_action_hint": packet.get("next_action"),
        "authorization_note": (packet.get("authorization") or {}).get("note"),
    }
    # Refresh anchor to current HEAD (recon knowledge, not permission)
    session.repository_anchor = packet.get("head_sha") or session.repository_anchor
    session.state = SessionState.RECONSTRUCTED.value
    return session


def propose(
    session: WeaverSession,
    *,
    allowed_paths: list[str] | None = None,
    findings: list[str] | None = None,
    repo_root: str = ".",
) -> WeaverSession:
    if session.state not in (
        SessionState.CREATED.value,
        SessionState.RECONSTRUCTED.value,
    ):
        session.state = SessionState.BLOCKED.value
        session.message = f"cannot propose from state {session.state}"
        return session
    if session.state == SessionState.CREATED.value:
        run_recon(session, repo_root=repo_root)

    prop = build_deterministic_proposal(
        session.objective,
        anchor=session.repository_anchor,
        allowed_paths=allowed_paths,
        findings=findings,
    )
    session.proposal = prop.to_dict()
    session.state = SessionState.AWAITING_APPROVAL.value
    session.message = "proposal awaits explicit human approval"
    return session


def approve(
    session: WeaverSession,
    *,
    head_sha: str | None = None,
    repo_root: str = ".",
) -> WeaverSession:
    if session.state != SessionState.AWAITING_APPROVAL.value:
        session.state = SessionState.BLOCKED.value
        session.message = "not awaiting approval"
        return session
    if not session.proposal:
        session.state = SessionState.BLOCKED.value
        session.message = "no proposal"
        return session

    prop = normalize_proposal(session.proposal, anchor=session.repository_anchor)
    head = head_sha or current_head(repo_root)
    if prop.repository_anchor != head and session.repository_anchor != head:
        # anchor drift after proposal
        session.state = SessionState.BLOCKED.value
        session.message = "approval invalid: repository anchor changed"
        session.terminal_status = SessionState.BLOCKED.value
        return session

    approve_proposal(prop)
    binding = ApprovalBinding(
        proposal_id=prop.proposal_id,
        proposal_hash=proposal_content_hash(prop),
        repository_head_sha=head,
        approved_at=int(time.time()),
    )
    session.proposal = prop.to_dict()
    session.approval = asdict(binding)
    session.state = SessionState.APPROVED.value
    session.message = "proposal approved (explicit)"
    return session


def reject(session: WeaverSession) -> WeaverSession:
    if session.proposal:
        prop = normalize_proposal(session.proposal, anchor=session.repository_anchor)
        reject_proposal(prop)
        session.proposal = prop.to_dict()
    session.state = SessionState.REJECTED.value
    session.terminal_status = SessionState.REJECTED.value
    session.message = "proposal rejected by human"
    return session


def _validate_approval_binding(session: WeaverSession, prop: Proposal, head: str) -> bool:
    if not session.approval:
        return False
    binding = ApprovalBinding(**session.approval)
    return binding.matches(prop, head)


def execute(
    session: WeaverSession,
    spec: PassSpec,
    *,
    repo_root: str = ".",
) -> WeaverSession:
    """Execute only with explicit approval + valid PassSpec + binding."""
    if session.state != SessionState.APPROVED.value:
        session.state = SessionState.BLOCKED.value
        session.message = "execute requires APPROVED state"
        session.terminal_status = SessionState.BLOCKED.value
        return session
    if not session.proposal or not session.approval:
        session.state = SessionState.BLOCKED.value
        session.message = "missing proposal or approval"
        return session

    prop = normalize_proposal(session.proposal, anchor=session.repository_anchor)
    head = current_head(repo_root)
    if not _validate_approval_binding(session, prop, head):
        # try binding against session.repository_anchor if HEAD matches approval record
        binding = ApprovalBinding(**session.approval)
        if not binding.matches(prop, binding.repository_head_sha):
            session.state = SessionState.BLOCKED.value
            session.message = "stale or mutated proposal: approval binding failed"
            session.terminal_status = SessionState.BLOCKED.value
            return session
        if head != binding.repository_head_sha:
            session.state = SessionState.BLOCKED.value
            session.message = "approval invalid: HEAD changed since approval"
            session.terminal_status = SessionState.BLOCKED.value
            return session

    try:
        validate_proposal_against_spec(prop, spec)
    except ProposalError as e:
        session.state = SessionState.BLOCKED.value
        session.message = str(e)
        session.terminal_status = SessionState.BLOCKED.value
        return session

    session.pass_spec = {
        "pass_id": spec.pass_id,
        "allowed_paths": list(spec.allowed_paths),
        "forbidden_paths": list(spec.forbidden_paths),
        "base_sha": spec.base_sha,
    }
    session.state = SessionState.EXECUTING.value
    try:
        result = execute_approved_proposal(prop, spec, task=session.objective, repo_root=repo_root)
    except ProposalError as e:
        session.state = SessionState.FAILED.value
        session.terminal_status = SessionState.FAILED.value
        session.message = str(e)
        return session
    except Exception as e:
        session.state = SessionState.FAILED.value
        session.terminal_status = SessionState.FAILED.value
        session.message = str(e)
        return session

    session.execution_result = {
        "ok": result.ok,
        "status": result.status,
        "stage": result.stage,
        "message": result.message,
    }
    if result.status == "PENDING_PUBLICATION":
        session.state = SessionState.PENDING_PUBLICATION.value
        session.terminal_status = SessionState.PENDING_PUBLICATION.value
    elif result.status == "NO_CHANGE":
        session.state = SessionState.NO_CHANGE.value
        session.terminal_status = SessionState.NO_CHANGE.value
    elif result.ok and result.status in ("PASS", "COMPLETED"):
        session.state = SessionState.PUBLISHED.value
        session.terminal_status = SessionState.COMPLETED.value
    elif result.ok:
        session.state = SessionState.COMPLETED.value
        session.terminal_status = result.status
    else:
        session.state = result.status if result.status in (
            SessionState.BLOCKED.value,
            SessionState.FAILED.value,
            SessionState.PENDING_PUBLICATION.value,
        ) else SessionState.FAILED.value
        session.terminal_status = session.state
    session.message = result.message
    return session


def review_bundle(session: WeaverSession) -> dict[str, Any]:
    """Human-readable review payload (no secrets)."""
    prop = session.proposal or {}
    return {
        "session_id": session.session_id,
        "state": session.state,
        "objective": session.objective,
        "repository_anchor": session.repository_anchor,
        "findings": prop.get("findings"),
        "affected_paths": prop.get("affected_paths"),
        "proposed_changes": prop.get("proposed_changes"),
        "non_goals": prop.get("non_goals"),
        "risks": prop.get("risks"),
        "required_tests": prop.get("required_tests"),
        "required_builds": prop.get("required_builds"),
        "estimated_change_surface": prop.get("estimated_change_surface"),
        "candidate_execution_scope": prop.get("affected_paths"),
        "authorization_note": "PROPOSAL ≠ AUTHORIZATION. Explicit approve() required.",
    }
