from __future__ import annotations


def _manager(tmp_path, monkeypatch):
    import solspire.workevent_manager as mod
    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "workevents.db"))
    return mod.WorkEventManager()


def test_workevent_is_persistent_and_immutable_by_identity(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    event = manager.create(
        subject_ref="subject-a",
        workspace_ref="workspace-a",
        event_type="WORK_OPENED",
        occurred_at=1000.0,
        work_event_id="event-a",
    )

    loaded = manager.get("event-a", "subject-a")
    assert loaded is not None
    assert loaded.work_event_id == event.work_event_id
    assert loaded.recorded_at == event.recorded_at
    assert loaded.status == "RECORDED"

    try:
        manager.create(
            subject_ref="subject-a",
            workspace_ref="workspace-a",
            event_type="THREAD_CLOSED",
            occurred_at=2000.0,
            work_event_id="event-a",
        )
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate WorkEvent identity must be rejected")


def test_workevent_isolated_by_subject_and_workspace(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    event_a = manager.create(
        subject_ref="subject-a",
        workspace_ref="workspace-a",
        event_type="WORK_OPENED",
        occurred_at=1000.0,
        work_event_id="event-a",
    )
    event_b = manager.create(
        subject_ref="subject-b",
        workspace_ref="workspace-b",
        event_type="WORK_OPENED",
        occurred_at=1001.0,
        work_event_id="event-b",
    )

    assert manager.get("event-a", "subject-b") is None
    assert manager.get("event-b", "subject-a") is None
    assert [e.work_event_id for e in manager.list("subject-a")] == [event_a.work_event_id]
    assert [e.work_event_id for e in manager.list("subject-b")] == [event_b.work_event_id]


def test_workevent_rejects_authority_like_status_and_invalid_temporal_range(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    try:
        manager.create(
            subject_ref="subject-a",
            workspace_ref="workspace-a",
            event_type="APPROVAL_RECORDED",
            occurred_at=1000.0,
            status="AUTHORIZED",
        )
    except ValueError as exc:
        assert "Unsupported WorkEvent status" in str(exc)
    else:
        raise AssertionError("authorization must not be a WorkEvent status")

    try:
        manager.create(
            subject_ref="subject-a",
            workspace_ref="workspace-a",
            event_type="WORK_OPENED",
            occurred_at=1000.0,
            effective_from=2000.0,
            effective_until=1000.0,
        )
    except ValueError as exc:
        assert "effective_from" in str(exc)
    else:
        raise AssertionError("contradictory effective range must be rejected")


def test_workevent_does_not_require_or_create_authority_provenance_or_mutation_fields(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    event = manager.create(
        subject_ref="subject-a",
        workspace_ref="workspace-a",
        event_type="VERIFICATION_RECORDED",
        occurred_at=1000.0,
    )
    assert not hasattr(event, "authority_event")
    assert not hasattr(event, "provenance")
    assert not hasattr(event, "authorization")
    assert not hasattr(event, "mutation")
