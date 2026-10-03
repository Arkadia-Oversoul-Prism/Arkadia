from __future__ import annotations

from solspire.integration_health import project_integration_health


def test_integration_health_requires_live_probes_and_explicit_larder_binding(monkeypatch):
    from solspire import project_knowledge, project_store
    from types import SimpleNamespace

    monkeypatch.setattr("lab.engineering_lab.runtime.get_runtime", lambda: SimpleNamespace(
        overview=lambda uid: {"subject": uid}
    ))
    monkeypatch.setattr(project_knowledge, "build_project_context_for_weaver", lambda project: {
        "project_id": project["id"], "owner": project["owner_uid"],
        "authorization": {"Execution": "LOCKED"},
    })
    monkeypatch.setattr(project_knowledge, "build_knowledge_summary", lambda pid: {
        "project_id": pid, "sources": {"files": 1}
    })
    monkeypatch.setattr(project_knowledge, "build_derived_graph", lambda pid: {
        "project_id": pid, "kind": "DERIVED_BOUNDED_SEMANTIC",
        "counts": {"nodes": 1, "edges": 0},
    })
    monkeypatch.setattr(project_store, "list_events", lambda pid, limit=500: [
        {"event_type": "living_larder_order_bound",
         "data": {"order_id": "LL-TEST", "status": "pending", "total": 1000,
                  "source": "living_larder_orders"}}
    ])
    monkeypatch.setattr("solspire.integration_health._load_larder_orders", lambda: [
        {"order_id": "LL-TEST", "status": "pending", "total": 1000}
    ])
    monkeypatch.setattr("solspire.workspace_manager.get_workspace_manager", lambda:
                        SimpleNamespace(get_for_subject=lambda uid: SimpleNamespace(id="workspace-owner")))
    monkeypatch.setattr("solspire.workevent_manager.get_workevent_manager", lambda:
                        SimpleNamespace(list=lambda uid, workspace_ref, limit: [
                            SimpleNamespace(event_type="LIVING_LARDER_ORDER_BOUND",
                                            scope_ref="project-1", work_ref="project-1",
                                            artifact_refs=["living-larder-order:LL-TEST"])
                        ]))
    monkeypatch.setenv("SOLSPIRE_AGENT_IMAGE", "registry.example/agent@sha256:" + "a" * 64)
    monkeypatch.setenv("SOLSPIRE_CONTAINER_RUNTIME", "docker")
    monkeypatch.setattr("solspire.integration_health.shutil.which", lambda runtime: "/usr/bin/docker")
    monkeypatch.setattr("solspire.integration_health.subprocess.run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout="ok", stderr=""))

    result = project_integration_health(
        subject_uid="owner-1", project={"id": "project-1", "owner_uid": "owner-1"}
    )
    assert result["contract"] == "solspire.integration-health.v1"
    assert result["all_required_available"] is True
    assert result["capabilities"]["living_larder"]["detail"]["binding_state"] == "PROJECT_BOUND"
    assert result["capabilities"]["isolated_execution"]["detail"]["smoke_test_passed"] is True


def test_integration_health_does_not_infer_larder_binding(monkeypatch):
    from solspire import project_knowledge, project_store
    from types import SimpleNamespace

    monkeypatch.setattr("lab.engineering_lab.runtime.get_runtime", lambda: SimpleNamespace(
        overview=lambda uid: {"subject": uid}
    ))
    monkeypatch.setattr(project_knowledge, "build_project_context_for_weaver", lambda project: {
        "project_id": project["id"], "owner": project["owner_uid"], "authorization": {}
    })
    monkeypatch.setattr(project_knowledge, "build_knowledge_summary", lambda pid: {
        "project_id": pid, "sources": {}
    })
    monkeypatch.setattr(project_knowledge, "build_derived_graph", lambda pid: {
        "project_id": pid, "kind": "DERIVED_BOUNDED_SEMANTIC", "counts": {"nodes": 0, "edges": 0}
    })
    monkeypatch.setattr(project_store, "list_events", lambda pid, limit=500: [])
    monkeypatch.setattr("solspire.integration_health._load_larder_orders", lambda: [])
    monkeypatch.setattr("solspire.workspace_manager.get_workspace_manager", lambda:
                        SimpleNamespace(get_for_subject=lambda uid: None))
    monkeypatch.setenv("SOLSPIRE_AGENT_IMAGE", "registry.example/agent@sha256:" + "a" * 64)
    monkeypatch.setattr("solspire.integration_health.shutil.which", lambda runtime: "/usr/bin/docker")
    monkeypatch.setattr("solspire.integration_health.subprocess.run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout="ok", stderr=""))

    result = project_integration_health(
        subject_uid="owner-1", project={"id": "project-1", "owner_uid": "owner-1"}
    )
    assert result["capabilities"]["living_larder"]["state"] == "UNBOUND"
    assert result["all_required_available"] is False
