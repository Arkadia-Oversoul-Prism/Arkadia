"""
Arkadia Knowledge OS — Search Engine
=====================================
Multi-mode search: fulltext, semantic, tag, timeline, graph, project, people, reference.
All 8 modes are available and reachable via unified_search().
LAW IV: Oracle retrieves knowledge. Providers generate language.
"""

import json
import re
from typing import Optional

from knowledge.db import execute
from knowledge.embeddings import (
    embed_text, cosine_similarity, bm25_score, _tokenise, all_chunk_embeddings
)


# ─────────────────────────────────────────────────────────────────────────────
# Full-text search (SQLite LIKE across title + content)
# ─────────────────────────────────────────────────────────────────────────────

def fulltext_search(query: str, note_type: Optional[str] = None, limit: int = 20) -> list[dict]:
    terms = [t.strip() for t in query.split() if len(t.strip()) >= 2]
    if not terms:
        return []

    conditions = ["(title LIKE ? OR content LIKE ?)"] * len(terms)
    params: list = []
    for term in terms:
        params += [f"%{term}%", f"%{term}%"]

    if note_type:
        conditions.append("note_type = ?")
        params.append(note_type)

    where = " AND ".join(conditions)
    params.append(limit)

    return execute(
        f"SELECT id, uuid, title, note_type, created_at, vault_path, tags "
        f"FROM notes WHERE {where} ORDER BY updated_at DESC LIMIT ?",
        tuple(params),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Semantic search (embedding cosine similarity with BM25 fallback)
# ─────────────────────────────────────────────────────────────────────────────

def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    1. Embed the query via Gemini.
    2. Score all stored chunk embeddings by cosine similarity.
    3. If embedding unavailable, fall back to BM25.
    Returns ranked list of {note_id, chunk_id, score, content, title}.
    """
    query_vec = embed_text(query, task_type="RETRIEVAL_QUERY")
    chunks = all_chunk_embeddings()

    if not chunks:
        return []

    scored: list[dict] = []

    if query_vec:
        for chunk in chunks:
            try:
                chunk_vec = json.loads(chunk["vector"])
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append({
                    "score": score,
                    "chunk_id": chunk["chunk_id"],
                    "note_id": chunk["note_id"],
                    "content": chunk["content"],
                })
            except (TypeError, json.JSONDecodeError, ValueError):
                continue
    else:
        q_tokens = _tokenise(query)
        for chunk in chunks:
            doc_tokens = _tokenise(chunk["content"])
            score = bm25_score(q_tokens, doc_tokens)
            if score > 0:
                scored.append({
                    "score": score,
                    "chunk_id": chunk["chunk_id"],
                    "note_id": chunk["note_id"],
                    "content": chunk["content"],
                })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]

    if top:
        note_ids = list({r["note_id"] for r in top})
        phs = ",".join("?" * len(note_ids))
        notes_map = {
            n["id"]: n
            for n in execute(
                f"SELECT id, uuid, title, note_type, vault_path FROM notes WHERE id IN ({phs})",
                tuple(note_ids),
            )
        }
        for r in top:
            note = notes_map.get(r["note_id"], {})
            r.update({
                "note_uuid": note.get("uuid"),
                "title": note.get("title"),
                "note_type": note.get("note_type"),
            })

    return top


# ─────────────────────────────────────────────────────────────────────────────
# Tag search
# ─────────────────────────────────────────────────────────────────────────────

def tag_search(tags: list[str], limit: int = 20) -> list[dict]:
    if not tags:
        return []
    results: list[dict] = []
    for tag in tags:
        rows = execute(
            """
            SELECT n.id, n.uuid, n.title, n.note_type, n.created_at, n.vault_path
            FROM notes n
            JOIN note_tags nt ON nt.note_id = n.id
            JOIN tags t ON t.id = nt.tag_id
            WHERE t.name = ?
            ORDER BY n.updated_at DESC
            LIMIT ?
            """,
            (tag.lower(), limit),
        )
        results.extend(rows)
    seen: set[int] = set()
    deduped: list[dict] = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)
    return deduped


# ─────────────────────────────────────────────────────────────────────────────
# Timeline search
# ─────────────────────────────────────────────────────────────────────────────

def timeline_search(
    event_type: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    keyword: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = 50,
) -> list[dict]:
    conditions: list[str] = []
    params: list = []

    if event_type:
        conditions.append("event_type = ?"); params.append(event_type)
    if since:
        conditions.append("created_at >= ?"); params.append(since)
    if until:
        conditions.append("created_at <= ?"); params.append(until)
    if keyword:
        conditions.append("payload LIKE ?"); params.append(f"%{keyword}%")
    if project_id is not None:
        conditions.append("project_id = ?"); params.append(project_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    rows = execute(
        f"SELECT * FROM timeline {where} ORDER BY id DESC LIMIT ?", tuple(params)
    )
    for r in rows:
        try:
            r["payload"] = json.loads(r["payload"])
        except (TypeError, json.JSONDecodeError):
            pass
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Graph search (notes connected to a given note)
# ─────────────────────────────────────────────────────────────────────────────

def graph_search(note_id: int, relationship: Optional[str] = None, depth: int = 2) -> list[dict]:
    from knowledge.graph import traverse
    result = traverse(note_id, max_depth=depth, relationship_filter=relationship)
    return result["nodes"]


# ─────────────────────────────────────────────────────────────────────────────
# Project search
# ─────────────────────────────────────────────────────────────────────────────

def project_search(query: str, limit: int = 20) -> list[dict]:
    return execute(
        "SELECT * FROM projects WHERE name LIKE ? OR description LIKE ? ORDER BY updated_at DESC LIMIT ?",
        (f"%{query}%", f"%{query}%", limit),
    )


# ─────────────────────────────────────────────────────────────────────────────
# People search
# ─────────────────────────────────────────────────────────────────────────────

def people_search(query: str, limit: int = 20) -> list[dict]:
    return execute(
        "SELECT id, uuid, title, created_at FROM notes "
        "WHERE note_type = 'person' AND (title LIKE ? OR content LIKE ?) LIMIT ?",
        (f"%{query}%", f"%{query}%", limit),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Reference search
# ─────────────────────────────────────────────────────────────────────────────

def reference_search(query: str, limit: int = 20) -> list[dict]:
    return execute(
        "SELECT * FROM \"references\" WHERE target_ref LIKE ? OR label LIKE ? ORDER BY created_at DESC LIMIT ?",
        (f"%{query}%", f"%{query}%", limit),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unified search — all 8 modes, single call
# ─────────────────────────────────────────────────────────────────────────────

ALL_MODES = ["semantic", "fulltext", "tag", "timeline", "graph", "project", "people", "reference"]


def unified_search(
    query: str,
    modes: Optional[list[str]] = None,
    top_k: int = 20,
    note_id_for_graph: Optional[int] = None,
    project_id: Optional[int] = None,
) -> dict:
    """
    Run multiple search modes and return a consolidated result set.
    
    modes: subset of ["semantic","fulltext","tag","timeline","graph","project","people","reference"]
    Default: all modes except "graph" (graph requires a note_id anchor).
    """
    if modes is None:
        modes = ["semantic", "fulltext", "tag", "timeline", "project", "people", "reference"]

    results: dict = {}

    if "semantic" in modes:
        results["semantic"] = semantic_search(query, top_k=top_k)

    if "fulltext" in modes:
        results["fulltext"] = fulltext_search(query, limit=top_k)

    if "tag" in modes:
        tags = [t.lstrip("#") for t in re.findall(r"#\w+", query)]
        if not tags:
            # Extract bare words as potential tags
            tags = [w for w in query.lower().split() if len(w) >= 3][:5]
        results["tag"] = tag_search(tags, limit=top_k) if tags else []

    if "timeline" in modes:
        results["timeline"] = timeline_search(
            keyword=query, project_id=project_id, limit=min(top_k, 50)
        )

    if "graph" in modes and note_id_for_graph is not None:
        results["graph"] = graph_search(note_id_for_graph, depth=2)

    if "project" in modes:
        results["project"] = project_search(query, limit=10)

    if "people" in modes:
        results["people"] = people_search(query, limit=10)

    if "reference" in modes:
        results["reference"] = reference_search(query, limit=10)

    return results
