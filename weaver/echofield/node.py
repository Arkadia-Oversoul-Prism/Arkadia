"""
Node — Atomic Semantic Event

Represents a single scroll, utterance, or distilled intent.
Deterministic structure only. No execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime


class NodeState(Enum):
    """Node lifecycle state."""
    ANCHOR = "ANCHOR"
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    DECAYING = "DECAYING"


@dataclass
class Provenance:
    """Audit + sovereignty."""
    thread_id: str
    session_id: str
    checksum: str
    version: str


@dataclass
class VectorStack:
    """Orthogonal meaning axes."""
    identity: float = 0.0
    function: float = 0.0
    resonance: float = 0.0
    structure: float = 0.0
    mythic: float = 0.0
    directive: float = 0.0

    def __post_init__(self):
        """Quantize to [0, 1]."""
        for attr in self.__dataclass_fields__:
            value = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, float(value))))


@dataclass
class SymbolicPayload:
    """Grammar-as-geometry. Meaning-as-operators."""
    glyphs: List[str] = field(default_factory=list)
    operators: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class Weights:
    """Dynamic, computed—not authored."""
    coherence: float = 0.0
    recurrence: float = 0.0
    alignment: float = 0.0

    @property
    def total(self) -> float:
        """Total = coherence × recurrence × alignment."""
        return self.coherence * self.recurrence * self.alignment


@dataclass
class Node:
    """Atomic semantic event container."""
    node_id: str
    agent_id: str
    timestamp: str
    intent_signature: str
    vector_stack: VectorStack
    symbolic_payload: SymbolicPayload
    weights: Weights
    state: NodeState
    provenance: Provenance
    node_type: str = "NODE"

    def is_anchor(self) -> bool:
        """Check if this is an anchor node."""
        return self.state == NodeState.ANCHOR

    def decay_eligible(self) -> bool:
        """Check if eligible for decay."""
        return self.state in (NodeState.ACTIVE, NodeState.DORMANT)
