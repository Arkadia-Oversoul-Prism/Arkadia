"""Phase 3 bounded project activity projection contracts."""

from __future__ import annotations

import sys
from types import ModuleType

import solspire.activity_projection as projection


def _install_fakes(monkeypatch, *, existing=None):
    calls = {"create": [], "get": []}

    manager = ModuleType("solspire.workevent_manager")

    class Event:
        def __init__(self, payload):
            self.payload = payload

        def to_dict(self):
            return self.payload

    class Manager:
        def get(self, work_event_id, subject):
            calls["get"].append((work_event_id, subject))
            return existing

        def create(self, **kwargs):
            calls["create"].append(kwargs)
            return Event({"work_event_id": kwargs["work_event_id"], **kwargs})

    manager.get_workevent_manager = lambda: Manager()
    monkeypatch.setattr(projection, "get_workevent_manager", lambda: Manager())
    return calls


def test_project_event_maps_to_recorded_workevent(monkeypatch):
    calls = _install_fakes(monkeypatch)

    result = projection.project_event_to_workevent(
        subject_uid="user-1",
        workspace_id="workspace-1",
        project_id="project-1",
        event={
            "id": "event-1",
            "event_type": "task_created",
            "summary": "Task: calibrate",
            "created_at": 123.0,
            "data": {"task_id": "task-1"},
        },
    )

    assert result["work_event_id"] == "project-event:event-1"
    assert calls["create"][0]["event_type"] == "PROJECT_TASK_CREATED"
    assert calls["create"][0]["status"] == "RECORDED"
    assert calls["create"][0]["work_ref"] == "project-1"
    assert calls["create"][0]["artifact_refs"] == ["task-1"]


def test_projection_is_idempotent(monkeypatch):
    existing = type("Existing", (), {"to_dict": lambda self: {"work_event_id": "project-event:event-1"}})()
    calls = _install_fakes(monkeypatch, existing=existing)

    result = projection.project_event_to_workevent(
        subject_uid="user-1",
        workspace_id="workspace-1",
        project_id="project-1",
        event={
            "id": "event-1",
            "event_type": "file_created",
            "created_at": 123.0,
            "data": {"file_id": "file-1"},
        },
    )

    assert result["work_event_id"] == "project-event:event-1"
    assert calls["create"] == []


def test_unknown_project_event_is_not_promoted(monkeypatch):
    calls = _install_fakes(monkeypatch)

    result = projection.project_event_to_workevent(
        subject_uid="user-1",
        workspace_id="workspace-1",
        project_id="project-1",
        event={
            "id": "event-1",
            "event_type": "unknown_internal_event",
            "created_at": 123.0,
            "data": {},
        },
    )

    assert result is None
    assert calls["create"] == []


def test_projection_reports_unavailable_without_workspace(monkeypatch):
    workspace_manager = ModuleType("solspire.workspace_manager")
    workspace_manager.get_workspace_manager = lambda: type(
        "WM", (), {"get_for_subject": lambda self, uid: None}
    )()
    monkeypatch.setitem(sys.modules, "solspire.workspace_manager", workspace_manager)

    monkeypatch.setattr(projection, "get_workspace_manager", lambda: workspace_manager.get_workspace_manager())
    result = projection.project_activity_to_workspace("user-1")
    assert result["status"] == "UNAVAILABLE"
    assert result["work_events_created"] == 0
