"""Phase 2 bounded conversation bridge contract tests."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from solspire.conversation_bridge import ConversationBridgeError, append_conversation_turn


def _install_fakes(monkeypatch, *, ingest_result=None, ingest_error=None):
    calls: dict[str, list] = {
        "append": [],
        "thread": [],
        "ingest": [],
        "event": [],
    }

    project_store = ModuleType("solspire.project_store")
    conversation = {
        "id": "conv-123",
        "project_id": "project-1",
        "title": "Architecture thread",
    }

    def get_conversation(conv_id):
        return conversation if conv_id == conversation["id"] else None

    def append_message(conv_id, role, content):
        calls["append"].append((conv_id, role, content))
        return {"ok": True}

    def log_event(project_id, event_type, summary, data=None):
        calls["event"].append((project_id, event_type, summary, data))

    project_store.get_conversation = get_conversation
    project_store.append_message = append_message
    project_store.log_event = log_event
    monkeypatch.setitem(sys.modules, "solspire.project_store", project_store)

    knowledge_vault = ModuleType("knowledge.vault")

    def get_or_create_thread(session_id, title=None, user_id=None):
        calls["thread"].append((session_id, title, user_id))
        return 41

    knowledge_vault.get_or_create_thread = get_or_create_thread
    monkeypatch.setitem(sys.modules, "knowledge.vault", knowledge_vault)

    knowledge_pipeline = ModuleType("knowledge.pipeline")

    def ingest(**kwargs):
        calls["ingest"].append(kwargs)
        if ingest_error:
            raise ingest_error
        return ingest_result or {"uuid": "note-123"}

    knowledge_pipeline.ingest = ingest
    monkeypatch.setitem(sys.modules, "knowledge.pipeline", knowledge_pipeline)

    return calls


def test_project_turn_uses_same_conversation_uuid_as_knowledge_thread(monkeypatch):
    calls = _install_fakes(monkeypatch, ingest_result={"uuid": "note-123"})

    result = append_conversation_turn(
        project_id="project-1",
        conv_id="conv-123",
        role="user",
        content="Open the architecture thread.",
        user_id="user-1",
    )

    assert calls["append"] == [("conv-123", "user", "Open the architecture thread.")]
    assert calls["thread"] == [("conv-123", "Architecture thread", "user-1")]
    assert calls["ingest"][0]["thread_id"] == 41
    assert calls["ingest"][0]["user_id"] == "user-1"
    assert "Conversation: conv-123" in calls["ingest"][0]["content"]
    assert result["knowledge"]["status"] == "ingested"
    assert result["knowledge"]["thread_uuid"] == "conv-123"
    assert result["knowledge"]["note_uuid"] == "note-123"
    assert calls["event"][0][1] == "conversation_message"
    assert calls["event"][0][3]["thread_uuid"] == "conv-123"


def test_wrong_project_is_rejected_before_any_write(monkeypatch):
    calls = _install_fakes(monkeypatch)

    with pytest.raises(ConversationBridgeError, match="Conversation not found"):
        append_conversation_turn(
            project_id="different-project",
            conv_id="conv-123",
            role="user",
            content="Should not write.",
            user_id="user-1",
        )

    assert calls["append"] == []
    assert calls["thread"] == []
    assert calls["ingest"] == []
    assert calls["event"] == []


def test_knowledge_failure_is_explicit_not_fabricated(monkeypatch):
    calls = _install_fakes(monkeypatch, ingest_error=RuntimeError("embedding unavailable"))

    result = append_conversation_turn(
        project_id="project-1",
        conv_id="conv-123",
        role="user",
        content="Keep the project record.",
        user_id="user-1",
    )

    assert result["ok"] is True
    assert result["knowledge"]["status"] == "error"
    assert calls["append"]
    assert calls["event"][0][3]["knowledge"]["status"] == "error"


def test_empty_content_is_rejected(monkeypatch):
    _install_fakes(monkeypatch)

    with pytest.raises(ConversationBridgeError, match="content is required"):
        append_conversation_turn(
            project_id="project-1",
            conv_id="conv-123",
            role="user",
            content="   ",
            user_id="user-1",
        )
