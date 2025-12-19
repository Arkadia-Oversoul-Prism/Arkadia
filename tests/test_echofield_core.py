"""
Tests for Echofield Core

Ensures deterministic node, vector, edge operations.
"""

from weaver.echofield.node import Node, NodeState, VectorStack, Weights
from weaver.echofield.vector_stack import VectorStack as VS
from weaver.echofield.edge import Edge, RelationType
from weaver.echofield.field import Echofield


def test_vector_stack_quantization():
    """VectorStack clamps to [0, 1]."""
    vs = VectorStack(identity=1.5, function=-0.5)
    assert vs.identity == 1.0
    assert vs.function == 0.0


def test_vector_stack_similarity():
    """Cosine similarity computation."""
    vs1 = VS(identity=1.0, function=0.8)
    vs2 = VS(identity=1.0, function=0.8)
    similarity = vs1.cosine_similarity(vs2)
    assert 0.99 < similarity <= 1.0


def test_weights_total():
    """Weights.total computes correctly."""
    w = Weights(coherence=0.8, recurrence=0.9, alignment=0.7)
    assert 0.49 < w.total < 0.51


def test_edge_decay():
    """Edge strength decays over time."""
    edge = Edge("e1", "n1", "n2", RelationType.RESONATES_WITH, strength=1.0, decay_rate=0.1)
    assert edge.decayed_strength(0) == 1.0
    assert edge.decayed_strength(10) < 0.4


def test_node_anchor_check():
    """Anchor nodes identified correctly."""
    node = Node("n1", "agent", "2025-01-01T00:00:00", "intent", VectorStack(), None, Weights(), NodeState.ANCHOR, None)
    assert node.is_anchor()


def test_echofield_add_node():
    """Echofield tracks nodes."""
    field = Echofield("f1")
    field.add_node("n1")
    field.add_node("n1")  # Duplicate
    assert field.node_count() == 1


def test_echofield_anchors():
    """Echofield tracks anchors distinctly."""
    field = Echofield("f1")
    field.add_anchor("a1")
    assert field.is_anchor("a1")
    assert not field.is_anchor("n1")
