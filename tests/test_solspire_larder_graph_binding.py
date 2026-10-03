from __future__ import annotations

import json

from solspire import project_knowledge, project_store, semantic_graph


def test_explicit_larder_binding_becomes_source_backed_graph_edge(monkeypatch):
    event = {
        "id": "event-1",
        "event_type": "living_larder_order_bound",
        "summary": "Order bound",
        "data": json.dumps({"order_id": "LL-123", "total": 4200}),
    }
    monkeypatch.setattr(project_store, "list_files", lambda pid: [])
    monkeypatch.setattr(project_store, "list_repositories", lambda pid: [])
    monkeypatch.setattr(project_store, "list_tasks", lambda pid: [])
    monkeypatch.setattr(project_store, "list_memory", lambda pid: [])
    monkeypatch.setattr(project_store, "list_conversations", lambda pid: [])
    monkeypatch.setattr(project_store, "list_events", lambda pid: [event])

    graph = semantic_graph.build_bounded_semantic_graph("project-1")
    order = next(node for node in graph["nodes"] if node["id"] == "living_larder_order:LL-123")
    edge = next(edge for edge in graph["edges"] if edge["type"] == "BINDS")
    assert order["type"] == "LivingLarderOrder"
    assert edge["evidence_id"] == "event-1"
    assert edge["classification"] == "SOURCE-BACKED"
    assert any(e["from"] == "project:project-1" and e["to"] == "event:event-1"
               and e["type"] == "HAS_EVENT" for e in graph["edges"])


def test_arkana_context_includes_only_explicitly_bound_larder_snapshot(monkeypatch):
    event = {
        "id": "event-1", "event_type": "living_larder_order_bound",
        "summary": "Order bound", "created_at": 10.0,
        "data": json.dumps({"order_id": "LL-123", "status": "pending",
                            "subtotal": 4000, "delivery_fee": 200,
                            "total": 4200, "item_count": 2,
                            "snapshot_digest": "sha256:test"}),
    }
    monkeypatch.setattr(project_knowledge, "build_knowledge_summary", lambda pid: {
        "sources": {}, "items": {}, "embeddings": {}
    })
    monkeypatch.setattr(project_knowledge, "build_derived_graph", lambda pid: {
        "project_id": pid, "kind": "DERIVED_BOUNDED_SEMANTIC", "nodes": [], "edges": [], "counts": {}
    })
    monkeypatch.setattr(project_store, "list_events", lambda pid, limit=100: [event])
    monkeypatch.setattr("solspire.workspace_manager.get_workspace_manager",
                        lambda: type("WorkspaceManager", (), {
                            "get_for_subject": lambda self, uid: type("Workspace", (), {
                                "id": "workspace-owner",
                                "to_dict": lambda self: {"id": "workspace-owner"},
                            })()
                        })())
    monkeypatch.setattr("solspire.pulse_manager.get_pulse_manager",
                        lambda: type("PulseManager", (), {
                            "get_for_subject_date": lambda self, *args: None
                        })())
    witnessed = type("WorkEvent", (), {
        "event_type": "LIVING_LARDER_ORDER_BOUND",
        "scope_ref": "project-1", "work_ref": "project-1",
        "artifact_refs": ["living-larder-order:LL-123"],
        "to_dict": lambda self: {
            "event_type": self.event_type, "scope_ref": self.scope_ref,
            "work_ref": self.work_ref, "artifact_refs": self.artifact_refs,
        },
    })()
    monkeypatch.setattr("solspire.workevent_manager.get_workevent_manager",
                        lambda: type("WorkEventManager", (), {
                            "list": lambda self, *args: [witnessed]
                        })())

    context = project_knowledge.build_project_context_for_weaver({
        "id": "project-1", "name": "Eden", "owner_uid": "owner-1"
    })
    assert context["living_larder"]["binding_state"] == "PROJECT_BOUND"
    assert context["living_larder"]["orders"][0]["order_id"] == "LL-123"
    assert context["living_larder"]["orders"][0]["total"] == 4200
    assert context["continuity"]["binding_state"]["daily_pulse"] == "UNKNOWN"



def test_knowledge_os_distinguishes_unavailable_source_from_empty_source(monkeypatch):
    monkeypatch.setattr(project_store, "list_memory",
                        lambda pid: (_ for _ in ()).throw(RuntimeError("memory store unavailable")))
    monkeypatch.setattr(project_store, "list_files", lambda pid: [])
    monkeypatch.setattr(project_store, "list_repositories", lambda pid: [])
    monkeypatch.setattr(project_store, "list_tasks", lambda pid: [])
    monkeypatch.setattr(project_store, "list_events", lambda pid: [])
    monkeypatch.setattr(project_store, "list_conversations", lambda pid: [])

    class Embeddings:
        def describe(self, project_id):
            return {"state": "UNCONFIGURED", "project_id": project_id}

    summary = project_knowledge.build_knowledge_summary("project-1", embedding_provider=Embeddings())
    assert summary["sources"]["memory"] == 0
    assert summary["source_health"]["state"] == "PARTIAL"
    assert "memory" in summary["source_health"]["errors"]

def test_arkana_context_does_not_turn_unavailable_sources_into_empty_data(monkeypatch):
    monkeypatch.setattr(project_knowledge, "build_knowledge_summary", lambda pid: {
        "project_id": pid,
        "sources": {"memory": 0, "files": 0},
        "items": {"repositories": []},
        "embeddings": {"state": "UNAVAILABLE"},
        "source_health": {"state": "PARTIAL", "errors": {"memory": "RuntimeError: unavailable"}},
    })
    monkeypatch.setattr(project_store, "list_events",
                        lambda pid, limit=100: (_ for _ in ()).throw(RuntimeError("event store unavailable")))
    monkeypatch.setattr("solspire.workspace_manager.get_workspace_manager",
                        lambda: (_ for _ in ()).throw(RuntimeError("workspace unavailable")))

    context = project_knowledge.build_project_context_for_weaver({
        "id": "project-1", "name": "Eden", "owner_uid": "owner-1"
    })

    assert context["knowledge"] is None
    assert context["repositories"] is None
    assert context["knowledge_source_health"]["state"] == "PARTIAL"
    assert context["project_events"] is None
    assert context["project_events_state"] == "UNAVAILABLE"
    assert context["continuity"]["work_events"] is None
    assert context["continuity"]["binding_state"]["workevents"] == "UNAVAILABLE"
    assert context["living_larder"]["orders"] is None
