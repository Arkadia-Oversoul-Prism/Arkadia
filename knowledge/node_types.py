"""
Arkadia Knowledge OS — Canonical Type Vocabulary
=================================================
Single source of truth for all node types and relationship types.

LAW I: One capability. One implementation. One canonical home.

vault.py and graph.py import from here.
Do NOT define RELATIONSHIP_TYPES or NODE_TYPES anywhere else.

Constitutional spec: docs/KNOWLEDGE_GRAPH_SPEC.md
"""

# ─────────────────────────────────────────────────────────────────────────────
# Canonical node types
# Every object ingested into the Knowledge OS must have one of these types.
# ─────────────────────────────────────────────────────────────────────────────

NODE_TYPES: list[str] = [
    # Core semantic types
    "document",       # Imported or uploaded document
    "conversation",   # Oracle / ReasoMate exchange
    "person",         # Individual — author, participant, historical figure
    "project",        # A defined body of work
    "organization",   # Company, institution, community body
    "community",      # Social or knowledge community
    "concept",        # Abstract idea, principle, or doctrine
    "scroll",         # Curated Spiral Codex article
    "chapter",        # Encyclopedia Galactica chapter
    "place",          # Geographic or cosmological location
    "timeline_event", # Historical or projected event
    "media",          # Audio, video, image asset
    "task",           # Actionable item or open loop
    "note",           # General catch-all

    # Legacy types — preserved for backward compatibility; do not use in new code
    "research",       # → document
    "book",           # → document
    "idea",           # → concept
    "decision",       # → note
    "daily",          # → note
]

# Mapping: note_type → vault subdirectory
TYPE_TO_DIR: dict[str, str] = {
    "document":       "Documents",
    "conversation":   "Projects",
    "person":         "People",
    "project":        "Projects",
    "organization":   "Organizations",
    "community":      "Communities",
    "concept":        "Ideas",
    "scroll":         "Scrolls",
    "chapter":        "Encyclopedia",
    "place":          "Places",
    "timeline_event": "Timeline",
    "media":          "Media",
    "task":           "Projects",
    "note":           "Ideas",
    # Legacy mappings
    "research":       "Research",
    "book":           "Books",
    "idea":           "Ideas",
    "decision":       "Projects",
    "daily":          "Daily",
}

# ─────────────────────────────────────────────────────────────────────────────
# Canonical relationship types — imported from relationship_types.py
# LAW I: One capability. One implementation. One canonical home.
# The authoritative definition lives in knowledge/relationship_types.py.
# ─────────────────────────────────────────────────────────────────────────────

from knowledge.relationship_types import (  # noqa: E402
    RELATIONSHIP_TYPES,
    RELATIONSHIP_TYPES_SET,
    validate_relationship,
    RELATIONSHIP_REGISTRY,
)

# Fast O(1) lookup set for node types
NODE_TYPES_SET: frozenset[str] = frozenset(NODE_TYPES)


def validate_node_type(note_type: str) -> bool:
    """Return True if note_type is canonical. Does not raise."""
    return note_type in NODE_TYPES_SET
