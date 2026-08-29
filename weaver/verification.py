"""WEAVER-K12 — Evidence-grounded verification + proof reconciliation.

VERIFICATION ≠ AUTHORIZATION ≠ EXECUTION. Read-only.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .engineering_plan import EngineeringPlan
from .pass_spec import PassSpec, current_head, current_origin_main, path_in_allowlist


class VerificationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    STALE = "STALE"


class PublicationStatus(str, Enum):
    PUBLISHED = "PUBLISHED"
    LOCAL_ONLY = "LOCAL_ONLY"
    REMOTE_MISMATCH = "REMOTE_MISMATCH"
    UNKNOWN = "UNKNOWN"
    NOT_REQUIRED = "NOT_REQUIRED"


class PathStatus(str, Enum):
    MATCH = "MATCH"
    MISSING = "MISSING"
    UNEXPECTED = "UNEXPECTED"
    CHANGED = "CHANGED"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"


@dataclass
class VerificationReport:
    schema_version: str = "1.0.0"
    verification_id: str = ""
    bound_head_sha: str = ""
    bound_origin_sha: str | None = None
    plan: dict[str, Any] = field(default_factory=dict)
    scope: dict[str, Any] = field(default_factory=dict)
    implementation: dict[str, Any] = field(default_factory=dict)
    tests: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    publication: dict[str, Any] = field(default_factory=dict)
    risks: dict[str, Any] = field(default_factory=dict)
    proof_matrix: list[dict[str, Any]] = field(default_factory=list)
    verdict: dict[str, Any] = field(default_factory=dict)
    authorization: dict[str, Any] = field(default_factory=dict)
    review_bundle: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_content_hash(plan: EngineeringPlan | dict[str, Any]) -> str:
    if isinstance(plan, EngineeringPlan):
        data = {
            "plan_id": plan.plan_id,
            "objective": plan.objective,
            "affected_paths": list(plan.affected_paths),
            "implementation_steps": list(plan.implementation_steps),
            "proposed_changes": list(plan.proposed_changes),
        }
    else:
        data = {
            "plan_id": plan.get("plan_id"),
            "objective": plan.get("objective"),
            "affected_paths": list(plan.get("affected_paths") or []),
            "implementation_steps": list(plan.get("implementation_steps") or []),
            "proposed_changes": list(plan.get("proposed_changes") or []),
        }
    blob = json.dumps(data, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _vid(*parts: str) -> str:
    return "ver-" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def _git_changed_paths(repo_root: str, base_sha: str | None = None) -> list[str]:
    """Paths changed vs base_sha (or empty tree / working tree status)."""
    paths: list[str] = []
    if base_sha:
        r = subprocess.run(
            ["git", "diff", "--name-only", f"{base_sha}..HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            paths.extend([ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()])
    r2 = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    for line in (r2.stdout or "").splitlines():
        if not line.strip():
            continue
        p = line[3:].strip() if len(line) > 3 else line.strip()
        if " -> " in p:
            p = p.split(" -> ", 1)[-1]
        if p and p not in paths:
            paths.append(p)
    return sorted(set(paths))


def verify_implementation(
    plan: EngineeringPlan | dict[str, Any],
    *,
    actual_paths: list[str] | None = None,
    base_sha: str | None = None,
    expected_plan_hash: str | None = None,
    test_results: dict[str, Any] | None = None,
    result_sha: str | None = None,
    remote_sha: str | None = None,
    publication_required: bool = False,
    pass_spec: PassSpec | None = None,
    architecture_evidence: dict[str, Any] | None = None,
    bound_head_sha: str | None = None,
    bound_origin_sha: str | None = None,
    repo_root: str = ".",
) -> VerificationReport:
    """Read-only reconciliation of plan intent vs observed evidence."""
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    bound_head = bound_head_sha or head
    bound_origin = bound_origin_sha if bound_origin_sha is not None else origin

    if isinstance(plan, EngineeringPlan):
        plan_id = plan.plan_id
        planned_paths = sorted(plan.affected_paths)
        objective = plan.objective
        required_tests = list((plan.test_strategy or {}).get("required_tests") or [])
        plan_hash = plan_content_hash(plan)
        risks_in = list(plan.risk_register or [])
    else:
        plan_id = str(plan.get("plan_id") or "")
        planned_paths = sorted(plan.get("affected_paths") or [])
        objective = str(plan.get("objective") or "")
        required_tests = list((plan.get("test_strategy") or {}).get("required_tests") or [])
        plan_hash = plan_content_hash(plan)
        risks_in = list(plan.get("risk_register") or [])

    # Staleness vs bound
    if bound_head != head or (bound_origin is not None and origin is not None and bound_origin != origin):
        report = VerificationReport(
            verification_id=_vid(plan_id, bound_head, "stale"),
            bound_head_sha=bound_head,
            bound_origin_sha=bound_origin,
            verdict={
                "status": VerificationVerdict.STALE.value,
                "reasons": [f"bound head {bound_head} != current {head}"],
            },
            authorization={
                "current_pass_authorized": False,
                "note": "VERIFICATION ≠ AUTHORIZATION",
            },
        )
        report.review_bundle = _review(report, objective)
        return report

    # Plan binding
    plan_binding = "valid"
    if expected_plan_hash and expected_plan_hash != plan_hash:
        plan_binding = "PLAN_BINDING_MISMATCH"

    actual = sorted(set(actual_paths if actual_paths is not None else _git_changed_paths(repo_root, base_sha)))

    path_rows: list[dict[str, Any]] = []
    matched, missing, unexpected = [], [], []
    for p in planned_paths:
        if p in actual or any(a == p or a.startswith(p.rstrip("/") + "/") for a in actual):
            path_rows.append({"path": p, "status": PathStatus.MATCH.value, "evidence": "git_or_provided_paths"})
            matched.append(p)
        else:
            path_rows.append({"path": p, "status": PathStatus.MISSING.value, "evidence": "git_or_provided_paths"})
            missing.append(p)
    for a in actual:
        if not any(a == p or a.startswith(p.rstrip("/") + "/") or p.startswith(a.rstrip("/") + "/") for p in planned_paths):
            path_rows.append({"path": a, "status": PathStatus.UNEXPECTED.value, "evidence": "git_or_provided_paths"})
            unexpected.append(a)

    scope_match = not missing and not unexpected
    # authorized vs planned vs actual
    authorized_paths = list(pass_spec.allowed_paths) if pass_spec else []
    unauthorized_actual = []
    if pass_spec:
        for a in actual:
            if not path_in_allowlist(a, pass_spec.allowed_paths):
                unauthorized_actual.append(a)

    # Tests
    tr = test_results or {}
    executed = list(tr.get("executed") or [])
    passed = list(tr.get("passed") or [])
    failed = list(tr.get("failed") or [])
    not_executed = [t for t in required_tests if t not in executed]
    test_block = {
        "required": sorted(required_tests),
        "executed": sorted(executed),
        "passed": sorted(passed),
        "failed": sorted(failed),
        "missing": sorted(not_executed),
        "note": "Static discoverability is not runtime coverage",
    }

    # Architecture
    arch = architecture_evidence or {}
    arch_block = {
        "expected_boundaries": arch.get("expected_boundaries") or ["weaver control-plane"],
        "observed_boundaries": arch.get("observed_boundaries") or [],
        "violations": sorted(arch.get("violations") or []),
        "status": arch.get("status") or ("UNKNOWN" if not architecture_evidence else "PROVIDED"),
    }

    # Publication
    rs = result_sha or head
    rem = remote_sha if remote_sha is not None else origin
    if not publication_required:
        pub_status = PublicationStatus.NOT_REQUIRED.value
    elif rem is None:
        pub_status = PublicationStatus.UNKNOWN.value
    elif rs == rem == head:
        pub_status = PublicationStatus.PUBLISHED.value
    elif rs == head and rem != head:
        pub_status = PublicationStatus.REMOTE_MISMATCH.value
    elif rs == head and rem is None:
        pub_status = PublicationStatus.LOCAL_ONLY.value
    else:
        pub_status = PublicationStatus.REMOTE_MISMATCH.value if rem != rs else PublicationStatus.LOCAL_ONLY.value

    publication = {
        "required": publication_required,
        "result_sha": rs,
        "remote_sha": rem,
        "status": pub_status,
        "matches": pub_status == PublicationStatus.PUBLISHED.value
        or (not publication_required),
    }

    # Evidence buckets
    supporting = [
        {"kind": "FACT", "claim": f"HEAD is {head}", "source": "git"},
        {"kind": "FACT", "claim": f"planned paths={planned_paths}", "source": "plan"},
        {"kind": "FACT", "claim": f"actual paths={actual}", "source": "git_or_input"},
    ]
    contradictory = []
    unknown = [{"kind": "UNKNOWN", "claim": "runtime behavior not established by static verification"}]
    if unexpected:
        contradictory.append({"kind": "FACT", "claim": f"unexpected paths: {unexpected}", "source": "diff"})
    if failed:
        contradictory.append({"kind": "FACT", "claim": f"failed tests: {failed}", "source": "test_results"})
    if plan_binding != "valid":
        contradictory.append({"kind": "FACT", "claim": "plan hash mismatch", "source": "plan_binding"})

    # Proof matrix
    matrix = [
        {
            "claim": "Planned files changed",
            "evidence": "git_or_provided_paths",
            "status": "VERIFIED" if not missing else ("FAILED" if planned_paths else "VERIFIED"),
        },
        {
            "claim": "No unexpected files",
            "evidence": "git_or_provided_paths",
            "status": "VERIFIED" if not unexpected else "FAILED",
        },
        {
            "claim": "Required tests passed",
            "evidence": "test_results",
            "status": (
                "VERIFIED"
                if required_tests and not failed and not not_executed and set(required_tests).issubset(set(passed))
                else (
                    "FAILED"
                    if failed
                    else ("INSUFFICIENT_EVIDENCE" if required_tests else "VERIFIED")
                )
            ),
        },
        {
            "claim": "Architecture preserved",
            "evidence": "architecture_evidence",
            "status": "FAILED" if arch_block["violations"] else ("UNKNOWN" if arch_block["status"] == "UNKNOWN" else "VERIFIED"),
        },
        {
            "claim": "Publication complete",
            "evidence": "git remote",
            "status": (
                "VERIFIED"
                if publication["matches"]
                else ("FAILED" if publication_required else "VERIFIED")
            ),
        },
        {
            "claim": "Runtime behavior",
            "evidence": "no runtime proof",
            "status": "UNKNOWN",
        },
        {
            "claim": "Plan binding",
            "evidence": "plan_hash",
            "status": "VERIFIED" if plan_binding == "valid" else "FAILED",
        },
    ]

    # Verdict
    reasons: list[str] = []
    status = VerificationVerdict.VERIFIED.value
    if plan_binding != "valid":
        status = VerificationVerdict.FAILED.value
        reasons.append("PLAN_BINDING_MISMATCH")
    if failed:
        status = VerificationVerdict.FAILED.value
        reasons.append("required tests failed")
    if unauthorized_actual:
        status = VerificationVerdict.FAILED.value
        reasons.append("actual paths outside PassSpec")
    if unexpected and status != VerificationVerdict.FAILED.value:
        status = VerificationVerdict.PARTIALLY_VERIFIED.value
        reasons.append("unexpected paths present")
    if missing and planned_paths:
        if status == VerificationVerdict.VERIFIED.value:
            status = VerificationVerdict.PARTIALLY_VERIFIED.value
        reasons.append("planned paths missing from actual changes")
    if required_tests and not_executed and not failed and status == VerificationVerdict.VERIFIED.value:
        status = VerificationVerdict.INSUFFICIENT_EVIDENCE.value
        reasons.append("required tests not executed")
    if publication_required and pub_status not in (
        PublicationStatus.PUBLISHED.value,
        PublicationStatus.NOT_REQUIRED.value,
    ):
        if status == VerificationVerdict.VERIFIED.value:
            status = VerificationVerdict.PARTIALLY_VERIFIED.value
        reasons.append(f"publication status={pub_status}")
    if not reasons and status == VerificationVerdict.VERIFIED.value:
        reasons.append("all checked claims supported by available evidence")

    report = VerificationReport(
        verification_id=_vid(plan_id, head, status),
        bound_head_sha=bound_head,
        bound_origin_sha=bound_origin,
        plan={"plan_id": plan_id, "plan_hash": plan_hash, "binding": plan_binding, "objective": objective},
        scope={
            "planned_paths": planned_paths,
            "actual_paths": actual,
            "unexpected_paths": unexpected,
            "missing_paths": missing,
            "matched_paths": matched,
            "authorized_paths": authorized_paths,
            "unauthorized_actual": unauthorized_actual,
            "scope_match": scope_match,
        },
        implementation={
            "path_rows": path_rows,
            "implementation_match": scope_match and not missing,
        },
        tests=test_block,
        architecture=arch_block,
        evidence={"supporting": supporting, "contradictory": contradictory, "unknown": unknown},
        publication=publication,
        risks={
            "from_plan": risks_in,
            "newly_detected": ([{"item": "unexpected paths", "paths": unexpected}] if unexpected else [])
            + ([{"item": "unauthorized actual", "paths": unauthorized_actual}] if unauthorized_actual else []),
            "unresolved": reasons,
        },
        proof_matrix=matrix,
        verdict={"status": status, "reasons": reasons},
        authorization={
            "current_pass_authorized": False,
            "note": "VERIFICATION ≠ AUTHORIZATION. Read-only reconciliation only.",
        },
    )
    report.review_bundle = _review(report, objective)
    return report


def _review(report: VerificationReport, objective: str) -> dict[str, Any]:
    return {
        "objective": objective,
        "verdict": report.verdict,
        "intended_paths": (report.scope or {}).get("planned_paths"),
        "actual_paths": (report.scope or {}).get("actual_paths"),
        "unexpected": (report.scope or {}).get("unexpected_paths"),
        "missing": (report.scope or {}).get("missing_paths"),
        "tests": report.tests,
        "publication": report.publication,
        "proof_matrix": report.proof_matrix,
        "risks": report.risks,
        "authorization": report.authorization,
        "next_action": "awaiting human authorization",
    }


def verify_transaction_result(
    *,
    plan: EngineeringPlan | dict[str, Any],
    changed_paths: list[str],
    test_results: dict[str, Any] | None = None,
    result_sha: str | None = None,
    remote_sha: str | None = None,
    publication_required: bool = False,
    pass_spec: PassSpec | None = None,
    repo_root: str = ".",
) -> VerificationReport:
    """Normalize session/transaction-like results into VerificationReport. Does not run transactions."""
    return verify_implementation(
        plan,
        actual_paths=changed_paths,
        test_results=test_results,
        result_sha=result_sha,
        remote_sha=remote_sha,
        publication_required=publication_required,
        pass_spec=pass_spec,
        repo_root=repo_root,
    )
