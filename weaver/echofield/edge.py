"""
Edge — Non-Hierarchical Lattice Binding

Connects nodes without creating hierarchy.
Deterministic relation and strength computation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RelationType(Enum):
    """Relation types for non-hierarchical binding."""
    RESONATES_WITH = "RESONATES_WITH"
    REFINES = "REFINES"
    DIVERGES_FROM = "DIVERGES_FROM"
    ANCHORS = "ANCHORS"


@dataclass
class Edge:
    """Non-hierarchical edge binding."""
    edge_id: str
    from_node_id: str
    to_node_id: str
    relation: RelationType
    strength: float = 0.0
    decay_rate: float = 0.01

    def __post_init__(self):
        """Clamp strength to [0, 1]."""
        self.strength = max(0.0, min(1.0, float(self.strength)))
        self.decay_rate = max(0.0, min(1.0, float(self.decay_rate)))

    def decayed_strength(self, time_steps: int) -> float:
        """
        Compute decayed strength after N time steps.
        strength_t = strength * (1 - decay_rate)^t
        """
        return self.strength * ((1 - self.decay_rate) ** time_steps)

    def is_strong(self, threshold: float = 0.7) -> bool:
        """Check if edge strength exceeds threshold."""
        return self.strength >= threshold
