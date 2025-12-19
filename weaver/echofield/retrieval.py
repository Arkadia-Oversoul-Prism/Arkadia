"""
Retrieval — Distillation-Forced Retrieval

Forces compression and prevents verbosity.
Deterministic node selection.
"""

from typing import List, Dict, Optional, Tuple


class RetrievalEngine:
    """Distillation-forced retrieval with anti-verbosity."""

    def __init__(self, max_nodes: int = 7, similarity_threshold: float = 0.78, anti_verbosity: bool = True):
        self.max_nodes = max_nodes
        self.similarity_threshold = similarity_threshold
        self.anti_verbosity = anti_verbosity

    def retrieve(
        self,
        query_vector: Tuple[float, ...],
        node_vectors: Dict[str, Tuple[float, ...]],
        anchor_ids: List[str],
        weights: Dict[str, float]
    ) -> List[str]:
        """
        Retrieve most relevant nodes.

        Biases toward anchors and high-weight nodes.
        Enforces similarity threshold.
        Returns at most max_nodes results.
        """
        scored_nodes = []

        for node_id, node_vector in node_vectors.items():
            # Compute cosine similarity
            similarity = self._cosine_similarity(query_vector, node_vector)

            # Skip if below threshold
            if similarity < self.similarity_threshold:
                continue

            # Compute final score with bias
            score = similarity
            if node_id in anchor_ids:
                score *= 1.4  # Anchor boost
            if weights.get(node_id, 0) > 0.7:
                score *= 1.2  # High-weight boost

            scored_nodes.append((node_id, score))

        # Sort by score descending
        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        # Return top max_nodes
        return [node_id for node_id, _ in scored_nodes[:self.max_nodes]]

    @staticmethod
    def _cosine_similarity(vec_a: Tuple[float, ...], vec_b: Tuple[float, ...]) -> float:
        """Compute cosine similarity."""
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = sum(a ** 2 for a in vec_a) ** 0.5
        magnitude_b = sum(b ** 2 for b in vec_b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
