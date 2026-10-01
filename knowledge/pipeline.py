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
from knowledge.vault import create_note, update_note, get_note, add_graph_edge
from knowledge.relationship_types import RELATIONSHIP_TYPES
from knowledge import embeddings
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

        vector = embeddings.embed_text(chunk["content"])
        if vector:
            embeddings.store_chunk_embedding(chunk["id"], vector)
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

def _ingest_core(
    title: str,
    content: str,
    note_type: str = "note",
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    participants: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    links: Optional[list[str]] = None,
    source_provider: Optional[str] = None,
    user_id: Optional[str] = None,
    auto_tag: bool = True,
    auto_embed: bool = True,
    auto_link: bool = True,
) -> dict:
    """Canonical note-write pipeline after SOURCE → CAPTURE has completed."""
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

    # ── 3. Create note ────────────────────────────────────────────────────────
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
        user_id=user_id,
    )
    note_id = note["id"]

    # ── 4. Persist tags ───────────────────────────────────────────────────────
    upsert_tags(note_id, final_tags)

    # ── 5. Chunk ──────────────────────────────────────────────────────────────
    chunks = chunk_text(content)
    store_chunks(note_id, chunks)

    # ── 6. Embed (async-friendly: runs inline, caller can also queue async) ──
    if auto_embed:
        embed_note_chunks(note_id)

    # ── 7. Semantic enrichment ────────────────────────────────────────────────
    if auto_link and note_id:
        try:
            from knowledge.enrichment import schedule_enrichment
            schedule_enrichment(note_id)
        except Exception:
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
    user_id: Optional[str] = None,
    auto_tag: bool = True,
    auto_embed: bool = True,
    auto_link: bool = True,
    capture_source_kind: Optional[str] = None,
    capture_source_ref: Optional[str] = None,
    capture_source_title: Optional[str] = None,
    captured_by: Optional[str] = "knowledge.pipeline",
    captured_by_kind: str = "system",
    authored_by: Optional[str] = None,
    authored_by_kind: str = "unknown",
) -> dict:
    """Shared ingress: SOURCE → CAPTURE → canonical Knowledge OS note.

    Every normal knowledge-ingestion call crosses the existing GATE-01 capture
    boundary before note creation. Existing callers remain source-compatible;
    callers may supply explicit source/actor metadata when it is actually known.
    """
    from knowledge import capture as cap

    kind_by_note_type = {
        "conversation": "message",
        "document": "document",
        "scroll": "document",
        "task": "system",
        "note": "system",
    }
    source_kind = capture_source_kind or kind_by_note_type.get(note_type, "system")
    source_ref = capture_source_ref or source_provider or f"pipeline:{note_type}"
    source_title = capture_source_title or title

    source = cap.register_source(
        source_kind=source_kind,
        source_ref=source_ref,
        title=source_title,
    )
    capture_record = cap.capture(
        source_uuid=source["source_uuid"],
        raw_content=content,
        content_kind=(
            "message" if note_type == "conversation"
            else "document" if note_type in {"document", "scroll"}
            else "system"
        ),
        captured_by=captured_by,
        captured_by_kind=captured_by_kind,
        authored_by=authored_by,
        authored_by_kind=authored_by_kind,
    )

    result = _ingest_core(
        title=title,
        content=content,
        note_type=note_type,
        project_id=project_id,
        thread_id=thread_id,
        participants=participants,
        tags=tags,
        links=links,
        source_provider=source_provider,
        user_id=user_id,
        auto_tag=auto_tag,
        auto_embed=auto_embed,
        auto_link=auto_link,
    )

    note_id = (
        (result.get("existing") or {}).get("id")
        if result.get("duplicate")
        else result.get("id")
    )
    if note_id is not None:
        capture_record = cap.bind_capture_to_note(
            capture_uuid=capture_record["capture_uuid"],
            note_id=note_id,
        )

    return {
        **result,
        "capture": cap.provenance_for_capture(capture_record["capture_uuid"]),
    }


def ingest_conversation(
    prompt: str,
    response: str,
    provider: str,
    persona: Optional[str] = None,
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> dict:
    """
    Convenience wrapper: ingest a full conversation exchange as a knowledge note.
    The raw exchange crosses the shared capture boundary before operational
    prompt/response timeline events are emitted.
    """
    content = f"## Prompt\n\n{prompt}\n\n## Response\n\n{response}"
    title = prompt[:80] + ("…" if len(prompt) > 80 else "")

    result = ingest(
        title=title,
        content=content,
        note_type="conversation",
        project_id=project_id,
        thread_id=thread_id,
        source_provider=provider,
        user_id=user_id,
    )

    # Operational continuity remains distinct from provenance and authorship.
    tl.record(
        "prompt",
        {"prompt": prompt[:500]},
        project_id=project_id,
        provider=provider,
        persona=persona,
    )
    tl.record(
        "response",
        {"response": response[:1000]},
        project_id=project_id,
        provider=provider,
        persona=persona,
    )

    return result
