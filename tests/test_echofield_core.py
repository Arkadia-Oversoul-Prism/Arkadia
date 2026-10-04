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


def test_resolver_module_is_importable():
    """Every module the package declares must import.

    `weaver/echofield/__init__.py` lists `resolver.py` as part of the package, but the
    module annotated its arguments with `Dict` without importing it, so it raised
    `NameError` on import while its six siblings imported cleanly. Imported lazily here
    so a regression fails this node rather than erroring the whole file.
    """
    import importlib

    module = importlib.import_module("weaver.echofield.resolver")
    assert hasattr(module, "ConflictResolver")
    assert hasattr(module, "ConflictRule")


def _node(node_id, *, node_type="NODE", directive=0.0, glyphs=0, operators=None):
    return {
        "node_id": node_id,
        "node_type": node_type,
        "vector_stack": {"directive": directive},
        "symbolic_payload": {"glyphs": ["g"] * glyphs, "operators": operators or []},
    }


def test_resolver_anchor_beats_non_anchor():
    """Rule 1: an ANCHOR node dominates a non-anchor, in either argument order.

    The winner's id is the anchor's, not merely "the first argument", so argument order
    must not change the outcome.
    """
    from weaver.echofield.resolver import ConflictResolver

    anchor = _node("a", node_type="ANCHOR")
    plain = _node("b")
    assert ConflictResolver.resolve(anchor, plain) == "a"
    assert ConflictResolver.resolve(plain, anchor) == "a"


def test_resolver_higher_directive_wins_beyond_margin():
    """Rule 2: the higher directive wins, but only past the 0.1 margin."""
    from weaver.echofield.resolver import ConflictResolver

    assert ConflictResolver.resolve(_node("a", directive=0.5), _node("b", directive=0.2)) == "a"
    assert ConflictResolver.resolve(_node("a", directive=0.2), _node("b", directive=0.5)) == "b"
    # Within the margin the directive axis is inconclusive and Rule 3 decides instead.
    assert ConflictResolver.resolve(_node("a", directive=0.5, glyphs=3), _node("b", directive=0.45)) == "b"


def test_resolver_lower_entropy_wins():
    """Rule 3: fewer glyphs (lower entropy) wins when earlier rules tie."""
    from weaver.echofield.resolver import ConflictResolver

    assert ConflictResolver.resolve(_node("a", glyphs=1), _node("b", glyphs=4)) == "a"
    assert ConflictResolver.resolve(_node("a", glyphs=4), _node("b", glyphs=1)) == "b"


def test_resolver_returns_none_when_unresolvable():
    """No rule discriminates -> None, i.e. a CLARITY_REQUEST rather than a guess."""
    from weaver.echofield.resolver import ConflictResolver

    assert ConflictResolver.resolve(_node("a", glyphs=2), _node("b", glyphs=2)) is None


def test_resolver_contradiction_requires_disjoint_critical_operators():
    """`contradicts` fires only when both sides carry critical ops and they differ."""
    from weaver.echofield.resolver import ConflictResolver

    assert ConflictResolver.contradicts(
        _node("a", operators=["DEFINE"]), _node("b", operators=["ANCHOR"])
    )
    # Same critical operator is agreement, not contradiction.
    assert not ConflictResolver.contradicts(
        _node("a", operators=["DEFINE"]), _node("b", operators=["DEFINE"])
    )
    # One side has no critical operator, so there is nothing to contradict.
    assert not ConflictResolver.contradicts(
        _node("a", operators=["DEFINE"]), _node("b", operators=["OBSERVE"])
    )
