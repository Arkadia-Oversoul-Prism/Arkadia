"""
Field — Echofield Container

Persistent resonance field across threads.
Deterministic policy application.
"""

from dataclasses import dataclass, field as dataclass_field
from typing import List, Dict, Optional
from enum import Enum


class DecayPolicy:
    """Semantic decay policy, not temporal."""
    def __init__(self, base_rate: float = 0.01, divergence_multiplier: float = 1.5, reinforcement_divisor: float = 2.0):
        self.base_rate = base_rate
        self.divergence_multiplier = divergence_multiplier
        self.reinforcement_divisor = reinforcement_divisor


class RetrievalPolicy:
    """Distillation-forced retrieval policy."""
    def __init__(self, bias: Optional[List[str]] = None, max_nodes: int = 7, similarity_threshold: float = 0.78, anti_verbosity: bool = True):
        self.bias = bias or ["ANCHOR", "HIGH_WEIGHT"]
        self.max_nodes = max_nodes
        self.similarity_threshold = similarity_threshold
        self.anti_verbosity = anti_verbosity


@dataclass
class Echofield:
    """Persistent resonance field across threads."""
    field_id: str
    nodes: List[str] = dataclass_field(default_factory=list)
    edges: List[str] = dataclass_field(default_factory=list)
    anchors: List[str] = dataclass_field(default_factory=list)
    decay_policy: DecayPolicy = dataclass_field(default_factory=DecayPolicy)
    retrieval_policy: RetrievalPolicy = dataclass_field(default_factory=RetrievalPolicy)

    def add_node(self, node_id: str) -> None:
        """Add node to field."""
        if node_id not in self.nodes:
            self.nodes.append(node_id)

    def add_edge(self, edge_id: str) -> None:
        """Add edge to field."""
        if edge_id not in self.edges:
            self.edges.append(edge_id)

    def add_anchor(self, anchor_id: str) -> None:
        """Add anchor to field."""
        if anchor_id not in self.anchors:
            self.anchors.append(anchor_id)

    def is_anchor(self, node_id: str) -> bool:
        """Check if node is an anchor."""
        return node_id in self.anchors

    def node_count(self) -> int:
        """Return count of nodes."""
        return len(self.nodes)

    def anchor_count(self) -> int:
        """Return count of anchors."""
        return len(self.anchors)
