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

# Provider/persona provenance stamped on archived Oracle turns.
ORACLE_PROVIDER = "gemini"
ARKANA_PERSONA = "arkana"


def resolve_thread_id(session_id: str) -> Optional[int]:
    """Map an external session_id onto a Knowledge OS thread id (read-only).

    Returns None for empty/anonymous sessions. Does NOT create a thread on
    retrieval — threads are created at archival time so a retrieval-only
    request never mutates state.
    """
    try:
        from knowledge.vault import get_thread_id
        return get_thread_id(session_id)
    except Exception as e:
        logger.debug(f"[SPINE] thread resolve skipped: {e}")
        return None


def retrieve_arkana_context(message: str, session_id: str = "",
                            token_budget: int = 2000) -> tuple[str, dict]:
    """Retrieve relevant Knowledge OS context for an incoming Oracle turn.

    Returns (context_block_text, meta). The context block is a compact,
    provider-injectable string built by format_context_for_provider. meta
    carries retrieval diagnostics (note count, thread_id, source) so the
    runtime can report transparency without exposing raw vault rows.

    When retrieval returns nothing, an empty block is returned — the runtime
    must NOT fabricate historical context.
    """
    meta: dict = {
        "session_id": session_id or None,
        "thread_id": None,
        "notes_retrieved": 0,
        "source": "knowledge_os",
    }
    try:
        from knowledge.context_engine import assemble_context, format_context_for_provider
        thread_id = resolve_thread_id(session_id)
        meta["thread_id"] = thread_id
        package = assemble_context(
            message,
            thread_id=thread_id,
            token_budget=token_budget,
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
                       token_budget: int = 2000) -> tuple[str, dict]:
    """Return the provider-injectable retrieved-memory block + diagnostics.

    Wraps retrieve_arkana_context with the canonical header/footer so the
    Oracle runtime injects a single string. Returns ("", meta) when nothing
    was retrieved — callers must not fabricate memory from an empty block.
    """
    text, meta = retrieve_arkana_context(message, session_id, token_budget)
    if not text or not text.strip():
        return "", meta
    return _MEMORY_HEADER + text + _MEMORY_FOOTER, meta


def archive_oracle_turn(user_input: str, response: str,
                        session_id: str = "") -> None:
    """Fire-and-forget: archive an Oracle/Arkana turn into the Knowledge OS.

    Uses the purpose-built ingest_conversation() so the turn is recorded with:
      - note_type=conversation
      - thread linkage (so future assemble_context(thread_id=...) finds it)
      - provider/persona provenance on the timeline
    Never blocks the Oracle response — all failures are swallowed+logged.
    """
    if not user_input and not response:
        return
    try:
        from knowledge.vault import get_or_create_thread
        from knowledge.pipeline import ingest_conversation
        thread_id = get_or_create_thread(session_id) if session_id else None
        ingest_conversation(
            prompt=user_input,
            response=response,
            provider=ORACLE_PROVIDER,
            persona=ARKANA_PERSONA,
            thread_id=thread_id,
        )
    except Exception as e:
        # Never block the Oracle response on archival failure.
        logger.warning(f"[SPINE] oracle turn archival failed: {e}")


__all__ = [
    "resolve_thread_id",
    "retrieve_arkana_context",
    "archive_oracle_turn",
    "ORACLE_PROVIDER",
    "ARKANA_PERSONA",
]
