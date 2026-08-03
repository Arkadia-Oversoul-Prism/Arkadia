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
# Canonical relationship types
# Every graph_edges row must use one of these relationship values.
# ─────────────────────────────────────────────────────────────────────────────

RELATIONSHIP_TYPES: list[str] = [
    # Semantic
    "references",     # A cites or points to B
    "derived_from",   # A is built on or sourced from B
    "contradicts",    # A directly opposes B
    "supported_by",   # A is validated by B
    "inspired_by",    # A was creatively motivated by B
    "mentions",       # A contains a reference to B without deep dependency

    # Structural
    "belongs_to",     # A is a member of collection B
    "part_of",        # A is a sub-element of B
    "child_of",       # A descends from B in a hierarchy
    "parent_of",      # A contains B as a child element
    "follows",        # A comes after B in sequence
    "precedes",       # A comes before B in sequence

    # Authorship / Provenance
    "authored_by",    # A was created by person B
    "generated_by",   # A was produced by a system B
    "reviewed_by",    # A was evaluated by B

    # General
    "relates_to",     # Catch-all semantic connection
    "extends",        # A builds upon B
    "summarizes",     # A is a condensed version of B
    "implements",     # A is a concrete realisation of B
]

# Fast O(1) lookup sets
NODE_TYPES_SET: frozenset[str] = frozenset(NODE_TYPES)
RELATIONSHIP_TYPES_SET: frozenset[str] = frozenset(RELATIONSHIP_TYPES)


def validate_node_type(note_type: str) -> bool:
    """Return True if note_type is canonical. Does not raise."""
    return note_type in NODE_TYPES_SET


def validate_relationship(relationship: str) -> bool:
    """Return True if relationship is canonical. Does not raise."""
    return relationship in RELATIONSHIP_TYPES_SET
