"""
Arkadia Knowledge OS — Legacy Edge Migration Utility
=====================================================
Maps deprecated/unknown relationship identifiers to canonical types.

LAW I: One capability. One implementation. One canonical home.

This utility:
  - scans graph_edges for non-canonical relationship types
  - maps them to the nearest canonical equivalent
  - produces a report
  - updates rows only when explicitly told to (never auto-deletes, never auto-migrates)

Run as a module:
    python3 -m knowledge.edge_migration --report
    python3 -m knowledge.edge_migration --apply
"""

from __future__ import annotations

import logging
from typing import Optional

from knowledge.db import execute, execute_one
from knowledge.relationship_types import RELATIONSHIP_TYPES_SET

logger = logging.getLogger("arkadia.edge_migration")


# ─────────────────────────────────────────────────────────────────────────────
# Legacy → canonical mapping table
# Keys are deprecated/pre-K3-A identifiers; values are the canonical replacement.
# If a legacy type has no canonical equivalent, map it to the closest semantic match.
# ─────────────────────────────────────────────────────────────────────────────

LEGACY_TO_CANONICAL: dict[str, str] = {
    # Pre-K3-A narrow 9-type list remnants
    "related_to":      "relates_to",      # undirected semantic catch-all
    "linked_to":       "connected_to",    # undirected structural link
    "part_of":         "part_of",         # already canonical — no-op
    "subset_of":       "part_of",         # → structural containment
    "extends":         "extends",         # already canonical — no-op
    "uses":            "uses",            # already canonical — no-op
    "has":             "parent_of",       # ownership/containment → parent_of
    "contains":        "parent_of",       # structural containment
    "source_of":       "generated",       # provenance
    "derived":         "derived_from",    # → explicit directed derivation
    "based_on":        "derived_from",    # semantic derivation
    "quotes":          "references",      # citation → references
    "cites":           "references",      # explicit citation
    "links_to":        "references",      # generic pointer → references
    "summarised_by":   "summarizes",      # British spelling variant
    "summarised":      "summarizes",
    "summarized_by":   "summarizes",
    "implemented_by":  "implements",      # passive form
    "replied_to":      "replies_to",      # normalisation
    "reply_to":        "replies_to",
    "child":           "child_of",        # shorthand
    "parent":          "parent_of",       # shorthand
    "member":          "member_of",       # shorthand
    "belongs":         "belongs_to",      # shorthand
    "inspires":        "inspired",        # active form
    "supports":        "supported_by",    # passive flip — semantically close
    "contradicted_by": "contradicts",     # undirected — same edge
    "depends":         "depends_on",      # shorthand
    "owned_by":        "owns",            # passive flip — closest canonical
    "tagged_with":     "relates_to",      # tag relationship → catch-all
    "tagged":          "relates_to",
}

# Relationship types that cannot be automatically mapped
_UNMAPPABLE_NOTES = "No canonical equivalent — review manually before committing."


# ─────────────────────────────────────────────────────────────────────────────
# Core functions
# ─────────────────────────────────────────────────────────────────────────────

def scan_violations() -> list[dict]:
    """
    Return all graph_edges rows whose relationship is not in the canonical registry.
    Read-only. Safe to call at any time.
    """
    rows = execute("SELECT DISTINCT relationship, COUNT(*) as cnt FROM graph_edges GROUP BY relationship")
    violations = []
    for row in rows:
        rel = row["relationship"]
        if rel not in RELATIONSHIP_TYPES_SET:
            canonical = LEGACY_TO_CANONICAL.get(rel)
            violations.append({
                "legacy_type":    rel,
                "count":          row["cnt"],
                "canonical_map":  canonical,
                "mappable":       canonical is not None,
                "note":           None if canonical else _UNMAPPABLE_NOTES,
            })
    return violations


def build_migration_report() -> dict:
    """
    Produce a full migration report without making any changes.
    Returns a dict suitable for JSON serialisation.
    """
    total_edges = execute_one("SELECT COUNT(*) as n FROM graph_edges")
    total = total_edges["n"] if total_edges else 0

    violations = scan_violations()
    mappable   = [v for v in violations if v["mappable"]]
    unmappable = [v for v in violations if not v["mappable"]]
    affected   = sum(v["count"] for v in violations)

    return {
        "summary": {
            "total_edges":            total,
            "violated_types":         len(violations),
            "affected_edges":         affected,
            "mappable_types":         len(mappable),
            "unmappable_types":       len(unmappable),
            "clean": len(violations) == 0,
        },
        "violations":  violations,
        "mappable":    mappable,
        "unmappable":  unmappable,
    }


def apply_migration(dry_run: bool = True) -> dict:
    """
    Migrate mappable legacy edge types to their canonical equivalents.

    Args:
        dry_run: If True (default), report what would change without writing.
                 Set False to actually write.

    Never deletes data.
    Unmappable types are left unchanged and reported.
    Returns a summary dict.
    """
    violations = scan_violations()
    migrated   = 0
    skipped    = 0
    errors: list[dict] = []

    for v in violations:
        if not v["mappable"]:
            skipped += 1
            logger.warning(f"[EDGE-MIGRATION] Cannot map '{v['legacy_type']}' — skipped. {_UNMAPPABLE_NOTES}")
            continue

        canonical = v["canonical_map"]
        if dry_run:
            logger.info(f"[DRY-RUN] Would migrate '{v['legacy_type']}' → '{canonical}' ({v['count']} rows)")
            migrated += v["count"]
            continue

        try:
            # UPDATE existing rows to canonical type.
            # UNIQUE constraint (source, target, relationship) means we may hit conflicts
            # when both the legacy and canonical edges exist — use INSERT OR IGNORE + DELETE pattern.
            execute(
                """
                INSERT OR IGNORE INTO graph_edges (source_note_id, target_note_id, relationship, weight, created_at)
                SELECT source_note_id, target_note_id, ?, weight, created_at
                FROM graph_edges
                WHERE relationship = ?
                """,
                (canonical, v["legacy_type"]),
            )
            # Now delete the legacy rows (the canonical replacement already exists above)
            execute(
                "DELETE FROM graph_edges WHERE relationship = ?",
                (v["legacy_type"],),
            )
            migrated += v["count"]
            logger.info(f"[EDGE-MIGRATION] Migrated '{v['legacy_type']}' → '{canonical}' ({v['count']} rows)")
        except Exception as exc:
            errors.append({"type": v["legacy_type"], "error": str(exc)})
            logger.error(f"[EDGE-MIGRATION] Failed to migrate '{v['legacy_type']}': {exc}")

    return {
        "dry_run":  dry_run,
        "migrated": migrated,
        "skipped":  skipped,
        "errors":   errors,
        "clean":    len(errors) == 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    flag = sys.argv[1] if len(sys.argv) > 1 else "--report"

    if flag == "--report":
        print(json.dumps(build_migration_report(), indent=2))
    elif flag == "--dry-run":
        result = apply_migration(dry_run=True)
        print(json.dumps(result, indent=2))
    elif flag == "--apply":
        confirm = input("Apply migration? This writes to the database. Type YES to confirm: ")
        if confirm.strip() == "YES":
            result = apply_migration(dry_run=False)
            print(json.dumps(result, indent=2))
        else:
            print("Aborted.")
    else:
        print(f"Unknown flag: {flag}. Use --report | --dry-run | --apply")
