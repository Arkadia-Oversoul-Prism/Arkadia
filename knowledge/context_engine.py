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
from knowledge import embeddings as emb
from knowledge.graph import traverse

# Approximate token budget for the context package sent to a provider.
# 4 chars ≈ 1 token (conservative estimate)
DEFAULT_TOKEN_BUDGET = 3000  # tokens
CHARS_PER_TOKEN = 4


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


#: A conversation note records a real exchange between a person and Arkana. It is
#: private to its owner and must never be reachable from the NULL-owner tier,
#: which exists for the seeded public corpus (scrolls, documents, notes).
_CONVERSATION_NOTE_TYPE = "conversation"


def _owner_scope_sql(user_id: Optional[str], thread_id: Optional[int] = None) -> tuple[str, tuple]:
    """SQL predicate + params for the notes a retrieval for ``user_id`` may surface.

    Three things are reachable, and nothing else:

    * the seeded public corpus — NULL-owner notes that are not conversation
      material (scrolls, documents, notes), which is shared by design;
    * notes owned by the caller;
    * conversation notes in a thread the caller may address, which is what
      preserves session continuity for a caller who has no owner yet.

    A conversation note records a real exchange between a person and Arkana, so
    it is deliberately excluded from the shared tier in both branches: an
    ownerless turn is reachable through its own thread, never by everyone.

    ``session_id`` is client-supplied, so addressing a thread is not by itself
    authority over it. An ownerless caller's continuity therefore comes from an
    ownerless thread, never from a thread that names another owner.
    """
    uid = (user_id or "").strip() or None
    disjuncts = ["(user_id IS NULL AND note_type <> ?)"]
    params: list = [_CONVERSATION_NOTE_TYPE]
    if uid:
        # An owner's notes are all reachable; no thread clause is needed.
        disjuncts.append("user_id = ?")
        params.append(uid)
    elif thread_id is not None:
        # An ownerless caller has no owner to match, so continuity comes from an
        # ownerless thread. `session_id` is client-supplied, so the thread's own
        # owner is checked too — a guessed id must not address someone's thread.
        disjuncts.append(
            "(thread_id = ? AND user_id IS NULL AND thread_id IN "
            "(SELECT id FROM threads WHERE user_id IS NULL))"
        )
        params.append(thread_id)
    return f"({' OR '.join(disjuncts)})", tuple(params)


def retrievable_note_ids(user_id: Optional[str],
                         thread_id: Optional[int] = None) -> set[int]:
    """Note ids a retrieval for ``user_id`` may surface. See `_owner_scope_sql`."""
    clause, params = _owner_scope_sql(user_id, thread_id)
    rows = execute(f"SELECT id FROM notes WHERE {clause}", params)
    return {row["id"] for row in rows}


def _project_owner_clause(user_id: Optional[str]) -> tuple[str, tuple]:
    """Projects carry the same owner semantics as the note public corpus."""
    uid = (user_id or "").strip() or None
    if uid:
        return "(user_id = ? OR user_id IS NULL)", (uid,)
    return "user_id IS NULL", ()


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
    user_id: Optional[str] = None,
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
    query_vec = emb.embed_text(query, task_type="RETRIEVAL_QUERY")
    # Local-first (LAW II): when the query embedding is unavailable (Gemini
    # offline/unconfigured), score raw chunks by BM25 instead of cosine.
    # emb.all_chunk_embeddings() JOINs chunks→embeddings and returns [] when 0
    # embeddings exist, which would otherwise make the BM25 fallback dead.
    if query_vec is not None:
        all_chunks_local = emb.all_chunk_embeddings()
    else:
        all_chunks_local = emb.all_chunks()

    # Apply thread_id filter if provided — only retrieve chunks from that thread's notes
    if thread_id is not None:
        thread_note_ids = {
            row["id"]
            for row in execute("SELECT id FROM notes WHERE thread_id = ?", (thread_id,))
        }
        if thread_note_ids:
            all_chunks_local = [c for c in all_chunks_local if c["note_id"] in thread_note_ids]

    # Private boundary: retrieval is scoped to the caller's owner. This filter
    # applies to BOTH branches — an anonymous caller is scoped to the public
    # corpus plus its own session thread, not left unscoped.
    owned_ids = retrievable_note_ids(user_id, thread_id)
    all_chunks_local = [c for c in all_chunks_local if c["note_id"] in owned_ids]

    scored: list[dict] = []
    if query_vec and all_chunks_local:
        for chunk in all_chunks_local:
            try:
                chunk_vec = json.loads(chunk["vector"])
                score = emb.cosine_similarity(query_vec, chunk_vec)
                scored.append({**chunk, "score": score})
            except (TypeError, json.JSONDecodeError, ValueError):
                continue
        scored.sort(key=lambda x: x["score"], reverse=True)
    elif all_chunks_local:
        q_tokens = emb._tokenise(query)
        for chunk in all_chunks_local:
            doc_tokens = emb._tokenise(chunk["content"])
            score = emb.bm25_score(q_tokens, doc_tokens)
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
            expansion = traverse(nid, max_depth=graph_depth, user_id=user_id)
            for node in expansion["nodes"]:
                # Defense in depth: the traversal helper admits the NULL-owner
                # tier, which can still hold legacy conversation notes. Re-apply
                # the retrieval boundary so a graph hop cannot re-expose one.
                if node["id"] not in owned_ids:
                    continue
                if node["id"] not in relevant_ids:
                    node_tokens = _approx_tokens(node.get("title", ""))
                    if budget_used + node_tokens <= token_budget * 0.85:
                        graph_nodes.append({"note": node, "via": nid})
                        budget_used += node_tokens
        context["graph_expansions"] = graph_nodes[:6]

    # ── Step 5: Project context ─────────────────────────────────────────────
    if project_id and budget_used < token_budget * 0.9:
        proj_clause, proj_params = _project_owner_clause(user_id)
        note_clause, note_params = _owner_scope_sql(user_id)
        project = execute(
            f"SELECT id, uuid, name, description, tags FROM projects WHERE id = ? AND {proj_clause}",
            (project_id, *proj_params),
        )
        if project:
            p = dict(project[0])
            desc_tokens = _approx_tokens(p.get("description", ""))
            if budget_used + desc_tokens <= token_budget * 0.92:
                recent_proj_notes = execute(
                    "SELECT id, uuid, title, note_type, created_at FROM notes "
                    f"WHERE project_id = ? AND {note_clause} "
                    "ORDER BY updated_at DESC LIMIT 5",
                    (project_id, *note_params),
                )
                p["recent_notes"] = recent_proj_notes
                context["project_context"] = p
                budget_used += desc_tokens

    # ── Step 6: Recent timeline ─────────────────────────────────────────────
    if include_timeline and budget_used < token_budget:
        # Reuse the canonical owner clause rather than restating the boundary:
        # it is fail-closed (``1 = 0``) for an anonymous caller, so this channel
        # can never surface another owner's activity.
        from knowledge.timeline import _timeline_owner_clause
        tl_conditions: list[str] = []
        tl_params: list = []
        owner_sql, owner_params = _timeline_owner_clause(user_id)
        tl_conditions.append(owner_sql); tl_params.extend(owner_params)
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
