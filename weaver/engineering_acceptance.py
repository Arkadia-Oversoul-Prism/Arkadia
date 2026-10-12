"""Deterministic, side-effect-free evaluation of engineering merge readiness.

This module evaluates evidence; it does not merge, deploy, or authenticate callers.
Adapters must collect authoritative GitHub/provider facts and pass them here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Mapping, Sequence


_SHA = re.compile(r"^[0-9a-f]{40}$")


class CheckState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_TESTED = "NOT_TESTED"


class RiskClass(str, Enum):
    ROUTINE = "ROUTINE"
    ELEVATED = "ELEVATED"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"


class Decision(str, Enum):
    BLOCKED = "BLOCKED"
    NOT_READY = "NOT_READY"
    READY_FOR_HUMAN_DECISION = "READY_FOR_HUMAN_DECISION"
    READY_TO_MERGE = "READY_TO_MERGE"


@dataclass(frozen=True)
class GateEvidence:
    name: str
    state: CheckState
    tested_sha: str
    artifact_url: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class ReviewEvidence:
    approved: bool
    reviewer: str
    reviewed_sha: str
    independent: bool = True


@dataclass(frozen=True)
class MergePolicy:
    version: str
    required_gates: tuple[str, ...]
    auto_merge_risk_classes: frozenset[RiskClass] = frozenset()
    require_independent_approval: bool = True
    require_post_merge_verification: bool = True


@dataclass(frozen=True)
class PullRequestEvidence:
    pr_number: int
    head_sha: str
    base_sha: str
    observed_head_sha: str
    observed_base_sha: str
    checks: Mapping[str, GateEvidence]
    reviews: Sequence[ReviewEvidence] = ()
    draft: bool = False
    mergeable: bool = True
    branch_protection_satisfied: bool = False
    risk_class: RiskClass = RiskClass.ROUTINE
    explicit_human_approval: bool = False
    policy_authorizes_auto_merge: bool = False
    evidence_complete: bool = True
    policy_version: str = ""


@dataclass(frozen=True)
class AcceptanceDecision:
    decision: Decision
    reasons: tuple[str, ...]
    candidate_sha: str
    policy_version: str
    required_gates: tuple[str, ...]
    post_merge_verification_required: bool


def evaluate_merge_readiness(
    pr: PullRequestEvidence, policy: MergePolicy
) -> AcceptanceDecision:
    """Return a deterministic decision from a single observed evidence snapshot.

    READY_TO_MERGE means an independently enforced policy may invoke a merge API;
    it is not itself a merge command or proof that the merge happened.
    """
    reasons: list[str] = []
    candidate_sha = pr.head_sha if _SHA.fullmatch(pr.head_sha or "") else ""
    if not candidate_sha or not _SHA.fullmatch(pr.base_sha or ""):
        reasons.append("candidate and base must be full lowercase 40-character SHAs")
    if pr.observed_head_sha != pr.head_sha:
        reasons.append("observed PR head differs from evaluated candidate SHA")
    if pr.observed_base_sha != pr.base_sha:
        reasons.append("observed PR base differs from evaluated base SHA")
    if pr.risk_class is RiskClass.UNKNOWN:
        reasons.append("risk classification is unknown")
    if pr.policy_version != policy.version:
        reasons.append("evidence policy version does not match active policy")
    if not pr.evidence_complete:
        reasons.append("required evidence bundle is incomplete")
    if pr.draft:
        reasons.append("pull request is still a draft")
    if not pr.mergeable:
        reasons.append("GitHub reports merge conflicts or unknown mergeability")
    if not pr.branch_protection_satisfied:
        reasons.append("repository branch-protection requirements are not satisfied")

    for name in policy.required_gates:
        evidence = pr.checks.get(name)
        if evidence is None:
            reasons.append(f"required gate missing: {name}")
            continue
        if evidence.tested_sha != pr.head_sha:
            reasons.append(f"gate evidence is stale for candidate SHA: {name}")
        if evidence.state is not CheckState.PASS:
            reasons.append(f"required gate is {evidence.state.value}: {name}")
        if not evidence.artifact_url:
            reasons.append(f"required gate lacks an evidence artifact: {name}")

    approvals = [
        review for review in pr.reviews
        if review.approved
        and review.reviewed_sha == pr.head_sha
        and review.reviewer.strip()
        and (review.independent or not policy.require_independent_approval)
    ]
    if policy.require_independent_approval and not approvals:
        reasons.append("independent approval for the exact candidate SHA is missing")

    if reasons:
        blocking_prefixes = (
            "candidate and base must be",
            "observed PR head differs",
            "observed PR base differs",
            "risk classification is unknown",
            "evidence policy version does not match",
            "required evidence bundle is incomplete",
            "required gate missing:",
            "gate evidence is stale",
            "required gate lacks an evidence artifact:",
            "repository branch-protection requirements are not satisfied",
        )
        decision = Decision.BLOCKED if any(
            reason.startswith(blocking_prefixes) for reason in reasons
        ) else Decision.NOT_READY
    elif pr.risk_class in policy.auto_merge_risk_classes and pr.policy_authorizes_auto_merge:
        decision = Decision.READY_TO_MERGE
    elif pr.explicit_human_approval:
        decision = Decision.READY_TO_MERGE
    else:
        decision = Decision.READY_FOR_HUMAN_DECISION
        reasons.append("gates passed; no applicable merge authorization is recorded")

    return AcceptanceDecision(
        decision=decision,
        reasons=tuple(reasons),
        candidate_sha=candidate_sha,
        policy_version=policy.version,
        required_gates=policy.required_gates,
        post_merge_verification_required=policy.require_post_merge_verification,
    )
