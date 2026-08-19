"""PHASE 0B private retrieval isolation — synthetic users, no Firebase."""
from __future__ import annotations
import os, tempfile
import pytest

_tmpdir = tempfile.mkdtemp(prefix="arkadia_isolation_")
os.environ["ARKADIA_DB_PATH"] = os.path.join(_tmpdir, "test.db")

from knowledge.db import get_connection
from knowledge.vault import (
    create_note, get_note, get_note_by_id, list_notes,
    create_project, get_project, list_projects,
)
from knowledge.graph import add_edge, traverse, find_path, full_graph_export, accessible_note_ids
from knowledge import timeline as tl

USER_A, USER_B = "isolation-user-a", "isolation-user-b"
CANARY_A = "ARKADIA_PRIVATE_CANARY_USER_A_20260819"
CANARY_B = "ARKADIA_PRIVATE_CANARY_USER_B_20260819"
PUBLIC_MARK = "ARKADIA_PUBLIC_CORPUS_MARKER_20260819"

@pytest.fixture(autouse=True)
def _fresh_db():
    conn = get_connection()
    for table in ("graph_edges", "timeline", "chunks", "embeddings", "note_tags", "notes", "threads", "projects"):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()
    yield

def test_direct_note_isolation():
    a = create_note(title=CANARY_A, content=f"secret {CANARY_A}", user_id=USER_A)
    b = create_note(title=CANARY_B, content=f"secret {CANARY_B}", user_id=USER_B)
    pub = create_note(title=PUBLIC_MARK, content=f"public {PUBLIC_MARK}", user_id=None)
    assert get_note(a["uuid"], user_id=USER_A) is not None
    assert get_note(a["uuid"], user_id=USER_B) is None
    assert get_note(a["uuid"], user_id=None) is None
    assert get_note(b["uuid"], user_id=USER_B) is not None
    assert get_note(b["uuid"], user_id=USER_A) is None
    assert get_note(pub["uuid"], user_id=None) is not None

def test_direct_node_by_id_isolation():
    a = create_note(title=CANARY_A, content="x", user_id=USER_A)
    assert get_note_by_id(a["id"], user_id=USER_A) is not None
    assert get_note_by_id(a["id"], user_id=USER_B) is None
    assert get_note_by_id(a["id"], user_id=None) is None

def test_full_graph_isolation():
    a = create_note(title=CANARY_A, content="a", user_id=USER_A)
    b = create_note(title=CANARY_B, content="b", user_id=USER_B)
    pub = create_note(title=PUBLIC_MARK, content="p", user_id=None)
    ids_a = {n["id"] for n in full_graph_export(user_id=USER_A)["nodes"]}
    ids_b = {n["id"] for n in full_graph_export(user_id=USER_B)["nodes"]}
    ids_0 = {n["id"] for n in full_graph_export(user_id=None)["nodes"]}
    assert a["id"] in ids_a and b["id"] not in ids_a and pub["id"] in ids_a
    assert b["id"] in ids_b and a["id"] not in ids_b
    assert pub["id"] in ids_0 and a["id"] not in ids_0

def test_graph_traversal_isolation():
    a1 = create_note(title="A1", content="a1", user_id=USER_A)
    a2 = create_note(title="A2", content="a2", user_id=USER_A)
    b1 = create_note(title="B1", content="b1", user_id=USER_B)
    add_edge(a1["id"], a2["id"], "references")
    ta = traverse(a1["id"], max_depth=2, user_id=USER_A)
    assert a1["id"] in {n["id"] for n in ta["nodes"]} and b1["id"] not in {n["id"] for n in ta["nodes"]}
    assert traverse(b1["id"], max_depth=2, user_id=USER_A)["nodes"] == []
    assert traverse(a1["id"], max_depth=2, user_id=None)["nodes"] == []

def test_cross_boundary_graph_edge():
    a1 = create_note(title="A1x", content="a", user_id=USER_A)
    b1 = create_note(title="B1x", content="b", user_id=USER_B)
    add_edge(a1["id"], b1["id"], "references")
    assert b1["id"] not in {n["id"] for n in traverse(a1["id"], max_depth=2, user_id=USER_A)["nodes"]}
    assert a1["id"] not in {n["id"] for n in traverse(b1["id"], max_depth=2, user_id=USER_B)["nodes"]}

def test_path_isolation():
    a1 = create_note(title="Ap1", content="a", user_id=USER_A)
    a2 = create_note(title="Ap2", content="a", user_id=USER_A)
    b1 = create_note(title="Bp1", content="b", user_id=USER_B)
    add_edge(a1["id"], a2["id"], "references")
    add_edge(a2["id"], b1["id"], "references")
    assert find_path(a1["id"], a2["id"], user_id=USER_A) == [a1["id"], a2["id"]]
    assert find_path(a1["id"], b1["id"], user_id=USER_A) == []
    assert find_path(a1["id"], a2["id"], user_id=None) == []

def test_neighbour_isolation():
    a1 = create_note(title="An1", content="a", user_id=USER_A)
    a2 = create_note(title="An2", content="a", user_id=USER_A)
    pub = create_note(title="PubN", content="p", user_id=None)
    b1 = create_note(title="Bn1", content="b", user_id=USER_B)
    add_edge(a1["id"], a2["id"], "references")
    add_edge(a1["id"], pub["id"], "references")
    add_edge(a1["id"], b1["id"], "references")
    ids = {n["id"] for n in traverse(a1["id"], max_depth=1, user_id=USER_A)["nodes"]}
    assert a2["id"] in ids and pub["id"] in ids and b1["id"] not in ids

def test_timeline_isolation():
    a = create_note(title=CANARY_A, content="t", user_id=USER_A)
    b = create_note(title=CANARY_B, content="t", user_id=USER_B)
    tl.record("knowledge_created", {"title": CANARY_A}, note_id=a["id"], user_id=USER_A)
    tl.record("knowledge_created", {"title": CANARY_B}, note_id=b["id"], user_id=USER_B)
    ea, eb, e0 = tl.query(limit=100, user_id=USER_A), tl.query(limit=100, user_id=USER_B), tl.query(limit=100, user_id=None)
    assert any(e.get("note_id") == a["id"] for e in ea) and not any(e.get("note_id") == b["id"] for e in ea)
    assert any(e.get("note_id") == b["id"] for e in eb)
    assert e0 == []
    assert tl.recent(limit=20, user_id=None) == []

def test_project_isolation():
    pa = create_project("Secret Project A", user_id=USER_A)
    pb = create_project("Secret Project B", user_id=USER_B)
    pub = create_project("Public Project", user_id=None)
    assert get_project(pa["uuid"], user_id=USER_A) is not None
    assert get_project(pa["uuid"], user_id=USER_B) is None
    assert get_project("Secret Project A", user_id=USER_B) is None
    names_a = {p["name"] for p in list_projects(user_id=USER_A)}
    names_0 = {p["name"] for p in list_projects(user_id=None)}
    assert "Secret Project A" in names_a and "Secret Project B" not in names_a
    assert "Public Project" in names_0 and "Secret Project A" not in names_0

def test_public_corpus_preserved():
    pub = create_note(title=PUBLIC_MARK, content="open", user_id=None)
    assert get_note(pub["uuid"], user_id=None) is not None
    assert any(n["uuid"] == pub["uuid"] for n in list_notes(user_id=None))

def test_list_notes_ownership():
    create_note(title=CANARY_A, content="a", user_id=USER_A)
    create_note(title=CANARY_B, content="b", user_id=USER_B)
    create_note(title=PUBLIC_MARK, content="p", user_id=None)
    ta = {n["title"] for n in list_notes(user_id=USER_A, limit=100)}
    t0 = {n["title"] for n in list_notes(user_id=None, limit=100)}
    assert CANARY_A in ta and CANARY_B not in ta and PUBLIC_MARK in ta
    assert PUBLIC_MARK in t0 and CANARY_A not in t0

def test_accessible_note_ids():
    a = create_note(title="A", content="a", user_id=USER_A)
    b = create_note(title="B", content="b", user_id=USER_B)
    p = create_note(title="P", content="p", user_id=None)
    assert a["id"] in accessible_note_ids(USER_A) and b["id"] not in accessible_note_ids(USER_A)
    assert p["id"] in accessible_note_ids(None) and a["id"] not in accessible_note_ids(None)
