"""
Arkadia Knowledge OS — Context Engine
=======================================
Assembles the context package sent to any AI provider.
NEVER prepend a giant memory file.
Instead: query → embed → semantic search → graph expand → assemble package.

Improvements over initial version:
- thread_id filtering is applied throughout
- Approximate token budget tracking (1 token ≈ 4 chars)
- Context is truncated when budget would be exceeded
LAW IV: Oracle retrieves knowledge. Providers generate language.
"""

import json
from typing import Optional

from knowledge.db import execute
from knowledge.embeddings import (
    embed_text, cosine_similarity, all_chunk_embeddings, bm25_score, _tokenise
)
from knowledge.graph import traverse

# Approximate token budget for the context package sent to a provider.
# 4 chars ≈ 1 token (conservative estimate)
DEFAULT_TOKEN_BUDGET = 3000  # tokens
CHARS_PER_TOKEN = 4


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def assemble_context(
    query: str,
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    max_notes: int = 8,
    max_chunks_per_note: int = 3,
    graph_depth: int = 1,
    include_timeline: bool = True,
    timeline_limit: int = 10,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
) -> dict:
    """
    Build a context package for a provider call.

    Pipeline:
      1. Embed query
      2. Semantic search → top relevant chunks (filtered by thread if provided)
      3. Resolve unique notes from chunks
      4. Graph-expand each note (1 hop)
      5. Add project context (if any)
      6. Add recent timeline (filtered by project/thread)
      7. Return structured context package with token budget tracking

    The provider receives ONLY this package, not the raw vault.
    """
    context: dict = {
        "query": query,
        "relevant_notes": [],
        "graph_expansions": [],
        "project_context": None,
        "recent_timeline": [],
        "token_budget_total": token_budget,
        "token_budget_used": 0,
    }

    budget_used = 0

    # ── Step 1+2: Semantic search ──────────────────────────────────────────
    query_vec = embed_text(query, task_type="RETRIEVAL_QUERY")
    all_chunks = all_chunk_embeddings()

    # Apply thread_id filter if provided — only retrieve chunks from that thread's notes
    if thread_id is not None:
        thread_note_ids = {
            row["id"]
            for row in execute("SELECT id FROM notes WHERE thread_id = ?", (thread_id,))
        }
        if thread_note_ids:
            all_chunks = [c for c in all_chunks if c["note_id"] in thread_note_ids]

    scored: list[dict] = []
    if query_vec and all_chunks:
        for chunk in all_chunks:
            try:
                chunk_vec = json.loads(chunk["vector"])
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append({**chunk, "score": score})
            except (TypeError, json.JSONDecodeError, ValueError):
                continue
        scored.sort(key=lambda x: x["score"], reverse=True)
    elif all_chunks:
        q_tokens = _tokenise(query)
        for chunk in all_chunks:
            doc_tokens = _tokenise(chunk["content"])
            score = bm25_score(q_tokens, doc_tokens)
            if score > 0:
                scored.append({**chunk, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)

    # ── Step 3: Resolve unique notes, respect token budget ─────────────────
    seen_note_ids: list[int] = []
    note_chunks: dict[int, list[str]] = {}
    for chunk in scored:
        nid = chunk["note_id"]
        chunk_tokens = _approx_tokens(chunk["content"])
        if budget_used + chunk_tokens > token_budget * 0.6:
            break  # Reserve 40% for graph/project/timeline
        if nid not in note_chunks:
            if len(note_chunks) >= max_notes:
                break
            seen_note_ids.append(nid)
            note_chunks[nid] = []
        if len(note_chunks[nid]) < max_chunks_per_note:
            note_chunks[nid].append(chunk["content"])
            budget_used += chunk_tokens

    # Fetch note metadata
    relevant_notes: list[dict] = []
    if seen_note_ids:
        phs = ",".join("?" * len(seen_note_ids))
        notes = execute(
            f"SELECT id, uuid, title, note_type, tags, created_at FROM notes WHERE id IN ({phs})",
            tuple(seen_note_ids),
        )
        notes_by_id = {n["id"]: n for n in notes}
        for nid in seen_note_ids:
            if nid in notes_by_id:
                n = dict(notes_by_id[nid])
                n["relevant_chunks"] = note_chunks.get(nid, [])
                relevant_notes.append(n)

    context["relevant_notes"] = relevant_notes

    # ── Step 4: Graph expansion (1 hop) ────────────────────────────────────
    if seen_note_ids and graph_depth > 0 and budget_used < token_budget * 0.8:
        graph_nodes: list[dict] = []
        relevant_ids = {n["id"] for n in relevant_notes}
        for nid in seen_note_ids[:4]:
            expansion = traverse(nid, max_depth=graph_depth)
            for node in expansion["nodes"]:
                if node["id"] not in relevant_ids:
                    node_tokens = _approx_tokens(node.get("title", ""))
                    if budget_used + node_tokens <= token_budget * 0.85:
                        graph_nodes.append({"note": node, "via": nid})
                        budget_used += node_tokens
        context["graph_expansions"] = graph_nodes[:6]

    # ── Step 5: Project context ─────────────────────────────────────────────
    if project_id and budget_used < token_budget * 0.9:
        project = execute(
            "SELECT id, uuid, name, description, tags FROM projects WHERE id = ?",
            (project_id,),
        )
        if project:
            p = dict(project[0])
            desc_tokens = _approx_tokens(p.get("description", ""))
            if budget_used + desc_tokens <= token_budget * 0.92:
                recent_proj_notes = execute(
                    "SELECT id, uuid, title, note_type, created_at FROM notes "
                    "WHERE project_id = ? ORDER BY updated_at DESC LIMIT 5",
                    (project_id,),
                )
                p["recent_notes"] = recent_proj_notes
                context["project_context"] = p
                budget_used += desc_tokens

    # ── Step 6: Recent timeline ─────────────────────────────────────────────
    if include_timeline and budget_used < token_budget:
        tl_conditions: list[str] = []
        tl_params: list = []
        if project_id:
            tl_conditions.append("project_id = ?"); tl_params.append(project_id)
        if thread_id is not None:
            tl_conditions.append("note_id IN (SELECT id FROM notes WHERE thread_id = ?)")
            tl_params.append(thread_id)
        where = f"WHERE {' AND '.join(tl_conditions)}" if tl_conditions else ""
        tl_params.append(timeline_limit)
        rows = execute(
            f"SELECT event_type, payload, provider, persona, created_at "
            f"FROM timeline {where} ORDER BY id DESC LIMIT ?",
            tuple(tl_params),
        )
        for r in rows:
            try:
                r["payload"] = json.loads(r["payload"])
            except (TypeError, json.JSONDecodeError):
                pass
        context["recent_timeline"] = list(reversed(rows))
        budget_used += _approx_tokens(str(rows))

    context["token_budget_used"] = budget_used
    return context


def format_context_for_provider(context_package: dict) -> str:
    """
    Render the context package into a compact string for injection into a provider prompt.
    Keeps it token-efficient — no redundant metadata.
    """
    lines: list[str] = []

    if context_package.get("project_context"):
        p = context_package["project_context"]
        lines.append(f"## Project: {p['name']}")
        if p.get("description"):
            lines.append(p["description"])
        lines.append("")

    if context_package.get("relevant_notes"):
        lines.append("## Relevant Knowledge")
        for note in context_package["relevant_notes"]:
            lines.append(f"### {note['title']} ({note['note_type']})")
            for chunk in note.get("relevant_chunks", [])[:3]:
                lines.append(chunk)
            lines.append("")

    if context_package.get("graph_expansions"):
        lines.append("## Related Nodes")
        for exp in context_package["graph_expansions"]:
            node = exp.get("note", {})
            lines.append(f"- {node.get('title', '?')} ({node.get('note_type', '?')})")
        lines.append("")

    if context_package.get("recent_timeline"):
        lines.append("## Recent Activity")
        for event in context_package["recent_timeline"][-5:]:
            lines.append(f"- [{event['event_type']}] {event['created_at']}")
        lines.append("")

    return "\n".join(lines)
