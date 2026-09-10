from __future__ import annotations

REQUIRED_TOP = (
    "proposal_id",
    "title",
    "problem",
    "current_state",
    "target_state",
    "canon_alignment",
    "affected_components",
    "dependencies",
    "implementation",
    "tests",
    "migration",
    "risk",
    "expected_outcomes",
    "alternatives",
    "confidence",
    "approval_required",
)

RISK_LEVELS = frozenset({"low", "medium", "high"})
ROLLBACK = frozenset({"easy", "medium", "hard"})


def validate_proposal_dict(p: dict) -> list[str]:
    """Return list of schema errors (empty = valid)."""
    errs: list[str] = []
    for k in REQUIRED_TOP:
        if k not in p:
            errs.append(f"missing:{k}")
    if "problem" in p and isinstance(p["problem"], dict):
        if not p["problem"].get("description"):
            errs.append("problem.description required")
        if "evidence" not in p["problem"] or not isinstance(p["problem"]["evidence"], list):
            errs.append("problem.evidence must be a list")
    else:
        if "problem" in p:
            errs.append("problem must be object")
    risk = p.get("risk")
    if isinstance(risk, dict):
        for dim in ("technical", "security", "product"):
            if risk.get(dim) not in RISK_LEVELS:
                errs.append(f"risk.{dim} must be low|medium|high")
        if risk.get("rollback") not in ROLLBACK:
            errs.append("risk.rollback must be easy|medium|hard")
    elif "risk" in p:
        errs.append("risk must be object")
    conf = p.get("confidence")
    if conf is not None:
        try:
            c = float(conf)
            if not 0.0 <= c <= 1.0:
                errs.append("confidence must be 0.0–1.0")
        except (TypeError, ValueError):
            errs.append("confidence must be float")
    if p.get("approval_required") is not True:
        errs.append("approval_required must be true (Phase 4: no silent execution)")
    if p.get("execution") is True or p.get("auto_apply") is True:
        errs.append("execution/auto_apply forbidden in Phase 4 proposals")
    pid = p.get("proposal_id")
    if pid is not None and not (isinstance(pid, str) and pid.startswith("EV-")):
        errs.append("proposal_id must start with EV-")
    return errs
