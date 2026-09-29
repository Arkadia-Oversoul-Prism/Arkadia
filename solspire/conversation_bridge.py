"""Bounded Phase 2 bridge for project conversation turns.

One server-side composition path:
project conversation -> Knowledge OS thread/note -> project activity event.

This module introduces orchestration only. It does not create a second
conversation, graph, embedding, or activity store.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("solspire.conversation_bridge")


class ConversationBridgeError(ValueError):
    """Raised when a project conversation turn cannot be composed."""


def append_conversation_turn(
    project_id: str,
    conv_id: str,
    role: str,
    content: str,
    user_id: str,
) -> dict[str, Any]:
    """Persist one project conversation turn across the existing substrates.

    The project conversation UUID is reused as the Knowledge OS thread UUID.
    The Knowledge OS still owns its integer threads.id internally; no new
    thread identifier is invented by the project layer.
    """
    role_value = (role or "user").strip() or "user"
    content_value = (content or "").strip()
    uid = (user_id or "").strip()

    if not uid:
        raise ConversationBridgeError("Authenticated user is required")
    if not content_value:
        raise ConversationBridgeError("Conversation content is required")

    from solspire.project_store import (
        append_message,
        get_conversation,
        log_event,
    )

    conversation = get_conversation(conv_id)
    if not conversation or str(conversation.get("project_id")) != str(project_id):
        raise ConversationBridgeError("Conversation not found")

    # Project conversation remains the canonical project record.
    append_message(conv_id, role_value, content_value)

    knowledge: dict[str, Any] = {
        "status": "not_attempted",
        "thread_uuid": conv_id,
        "thread_id": None,
        "note_uuid": None,
    }

    try:
        from knowledge.pipeline import ingest
        from knowledge.vault import get_or_create_thread

        thread_id = get_or_create_thread(
            conv_id,
            title=conversation.get("title") or "Project conversation",
            user_id=uid,
        )

        # The conversation UUID is deliberately included in the note content
        # because Knowledge OS duplicate detection is content-scoped. This
        # preserves one note per project turn without changing the canonical
        # pipeline or introducing a second dedupe authority.
        note_content = (
            f"Project: {project_id}\n"
            f"Conversation: {conv_id}\n"
            f"Role: {role_value}\n\n"
            f"{content_value}"
        )

        conversation_title = conversation.get("title") or "Project conversation"
        note = ingest(
            title=f"{conversation_title} · {role_value}"[:200],
            content=note_content,
            note_type="conversation",
            thread_id=thread_id,
            tags=[
                "solspire",
                "project-conversation",
                role_value,
                f"project:{project_id}",
            ],
            source_provider="solspire_project",
            user_id=uid,
            auto_tag=True,
            auto_embed=True,
            auto_link=True,
        )

        knowledge.update(
            {
                "status": "ingested",
                "thread_id": thread_id,
                "note_uuid": note.get("uuid"),
                "duplicate": bool(note.get("duplicate")),
            }
        )
    except Exception:
        # The project turn is already durable. Surface the degraded bridge
        # state explicitly in the activity event rather than manufacturing
        # successful Knowledge OS continuity.
        knowledge["status"] = "error"
        logger.exception(
            "Knowledge OS ingestion failed for project=%s conversation=%s",
            project_id,
            conv_id,
        )

    log_event(
        project_id,
        "conversation_message",
        f"Conversation message ({role_value}): {content_value[:120]}",
        {
            "conversation_id": conv_id,
            "thread_uuid": conv_id,
            "role": role_value,
            "knowledge": knowledge,
        },
    )

    return {
        "ok": True,
        "message": {
            "conversation_id": conv_id,
            "role": role_value,
            "content": content_value,
        },
        "knowledge": knowledge,
    }


__all__ = ["ConversationBridgeError", "append_conversation_turn"]
