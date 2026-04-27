"""SolSpire — Tool Registry.

Single source of truth for what tools exist, their type (deterministic /
llm / memory / command), the input shape they accept, and the output
shape they produce. The routing engine and the executor both read from
here so adding a tool is a one-line change.
"""
from __future__ import annotations

from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "name":   "arkadia_generate",
        "type":   "deterministic",
        "input":  {"theme": "str?"},
        "output": "text",
        "purpose": "Symbolic 4-line verse from the Arkadia engine. "
                   "Use when output structure matters.",
    },
    {
        "name":   "arkadia_compress",
        "type":   "deterministic",
        "input":  {"text": "str"},
        "output": "text",
        "purpose": "Lossless symbolic-token compression via the Arkadia lexicon.",
    },
    {
        "name":   "arkadia_expand",
        "type":   "deterministic",
        "input":  {"text": "str"},
        "output": "text",
        "purpose": "Reverse of arkadia_compress.",
    },
    {
        "name":   "gemini_chat",
        "type":   "llm",
        "input":  {"prompt": "str", "context": "str?"},
        "output": "text",
        "purpose": "Open-ended reasoning, advice, adaptation. "
                   "Use when structure is not the goal.",
    },
    {
        "name":   "oracle_query",
        "type":   "memory",
        "input":  {"keys": "list[str]?"},
        "output": "context",
        "purpose": "Read from the Oracle in-memory state.",
    },
    {
        "name":   "oracle_update",
        "type":   "memory",
        "input":  {"<key>": "any"},
        "output": "ack",
        "purpose": "Write/accumulate values into the Oracle state.",
    },
    {
        "name":   "image_generate",
        "type":   "command",
        "input":  {"count": "int"},
        "output": "list[image_descriptor]",
        "purpose": "Produce N image descriptors (stubbed in Phase 2).",
    },
]

_TOOLS_BY_NAME: dict[str, dict[str, Any]] = {t["name"]: t for t in TOOLS}


def get_tool(name: str) -> dict[str, Any] | None:
    return _TOOLS_BY_NAME.get(name)


def list_tools() -> list[dict[str, Any]]:
    return list(TOOLS)


# ── Mapping from internal task type → registered tool name ──────────────────
TASK_TO_TOOL = {
    "text_generate":  "arkadia_generate",
    "compress":       "arkadia_compress",
    "image_generate": "image_generate",
    "oracle_update":  "oracle_update",
    "query":          "oracle_query",
    "llm_fallback":   "gemini_chat",
}


__all__ = ["TOOLS", "TASK_TO_TOOL", "get_tool", "list_tools"]
