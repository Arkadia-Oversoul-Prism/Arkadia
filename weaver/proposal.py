"""WEAVER-K5 — Governed engineering Proposal (not authorization).

PROPOSAL ≠ AUTHORIZATION. PLAN ≠ AUTHORIZATION. CONTEXT ≠ AUTHORIZATION.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .pass_spec import PassSpec, PassSpecError, path_in_allowlist
from .plan import Plan, PlanError, validate_plan_against_spec


class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


class ProposalError(Exception):
    """Proposal validation failure."""


def normalize_path(path: str) -> str:
    p = path.replace("\\", "/").strip().lstrip("./")
    while "//" in p:
        p = p.replace("//", "/")
    return p


def normalize_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in paths or []:
        n = normalize_path(str(raw))
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return sorted(out)


def normalize_tests(tests: list[str]) -> list[str]:
    return normalize_paths(tests)


@dataclass
class Proposal:
    proposal_id: str
    objective: str
    repository_anchor: str
    findings: list[str] = field(default_factory=list)
    affected_paths: list[str] = field(default_factory=list)
    proposed_changes: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    required_builds: list[str] = field(default_factory=list)
    estimated_change_surface: str = "small"
    authorization_status: str = ProposalStatus.PROPOSED.value
    deferred: list[str] = field(default_factory=list)  # requires new authorization
    recommended_pass_spec: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Proposal":
        if not isinstance(data, dict):
            raise ProposalError("proposal must be a dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        raw = {k: v for k, v in data.items() if k in known}
        if "proposal_id" not in raw or "objective" not in raw or "repository_anchor" not in raw:
            raise ProposalError("malformed proposal: missing required fields")
        return cls(**raw)


def _stable_id(objective: str, anchor: str) -> str:
    h = hashlib.sha256(f"{anchor}:{objective}".encode()).hexdigest()[:12]
    return f"prop-{h}"


def normalize_proposal(raw: dict[str, Any] | Proposal, *, anchor: str, objective: str | None = None) -> Proposal:
    """Deterministic normalization / schema validation layer."""
    if isinstance(raw, Proposal):
        data = raw.to_dict()
    else:
        data = dict(raw)
    obj = objective or data.get("objective") or ""
    if not obj:
        raise ProposalError("malformed proposal: objective required")
    anchor = (data.get("repository_anchor") or anchor or "").strip()
    if not anchor:
        raise ProposalError("malformed proposal: repository_anchor required")

    prop = Proposal(
        proposal_id=data.get("proposal_id") or _stable_id(obj, anchor),
        objective=obj.strip(),
        repository_anchor=anchor,
        findings=list(data.get("findings") or []),
        affected_paths=normalize_paths(list(data.get("affected_paths") or [])),
        proposed_changes=list(data.get("proposed_changes") or []),
        non_goals=list(data.get("non_goals") or []),
        risks=list(data.get("risks") or []),
        required_tests=normalize_tests(list(data.get("required_tests") or [])),
        required_builds=normalize_tests(list(data.get("required_builds") or [])),
        estimated_change_surface=str(data.get("estimated_change_surface") or "small"),
        authorization_status=str(data.get("authorization_status") or ProposalStatus.PROPOSED.value),
        deferred=list(data.get("deferred") or []),
        recommended_pass_spec=dict(data.get("recommended_pass_spec") or {}),
    )
    if prop.authorization_status not in {s.value for s in ProposalStatus}:
        raise ProposalError(f"invalid authorization_status: {prop.authorization_status}")
    return prop


def validate_proposal_against_spec(proposal: Proposal, spec: PassSpec) -> None:
    """Reject proposals that touch forbidden or non-allowed paths."""
    for path in proposal.affected_paths:
        for forbidden in spec.forbidden_paths:
            f = normalize_path(forbidden)
            n = normalize_path(path)
            if f and (n == f or n.startswith(f.rstrip("/") + "/") or n.startswith(f)):
                raise ProposalError(f"forbidden path in proposal: {path}")
        if not path_in_allowlist(path, spec.allowed_paths):
            # move to deferred rather than silent include — still reject for execution
            raise ProposalError(f"out of scope path in proposal: {path}")


def proposal_cannot_expand_spec(proposal: Proposal, spec: PassSpec) -> PassSpec:
    validate_proposal_against_spec(proposal, spec)
    return spec


def approve_proposal(proposal: Proposal) -> Proposal:
    if proposal.authorization_status == ProposalStatus.REJECTED.value:
        raise ProposalError("cannot approve a rejected proposal")
    if proposal.authorization_status == ProposalStatus.INVALID.value:
        raise ProposalError("cannot approve an invalid proposal")
    proposal.authorization_status = ProposalStatus.APPROVED.value
    return proposal


def reject_proposal(proposal: Proposal) -> Proposal:
    proposal.authorization_status = ProposalStatus.REJECTED.value
    return proposal


def build_deterministic_proposal(
    objective: str,
    *,
    anchor: str,
    allowed_paths: list[str] | None = None,
    findings: list[str] | None = None,
) -> Proposal:
    """No-LLM path: proposal from objective + optional path hints."""
    paths = normalize_paths(list(allowed_paths or []))
    return normalize_proposal(
        {
            "objective": objective,
            "repository_anchor": anchor,
            "findings": findings or ["Deterministic proposal from objective and path hints."],
            "affected_paths": paths,
            "proposed_changes": [f"Work within: {p}" for p in paths[:20]],
            "non_goals": ["Scope expansion", "Self-authorization", "Product work outside objective"],
            "risks": ["Proposal treated as authorization"],
            "required_tests": ["tests/test_weaver_k5.py"],
            "authorization_status": ProposalStatus.PROPOSED.value,
        },
        anchor=anchor,
        objective=objective,
    )


def candidate_pass_spec_from_proposal(proposal: Proposal, base: PassSpec) -> PassSpec:
    """Recommend a PassSpec-compatible envelope — does NOT authorize execution."""
    paths = proposal.affected_paths or list(base.allowed_paths)
    # never enlarge beyond base if base was provided with constraints
    filtered = [p for p in paths if path_in_allowlist(p, base.allowed_paths)]
    if not filtered:
        filtered = list(base.allowed_paths)
    return PassSpec(
        pass_id=base.pass_id,
        objective=proposal.objective or base.objective,
        base_sha=base.base_sha,
        allowed_paths=filtered,
        forbidden_paths=list(base.forbidden_paths),
        required_tests=proposal.required_tests or list(base.required_tests),
        required_builds=proposal.required_builds or list(base.required_builds),
        non_goals=list(dict.fromkeys(list(base.non_goals) + list(proposal.non_goals))),
        commit_required=base.commit_required,
        push_allowed=base.push_allowed,
        publication_required=base.publication_required,
        human_approval_required=True,
        checkpoint_required=base.checkpoint_required,
        provider=base.provider,
    )


def proposal_to_plan(proposal: Proposal) -> Plan:
    if proposal.authorization_status != ProposalStatus.APPROVED.value:
        raise ProposalError("only APPROVED proposals may become plans for execution")
    return Plan(
        pass_id=proposal.proposal_id,
        objective=proposal.objective,
        rationale="; ".join(proposal.findings[:5]),
        proposed_files=list(proposal.affected_paths),
        implementation_steps=list(proposal.proposed_changes) or ["Implement within approved scope"],
        required_tests=list(proposal.required_tests),
        required_builds=list(proposal.required_builds),
        architectural_impact=["Weaver control-plane proposal"],
        risks=list(proposal.risks),
        expected_outcome="Execute under existing K3 transaction",
        approved=True,
    )


def execute_approved_proposal(
    proposal: Proposal,
    spec: PassSpec,
    *,
    task: str | None = None,
    repo_root: str = ".",
):
    """Hand off to K3 transaction only when APPROVED and in-scope."""
    if proposal.authorization_status != ProposalStatus.APPROVED.value:
        raise ProposalError("unapproved or rejected proposal cannot execute")
    validate_proposal_against_spec(proposal, spec)
    plan = proposal_to_plan(proposal)
    # Plan pass_id should align with PassSpec for K3 validation
    plan.pass_id = spec.pass_id
    from .transaction import run_transaction

    return run_transaction(
        spec,
        task=task or proposal.objective,
        plan=plan,
        require_plan_approval=True,
        auto_approve_if_spec_is_authorization=False,
        repo_root=repo_root,
    )
