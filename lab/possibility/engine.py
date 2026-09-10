"""Deterministic opportunity recognition for Phase 8.

The engine only recognizes and structures possibilities. It has no execution,
mutation, build, revert, or deployment capability.
"""

from typing import Any

from .schema import Opportunity


def generate_opportunities(
    capabilities: list[str],
    patterns: list[str],
    trajectory: list[str],
    unused_infrastructure: list[str],
    recurring_needs: list[str],
) -> list[Opportunity]:
    """Generate deterministic opportunities from supplied evidence.

    A single golden rule is intentionally simple: a capability + supporting
    pattern + trajectory signal produces one structured opportunity. Inputs are
    treated as evidence, never as authorization to act.
    """
    opportunities: list[Opportunity] = []
    if not capabilities or not patterns or not trajectory:
        return opportunities

    capability = capabilities[0]
    pattern = patterns[0]
    direction = trajectory[0]
    infrastructure = unused_infrastructure[0] if unused_infrastructure else "none identified"
    need = recurring_needs[0] if recurring_needs else "none identified"

    opportunities.append(
        Opportunity(
            title=f"Extend {capability} into a governed opportunity path",
            provenance={
                "capability": [capability],
                "pattern": [pattern],
                "trajectory": [direction],
                "unused_infrastructure": [infrastructure],
                "recurring_need": [need],
            },
            value="Structured opportunity for human evaluation before any product or execution decision.",
            evidence=[
                f"capability:{capability}",
                f"pattern:{pattern}",
                f"trajectory:{direction}",
            ],
            cost="Requires human scoping and subsequent engineering/commercial assessment.",
            risk="Opportunity recognition can overstate value if evidence is incomplete; no action is implied.",
            alignment="Recognition-only Phase 8 scope; human approval remains required.",
        )
    )
    return opportunities


def opportunity_payloads(**inputs: Any) -> list[dict[str, Any]]:
    """Return JSON-ready opportunity records without adding execution metadata."""
    return [item.to_dict() for item in generate_opportunities(**inputs)]
