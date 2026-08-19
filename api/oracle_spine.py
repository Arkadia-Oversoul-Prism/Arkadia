"""
Arkadia Prism — Conversational Spine
=====================================
The canonical Oracle/Arkana runtime helpers shared by every conversational
surface (Oracle Chat, ReasoMate, NovaNet). This module exists so that:

  1. Contextual retrieval flows through the Knowledge OS context engine
     (knowledge.context_engine.assemble_context) rather than only the
     corpus keyword path.
  2. Conversation archival links each turn to a thread keyed on a stable,
     interface-independent session_id, so memory is human-owned and
     longitudinal rather than per-surface.
  3. api/main.py stays within its line budget — the spine logic lives here.

ONE INTELLIGENCE SPINE. MANY INTERFACES.
LAW IV: Oracle retrieves knowledge. Providers generate language.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("arkadia.oracle_spine")

ORACLE_PROVIDER = "gemini"
ARKANA_PERSONA = "arkana"


def resolve_thread_id(session_id: str, user_id: str = "") -> Optional[int]:
    """Map an external session_id onto a Knowledge OS thread id (read-only).

    Returns None for empty/anonymous sessions. Does NOT create a thread on
    retrieval — threads are created at archival time so a retrieval-only
    request never mutates state.

    When ``user_id`` is provided, only resolves threads owned by that user
    (or legacy NULL-owner threads), enforcing the private boundary.
    """
    try:
        from knowledge.vault import get_thread_id
        return get_thread_id(session_id, user_id=user_id or None)
    except Exception as e:
        logger.debug(f"[SPINE] thread resolve skipped: {e}")
        return None


def retrieve_arkana_context(message: str, session_id: str = "",
                            token_budget: int = 2000,
                            user_id: str = "") -> tuple[str, dict]:
    """Retrieve relevant Knowledge OS context for an incoming Oracle turn."""
    meta: dict = {
        "session_id": session_id or None,
        "thread_id": None,
        "user_id": user_id or None,
        "notes_retrieved": 0,
        "source": "knowledge_os",
    }
    try:
        from knowledge.context_engine import assemble_context, format_context_for_provider
        thread_id = resolve_thread_id(session_id, user_id=user_id)
        meta["thread_id"] = thread_id
        package = assemble_context(
            message,
            thread_id=thread_id,
            token_budget=token_budget,
            user_id=user_id or None,
        )
        block = format_context_for_provider(package)
        meta["notes_retrieved"] = len(package.get("relevant_notes", []))
        return block, meta
    except Exception as e:
        logger.warning(f"[SPINE] context retrieval failed: {e}")
        meta["source"] = "knowledge_os_error"
        return "", meta


_MEMORY_HEADER = (
    "\n\n== RETRIEVED CONTEXTUAL MEMORY — KNOWLEDGE OS ==\n"
    "The following is relevant context retrieved from prior conversations and "
    "knowledge you have archived with this node. It is retrieved historical "
    "context, NOT the current conversation. Use it to preserve continuity — "
    "do not claim to 'remember' it as lived experience, and do not fabricate "
    "beyond what is shown:\n\n"
)
_MEMORY_FOOTER = "\n== END RETRIEVED MEMORY =="


def build_memory_block(message: str, session_id: str = "",
                       token_budget: int = 2000,
                       user_id: str = "") -> tuple[str, dict]:
    """Return the provider-injectable retrieved-memory block + diagnostics."""
    text, meta = retrieve_arkana_context(
        message, session_id, token_budget, user_id=user_id,
    )
    if not text or not text.strip():
        return "", meta
    return _MEMORY_HEADER + text + _MEMORY_FOOTER, meta


def archive_oracle_turn(user_input: str, response: str,
                        session_id: str = "",
                        user_id: str = "") -> None:
    """Fire-and-forget: archive an Oracle/Arkana turn into the Knowledge OS."""
    if not user_input and not response:
        return
    try:
        from knowledge.vault import get_or_create_thread
        from knowledge.pipeline import ingest_conversation
        uid = (user_id or "").strip() or None
        thread_id = (
            get_or_create_thread(session_id, user_id=uid) if session_id else None
        )
        ingest_conversation(
            prompt=user_input,
            response=response,
            provider=ORACLE_PROVIDER,
            persona=ARKANA_PERSONA,
            thread_id=thread_id,
            user_id=uid,
        )
    except Exception as e:
        logger.warning(f"[SPINE] oracle turn archival failed: {e}")


__all__ = [
    "resolve_thread_id",
    "retrieve_arkana_context",
    "archive_oracle_turn",
    "ORACLE_PROVIDER",
    "ARKANA_PERSONA",
]
