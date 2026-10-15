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

from typing import Optional

from knowledge.db import execute, execute_one


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _count(sql: str, params: tuple = ()) -> int:
    row = execute_one(sql, params)
    if row is None:
        return 0
    # knowledge.db returns each row as a dict keyed by column name, so take the
    # first *value*. Iterating the row would yield the column name, not the count.
    return next(iter(row.values()))


# ─────────────────────────────────────────────────────────────────────────────
# Ownership scoping
#
# Knowledge OS visibility is owner-or-public: an authenticated caller sees their
# own rows plus the NULL-owner public corpus, an anonymous caller sees the public
# corpus only. Every check below is evaluated over that accessible subgraph, so
# the health surface can never describe — or leak a title from — another owner's
# private material. Mirrors knowledge.search._notes_owner_sql and
# knowledge.graph.accessible_note_ids.
# ─────────────────────────────────────────────────────────────────────────────

def _note_owner_clause(user_id: Optional[str], alias: str = "") -> tuple[str, tuple]:
    col = f"{alias}.user_id" if alias else "user_id"
    if user_id:
        return f"({col} = ? OR {col} IS NULL)", (user_id,)
    return f"{col} IS NULL", ()


def _accessible_edge_sql(
    user_id: Optional[str],
    select: str = "e.source_note_id, e.target_note_id",
) -> tuple[str, tuple]:
    """Edges whose BOTH endpoints are accessible, as a subquery-selectable body."""
    source_clause, source_params = _note_owner_clause(user_id, "s")
    target_clause, target_params = _note_owner_clause(user_id, "t")
    sql = (
        f"SELECT {select} FROM graph_edges e "
        "JOIN notes s ON s.id = e.source_note_id "
        "JOIN notes t ON t.id = e.target_note_id "
        f"WHERE {source_clause} AND {target_clause}"
    )
    return sql, (*source_params, *target_params)


# ─────────────────────────────────────────────────────────────────────────────
# Individual checks
# ─────────────────────────────────────────────────────────────────────────────

def _check_orphan_nodes(user_id: Optional[str] = None) -> dict:
    """Nodes with no accessible edges (no outbound AND no inbound)."""
    note_clause, note_params = _note_owner_clause(user_id, "n")
    edge_sql, edge_params = _accessible_edge_sql(user_id)
    total_nodes = _count(
        f"SELECT COUNT(*) FROM notes n WHERE {note_clause}", note_params
    )
    orphan_count = _count(
        f"""
        SELECT COUNT(*) FROM notes n
        WHERE {note_clause}
          AND n.id NOT IN (SELECT source_note_id FROM ({edge_sql}))
          AND n.id NOT IN (SELECT target_note_id FROM ({edge_sql}))
        """,
        (*note_params, *edge_params, *edge_params),
    )
    return {
        "total_nodes": total_nodes,
        "orphan_nodes": orphan_count,
        "orphan_ratio": round(orphan_count / total_nodes, 4) if total_nodes else 0.0,
        "status": "warn" if orphan_count > total_nodes * 0.5 else "ok",
    }


def _check_duplicate_nodes(user_id: Optional[str] = None) -> dict:
    """Notes with identical checksums (content duplicates)."""
    clause, params = _note_owner_clause(user_id)
    dup_count = _count(
        f"""
        SELECT COUNT(*) FROM (
            SELECT checksum FROM notes
            WHERE checksum IS NOT NULL AND {clause}
            GROUP BY checksum HAVING COUNT(*) > 1
        )
        """,
        params,
    )
    return {
        "duplicate_groups": dup_count,
        "status": "warn" if dup_count > 0 else "ok",
    }


def _check_invalid_references() -> dict:
    """Edges referencing notes that no longer exist.

    Deliberately evaluated over the *whole* store, not the accessible subgraph:
    a dangling edge is referential corruption, and scoping the probe would hide
    corruption behind the caller's visibility. It reports a count only — no
    title, owner, or per-owner breakdown — so it discloses no private material.
    """
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


def _check_ontology_violations(user_id: Optional[str] = None) -> dict:
    """
    Accessible edges whose relationship type is NOT in the canonical registry.
    These were written before the ontology was frozen, or via a bug.
    """
    from knowledge.relationship_types import RELATIONSHIP_TYPES_SET
    edge_sql, edge_params = _accessible_edge_sql(user_id, select="e.relationship")
    all_rel_rows = execute(
        f"SELECT DISTINCT relationship FROM ({edge_sql})", edge_params
    )
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


def _check_embedding_completeness(user_id: Optional[str] = None) -> dict:
    """Notes whose embedding pipeline has not completed."""
    clause, params = _note_owner_clause(user_id)
    total = _count(f"SELECT COUNT(*) FROM notes WHERE {clause}", params)
    pending = _count(f"SELECT COUNT(*) FROM notes WHERE embedding_status = 'pending' AND {clause}", params)
    partial = _count(f"SELECT COUNT(*) FROM notes WHERE embedding_status = 'partial' AND {clause}", params)
    complete = _count(f"SELECT COUNT(*) FROM notes WHERE embedding_status = 'complete' AND {clause}", params)
    failed  = _count(f"SELECT COUNT(*) FROM notes WHERE embedding_status = 'failed' AND {clause}", params)
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


def _check_graph_connectivity(user_id: Optional[str] = None) -> dict:
    """
    Counts distinct connected components via a simple union-find on edges.
    Returns component count — a fully connected graph has 1.

    Only edges with both endpoints accessible to ``user_id`` participate, so a
    private node cannot be joined to the caller's view through a shared edge.
    """
    edge_sql, edge_params = _accessible_edge_sql(user_id)
    all_edges = execute(edge_sql, edge_params)
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

def evaluate_graph_health(user_id: Optional[str] = None) -> dict:
    """
    Run all health checks and return a structured health summary.

    ``user_id`` scopes every check to the caller's accessible subgraph (own rows
    plus the NULL-owner public corpus); anonymous callers see the public corpus
    only. No check exposes another owner's material.

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
            "orphan_nodes":           _check_orphan_nodes(user_id),
            "duplicate_nodes":        _check_duplicate_nodes(user_id),
            "invalid_references":     _check_invalid_references(),
            "ontology_violations":    _check_ontology_violations(user_id),
            "embedding_completeness": _check_embedding_completeness(user_id),
            "graph_connectivity":     _check_graph_connectivity(user_id),
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
