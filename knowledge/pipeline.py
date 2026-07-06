"""
Arkadia Knowledge OS — Knowledge Pipeline
==========================================
Every conversation/response flows through this pipeline.
Nothing is discarded.

Conversation → Markdown → Chunking → Embedding → SQLite → Graph → Timeline → Index

LAW I: One pipeline. One canonical home.
LAW IV: Oracle retrieves knowledge. Providers generate language.
"""

import hashlib
import json
import re
from typing import Optional

from knowledge import db
from knowledge.db import execute, execute_one, last_insert_id
from knowledge.vault import create_note, update_note, get_note, add_graph_edge, RELATIONSHIP_TYPES
from knowledge.embeddings import embed_text, store_chunk_embedding
from knowledge import timeline as tl
from knowledge import graph as kg


# ─────────────────────────────────────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────────────────────────────────────

def chunk_text(text: str, max_tokens: int = 512, overlap: int = 64) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Splits on paragraph boundaries first, then sentence boundaries.
    """
    # Normalise whitespace
    text = re.sub(r"\n{3,}", "\n\n", text.strip())

    # Split on double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len((current + "\n\n" + para).split()) <= max_tokens:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If single paragraph is too long, split by sentence
            if len(para.split()) > max_tokens:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sent_chunk = ""
                for sentence in sentences:
                    if len((sent_chunk + " " + sentence).split()) <= max_tokens:
                        sent_chunk = (sent_chunk + " " + sentence).strip()
                    else:
                        if sent_chunk:
                            chunks.append(sent_chunk)
                        sent_chunk = sentence
                if sent_chunk:
                    current = sent_chunk
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def store_chunks(note_id: int, chunks: list[str]) -> list[int]:
    """Insert chunks for a note, return list of chunk IDs."""
    chunk_ids: list[int] = []
    for i, chunk_text in enumerate(chunks):
        word_count = len(chunk_text.split())
        execute(
            "INSERT INTO chunks (note_id, content, position, token_count) VALUES (?, ?, ?, ?)",
            (note_id, chunk_text, i, word_count),
        )
        chunk_ids.append(last_insert_id())
    return chunk_ids


# ─────────────────────────────────────────────────────────────────────────────
# Embedding pipeline step
# ─────────────────────────────────────────────────────────────────────────────

def embed_note_chunks(note_id: int) -> bool:
    """
    Embed all unemedded chunks for a note.
    Updates note.embedding_status → 'complete' or 'failed'.
    Returns True if all embeddings succeeded.
    """
    chunks = execute("SELECT * FROM chunks WHERE note_id = ?", (note_id,))
    if not chunks:
        return False

    success_count = 0
    for chunk in chunks:
        # Skip if already embedded
        existing = execute_one(
            "SELECT id FROM embeddings WHERE chunk_id = ?", (chunk["id"],)
        )
        if existing:
            success_count += 1
            continue

        vector = embed_text(chunk["content"])
        if vector:
            store_chunk_embedding(chunk["id"], vector)
            success_count += 1

    status = "complete" if success_count == len(chunks) else (
        "partial" if success_count > 0 else "pending"
    )
    execute("UPDATE notes SET embedding_status = ? WHERE id = ?", (status, note_id))

    tl.record(
        "embed_complete",
        {"note_id": note_id, "chunks": len(chunks), "embedded": success_count, "status": status},
        note_id=note_id,
    )
    return status == "complete"


# ─────────────────────────────────────────────────────────────────────────────
# Tag management
# ─────────────────────────────────────────────────────────────────────────────

def upsert_tags(note_id: int, tags: list[str]) -> None:
    for tag_name in tags:
        tag_name = tag_name.lower().strip()
        if not tag_name:
            continue
        execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
        tag_row = execute_one("SELECT id FROM tags WHERE name = ?", (tag_name,))
        if tag_row:
            execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                (note_id, tag_row["id"]),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Auto-tag extraction (simple NLP, no provider call needed)
# ─────────────────────────────────────────────────────────────────────────────

_STOP_WORDS = {"the", "and", "for", "that", "this", "with", "are", "was", "has", "have",
               "not", "but", "from", "they", "you", "your", "what", "when", "where", "how"}

def extract_tags(title: str, content: str, max_tags: int = 8) -> list[str]:
    """Extract candidate tags from title and content using frequency analysis."""
    text = (title + " " + content).lower()
    words = re.findall(r"\b[a-z]{4,}\b", text)
    freq: dict[str, int] = {}
    for w in words:
        if w not in _STOP_WORDS:
            freq[w] = freq.get(w, 0) + 1
    # Also extract explicit #hashtags
    hashtags = re.findall(r"#([a-z]\w+)", text)
    for h in hashtags:
        freq[h] = freq.get(h, 0) + 10  # boost

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:max_tags]]


# ─────────────────────────────────────────────────────────────────────────────
# Duplicate detection
# ─────────────────────────────────────────────────────────────────────────────

def find_duplicates(content: str) -> Optional[dict]:
    """Check if an identical note (by checksum) already exists."""
    chk = hashlib.sha256(content.encode()).hexdigest()
    return execute_one("SELECT id, uuid, title FROM notes WHERE checksum = ?", (chk,))


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline entry point
# ─────────────────────────────────────────────────────────────────────────────

def ingest(
    title: str,
    content: str,
    note_type: str = "note",
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    participants: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    links: Optional[list[str]] = None,
    source_provider: Optional[str] = None,
    auto_tag: bool = True,
    auto_embed: bool = True,
    auto_link: bool = True,
) -> dict:
    """
    Full knowledge pipeline:
    1. Duplicate check
    2. Create note (Markdown + SQLite)
    3. Auto-tag extraction
    4. Chunk text
    5. Embed chunks
    6. Auto-link to related notes
    7. Timeline record
    Returns the created note dict.
    """

    # ── 1. Duplicate detection ───────────────────────────────────────────────
    dupe = find_duplicates(content)
    if dupe:
        return {"duplicate": True, "existing": dupe}

    # ── 2. Auto-tags ─────────────────────────────────────────────────────────
    final_tags = list(tags or [])
    if auto_tag:
        auto_tags = extract_tags(title, content)
        for t in auto_tags:
            if t not in final_tags:
                final_tags.append(t)

    # ── 3. Create note ───────────────────────────────────────────────────────
    note = create_note(
        title=title,
        content=content,
        note_type=note_type,
        project_id=project_id,
        thread_id=thread_id,
        participants=participants,
        tags=final_tags,
        links=links,
        source_provider=source_provider,
    )
    note_id = note["id"]

    # ── 4. Persist tags ──────────────────────────────────────────────────────
    upsert_tags(note_id, final_tags)

    # ── 5. Chunk ─────────────────────────────────────────────────────────────
    chunks = chunk_text(content)
    store_chunks(note_id, chunks)

    # ── 6. Embed (async-friendly: runs inline, caller can also queue async) ──
    if auto_embed:
        embed_note_chunks(note_id)

    # ── 7. Auto-link via tag similarity ──────────────────────────────────────
    if auto_link and note_id:
        # Find recent notes with overlapping tags
        candidate_rows = execute(
            "SELECT DISTINCT n.id FROM notes n JOIN note_tags nt ON nt.note_id = n.id "
            "JOIN tags t ON t.id = nt.tag_id WHERE t.name IN ({}) AND n.id != ? LIMIT 20".format(
                ",".join("?" * len(final_tags))
            ),
            tuple(final_tags) + (note_id,),
        ) if final_tags else []

        for cand in candidate_rows:
            try:
                add_graph_edge(note_id, cand["id"], "references", weight=0.5)
                tl.record(
                    "graph_link",
                    {"source": note_id, "target": cand["id"], "relationship": "references"},
                    note_id=note_id,
                    project_id=project_id,
                )
            except Exception:
                pass

    # ── 8. Timeline record ───────────────────────────────────────────────────
    tl.record(
        "knowledge_created",
        {
            "note_id": note_id,
            "note_uuid": note["uuid"],
            "title": title,
            "type": note_type,
            "chunks": len(chunks),
            "tags": final_tags,
        },
        note_id=note_id,
        project_id=project_id,
        provider=source_provider,
    )

    return {**note, "chunks_created": len(chunks), "tags_applied": final_tags}


def ingest_conversation(
    prompt: str,
    response: str,
    provider: str,
    persona: Optional[str] = None,
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
) -> dict:
    """
    Convenience wrapper: ingest a full conversation exchange as a knowledge note.
    Records both prompt and response as timeline events, then ingests the combined content.
    LAW: Conversations become structured knowledge. Nothing is discarded.
    """
    # Timeline: record the exchange
    tl.record("prompt", {"prompt": prompt[:500]}, project_id=project_id, provider=provider, persona=persona)
    tl.record("response", {"response": response[:1000]}, project_id=project_id, provider=provider, persona=persona)

    # Build note content
    content = f"## Prompt\n\n{prompt}\n\n## Response\n\n{response}"
    title = prompt[:80] + ("…" if len(prompt) > 80 else "")

    return ingest(
        title=title,
        content=content,
        note_type="conversation",
        project_id=project_id,
        thread_id=thread_id,
        source_provider=provider,
    )
