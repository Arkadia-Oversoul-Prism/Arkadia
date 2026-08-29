"""WEAVER-K3 — structured engineering Plan (information, not authorization).

PLAN ≠ AUTHORIZATION. A plan cannot expand PassSpec permissions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .pass_spec import PassSpec, PassSpecError, path_in_allowlist


class PlanError(Exception):
    """Plan validation / scope failure."""


@dataclass
class Plan:
    pass_id: str
    objective: str
    rationale: str = ""
    proposed_files: list[str] = field(default_factory=list)
    implementation_steps: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    required_builds: list[str] = field(default_factory=list)
    architectural_impact: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    expected_outcome: str = ""
    approved: bool = False  # human approval marker; never set by the model alone

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Plan":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


def validate_plan_against_spec(plan: Plan, spec: PassSpec) -> None:
    """Reject plans that propose paths outside the PassSpec envelope."""
    if plan.pass_id and plan.pass_id != spec.pass_id:
        raise PlanError(f"plan pass_id mismatch: {plan.pass_id} != {spec.pass_id}")
    for path in plan.proposed_files:
        norm = path.replace("\\", "/").lstrip("./")
        for forbidden in spec.forbidden_paths:
            f = forbidden.replace("\\", "/").lstrip("./")
            if f and (norm == f or norm.startswith(f.rstrip("/") + "/") or norm.startswith(f)):
                raise PlanError(f"PLAN_OUT_OF_SCOPE forbidden: {path}")
        if not path_in_allowlist(path, spec.allowed_paths):
            raise PlanError(f"PLAN_OUT_OF_SCOPE not allowed: {path}")


def plan_cannot_expand_spec(plan: Plan, spec: PassSpec) -> PassSpec:
    """Return the original PassSpec unchanged — plans never mutate authorization."""
    validate_plan_against_spec(plan, spec)
    return spec


def build_plan_from_spec(spec: PassSpec, *, rationale: str = "", steps: list[str] | None = None) -> Plan:
    """Deterministic minimal plan derived from PassSpec (no LLM required)."""
    return Plan(
        pass_id=spec.pass_id,
        objective=spec.objective,
        rationale=rationale or "Derived from explicit PassSpec authorization.",
        proposed_files=list(spec.allowed_paths),
        implementation_steps=steps or ["Implement within allowed_paths only", "Run required_tests", "Finalize via session kernel"],
        required_tests=list(spec.required_tests),
        required_builds=list(spec.required_builds),
        architectural_impact=["Weaver control-plane only"],
        risks=["Scope creep if plan is treated as authorization"],
        expected_outcome="Authorized objective satisfied under K0.1 gates",
        approved=False,
    )


def approve_plan(plan: Plan) -> Plan:
    """Human approval boundary — call only after explicit human authorization for this plan."""
    plan.approved = True
    return plan
