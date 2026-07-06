"""
Arkadia Knowledge OS — Embeddings Layer
========================================
Generates and stores 768-dim vectors via Gemini text-embedding-004.
Falls back to BM25-style keyword scoring when offline or unconfigured.
LAW II: Local First. Cloud sync is additive. Never required.
LAW IV: Oracle retrieves knowledge. Providers generate language.
"""

import json
import math
import os
import re
from typing import Optional

from knowledge.db import execute, execute_one, last_insert_id


# ─────────────────────────────────────────────────────────────────────────────
# Embedding generation
# ─────────────────────────────────────────────────────────────────────────────

def _gemini_embed(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[list[float]]:
    """Call Gemini text-embedding-004. Returns None when API unavailable."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type,
        )
        return result["embedding"]
    except Exception:
        return None


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[list[float]]:
    """
    Embed a single piece of text. Returns a float vector or None on failure.
    task_type: RETRIEVAL_DOCUMENT | RETRIEVAL_QUERY | SEMANTIC_SIMILARITY
    """
    return _gemini_embed(text, task_type)


# ─────────────────────────────────────────────────────────────────────────────
# Cosine similarity
# ─────────────────────────────────────────────────────────────────────────────

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─────────────────────────────────────────────────────────────────────────────
# BM25-style fallback (local-first, no API needed)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    return re.findall(r"\b[a-z]{3,}\b", text.lower())


def bm25_score(query_tokens: list[str], doc_tokens: list[str], k1: float = 1.5, b: float = 0.75, avg_dl: int = 200) -> float:
    freq: dict[str, int] = {}
    for t in doc_tokens:
        freq[t] = freq.get(t, 0) + 1
    score = 0.0
    dl = len(doc_tokens)
    for qt in query_tokens:
        tf = freq.get(qt, 0)
        if tf == 0:
            continue
        idf = math.log(1 + 1 / (tf + 0.5))
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
    return score


# ─────────────────────────────────────────────────────────────────────────────
# SQLite storage
# ─────────────────────────────────────────────────────────────────────────────

def store_chunk_embedding(chunk_id: int, vector: list[float], model: str = "text-embedding-004") -> int:
    execute(
        "INSERT INTO embeddings (chunk_id, vector, model) VALUES (?, ?, ?)",
        (chunk_id, json.dumps(vector), model),
    )
    return last_insert_id()


def get_chunk_embedding(chunk_id: int) -> Optional[list[float]]:
    row = execute_one("SELECT vector FROM embeddings WHERE chunk_id = ? ORDER BY id DESC LIMIT 1", (chunk_id,))
    if row:
        return json.loads(row["vector"])
    return None


def all_chunk_embeddings() -> list[dict]:
    """Return all chunks with their embeddings. Used by semantic search."""
    return execute(
        """
        SELECT c.id AS chunk_id, c.note_id, c.content, e.vector
        FROM chunks c
        JOIN embeddings e ON e.chunk_id = c.id
        ORDER BY e.id DESC
        """
    )
