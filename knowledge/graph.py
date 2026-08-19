"""
Arkadia Knowledge OS — Knowledge Graph
=======================================
Every note becomes a graph node.
Relationships are typed, directional, and weighted.
Graph traversal is BFS with configurable depth.
"""

import json
from typing import Optional

from knowledge.db import execute, execute_one
from knowledge.relationship_types import RELATIONSHIP_TYPES, RELATIONSHIP_TYPES_SET

def accessible_note_ids(user_id: Optional[str] = None) -> set[int]:
    if user_id:
        rows = execute("SELECT id FROM notes WHERE user_id = ? OR user_id IS NULL", (user_id,))
    else:
        rows = execute("SELECT id FROM notes WHERE user_id IS NULL")
    return {r["id"] for r in rows}


def note_is_accessible(note_id: int, user_id: Optional[str] = None) -> bool:
    if user_id:
        row = execute_one(
            "SELECT id FROM notes WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
            (note_id, user_id),
        )
    else:
        row = execute_one("SELECT id FROM notes WHERE id = ? AND user_id IS NULL", (note_id,))
    return row is not None



# ─────────────────────────────────────────────────────────────────────────────
# Edge operations
# ─────────────────────────────────────────────────────────────────────────────

def add_edge(source_id: int, target_id: int, relationship: str, weight: float = 1.0) -> None:
    if relationship not in RELATIONSHIP_TYPES:
        raise ValueError(f"Unknown relationship: {relationship}. Valid: {RELATIONSHIP_TYPES}")
    execute(
        """
        INSERT OR REPLACE INTO graph_edges
            (source_note_id, target_note_id, relationship, weight)
        VALUES (?, ?, ?, ?)
        """,
        (source_id, target_id, relationship, weight),
    )


def remove_edge(source_id: int, target_id: int, relationship: str) -> None:
    execute(
        "DELETE FROM graph_edges WHERE source_note_id=? AND target_note_id=? AND relationship=?",
        (source_id, target_id, relationship),
    )


def get_edges(note_id: int, direction: str = "both") -> list[dict]:
    """Return all edges for a note. direction: outbound | inbound | both"""
    if direction == "outbound":
        return execute("SELECT * FROM graph_edges WHERE source_note_id = ?", (note_id,))
    elif direction == "inbound":
        return execute("SELECT * FROM graph_edges WHERE target_note_id = ?", (note_id,))
    else:
        return execute(
            "SELECT * FROM graph_edges WHERE source_note_id = ? OR target_note_id = ?",
            (note_id, note_id),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Graph traversal
# ─────────────────────────────────────────────────────────────────────────────

def traverse(
    start_id: int,
    max_depth: int = 2,
    relationship_filter: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """BFS over the accessible subgraph only. Edges require both endpoints accessible."""
    allowed = accessible_note_ids(user_id)
    if start_id not in allowed:
        return {"nodes": [], "edges": []}

    visited: set[int] = {start_id}
    frontier: list[int] = [start_id]
    all_edges: list[dict] = []

    for _ in range(max_depth):
        if not frontier:
            break
        placeholders = ",".join("?" * len(frontier))
        conditions = f"(source_note_id IN ({placeholders}) OR target_note_id IN ({placeholders}))"
        params = tuple(frontier + frontier)
        if relationship_filter:
            conditions += " AND relationship = ?"
            params = params + (relationship_filter,)
        edges = execute(f"SELECT * FROM graph_edges WHERE {conditions}", params)
        next_frontier: list[int] = []
        for edge in edges:
            src, tgt = edge["source_note_id"], edge["target_note_id"]
            if src not in allowed or tgt not in allowed:
                continue
            all_edges.append(edge)
            for nid in (src, tgt):
                if nid not in visited and nid in allowed:
                    visited.add(nid)
                    next_frontier.append(nid)
        frontier = next_frontier

    all_nodes: list[dict] = []
    if visited:
        phs = ",".join("?" * len(visited))
        all_nodes = execute(
            f"SELECT id, uuid, title, note_type, created_at, user_id FROM notes WHERE id IN ({phs})",
            tuple(visited),
        )
    return {"nodes": all_nodes, "edges": all_edges}


def find_path(
    start_id: int,
    end_id: int,
    max_depth: int = 4,
    user_id: Optional[str] = None,
) -> list[int]:
    """Shortest path over accessible subgraph only."""
    from collections import deque
    allowed = accessible_note_ids(user_id)
    if start_id not in allowed or end_id not in allowed:
        return []
    queue: deque[list[int]] = deque([[start_id]])
    visited: set[int] = {start_id}
    while queue:
        path = queue.popleft()
        if len(path) > max_depth + 1:
            break
        current = path[-1]
        edges = execute(
            "SELECT target_note_id AS neighbor FROM graph_edges WHERE source_note_id = ? "
            "UNION "
            "SELECT source_note_id AS neighbor FROM graph_edges WHERE target_note_id = ?",
            (current, current),
        )
        for row in edges:
            neighbor = row["neighbor"]
            if neighbor not in allowed:
                continue
            if neighbor == end_id:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return []


def full_graph_export(user_id: Optional[str] = None) -> dict:
    """Export accessible graph only."""
    allowed = accessible_note_ids(user_id)
    if not allowed:
        return {"nodes": [], "edges": []}
    phs = ",".join("?" * len(allowed))
    nodes = execute(
        f"SELECT id, uuid, title, note_type, project_id, created_at, user_id FROM notes WHERE id IN ({phs})",
        tuple(allowed),
    )
    edges = execute(
        f"SELECT source_note_id, target_note_id, relationship, weight FROM graph_edges "
        f"WHERE source_note_id IN ({phs}) AND target_note_id IN ({phs})",
        tuple(list(allowed) + list(allowed)),
    )
    return {"nodes": nodes, "edges": edges}


# ─────────────────────────────────────────────────────────────────────────────
# Auto-linking heuristics
# ─────────────────────────────────────────────────────────────────────────────

def auto_detect_links(note_id: int, candidate_ids: list[int]) -> list[dict]:
    """
    Given a note and candidate notes, return pairs that should be linked,
    based on shared tags and title overlap.
    """
    note = execute_one("SELECT * FROM notes WHERE id = ?", (note_id,))
    if not note:
        return []

    note_tags = set(json.loads(note["tags"] or "[]"))
    suggestions: list[dict] = []

    for cid in candidate_ids:
        if cid == note_id:
            continue
        candidate = execute_one("SELECT * FROM notes WHERE id = ?", (cid,))
        if not candidate:
            continue
        c_tags = set(json.loads(candidate["tags"] or "[]"))
        shared = note_tags & c_tags
        if shared:
            suggestions.append({
                "source_id": note_id,
                "target_id": cid,
                "relationship": "references",
                "confidence": len(shared) / max(len(note_tags | c_tags), 1),
                "reason": f"Shared tags: {', '.join(shared)}",
            })

    return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)
