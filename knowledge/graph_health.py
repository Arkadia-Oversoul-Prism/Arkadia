"""
Arkadia Knowledge OS — Graph Health Service
============================================
Evaluates the structural integrity of the Knowledge Graph.

LAW I: One capability. One implementation. One canonical home.

This module is the single source of truth for graph health evaluation.
It will eventually power SolSpire diagnostics and any monitoring pipeline.
It does NOT modify any data — it is strictly read-only.
"""

from __future__ import annotations

from knowledge.db import execute, execute_one


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _count(sql: str, params: tuple = ()) -> int:
    row = execute_one(sql, params)
    if row is None:
        return 0
    # execute_one returns a sqlite3.Row; first value is the count
    return list(row)[0]


# ─────────────────────────────────────────────────────────────────────────────
# Individual checks
# ─────────────────────────────────────────────────────────────────────────────

def _check_orphan_nodes() -> dict:
    """Nodes with no edges (no outbound AND no inbound)."""
    total_nodes = _count("SELECT COUNT(*) FROM notes")
    orphan_count = _count(
        """
        SELECT COUNT(*) FROM notes n
        WHERE n.id NOT IN (SELECT source_note_id FROM graph_edges)
          AND n.id NOT IN (SELECT target_note_id FROM graph_edges)
        """
    )
    return {
        "total_nodes": total_nodes,
        "orphan_nodes": orphan_count,
        "orphan_ratio": round(orphan_count / total_nodes, 4) if total_nodes else 0.0,
        "status": "warn" if orphan_count > total_nodes * 0.5 else "ok",
    }


def _check_duplicate_nodes() -> dict:
    """Notes with identical checksums (content duplicates)."""
    dup_count = _count(
        """
        SELECT COUNT(*) FROM (
            SELECT checksum FROM notes
            WHERE checksum IS NOT NULL
            GROUP BY checksum HAVING COUNT(*) > 1
        )
        """
    )
    return {
        "duplicate_groups": dup_count,
        "status": "warn" if dup_count > 0 else "ok",
    }


def _check_invalid_references() -> dict:
    """Edges referencing notes that no longer exist."""
    dangling = _count(
        """
        SELECT COUNT(*) FROM graph_edges e
        WHERE e.source_note_id NOT IN (SELECT id FROM notes)
           OR e.target_note_id  NOT IN (SELECT id FROM notes)
        """
    )
    return {
        "dangling_edges": dangling,
        "status": "error" if dangling > 0 else "ok",
    }


def _check_ontology_violations() -> dict:
    """
    Edges whose relationship type is NOT in the canonical registry.
    These were written before the ontology was frozen, or via a bug.
    """
    from knowledge.relationship_types import RELATIONSHIP_TYPES_SET
    all_rel_rows = execute("SELECT DISTINCT relationship FROM graph_edges")
    violations: list[str] = [
        row["relationship"]
        for row in all_rel_rows
        if row["relationship"] not in RELATIONSHIP_TYPES_SET
    ]
    return {
        "unknown_relationship_types": violations,
        "violation_count": len(violations),
        "status": "error" if violations else "ok",
    }


def _check_embedding_completeness() -> dict:
    """Notes whose embedding pipeline has not completed."""
    total = _count("SELECT COUNT(*) FROM notes")
    pending = _count("SELECT COUNT(*) FROM notes WHERE embedding_status = 'pending'")
    partial = _count("SELECT COUNT(*) FROM notes WHERE embedding_status = 'partial'")
    complete = _count("SELECT COUNT(*) FROM notes WHERE embedding_status = 'complete'")
    failed  = _count("SELECT COUNT(*) FROM notes WHERE embedding_status = 'failed'")
    return {
        "total": total,
        "complete": complete,
        "pending": pending,
        "partial": partial,
        "failed": failed,
        "completion_ratio": round(complete / total, 4) if total else 0.0,
        "status": "ok" if pending == 0 and failed == 0 else (
            "warn" if failed == 0 else "error"
        ),
    }


def _check_graph_connectivity() -> dict:
    """
    Counts distinct connected components via a simple union-find on edges.
    Returns component count — a fully connected graph has 1.
    """
    all_edges = execute(
        "SELECT source_note_id, target_note_id FROM graph_edges"
    )
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent.get(x, x), x)
            x = parent.get(x, x)
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for edge in all_edges:
        s, t = edge["source_note_id"], edge["target_note_id"]
        if s not in parent:
            parent[s] = s
        if t not in parent:
            parent[t] = t
        union(s, t)

    if not parent:
        return {"components": 0, "status": "ok"}

    roots = {find(n) for n in parent}
    return {
        "components": len(roots),
        "status": "ok" if len(roots) <= 5 else "warn",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_graph_health() -> dict:
    """
    Run all health checks and return a structured health summary.

    Returns:
        {
            "overall": "ok" | "warn" | "error",
            "checks": {
                "orphan_nodes": {...},
                "duplicate_nodes": {...},
                "invalid_references": {...},
                "ontology_violations": {...},
                "embedding_completeness": {...},
                "graph_connectivity": {...},
            }
        }
    """
    try:
        checks = {
            "orphan_nodes":           _check_orphan_nodes(),
            "duplicate_nodes":        _check_duplicate_nodes(),
            "invalid_references":     _check_invalid_references(),
            "ontology_violations":    _check_ontology_violations(),
            "embedding_completeness": _check_embedding_completeness(),
            "graph_connectivity":     _check_graph_connectivity(),
        }
    except Exception as exc:
        return {
            "overall": "error",
            "error": str(exc),
            "checks": {},
        }

    statuses = [c.get("status", "ok") for c in checks.values()]
    if "error" in statuses:
        overall = "error"
    elif "warn" in statuses:
        overall = "warn"
    else:
        overall = "ok"

    return {"overall": overall, "checks": checks}
