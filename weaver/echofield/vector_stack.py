"""
VectorStack — Multi-axis Semantic Representation

Orthogonal axes for meaning without single-point embedding.
Deterministic comparison and weighting.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class VectorStack:
    """
    Six orthogonal axes for semantic representation.
    Each value ∈ [0, 1], quantized, comparable.
    """
    identity: float = 0.0
    function: float = 0.0
    resonance: float = 0.0
    structure: float = 0.0
    mythic: float = 0.0
    directive: float = 0.0

    def __post_init__(self):
        """Clamp all values to [0, 1]."""
        for attr in ['identity', 'function', 'resonance', 'structure', 'mythic', 'directive']:
            value = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, float(value))))

    def as_tuple(self) -> Tuple[float, ...]:
        """Return as comparable tuple."""
        return (self.identity, self.function, self.resonance, self.structure, self.mythic, self.directive)

    def cosine_similarity(self, other: 'VectorStack') -> float:
        """
        Compute cosine similarity between two stacks.
        Returns value ∈ [0, 1].
        """
        if not isinstance(other, VectorStack):
            return 0.0

        a = self.as_tuple()
        b = other.as_tuple()

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x ** 2 for x in a) ** 0.5
        magnitude_b = sum(y ** 2 for y in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def dominance_check(self, axis: str) -> bool:
        """
        Check if a given axis is dominant (> 0.8).
        Used for directive/identity checks.
        """
        return getattr(self, axis, 0.0) > 0.8
