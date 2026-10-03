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
