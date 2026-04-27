"""SolSpire Phase 3 — lightweight sub-agent simulation.

Spec (section 7): no real agents yet. Just role-prompted calls into
Gemini. Adds personality + framing without adding infrastructure.
"""
from __future__ import annotations

from typing import Any

from solspire import llm as llm_mod

ROLES: dict[str, str] = {
    "content_agent": (
        "You are a Content Agent. Produce concise, structured copy. "
        "Default to bullet points unless asked otherwise. Never invent facts."
    ),
    "finance_logger": (
        "You are a Finance Logger. Read transactional language and emit a "
        "clean JSON summary: {amount, currency, party, note}. "
        "If a field is missing, set it to null."
    ),
    "image_generator": (
        "You are an Image Generator brief writer. Convert a request into a "
        "list of short, vivid prompts (one per line)."
    ),
    "data_organizer": (
        "You are a Data Organizer. Take messy input and emit a tidy JSON "
        "object grouping the items by type."
    ),
    "default": (
        "You are a helpful assistant. Be precise and brief."
    ),
}


def list_roles() -> list[str]:
    return list(ROLES.keys())


def run_subagent(role: str, user_input: str) -> dict[str, Any]:
    """Single-shot Gemini call with a role-defined system prompt.

    Returns the same envelope as solspire.llm.call_llm so the engine
    can treat all LLM responses uniformly.
    """
    role_key = role if role in ROLES else "default"
    system = ROLES[role_key]
    composite_prompt = f"{system}\n\nUser input:\n{user_input}"
    result = llm_mod.call_llm({"parameters": {"prompt": composite_prompt}})
    result["role"] = role_key
    return result


__all__ = ["ROLES", "list_roles", "run_subagent"]
