from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lab.council import evaluate_proposal
from lab.evolution.schema import validate_proposal_dict


@dataclass(frozen=True)
class EvolutionProposal:
    data: dict[str, Any]
    council_consensus: str
    schema_errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.schema_errors and self.council_consensus in ("PASS", "DISAGREE")

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.data,
            "council_consensus": self.council_consensus,
            "schema_errors": list(self.schema_errors),
            "phase4_execution": False,
        }


def validate_proposal(p: dict[str, Any]) -> list[str]:
    return validate_proposal_dict(p)


def plan_from_patterns(
    patterns: list[dict[str, Any]],
    *,
    proposal_id: str = "EV-GOLDEN-001",
    title: str | None = None,
) -> EvolutionProposal:
    """Build one schema-bound proposal from pattern evidence. No side effects."""
    if not patterns:
        patterns = [{
            "pattern_id": "pattern:fixture-empty",
            "kind": "none",
            "confidence": 0.0,
            "evidence": [],
        }]
    primary = patterns[0]
    pid = primary.get("pattern_id", "pattern:unknown")
    title = title or f"Address structural pattern: {pid}"
    evidence_ids = [str(p.get("pattern_id", "unknown")) for p in patterns[:20]]
    components = []
    for p in patterns:
        for c in (p.get("components") or p.get("paths") or p.get("evidence") or [])[:10]:
            if isinstance(c, str) and c not in components:
                components.append(c)
    proposal: dict[str, Any] = {
        "proposal_id": proposal_id,
        "title": title,
        "problem": {
            "description": f"Lab-detected pattern requiring structured review: {pid}",
            "evidence": evidence_ids,
        },
        "current_state": {
            "patterns_observed": len(patterns),
            "primary_pattern": primary,
        },
        "target_state": {
            "pattern_resolved_or_accepted": True,
            "documentation_or_consolidation": "pending human approval",
        },
        "canon_alignment": {
            "authority_ceiling": 2,
            "mutation_proposed": False,
            "notes": "Phase 4 proposal only; execution requires later phase + human approval",
        },
        "affected_components": components[:50] or ["lab/"],
        "dependencies": [],
        "implementation": [
            "Human reviews proposal",
            "If approved, schedule under Phase 5+ governed execution (not this phase)",
        ],
        "tests": [
            "Schema validation (Phase 4 gate)",
            "Council advisory pass or recorded disagreement",
        ],
        "migration": ["none — proposal generation only"],
        "risk": {
            "technical": "low",
            "security": "low",
            "product": "low",
            "rollback": "easy",
        },
        "expected_outcomes": [
            "Structured evolution artifact available for human decision",
        ],
        "alternatives": [
            "Accept pattern as known limitation without change",
            "Defer to later phase",
        ],
        "confidence": float(primary.get("confidence") or 0.55),
        "approval_required": True,
    }
    schema_errors = tuple(validate_proposal_dict(proposal))
    # Council sees a Level-2 suggest-shaped advisory object derived from proposal
    council_input = {
        "id": proposal_id,
        "goal": title,
        "kind": "suggest",
        "authority_ceiling": 2,
        "mutation": False,
        "human_authorization": False,
        "bypasses_auth": False,
    }
    council = evaluate_proposal(council_input)
    return EvolutionProposal(
        data=proposal,
        council_consensus=council.consensus,
        schema_errors=schema_errors,
    )
