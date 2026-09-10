"""Bind Phase 9 decisions to Phase 5 governed dry-run execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lab.decision.schema import Decision, DecisionKind
from lab.execution.governed import execute_governed, GovernedExecutionResult


@dataclass
class BindingResult:
    decision_kind: str
    opportunity_title: str
    bound: bool
    reason: str
    execution: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_kind": self.decision_kind,
            "opportunity_title": self.opportunity_title,
            "bound": self.bound,
            "reason": self.reason,
            "execution": self.execution,
            "events": list(self.events),
            "merge": False,
            "deploy": False,
            "auto_execute": False,
        }


def bind_approved_decision(
    decision: Decision | dict[str, Any],
    *,
    mode: str = "dry_run",
) -> BindingResult:
    """Only APPROVE decisions may bind. Default mode is dry_run.

    prepare_pr still requires injected callables inside execute_governed and
    never merges/deploys. REJECT/DEFER never bind.
    """
    if isinstance(decision, dict):
        kind = str(decision.get("kind") or "")
        title = str(decision.get("opportunity_title") or "")
        rationale = str(decision.get("rationale") or "")
        prov = dict(decision.get("opportunity_provenance") or {})
        # Hard reject if caller smuggled true execution flags
        if decision.get("execution_authorized") is True:
            return BindingResult(
                decision_kind=kind,
                opportunity_title=title,
                bound=False,
                reason="execution_authorized must remain false; binding refuses elevated decision payloads",
            )
    else:
        kind = decision.kind.value if isinstance(decision.kind, DecisionKind) else str(decision.kind)
        title = decision.opportunity_title
        rationale = decision.rationale
        prov = dict(decision.opportunity_provenance or {})

    if kind != DecisionKind.APPROVE.value and kind != "APPROVE":
        return BindingResult(
            decision_kind=kind,
            opportunity_title=title,
            bound=False,
            reason=f"{kind} cannot bind to governed execution; only APPROVE may bind (still dry-run)",
        )

    if mode not in ("dry_run", "prepare_pr"):
        return BindingResult(
            decision_kind=kind,
            opportunity_title=title,
            bound=False,
            reason=f"unsupported mode {mode!r}; only dry_run|prepare_pr",
        )

    proposal = {
        "proposal_id": f"EV-PHASE10-{abs(hash(title)) % 10_000_000:07d}",
        "title": title,
        "rationale": rationale,
        "provenance": prov,
        "source": "phase9_decision",
        "phase": 10,
        "approval_required": True,
        "execution": False,
        "auto_apply": False,
    }
    result: GovernedExecutionResult = execute_governed(proposal, mode=mode)
    return BindingResult(
        decision_kind=kind,
        opportunity_title=title,
        bound=True,
        reason="bound to Phase 5 governed pipeline (no merge/deploy)",
        execution=result.to_dict(),
        events=list(result.events),
    )
