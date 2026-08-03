"""
Arkadia Knowledge OS — Semantic Enrichment Engine
==================================================
Automatically discovers and creates meaningful canonical relationships
between Knowledge Objects.

LAW I: One pipeline. No parallel storage. No fabrication.

This engine:
  - analyses a newly-ingested note against the existing graph
  - discovers relationships that already exist in the data
  - creates canonical edges with confidence weights
  - never invents links — only surfaces evidence-based connections
  - is idempotent: duplicate edges are silently ignored (UNIQUE constraint)

Entry points:
    enrich_note(note_id)          — enrich one note
    enrich_batch(note_ids)        — enrich multiple notes
    schedule_enrichment(note_id)  — launch in background thread
"""

from __future__ import annotations

import json
import logging
import re
import threading
from typing import Optional

from knowledge.db import execute, execute_one
from knowledge.graph import add_edge
from knowledge.relationship_types import RELATIONSHIP_TYPES_SET

logger = logging.getLogger("arkadia.enrichment")

# ─────────────────────────────────────────────────────────────────────────────
# Confidence thresholds
# ─────────────────────────────────────────────────────────────────────────────

# Only create an edge if the evidence score meets or exceeds this threshold.
# Scale: 0.0 – 1.0
MIN_CONFIDENCE   = 0.25
# Above this threshold, use a stronger relationship type where appropriate.
HIGH_CONFIDENCE  = 0.65


# ─────────────────────────────────────────────────────────────────────────────
# Evidence scorers
# Each scorer returns a list of (target_id, relationship, weight, reason) tuples.
# ─────────────────────────────────────────────────────────────────────────────

def _shared_tag_links(note: dict) -> list[tuple[int, str, float, str]]:
    """
    Discover notes that share tags with this note.
    → `relates_to` (low confidence) or `references` (high shared-tag ratio).
    """
    try:
        tags = json.loads(note.get("tags") or "[]")
    except (json.JSONDecodeError, TypeError):
        tags = []
    if not tags:
        return []

    note_id = note["id"]
    placeholders = ",".join("?" * len(tags))
    candidates = execute(
        f"""
        SELECT n.id, n.note_type, n.tags,
               COUNT(t.name) as shared_count
        FROM notes n
        JOIN note_tags nt ON nt.note_id = n.id
        JOIN tags t ON t.id = nt.tag_id
        WHERE t.name IN ({placeholders})
          AND n.id != ?
        GROUP BY n.id
        ORDER BY shared_count DESC
        LIMIT 30
        """,
        tuple(tags) + (note_id,),
    )

    results = []
    own_tag_count = len(tags)
    for c in candidates:
        try:
            c_tags = json.loads(c.get("tags") or "[]")
        except (json.JSONDecodeError, TypeError):
            c_tags = []
        shared = c["shared_count"]
        union  = max(len(set(tags) | set(c_tags)), 1)
        confidence = shared / union

        if confidence < MIN_CONFIDENCE:
            continue

        rel = "references" if confidence >= HIGH_CONFIDENCE else "relates_to"
        results.append((c["id"], rel, round(confidence, 3), f"Shared tags: {shared}/{union}"))

    return results


def _shared_project_links(note: dict) -> list[tuple[int, str, float, str]]:
    """
    Notes within the same project are structurally related.
    → `belongs_to` concept (but since belongs_to links to projects,
      we use `relates_to` for note-to-note within-project links).
    """
    project_id = note.get("project_id")
    if not project_id:
        return []

    note_id = note["id"]
    siblings = execute(
        """
        SELECT id FROM notes
        WHERE project_id = ? AND id != ?
        LIMIT 20
        """,
        (project_id, note_id),
    )
    return [
        (s["id"], "relates_to", 0.4, "Same project")
        for s in siblings
    ]


def _conversation_thread_links(note: dict) -> list[tuple[int, str, float, str]]:
    """
    Conversation notes in the same thread reply to each other.
    → `replies_to` for the previous note in the thread.
    """
    if note.get("note_type") != "conversation":
        return []

    thread_id = note.get("thread_id")
    if not thread_id:
        return []

    note_id    = note["id"]
    created_at = note.get("created_at", "")

    # Find the immediately preceding conversation in the same thread
    prev = execute_one(
        """
        SELECT id FROM notes
        WHERE thread_id = ? AND id != ? AND created_at < ?
          AND note_type = 'conversation'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (thread_id, note_id, created_at),
    )
    if prev:
        return [(prev["id"], "replies_to", 0.9, "Same thread, preceding message")]
    return []


def _type_affinity_links(note: dict) -> list[tuple[int, str, float, str]]:
    """
    Type-specific structural relationships:
    - scroll → chapter: `part_of` (Spiral Codex belongs to Encyclopedia)
    - document → document: `references` when title substring overlap found
    - chapter → chapter: `follows` if sequential numbering detected
    """
    note_id   = note["id"]
    note_type = note.get("note_type", "note")
    title     = note.get("title", "")
    results: list[tuple[int, str, float, str]] = []

    if note_type == "chapter":
        # Link to encyclopaedia chapters that share numeric sequence hints
        num_match = re.search(r"\b(\d+)\b", title)
        if num_match:
            num = int(num_match.group(1))
            # Find chapter with num-1 in its title
            all_chapters = execute(
                "SELECT id, title FROM notes WHERE note_type = 'chapter' AND id != ?",
                (note_id,),
            )
            for ch in all_chapters:
                prev_match = re.search(r"\b(\d+)\b", ch["title"] or "")
                if prev_match and int(prev_match.group(1)) == num - 1:
                    results.append((ch["id"], "follows", 0.7, f"Chapter sequence: {num-1} → {num}"))

    if note_type in ("document", "scroll"):
        # Title word overlap with other documents/scrolls
        title_words = set(re.findall(r"\b[a-zA-Z]{5,}\b", title.lower()))
        if len(title_words) >= 2:
            peers = execute(
                "SELECT id, title FROM notes WHERE note_type IN ('document', 'scroll') AND id != ? LIMIT 50",
                (note_id,),
            )
            for peer in peers:
                peer_words = set(re.findall(r"\b[a-zA-Z]{5,}\b", (peer["title"] or "").lower()))
                if not peer_words:
                    continue
                overlap = len(title_words & peer_words)
                conf = overlap / max(len(title_words | peer_words), 1)
                if conf >= MIN_CONFIDENCE:
                    results.append((peer["id"], "references", round(conf, 3),
                                    f"Title word overlap: {overlap} words"))

    return results


def _source_provider_links(note: dict) -> list[tuple[int, str, float, str]]:
    """
    Notes from the same source provider are loosely connected.
    → `connected_to` at low weight.
    """
    provider = note.get("source_provider")
    if not provider or provider.startswith("static:"):
        # Static corpus is too broad — skip to avoid flooding the graph
        return []

    note_id = note["id"]
    related = execute(
        """
        SELECT id FROM notes
        WHERE source_provider = ? AND id != ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (provider, note_id),
    )
    return [(r["id"], "connected_to", 0.3, f"Same source: {provider}") for r in related]


# ─────────────────────────────────────────────────────────────────────────────
# Edge writer
# ─────────────────────────────────────────────────────────────────────────────

def _write_edges(note_id: int, candidates: list[tuple[int, str, float, str]]) -> int:
    """
    Deduplicate candidates and write edges above the confidence threshold.
    Returns count of edges actually written.
    """
    written = 0
    # Deduplicate by (target_id, relationship) — keep highest confidence
    best: dict[tuple[int, str], tuple[float, str]] = {}
    for target_id, rel, conf, reason in candidates:
        key = (target_id, rel)
        if key not in best or conf > best[key][0]:
            best[key] = (conf, reason)

    for (target_id, rel), (conf, reason) in best.items():
        if conf < MIN_CONFIDENCE:
            continue
        if rel not in RELATIONSHIP_TYPES_SET:
            continue
        if target_id == note_id:
            continue
        try:
            add_edge(note_id, target_id, rel, weight=conf)
            written += 1
            logger.debug(f"[ENRICHMENT] {note_id}→{target_id} via '{rel}' (conf={conf:.2f}) — {reason}")
        except ValueError as exc:
            logger.warning(f"[ENRICHMENT] Skipped invalid edge: {exc}")
        except Exception:
            pass  # UNIQUE constraint violations are expected and safe to ignore

    return written


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def enrich_note(note_id: int) -> dict:
    """
    Run all evidence scorers for a single note and write qualifying edges.

    Returns:
        { "note_id": int, "edges_created": int, "scorers_run": int }
    """
    note = execute_one("SELECT * FROM notes WHERE id = ?", (note_id,))
    if not note:
        return {"note_id": note_id, "edges_created": 0, "error": "Note not found"}

    all_candidates: list[tuple[int, str, float, str]] = []

    scorers = [
        _shared_tag_links,
        _shared_project_links,
        _conversation_thread_links,
        _type_affinity_links,
        _source_provider_links,
    ]

    for scorer in scorers:
        try:
            all_candidates.extend(scorer(note))
        except Exception as exc:
            logger.warning(f"[ENRICHMENT] Scorer {scorer.__name__} failed for note {note_id}: {exc}")

    edges_created = _write_edges(note_id, all_candidates)

    return {
        "note_id":       note_id,
        "edges_created": edges_created,
        "scorers_run":   len(scorers),
        "candidates":    len(all_candidates),
    }


def enrich_batch(note_ids: list[int]) -> dict:
    """
    Enrich a batch of notes. Returns aggregate stats.
    """
    total_edges = 0
    errors: list[dict] = []

    for note_id in note_ids:
        try:
            result = enrich_note(note_id)
            total_edges += result.get("edges_created", 0)
        except Exception as exc:
            errors.append({"note_id": note_id, "error": str(exc)})

    return {
        "notes_processed": len(note_ids),
        "total_edges_created": total_edges,
        "errors": errors,
    }


def enrich_all_orphans(limit: int = 500) -> dict:
    """
    Find notes with no outbound edges and enrich them.
    Safe to call repeatedly — idempotent.
    """
    orphan_ids = execute(
        """
        SELECT id FROM notes
        WHERE id NOT IN (SELECT source_note_id FROM graph_edges)
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    ids = [r["id"] for r in orphan_ids]
    result = enrich_batch(ids)
    result["orphans_found"] = len(ids)
    return result


def schedule_enrichment(note_id: int) -> None:
    """
    Enrich a note in a background daemon thread.
    Non-blocking — startup and ingest latency unaffected.
    """
    def _run() -> None:
        try:
            enrich_note(note_id)
        except Exception as exc:
            logger.error(f"[ENRICHMENT] Background enrichment failed for note {note_id}: {exc}")

    t = threading.Thread(target=_run, name=f"enrich-{note_id}", daemon=True)
    t.start()


def schedule_orphan_enrichment() -> None:
    """
    Enrich all orphan notes in a background daemon thread.
    """
    def _run() -> None:
        try:
            result = enrich_all_orphans()
            logger.info(f"[ENRICHMENT] Orphan pass complete: {result}")
        except Exception as exc:
            logger.error(f"[ENRICHMENT] Orphan enrichment failed: {exc}")

    t = threading.Thread(target=_run, name="enrich-orphans", daemon=True)
    t.start()
    logger.info("[ENRICHMENT] Orphan enrichment thread launched")
