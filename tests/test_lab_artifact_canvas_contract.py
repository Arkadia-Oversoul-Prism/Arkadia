"""Engineering Lab artifact canvas — backend oracle (Workstream 4).

The canvas read surface (`LabArtifactCanvas`) reads two real handlers:

  * ``GET /api/lab/engineering/artifacts`` -> ``{"artifacts": [...], "count": n}``
  * ``GET /api/lab/engineering/canvas/{artifact_id}`` -> ``canvas_view(artifact)``

This file drives the **real** store and ``canvas_view`` over an isolated
database and pins the shape the console depends on, including the truthfulness
rule the renderer relies on: ``available`` is false when no content was captured,
so the client cannot present a placeholder as a real artifact.

Negative controls prove each detector fires on the defect it exists to catch.
"""
from __future__ import annotations

import uuid

import pytest

OWNER = "subject-owner"
OTHER = "subject-other"


@pytest.fixture()
def store(tmp_path, monkeypatch):
    from lab.engineering_lab import store as store_mod

    monkeypatch.setattr(store_mod, "_DB_PATH", str(tmp_path / "lab.db"))
    monkeypatch.setattr(store_mod, "_GLOBAL_STORE", None)
    return store_mod.get_store()


def _artifact(uid: str, *, kind: str = "markdown", title: str = "Report", content=None, session="SES-1"):
    return {
        "artifact_id": f"ART-{uuid.uuid4().hex[:12]}",
        "session_id": session,
        "run_id": "RUN-1",
        "kind": kind,
        "title": title,
        "content": content,
        "created_at": "2026-10-11T00:00:00+00:00",
    }


def _captured(view: dict) -> bool:
    """The truthfulness detector: does the descriptor claim content it lacks?"""
    if view["available"] and not view["artifact"].get("content"):
        return False
    if not view["available"] and not view["unavailable_reason"]:
        return False
    return True


# ---------------------------------------------------------------------------
# The list contract the console reads
# ---------------------------------------------------------------------------

def test_list_artifacts_returns_owner_scoped_records(store):
    a = _artifact(OWNER, content="# Hi")
    store.save_artifact(a, OWNER)
    listed = store.list_artifacts(OWNER)
    assert len(listed) == 1
    assert set(listed[0]) >= {"artifact_id", "session_id", "kind", "title", "created_at"}
    assert listed[0]["artifact_id"] == a["artifact_id"]


def test_list_artifacts_can_filter_by_session(store):
    store.save_artifact(_artifact(OWNER, session="SES-A"), OWNER)
    store.save_artifact(_artifact(OWNER, session="SES-B"), OWNER)
    assert len(store.list_artifacts(OWNER, "SES-A")) == 1
    assert len(store.list_artifacts(OWNER)) == 2


def test_reads_are_owner_scoped(store):
    a = _artifact(OWNER)
    store.save_artifact(a, OWNER)
    assert store.list_artifacts(OTHER) == []
    assert store.get_artifact(a["artifact_id"], OTHER) is None


# ---------------------------------------------------------------------------
# The canvas descriptor the renderer reads
# ---------------------------------------------------------------------------

def test_canvas_descriptor_keys_are_the_ones_the_console_reads(store):
    from lab.engineering_lab.artifacts import canvas_view

    a = _artifact(OWNER, content="# Hi")
    store.save_artifact(a, OWNER)
    view = canvas_view(store.get_artifact(a["artifact_id"], OWNER))
    assert set(view) == {"artifact", "renderer", "available", "kind", "actions", "unavailable_reason"}
    assert _captured(view)


def test_present_content_is_available_with_a_declared_renderer(store):
    from lab.engineering_lab.artifacts import canvas_view

    a = _artifact(OWNER, kind="markdown", content="# Hi")
    store.save_artifact(a, OWNER)
    view = canvas_view(store.get_artifact(a["artifact_id"], OWNER))
    assert view["available"] is True
    assert view["renderer"] == "MarkdownViewer"
    assert view["unavailable_reason"] == ""


def test_absent_content_is_unavailable_and_says_why(store):
    """A captured-but-empty artifact must not be rendered as if it had content."""
    from lab.engineering_lab.artifacts import canvas_view

    a = _artifact(OWNER, kind="json", content=None)
    store.save_artifact(a, OWNER)
    view = canvas_view(store.get_artifact(a["artifact_id"], OWNER))
    assert view["available"] is False
    assert view["unavailable_reason"]
    assert _captured(view)


def test_declared_actions_are_affordances_not_authority(store):
    """The descriptor declares UI affordances; none is an execution/authorization
    act, and the console wires none of them."""
    from lab.engineering_lab.artifacts import CANVAS_ACTIONS, canvas_view

    a = _artifact(OWNER, content="x")
    store.save_artifact(a, OWNER)
    view = canvas_view(store.get_artifact(a["artifact_id"], OWNER))
    assert view["actions"] == list(CANVAS_ACTIONS)
    assert set(CANVAS_ACTIONS) == {"INSPECT", "COMPARE", "ANNOTATE", "EXPORT", "ATTACH", "ARCHIVE"}
    for forbidden in ("EXECUTE", "AUTHORIZE", "APPROVE", "MERGE", "DEPLOY"):
        assert forbidden not in CANVAS_ACTIONS


# ---------------------------------------------------------------------------
# The handlers exist as declared, read-only GET routes
# ---------------------------------------------------------------------------

def test_canvas_routes_are_declared_get_routes():
    from pathlib import Path

    routes = (Path(__file__).resolve().parents[1] / "api" / "lab_routes.py").read_text(encoding="utf-8")
    assert '@router.get("/engineering/artifacts")' in routes
    assert '@router.get("/engineering/canvas/{artifact_id}")' in routes


def test_canvas_subresource_path_is_served():
    """The path the console builds must be a served path (parameter name aside)."""
    import re

    from api.main import app

    served = {re.sub(r"\{[^}]*\}", "{}", p) for p in app.openapi()["paths"].keys()}
    assert "/api/lab/engineering/canvas/{}" in served


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def test_negative_control_capture_detector_flags_a_fabricated_view():
    """The detector must report a descriptor that claims content it lacks, or one
    that is empty without saying why."""
    fabricated = {"available": True, "artifact": {"content": None}, "unavailable_reason": ""}
    assert _captured(fabricated) is False
    silent = {"available": False, "artifact": {"content": None}, "unavailable_reason": ""}
    assert _captured(silent) is False
    honest = {"available": False, "artifact": {"content": None}, "unavailable_reason": "nothing captured"}
    assert _captured(honest) is True
