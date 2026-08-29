"""WEAVER-K9 — Evidence-bound engineering analysis + planning.

ANALYSIS ≠ AUTHORIZATION. PLAN ≠ AUTHORIZATION.
Read-only relative to the authorized objective; does not write/commit/push/execute.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .continuation import ContinuityStatus, load_continuation
from .pass_spec import PassSpec, path_in_allowlist, current_head, current_origin_main
from .plan import Plan, validate_plan_against_spec, PlanError
from .recon import build_context_packet, architecture_summary, topology, test_inventory


class AnalysisResultKind(str, Enum):
    ANALYSIS_READY = "ANALYSIS_READY"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PROTECTED_BOUNDARY_CONFLICT = "PROTECTED_BOUNDARY_CONFLICT"


class EvidenceKind(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


PROTECTED_DEFAULT = [
    "solspire/",
    "ReasoMate",
    "Oracle",
    "Firebase",
    "arkadia-android/",
    "sonata-android/",
    "api/auth.py",
    "deployment",
]


@dataclass
class EvidenceItem:
    kind: str
    statement: str
    source: str = ""
    path: str = ""
    commit_sha: str = ""
    test_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EngineeringAnalysis:
    schema_version: str = "1.0.0"
    analysis_id: str = ""
    result_kind: str = AnalysisResultKind.ANALYSIS_READY.value
    repository: dict[str, Any] = field(default_factory=dict)
    objective: dict[str, Any] = field(default_factory=dict)
    recon: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    assessment: dict[str, Any] = field(default_factory=dict)
    proposed_change: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    risks: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    recommendation: dict[str, Any] = field(default_factory=dict)
    authorization: dict[str, Any] = field(default_factory=dict)
    continuation_state: str = ContinuityStatus.MISSING.value
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    generated_at: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _aid(objective: str, head: str) -> str:
    return "an-" + hashlib.sha256(f"{head}:{objective}".encode()).hexdigest()[:12]


def _fact(statement: str, **kwargs) -> dict[str, Any]:
    return EvidenceItem(EvidenceKind.FACT.value, statement, **kwargs).to_dict()


def _inf(statement: str, **kwargs) -> dict[str, Any]:
    return EvidenceItem(EvidenceKind.INFERENCE.value, statement, **kwargs).to_dict()


def _unk(statement: str, **kwargs) -> dict[str, Any]:
    return EvidenceItem(EvidenceKind.UNKNOWN.value, statement, **kwargs).to_dict()


def analyze_objective(
    objective: str,
    *,
    pass_spec: PassSpec | None = None,
    affected_path_hints: list[str] | None = None,
    repo_root: str = ".",
) -> EngineeringAnalysis:
    """Produce evidence-bound analysis. Never mutates the repository."""
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    cont_status, cont, cont_msg = load_continuation(repo_root)
    authorized = bool(pass_spec is not None)
    packet = build_context_packet(repo_root)
    arch = architecture_summary(repo_root)
    tops = topology(repo_root)
    tests = test_inventory(repo_root)

    analysis = EngineeringAnalysis(
        analysis_id=_aid(objective or "", head),
        repository={
            "remote": (packet.get("repository") or {}).get("remote"),
            "branch": packet.get("branch") or "main",
            "head_sha": head,
            "origin_sha": origin,
            "clean": packet.get("working_tree_clean"),
        },
        objective={
            "statement": (objective or "").strip(),
            "source": "human",
            "authorized": authorized,
        },
        continuation_state=cont_status.value,
        authorization={
            "current_pass_authorized": authorized,
            "note": "ANALYSIS ≠ AUTHORIZATION. Prior PassSpec / continuation cannot authorize this analysis execution.",
        },
        generated_at=int(time.time()),
    )

    if not (objective or "").strip():
        analysis.result_kind = AnalysisResultKind.BLOCKED.value
        analysis.unresolved.append("empty objective")
        return analysis

    facts: list[dict[str, Any]] = [
        _fact(f"HEAD is {head}", source="git", commit_sha=head),
        _fact(f"origin/main is {origin}", source="git", commit_sha=origin or ""),
        _fact(f"continuation load status is {cont_status.value}", source="weaver/continuation.py"),
        _fact(
            f"architecture source status is {arch.get('status')}",
            source=str(arch.get("source") or "tests/architecture/LAYER_MAP.py"),
        ),
        _fact(f"topology includes: {', '.join(tops[:12])}", source="filesystem"),
    ]
    inferences: list[dict[str, Any]] = [
        _inf("K1 context packet summarizes identity and inventory without granting PassSpec."),
        _inf("K8 continuation is historical knowledge only."),
    ]
    unknowns: list[dict[str, Any]] = [
        _unk("Whether a future product feature requires provider redesign."),
    ]
    if cont_status == ContinuityStatus.STALE:
        facts.append(_fact(f"continuation is STALE: {cont_msg}", source="load_continuation"))
    if cont_status == ContinuityStatus.MISSING:
        facts.append(_fact("no continuation artifact present", source="load_continuation"))

    # Relevant weaver modules
    weaver_root = Path(repo_root) / "weaver"
    relevant = []
    if weaver_root.is_dir():
        for p in sorted(weaver_root.glob("*.py")):
            relevant.append(str(p.relative_to(repo_root)).replace("\\", "/"))
    analysis.recon = {
        "relevant_components": ["weaver control-plane"],
        "architecture_layers": arch.get("layer_names") or {},
        "relevant_files": relevant[:40],
        "relevant_tests": [t for t in tests if "weaver" in t][:30],
        "relevant_history": (packet.get("recent_lineage") or [])[:5],
        "continuation_message": cont_msg,
    }

    constraints = {
        "protected_boundaries": list(PROTECTED_DEFAULT),
        "forbidden_paths": list(pass_spec.forbidden_paths) if pass_spec else [],
        "non_goals": list(pass_spec.non_goals) if pass_spec else [
            "Autonomous objectives",
            "Self-authorization",
            "Product work without PassSpec",
        ],
        "allowed_paths": list(pass_spec.allowed_paths) if pass_spec else [],
    }
    analysis.constraints = constraints

    hints = list(affected_path_hints or [])
    if pass_spec and not hints:
        hints = list(pass_spec.allowed_paths)[:10]

    # Scope gate on proposed paths
    out_of_scope = []
    forbidden_hit = []
    in_scope = []
    for raw in hints:
        path = raw.replace("\\", "/").lstrip("./")
        if pass_spec:
            for f in pass_spec.forbidden_paths:
                ff = f.replace("\\", "/").lstrip("./")
                if ff and (path == ff or path.startswith(ff.rstrip("/") + "/") or path.startswith(ff)):
                    forbidden_hit.append(path)
                    break
            else:
                if path_in_allowlist(path, pass_spec.allowed_paths):
                    in_scope.append(path)
                else:
                    out_of_scope.append(path)
        else:
            # no pass_spec: analysis may describe paths but not claim authorization
            in_scope.append(path)

    if forbidden_hit or (pass_spec and out_of_scope and not in_scope):
        analysis.result_kind = AnalysisResultKind.PROTECTED_BOUNDARY_CONFLICT.value
        analysis.unresolved.extend([f"out of scope: {p}" for p in out_of_scope])
        analysis.unresolved.extend([f"forbidden: {p}" for p in forbidden_hit])
        analysis.evidence = {"facts": facts, "inferences": inferences, "unknowns": unknowns}
        analysis.recommendation = {
            "action": "request expanded PassSpec",
            "rationale": "Proposed paths conflict with allowed/forbidden boundaries.",
        }
        return analysis

    # Protected product names in objective
    obj_l = objective.lower()
    for b in ("solspire", "reasomate", "oracle", "firebase", "android"):
        if b in obj_l and (not pass_spec or not any(b in a.lower() for a in pass_spec.allowed_paths)):
            analysis.result_kind = AnalysisResultKind.PROTECTED_BOUNDARY_CONFLICT.value
            analysis.unresolved.append(f"objective mentions protected area '{b}' without path authorization")
            analysis.evidence = {"facts": facts, "inferences": inferences, "unknowns": unknowns}
            return analysis

    analysis.assessment = {
        "current_behavior": "Governed Weaver stack K0.1–K8 provides recon, proposal, session, workbench, continuation.",
        "problem_statement": objective.strip(),
        "root_cause": "N/A until implementation; this is pre-change analysis.",
        "confidence": "medium" if authorized else "low (read-only, no PassSpec)",
    }

    steps = [
        "Inspect relevant files listed in recon.relevant_files",
        "Implement only within PassSpec.allowed_paths",
        "Add or update focused tests under tests/test_weaver_*.py as required",
        "Run required tests and architecture suite",
        "Commit and publish via K0.1 gates after human approval of plan",
    ]
    req_tests = [t for t in tests if "weaver" in t][:8]
    if pass_spec and pass_spec.required_tests:
        req_tests = list(pass_spec.required_tests)

    plan_obj = {
        "steps": steps,
        "required_tests": req_tests,
        "required_builds": list(pass_spec.required_builds) if pass_spec else [],
        "verification_requirements": [
            "git diff --check",
            "dirty paths ⊆ allowed_paths",
            "HEAD == origin/main after publication if publication_required",
        ],
        "affected_paths": in_scope,
    }

    # Validate as Plan if authorized
    if pass_spec and in_scope:
        try:
            p = Plan(
                pass_id=pass_spec.pass_id,
                objective=objective.strip(),
                rationale="K9 evidence-bound plan",
                proposed_files=in_scope,
                implementation_steps=steps,
                required_tests=req_tests,
                approved=False,
            )
            validate_plan_against_spec(p, pass_spec)
            plan_obj["plan_valid_against_spec"] = True
        except PlanError as e:
            analysis.result_kind = AnalysisResultKind.BLOCKED.value
            analysis.unresolved.append(str(e))
            analysis.evidence = {"facts": facts, "inferences": inferences, "unknowns": unknowns}
            return analysis

    analysis.proposed_change = {
        "summary": f"Address objective within {len(in_scope)} path(s).",
        "affected_paths": in_scope,
        "unchanged_paths": ["product surfaces unless explicitly authorized"],
    }
    analysis.plan = plan_obj
    analysis.risks = [
        {"level": "KNOWN", "item": "Analysis may be incomplete if relevant files are not under weaver/."},
        {"level": "POSSIBLE", "item": "Provider nondeterminism if LLM used outside this deterministic path."},
    ]
    analysis.unresolved.append("K9 does not execute the plan.")
    analysis.recommendation = {
        "action": "HUMAN REVIEW then K3 transaction if approved",
        "rationale": "K9 stops at planning boundary.",
    }
    analysis.alternatives = [
        {
            "id": "A",
            "benefit": "Minimal scoped change in weaver/",
            "cost": "May not cover product needs",
            "affected_paths": in_scope,
            "risk": "low",
            "confidence": "medium",
        },
        {
            "id": "B",
            "benefit": "Broader product change",
            "cost": "Requires expanded PassSpec",
            "affected_paths": [],
            "risk": "high without authorization",
            "confidence": "low",
        },
    ]
    analysis.evidence = {"facts": facts, "inferences": inferences, "unknowns": unknowns}
    if not authorized:
        analysis.assessment["confidence"] = "low (read-only)"
        analysis.recommendation["action"] = "Supply PassSpec for scoped authorized analysis refinement; still no auto-execute"
    analysis.result_kind = AnalysisResultKind.ANALYSIS_READY.value
    return analysis


def analysis_to_plan(analysis: EngineeringAnalysis, pass_spec: PassSpec) -> Plan:
    """Convert analysis plan section to K3 Plan — still requires human approval."""
    if not pass_spec:
        raise PlanError("PassSpec required")
    paths = list((analysis.proposed_change or {}).get("affected_paths") or [])
    steps = list((analysis.plan or {}).get("steps") or [])
    tests = list((analysis.plan or {}).get("required_tests") or [])
    p = Plan(
        pass_id=pass_spec.pass_id,
        objective=(analysis.objective or {}).get("statement") or pass_spec.objective,
        rationale="Derived from K9 analysis; not self-authorized",
        proposed_files=paths,
        implementation_steps=steps,
        required_tests=tests,
        approved=False,
    )
    validate_plan_against_spec(p, pass_spec)
    return p
