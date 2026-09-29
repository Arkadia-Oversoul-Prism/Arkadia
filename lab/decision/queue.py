"""Deterministic human decision queue over opportunities."""
from __future__ import annotations

from typing import Any, Iterable

from lab.possibility.schema import Opportunity

from .schema import Decision, DecisionKind


def record_decision(
    opportunity: Opportunity | dict[str, Any],
    kind: DecisionKind | str,
    rationale: str,
    *,
    decided_by: str = "human",
    notes: str = "",
) -> Decision:
    """Record a single human decision. Never authorizes execution."""
    if isinstance(kind, str):
        kind = DecisionKind(kind)
    if isinstance(opportunity, dict):
        title = str(opportunity.get("title") or "")
        prov = dict(opportunity.get("provenance") or {})
    else:
        title = opportunity.title
        prov = dict(opportunity.provenance or {})
    if not title:
        raise ValueError("opportunity title required")
    if not rationale.strip():
        raise ValueError("rationale required for auditable decision")
    return Decision(
        opportunity_title=title,
        kind=kind,
        rationale=rationale.strip(),
        decided_by=decided_by,
        opportunity_provenance=prov,
        notes=notes,
    )


def decide_opportunities(
    opportunities: Iterable[Opportunity | dict[str, Any]],
    policy: dict[str, str] | None = None,
) -> list[Decision]:
    """Apply an explicit decision policy map title→kind for tests/fixtures.

    Production use requires human-supplied policy; empty policy → all DEFER.
    Never auto-approves without explicit mapping.
    """
    policy = policy or {}
    out: list[Decision] = []
    for opp in opportunities:
        title = opp["title"] if isinstance(opp, dict) else opp.title
        kind_raw = policy.get(title, DecisionKind.DEFER.value)
        out.append(
            record_decision(
                opp,
                kind_raw,
                rationale=(
                    f"Explicit policy decision: {kind_raw}"
                    if title in policy
                    else "No human policy mapping; default DEFER (no action)."
                ),
            )
        )
    return out
