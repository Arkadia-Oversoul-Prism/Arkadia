"""
Resolver — Conflict Resolution Engine

Deterministic resolution rules.
No invented bridges, only clarity.
"""

from enum import Enum
from typing import Optional, Tuple


class ConflictRule(Enum):
    """Conflict resolution hierarchy."""
    ANCHOR_BEATS_NON_ANCHOR = 1
    HIGHER_DIRECTIVE_WINS = 2
    LOWER_ENTROPY_WINS = 3
    SUSPEND_OUTPUT = 4


class ConflictResolver:
    """Resolve node conflicts deterministically."""

    @staticmethod
    def resolve(
        node_a: Dict,
        node_b: Dict
    ) -> Optional[str]:
        """
        Resolve conflict between two nodes.

        Returns:
        - node_a_id if A dominates
        - node_b_id if B dominates
        - None if unresolvable (CLARITY_REQUEST)
        """
        # Rule 1: Anchor beats non-anchor
        a_is_anchor = node_a.get("node_type") == "ANCHOR"
        b_is_anchor = node_b.get("node_type") == "ANCHOR"

        if a_is_anchor and not b_is_anchor:
            return node_a.get("node_id")
        if b_is_anchor and not a_is_anchor:
            return node_b.get("node_id")

        # Rule 2: Higher directive wins
        a_directive = node_a.get("vector_stack", {}).get("directive", 0.0)
        b_directive = node_b.get("vector_stack", {}).get("directive", 0.0)

        if a_directive > b_directive + 0.1:
            return node_a.get("node_id")
        if b_directive > a_directive + 0.1:
            return node_b.get("node_id")

        # Rule 3: Lower entropy wins
        # (simplified: fewer glyphs = lower entropy)
        a_glyphs = len(node_a.get("symbolic_payload", {}).get("glyphs", []))
        b_glyphs = len(node_b.get("symbolic_payload", {}).get("glyphs", []))

        if a_glyphs < b_glyphs:
            return node_a.get("node_id")
        if b_glyphs < a_glyphs:
            return node_b.get("node_id")

        # Unresolvable
        return None

    @staticmethod
    def contradicts(node_a: Dict, node_b: Dict) -> bool:
        """Check if two nodes directly contradict."""
        a_operators = set(node_a.get("symbolic_payload", {}).get("operators", []))
        b_operators = set(node_b.get("symbolic_payload", {}).get("operators", []))

        # Simple check: if operators are disjoint on critical operations
        critical_ops = {"DEFINE", "ANCHOR"}
        return bool((a_operators & critical_ops) and (b_operators & critical_ops) and a_operators != b_operators)
