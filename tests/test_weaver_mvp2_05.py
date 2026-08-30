"""MVP2-05 — bounded semantic graph invariants."""
from __future__ import annotations

import solspire.project_store as store
from solspire.semantic_graph import build_bounded_semantic_graph


def test_only_explicit_event_references_become_semantic_edges(monkeypatch):
    monkeypatch.setattr(store, "list_files", lambda project_id: [{"id": "f1", "name": "a.py"}])
    monkeypatch.setattr(store, "list_repositories", lambda project_id: [{"id": "r1", "repo": "demo"}])
    monkeypatch.setattr(store, "list_tasks", lambda project_id: [{"id": "t1", "title": "Fix"}])
    monkeypatch.setattr(store, "list_memory", lambda project_id: [])
    monkeypatch.setattr(store, "list_conversations", lambda project_id: [])
    monkeypatch.setattr(
        store,
        "list_events",
        lambda project_id: [
            {"id": "e1", "event_type": "x", "summary": "file linked", "data": '{"file_id":"f1"}'},
            {"id": "e2", "event_type": "x", "summary": "unknown", "data": '{"file_id":"missing"}'},
        ],
    )

    graph = build_bounded_semantic_graph("p1")
    assert graph["kind"] == "DERIVED_BOUNDED_SEMANTIC"
    assert graph["edges"] == [
        {
            "from": "event:e1",
            "to": "file:f1",
            "type": "REFERENCES",
            "classification": "SOURCE-BACKED",
            "provenance": "project_store.events.data",
            "evidence_id": "e1",
        }
    ]


def test_semantic_graph_is_read_only_and_non_authoritative(monkeypatch):
    for name in ("list_files", "list_repositories", "list_tasks", "list_memory", "list_conversations", "list_events"):
        monkeypatch.setattr(store, name, lambda project_id: [])

    graph = build_bounded_semantic_graph("p2")
    assert graph["authorization"]["PassSpec"] == "NONE"
    assert graph["authorization"]["PatchApproval"] == "NONE"
    assert graph["authorization"]["Execution"] == "LOCKED"
    assert any("Not an authoritative graph store" in item for item in graph["limitations"])


def test_malformed_event_data_does_not_create_inferred_edges(monkeypatch):
    for name in ("list_files", "list_repositories", "list_tasks", "list_memory", "list_conversations"):
        monkeypatch.setattr(store, name, lambda project_id: [{"id": "x", "name": "x"}])
    monkeypatch.setattr(
        store,
        "list_events",
        lambda project_id: [{"id": "e1", "summary": "bad", "data": "not-json"}],
    )

    graph = build_bounded_semantic_graph("p3")
    assert graph["edges"] == []
