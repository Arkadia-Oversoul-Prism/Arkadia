"""
Arkadia Knowledge OS — Embedding Completion Queue
==================================================
Detects notes with pending or failed embeddings and processes them
in background batches after startup ingestion completes.

LAW I: One pipeline. embed_note_chunks() is the single embedding entry point.

Entry points:
    get_embedding_status()      — read-only progress summary
    process_pending_batch(n)    — process up to n pending notes
    schedule_embedding_pass()   — launch full pass in background thread
"""

from __future__ import annotations

import logging
import threading

from knowledge.db import execute, execute_one

logger = logging.getLogger("arkadia.embedding_queue")

# Max notes to embed per background pass (keeps memory bounded)
_BATCH_SIZE = 50


# ─────────────────────────────────────────────────────────────────────────────
# Status
# ─────────────────────────────────────────────────────────────────────────────

def get_embedding_status() -> dict:
    """
    Return a progress snapshot — read-only.
    """
    total    = execute_one("SELECT COUNT(*) as n FROM notes")["n"] or 0
    complete = execute_one("SELECT COUNT(*) as n FROM notes WHERE embedding_status = 'complete'")["n"] or 0
    pending  = execute_one("SELECT COUNT(*) as n FROM notes WHERE embedding_status = 'pending'")["n"] or 0
    partial  = execute_one("SELECT COUNT(*) as n FROM notes WHERE embedding_status = 'partial'")["n"] or 0
    failed   = execute_one("SELECT COUNT(*) as n FROM notes WHERE embedding_status = 'failed'")["n"] or 0

    coverage = round(complete / total, 4) if total else 0.0

    return {
        "total":    total,
        "complete": complete,
        "pending":  pending,
        "partial":  partial,
        "failed":   failed,
        "coverage": coverage,
        "backlog":  pending + partial + failed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Processing
# ─────────────────────────────────────────────────────────────────────────────

def process_pending_batch(batch_size: int = _BATCH_SIZE) -> dict:
    """
    Embed up to batch_size notes that have pending or partial embedding status.
    Returns a progress summary.
    """
    from knowledge.pipeline import embed_note_chunks

    # Process pending first, then partial
    candidates = execute(
        """
        SELECT id FROM notes
        WHERE embedding_status IN ('pending', 'partial')
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (batch_size,),
    )

    success = 0
    failed  = 0
    skipped = 0

    for row in candidates:
        note_id = row["id"]
        # Check if note has chunks — if not, skip (will be chunked on next ingest)
        chunk_count = execute_one("SELECT COUNT(*) as n FROM chunks WHERE note_id = ?", (note_id,))
        if not chunk_count or chunk_count["n"] == 0:
            skipped += 1
            continue

        try:
            ok = embed_note_chunks(note_id)
            if ok:
                success += 1
            else:
                failed += 1
        except Exception as exc:
            logger.warning(f"[EMBED-QUEUE] Failed to embed note {note_id}: {exc}")
            failed += 1

    return {
        "processed": len(candidates),
        "success":   success,
        "failed":    failed,
        "skipped":   skipped,
    }


def run_full_embedding_pass() -> dict:
    """
    Process ALL pending/partial notes in batches until the backlog is clear.
    Runs synchronously — call from a background thread.
    """
    total_success = 0
    total_failed  = 0
    passes        = 0
    max_passes    = 20  # safety cap

    while passes < max_passes:
        status = get_embedding_status()
        if status["backlog"] == 0:
            break

        batch_result = process_pending_batch(_BATCH_SIZE)
        total_success += batch_result["success"]
        total_failed  += batch_result["failed"]
        passes        += 1

        if batch_result["processed"] == 0:
            break  # nothing left to process

    final = get_embedding_status()
    summary = {
        "passes":        passes,
        "total_success": total_success,
        "total_failed":  total_failed,
        "final_status":  final,
    }
    logger.info(f"[EMBED-QUEUE] Full pass complete: {summary}")
    return summary


def schedule_embedding_pass() -> None:
    """
    Launch a full embedding pass in a background daemon thread.
    Non-blocking. Safe to call at startup after static ingestion.
    """
    def _run() -> None:
        try:
            run_full_embedding_pass()
        except Exception as exc:
            logger.error(f"[EMBED-QUEUE] Background embedding pass failed: {exc}", exc_info=True)

    t = threading.Thread(target=_run, name="embedding-pass", daemon=True)
    t.start()
    logger.info("[EMBED-QUEUE] Embedding completion pass launched")
