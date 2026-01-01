"""
Decay — Semantic Decay Calculation

Decay is semantic, not temporal.
Enforced by divergence and reinforcement.
"""

from typing import Optional


class SemanticDecay:
    """Semantic decay engine."""

    @staticmethod
    def compute_decay(
        base_weight: float,
        divergence_factor: float,
        reinforcement_factor: float,
        base_rate: float = 0.01,
        divergence_multiplier: float = 1.5,
        reinforcement_divisor: float = 2.0
    ) -> float:
        """
        Compute semantic decay.

        decay_rate = base_rate * divergence_factor * divergence_multiplier / (reinforcement_factor * reinforcement_divisor)
        new_weight = base_weight * (1 - decay_rate)
        """
        decay_rate = (
            base_rate *
            divergence_factor *
            divergence_multiplier /
            max(0.1, reinforcement_factor * reinforcement_divisor)
        )

        # Clamp decay_rate to [0, 1]
        decay_rate = max(0.0, min(1.0, decay_rate))

        new_weight = base_weight * (1 - decay_rate)
        return max(0.0, min(1.0, new_weight))

    @staticmethod
    def is_anchor_exempt(node_id: str, anchors: list) -> bool:
        """Check if node is decay-exempt anchor."""
        return node_id in anchors
