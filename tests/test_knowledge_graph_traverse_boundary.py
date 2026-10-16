"""Knowledge OS graph traversal — the returned edge list is a set, not a hop log.

``knowledge.graph.traverse`` seeds a BFS with the start node and expands to
``max_depth`` hops. The pre-repair accumulation appended an edge on *every* hop
whose frontier touched it, so a graph containing a cycle or a diamond returned the
same edge row more than once. Measured on a ``1->2, 1->3, 3->4`` fixture starting
at node 3 with ``max_depth=2``: edge ``1->3`` was returned twice, because node 1
is adjacent to both the start (3) and node 2, so the second hop rediscovered the
``1->3`` row.

The node set was already deduped by the ``visited`` set; only the edge list
carried the duplicate. The defect is therefore invisible to a node-set assertion
and was unpinned by the existing isolation and lineage guards, which assert node
membership only.

The edge row's identity is ``graph_edges.id`` (the schema declares
``UNIQUE(source_note_id, target_note_id, relationship)``), so the row id is the
correct dedupe key. This guard pins the *set* property over the returned edge list
and carries a negative control: the pre-repair accumulation is reconstructed
inline and must be observed to duplicate on the same fixture, so a fixture that no
longer triggers the class cannot pass silently.
"""

from __future__ import annotations

import os
import tempfile

os.environ["ARKADIA_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="arkadia_traverse_"), "test.db"
)

import pytest

from knowledge.db import execute, get_connection
from knowledge.graph import accessible_note_ids, add_edge, traverse
from knowledge.vault import create_note

USER_A = "traverse-user-a"


@pytest.fixture(autouse=True)
def _fresh_db():
    conn = get_connection()
    for table in (
        "graph_edges",
        "timeline",
        "chunks",
        "embeddings",
        "note_tags",
        "notes",
        "threads",
        "projects",
    ):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()
    yield


def _diamond_fixture() -> dict[str, int]:
    """Public notes ``1->2``, ``1->3``, ``3->4``. Node 1 is adjacent to both the
    start (3) and node 2, so a two-hop walk from 3 re-reaches edge ``1->3``."""
    a = create_note(title="T-PUB-A", content="a", user_id=None)
    b = create_note(title="T-PUB-B", content="b", user_id=None)
    c = create_note(title="T-PUB-C", content="c", user_id=None)
    d = create_note(title="T-PUB-D", content="d", user_id=None)
    add_edge(a["id"], b["id"], "references")
    add_edge(a["id"], c["id"], "references")
    add_edge(c["id"], d["id"], "references")
    return {"a": a["id"], "b": b["id"], "c": c["id"], "d": d["id"]}


def _duplicate_edge_ids(edges: list[dict]) -> set[int]:
    """Edge row ids that appear more than once in a returned edge list.

    This is the detector the negative control is proved against: a list that
    carries a repeated row must report it, and a correctly deduped list must not.
    """
    seen: set[int] = set()
    dupes: set[int] = set()
    for edge in edges:
        if edge["id"] in seen:
            dupes.add(edge["id"])
        seen.add(edge["id"])
    return dupes


def _pre_repair_traverse_edges(
    start_id: int, max_depth: int = 2, user_id: str | None = None
) -> list[dict]:
    """The pre-repair accumulation, reproduced verbatim for the negative control.

    It is the same BFS with the single difference that an edge is appended on
    every hop whose frontier touches it. Keeping it here — rather than describing
    it in prose — is what proves the fixture still triggers the class.
    """
    allowed = accessible_note_ids(user_id)
    if start_id not in allowed:
        return []
    visited: set[int] = {start_id}
    frontier: list[int] = [start_id]
    all_edges: list[dict] = []
    for _ in range(max_depth):
        if not frontier:
            break
        placeholders = ",".join("?" * len(frontier))
        conditions = f"(source_note_id IN ({placeholders}) OR target_note_id IN ({placeholders}))"
        params = tuple(frontier + frontier)
        edges = execute(f"SELECT * FROM graph_edges WHERE {conditions}", params)
        next_frontier: list[int] = []
        for edge in edges:
            src, tgt = edge["source_note_id"], edge["target_note_id"]
            if src not in allowed or tgt not in allowed:
                continue
            all_edges.append(edge)
            for nid in (src, tgt):
                if nid not in visited and nid in allowed:
                    visited.add(nid)
                    next_frontier.append(nid)
        frontier = next_frontier
    return all_edges


# ── negative control ─────────────────────────────────────────────────────────

def test_negative_control_fixture_triggers_the_pre_repair_duplication():
    """The fixture must actually exercise the class the guard protects.

    If this fails, the diamond is gone from the fixture and the positive
    assertions below would pass vacuously.
    """
    ids = _diamond_fixture()
    legacy = _pre_repair_traverse_edges(ids["c"], max_depth=2, user_id=None)
    assert _duplicate_edge_ids(legacy), (
        "fixture no longer produces a duplicated edge under the pre-repair "
        "accumulation; the guard would pass vacuously"
    )


def test_detector_flags_a_duplicated_edge_list():
    """The detector itself is not vacuous: a repeated row is reported."""
    rows = [
        {"id": 1, "source_note_id": 1, "target_note_id": 2},
        {"id": 1, "source_note_id": 1, "target_note_id": 2},
    ]
    assert _duplicate_edge_ids(rows) == {1}
    assert _duplicate_edge_ids([{"id": 7, "source_note_id": 1, "target_note_id": 2}]) == set()


# ── the invariant ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("depth", [1, 2, 3])
def test_traverse_returns_each_edge_at_most_once(depth):
    ids = _diamond_fixture()
    result = traverse(ids["c"], max_depth=depth, user_id=None)
    assert _duplicate_edge_ids(result["edges"]) == set()
    assert len(result["edges"]) == len({e["id"] for e in result["edges"]})


def test_dedup_does_not_drop_reachable_nodes():
    """Deduping the edge list must not change the reachable node set.

    The pre-repair and repaired walks must agree on nodes; only the edge list
    differs. This bounds the change to the edge projection.
    """
    ids = _diamond_fixture()
    legacy_edges = _pre_repair_traverse_edges(ids["c"], max_depth=2, user_id=None)
    legacy_nodes = {e["source_note_id"] for e in legacy_edges} | {
        e["target_note_id"] for e in legacy_edges
    } | {ids["c"]}
    fixed = traverse(ids["c"], max_depth=2, user_id=None)
    fixed_nodes = {n["id"] for n in fixed["nodes"]}
    assert legacy_nodes == fixed_nodes == {ids["a"], ids["b"], ids["c"], ids["d"]}


def test_depth_one_edge_list_is_unchanged():
    """A single hop cannot rediscover an edge, so depth 1 must be untouched."""
    ids = _diamond_fixture()
    result = traverse(ids["a"], max_depth=1, user_id=None)
    assert {(e["source_note_id"], e["target_note_id"]) for e in result["edges"]} == {
        (ids["a"], ids["b"]),
        (ids["a"], ids["c"]),
    }
    assert len(result["edges"]) == 2


def test_relationship_filter_still_selects_and_dedupes():
    ids = _diamond_fixture()
    add_edge(ids["a"], ids["d"], "derived_from")
    filtered = traverse(ids["c"], max_depth=2, relationship_filter="references", user_id=None)
    assert {e["relationship"] for e in filtered["edges"]} == {"references"}
    assert _duplicate_edge_ids(filtered["edges"]) == set()


def test_ownership_boundary_still_drops_out_of_scope_edges():
    """An edge with an inaccessible endpoint stays invisible, and the repair must
    not weaken that boundary by deduping across scopes."""
    ids = _diamond_fixture()
    private = create_note(title="T-PRIV", content="secret", user_id=USER_A)
    add_edge(ids["a"], private["id"], "references")

    anon = traverse(ids["a"], max_depth=2, user_id=None)
    anon_nodes = {n["id"] for n in anon["nodes"]}
    assert private["id"] not in anon_nodes
    assert all(
        private["id"] not in (e["source_note_id"], e["target_note_id"]) for e in anon["edges"]
    )

    owner = traverse(ids["a"], max_depth=2, user_id=USER_A)
    assert private["id"] in {n["id"] for n in owner["nodes"]}
    assert _duplicate_edge_ids(owner["edges"]) == set()
