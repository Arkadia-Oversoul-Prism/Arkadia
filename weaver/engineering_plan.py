"""WEAVER-K11 — Evidence-grounded engineering planning.

PLAN ≠ AUTHORIZATION. ANALYSIS ≠ PLAN APPROVAL ≠ EXECUTION.
Does not write, commit, push, or execute.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .analysis import EngineeringAnalysis, analyze_objective
from .evidence import evidence_for_analysis, query_evidence, collect_evidence
from .pass_spec import PassSpec, path_in_allowlist
from .plan import Plan, PlanError, validate_plan_against_spec


@dataclass
class EngineeringPlan:
    plan_id: str
    schema_version: str = "1.0.0"
    objective: str = ""
    problem_statement: str = ""
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    facts: list[dict[str, Any]] = field(default_factory=list)
    inferences: list[dict[str, Any]] = field(default_factory=list)
    unknowns: list[dict[str, Any]] = field(default_factory=list)
    affected_paths: list[str] = field(default_factory=list)
    proposed_changes: list[str] = field(default_factory=list)
    implementation_steps: list[str] = field(default_factory=list)
    test_strategy: dict[str, Any] = field(default_factory=dict)
    verification_strategy: list[str] = field(default_factory=list)
    risk_register: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    scope_status: str = "UNSCOPED"  # IN_SCOPE | OUT_OF_SCOPE | UNSCOPED
    authorization: dict[str, Any] = field(default_factory=dict)
    approval: dict[str, Any] = field(default_factory=dict)
    review_bundle: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EngineeringPlan":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


def _plan_id(objective: str, head: str, paths: list[str]) -> str:
    blob = f"{head}|{objective}|{','.join(sorted(paths))}"
    return "eplan-" + hashlib.sha256(blob.encode()).hexdigest()[:12]


def _norm_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for p in paths or []:
        n = p.replace("\\", "/").strip().lstrip("./")
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return sorted(out)


def build_engineering_plan(
    objective: str,
    *,
    pass_spec: PassSpec | None = None,
    affected_path_hints: list[str] | None = None,
    repo_root: str = ".",
) -> EngineeringPlan:
    """Deterministic planning from analysis + evidence. Never executes."""
    analysis = analyze_objective(
        objective,
        pass_spec=pass_spec,
        affected_path_hints=affected_path_hints,
        repo_root=repo_root,
    )
    head = (analysis.repository or {}).get("head_sha") or ""
    evidence_blob = (analysis.recon or {}).get("k10_evidence") or evidence_for_analysis(
        repo_root, subject_hints=(affected_path_hints or ["weaver/"])[:5]
    )

    facts = list((analysis.evidence or {}).get("facts") or [])
    inferences = list((analysis.evidence or {}).get("inferences") or [])
    unknowns = list((analysis.evidence or {}).get("unknowns") or [])

    paths = _norm_paths(
        list((analysis.proposed_change or {}).get("affected_paths") or [])
        or list(affected_path_hints or [])
        or (list(pass_spec.allowed_paths) if pass_spec else [])
    )

    # Scope validation
    scope_status = "UNSCOPED"
    out_of_scope: list[str] = []
    if pass_spec:
        scope_status = "IN_SCOPE"
        filtered: list[str] = []
        for path in paths:
            ok = path_in_allowlist(path, pass_spec.allowed_paths)
            forbidden = False
            for f in pass_spec.forbidden_paths:
                ff = f.replace("\\", "/").lstrip("./")
                if ff and (path == ff or path.startswith(ff.rstrip("/") + "/") or path.startswith(ff)):
                    forbidden = True
                    break
            if forbidden or not ok:
                out_of_scope.append(path)
                scope_status = "OUT_OF_SCOPE"
            else:
                filtered.append(path)
        paths = filtered if filtered else paths
        if out_of_scope and not filtered:
            scope_status = "OUT_OF_SCOPE"

    # Dependencies from evidence queries
    deps: list[str] = []
    for p in paths[:10]:
        q = (evidence_blob.get("queries") or {}).get(p) or {}
        for rel in q.get("imports") or []:
            t = rel.get("target")
            if t and t not in deps:
                deps.append(t)

    # Test strategy from evidence
    discoverable: list[str] = []
    missing: list[str] = []
    for p in paths[:10]:
        q = (evidence_blob.get("queries") or {}).get(p)
        if not q:
            # try collect on demand for path
            try:
                idx = collect_evidence(repo_root, roots=["weaver", "tests"])
                q = query_evidence(idx, p)
            except Exception:
                q = {}
        kind = (q or {}).get("test_map_kind") or "UNKNOWN"
        tests = [t.get("source") for t in (q or {}).get("tests") or [] if t.get("source")]
        if kind == "DIRECT_TEST_REFERENCE" and tests:
            discoverable.extend(tests)
        elif kind == "NO_DISCOVERABLE_TEST":
            missing.append(p)

    discoverable = sorted(set(discoverable))
    steps = list((analysis.plan or {}).get("steps") or [])
    if not steps:
        steps = [
            "Inspect affected paths against current HEAD",
            "Implement minimal change within allowed_paths",
            "Add or update focused tests",
            "Run required tests and architecture suite",
            "Human approval then K3 transaction / publication gates",
        ]

    proposed = list((analysis.proposed_change or {}).get("summary") and [(analysis.proposed_change or {}).get("summary")] or [])
    if not proposed:
        proposed = [f"Modify {p}" for p in paths[:8]]

    risks = [
        {
            "risk_id": "r-scope",
            "description": "Change may touch more files than evidence predicts",
            "likelihood": "medium",
            "impact": "medium",
            "mitigation": "Keep PassSpec allow-list tight; diff gate",
            "status": "KNOWN",
        },
        {
            "risk_id": "r-tests",
            "description": "Missing discoverable tests for some paths",
            "likelihood": "medium" if missing else "low",
            "impact": "high",
            "mitigation": "Add focused tests before publication",
            "status": "KNOWN" if missing else "INFERRED",
        },
    ]
    for r in analysis.risks or []:
        risks.append(
            {
                "risk_id": "r-analysis",
                "description": r.get("item") if isinstance(r, dict) else str(r),
                "likelihood": "unknown",
                "impact": "unknown",
                "mitigation": "Human review",
                "status": (r.get("level") if isinstance(r, dict) else "INFERRED"),
            }
        )

    alts = list(analysis.alternatives or [])
    non_goals = list((analysis.constraints or {}).get("non_goals") or [])
    if pass_spec:
        non_goals = list(dict.fromkeys(non_goals + list(pass_spec.non_goals)))

    authorized = bool(pass_spec is not None)
    plan_id = _plan_id(objective, head, paths)

    evidence_refs = []
    for f in facts[:20]:
        evidence_refs.append(
            {
                "kind": f.get("kind"),
                "statement": f.get("statement"),
                "source": f.get("source"),
                "path": f.get("path"),
                "commit_sha": f.get("commit_sha") or head,
            }
        )

    verification = list((analysis.plan or {}).get("verification_requirements") or [])
    if not verification:
        verification = [
            "git diff --check",
            "dirty paths ⊆ allowed_paths",
            "pytest focused + architecture",
        ]

    test_strategy = {
        "discoverable_tests": discoverable,
        "paths_without_discoverable_tests": sorted(set(missing)),
        "required_tests": list((analysis.plan or {}).get("required_tests") or discoverable[:8]),
        "note": "DIRECT_TEST_REFERENCE is static discoverability, not runtime coverage",
    }

    review = {
        "objective": objective,
        "problem": (analysis.assessment or {}).get("problem_statement") or objective,
        "evidence_summary": {
            "fact_count": len(facts),
            "inference_count": len(inferences),
            "unknown_count": len(unknowns),
            "k10_files": (evidence_blob.get("index_summary") or {}).get("file_count"),
        },
        "proposed_change": proposed,
        "affected_paths": paths,
        "implementation_steps": steps,
        "test_strategy": test_strategy,
        "verification_strategy": verification,
        "risks": risks,
        "unknowns": unknowns,
        "alternatives": alts,
        "scope_status": scope_status,
        "authorization_status": "AUTHORIZED_ENVELOPE" if authorized else "NONE",
        "approval": False,
        "next_action": "awaiting human authorization",
    }

    return EngineeringPlan(
        plan_id=plan_id,
        objective=objective,
        problem_statement=(analysis.assessment or {}).get("problem_statement") or objective,
        evidence_refs=evidence_refs,
        facts=facts,
        inferences=inferences,
        unknowns=unknowns,
        affected_paths=paths,
        proposed_changes=proposed,
        implementation_steps=steps,
        test_strategy=test_strategy,
        verification_strategy=verification,
        risk_register=risks,
        dependencies=sorted(deps)[:30],
        alternatives=alts,
        non_goals=non_goals,
        scope_status=scope_status,
        authorization={
            "current_pass_authorized": authorized,
            "state": "PASS_SPEC" if authorized else "NONE",
            "note": "PLAN ≠ AUTHORIZATION. approval=false until human acts.",
        },
        approval={"approved": False},
        review_bundle=review,
    )


def engineering_plan_to_k3(
    eplan: EngineeringPlan,
    pass_spec: PassSpec,
) -> Plan:
    """Translate to K3 Plan. Does not approve or execute."""
    if eplan.scope_status == "OUT_OF_SCOPE":
        raise PlanError("PLAN_OUT_OF_SCOPE")
    if not pass_spec:
        raise PlanError("PassSpec required")
    plan = Plan(
        pass_id=pass_spec.pass_id,
        objective=eplan.objective or pass_spec.objective,
        rationale="K11 evidence-grounded plan; not self-authorized",
        proposed_files=list(eplan.affected_paths),
        implementation_steps=list(eplan.implementation_steps),
        required_tests=list((eplan.test_strategy or {}).get("required_tests") or []),
        required_builds=list(pass_spec.required_builds),
        architectural_impact=["Weaver control-plane"],
        risks=[r.get("description", "") for r in eplan.risk_register],
        expected_outcome="Human-approved K3 transaction",
        approved=False,
    )
    validate_plan_against_spec(plan, pass_spec)
    return plan


def review_engineering_plan(eplan: EngineeringPlan) -> dict[str, Any]:
    return dict(eplan.review_bundle or eplan.to_dict())
