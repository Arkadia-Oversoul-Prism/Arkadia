from __future__ import annotations


def _manager(tmp_path, monkeypatch):
    import solspire.workload_manager as mod
    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "workloads.db"))
    return mod.CanonicalWorkloadManager()


def test_barnabas_workload_is_idempotent_and_bounded(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    first = manager.create_canonical_barnabas(subject_ref="subject-a", workspace_ref="workspace-a")
    second = manager.create_canonical_barnabas(subject_ref="subject-a", workspace_ref="workspace-a")
    assert first.workload_id == second.workload_id
    assert first.status == "PROPOSED"
    assert first.phase == "STRUCTURE_PROVISIONED"
    assert first.work_event_refs == []
    assert first.provenance_refs == []
    assert first.authorization_refs == []
    assert first.approval_refs == []
    assert not hasattr(first, "credentials")
    assert not hasattr(first, "mutation")


def test_barnabas_workload_isolated_by_subject_and_workspace(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    workload_a = manager.create_canonical_barnabas(subject_ref="subject-a", workspace_ref="workspace-a")
    workload_b = manager.create_canonical_barnabas(subject_ref="subject-b", workspace_ref="workspace-b")
    assert manager.get_for_subject("subject-a", "workspace-a").workload_id == workload_a.workload_id
    assert manager.get_for_subject("subject-b", "workspace-b").workload_id == workload_b.workload_id
    assert manager.get_for_subject("subject-b", "workspace-a") is None
    assert manager.get_for_subject("subject-a", "workspace-b") is None


def test_workload_owner_does_not_become_authority(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    workload = manager.create_canonical_barnabas(subject_ref="subject-a", workspace_ref="workspace-a")
    assert workload.owner_ref == "subject-a"
    assert workload.authorization_refs == []
    assert workload.approval_refs == []
    assert workload.provenance_refs == []


def test_workload_has_no_live_project_data_or_execution_state(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    workload = manager.create_canonical_barnabas(subject_ref="subject-a", workspace_ref="workspace-a")
    assert workload.participant_refs == []
    assert workload.deliverable_refs == []
    assert workload.artifact_refs == []
    assert workload.evidence_refs == []
    assert workload.decision_refs == []
    assert workload.work_event_refs == []
    assert workload.created_by_event is None
