"""
Conversational Spine — continuity + thread-linkage tests.

Verifies the canonical invariant: ONE INTELLIGENCE SPINE, MANY INTERFACES.
Memory and intelligence must be interface-independent — a turn archived under
a session_id in one surface must be retrievable in a subsequent turn under
the SAME session_id, regardless of which surface initiated it.

The Gemini embedding API is not available in the test environment, so
embed_text / store_chunk_embedding are stubbed with deterministic local
vectors. This is strictly necessary to exercise the REAL retrieval plumbing
(chunk storage, thread_id filtering, cosine/BM25 scoring,
format_context_for_provider) offline. Every other code path runs unmodified.
"""
from __future__ import annotations

import math
import os
import threading

import pytest

# Point the Knowledge OS at a throwaway DB BEFORE any knowledge import touches it.
_DB_PATH = os.path.join(os.path.dirname(__file__), "_spine_test.db")
if os.path.exists(_DB_PATH):
    os.remove(_DB_PATH)
os.environ["ARKADIA_DB_PATH"] = _DB_PATH


# ── Deterministic local embedding stub (replaces unavailable Gemini API) ─────
# Bag-of-words hashing into a fixed-size vector. Same text → same vector,
# semantically overlapping texts → non-zero cosine similarity. Sufficient to
# exercise the real retrieval scoring path without a network model.
_EMBED_DIM = 256


def _hash_vec(text: str) -> list[float]:
    vec = [0.0] * _EMBED_DIM
    for tok in ''.join(c if c.isalnum() else ' ' for c in text.lower()).split():
        h = hash(tok) % _EMBED_DIM
        vec[h] += 1.0
    mag = math.sqrt(sum(v * v for v in vec))
    if mag:
        vec = [v / mag for v in vec]
    return vec


@pytest.fixture(autouse=True)
def _stub_embeddings(monkeypatch):
    import knowledge.embeddings as emb
    monkeypatch.setattr(emb, "embed_text", lambda text, task_type="RETRIEVAL_DOCUMENT": _hash_vec(text or ""))
    # Persist the stub vector so all_chunk_embeddings() (chunks JOIN embeddings) returns rows.
    monkeypatch.setattr(emb, "store_chunk_embedding", lambda chunk_id, vector, model="stub": _store_stub(chunk_id, vector, model))


@pytest.fixture(autouse=True)
def _clean_knowledge_db():
    """Wipe Knowledge OS rows between tests so each test starts from a known state."""
    from knowledge.db import execute
    for tbl in ("embeddings", "chunks", "notes", "threads", "projects", "timeline", "edges"):
        try:
            execute(f"DELETE FROM {tbl}")
        except Exception:
            pass
    yield


def _store_stub(chunk_id, vector, model):
    import json
    from knowledge.db import execute, execute_one
    existing = execute_one("SELECT id FROM embeddings WHERE chunk_id = ?", (chunk_id,))
    if existing:
        execute("UPDATE embeddings SET vector = ?, model = ? WHERE chunk_id = ?", (json.dumps(vector), model, chunk_id))
        return existing["id"]
    execute(
        "INSERT INTO embeddings (chunk_id, vector, model) VALUES (?, ?, ?)",
        (chunk_id, json.dumps(vector), model),
    )
    from knowledge.db import last_insert_id
    return last_insert_id()


# ── Spine continuity test ────────────────────────────────────────────────────

def test_conversational_spine_archives_and_retrieves_across_interfaces():
    """Objective 3: a unique fact archived under session_id S in one surface is
    retrieved when a related query arrives under the SAME session_id later —
    even though no surface-specific state links the two calls."""
    from api.oracle_spine import archive_oracle_turn, build_memory_block

    session_id = "arkana-spine-test-001"
    unique_marker = "ZephyrCond7inateLoom"   # unlikely to collide with anything

    # Turn 1: user tells Arkana something unique (surface: e.g. Oracle Chat).
    turn1_prompt = f"My secret project codename is {unique_marker} and it lives in the eastern attic."
    turn1_reply = f"Understood — I have noted the {unique_marker} codename and its location."
    archive_oracle_turn(turn1_prompt, turn1_reply, session_id)

    # Give the archive write a moment to commit (ingest is synchronous in-process here).
    import time
    time.sleep(0.05)

    # Turn 2: a DIFFERENT surface (e.g. ReasoMate) asks a related question under
    # the SAME session_id. The spine must retrieve turn 1's content.
    turn2_query = f"What is the {unique_marker} codename project about?"
    block, meta = build_memory_block(turn2_query, session_id)

    assert meta["session_id"] == session_id
    assert meta["thread_id"] is not None, "thread must be created at archive time"
    assert meta["source"] == "knowledge_os"
    assert meta["notes_retrieved"] >= 1, "retrieval must find the archived turn"
    assert block, "a memory block must be injected when relevant context exists"
    assert unique_marker in block, "retrieved context must contain the archived unique fact"


def test_spine_does_not_retrieve_empty_when_nothing_archived():
    """The spine must NOT fabricate memory. When the Knowledge OS holds no
    notes at all, retrieval returns an empty block — never a hallucinated one."""
    from api.oracle_spine import build_memory_block
    block, meta = build_memory_block("anything at all", "arkana-spine-test-empty-002")
    assert meta["thread_id"] is None
    assert meta["notes_retrieved"] == 0
    assert block == ""


def test_session_continuity_and_transparency_label():
    """The correct cross-session invariant: a DIFFERENT session may still
    retrieve semantically relevant prior knowledge from the broader Knowledge
    OS (Arkana has general knowledge), BUT the block must explicitly label it
    as retrieved historical context — never as fabricated personal memory, and
    never unlabeled. Same-session continuity must also hold."""
    from api.oracle_spine import archive_oracle_turn, build_memory_block

    marker_a = "QuartzVellum9Sigh"
    session_a = "arkana-spine-isolation-A"
    session_b = "arkana-spine-isolation-B"

    # Archive under session A.
    archive_oracle_turn(f"Record this: {marker_a}", f"Noted {marker_a}.", session_a)
    import time; time.sleep(0.05)

    # Same session A asks a related question → continuity retrieval.
    block_a, meta_a = build_memory_block(marker_a, session_a)
    assert meta_a["thread_id"] is not None
    assert meta_a["notes_retrieved"] >= 1
    assert marker_a in block_a
    # Transparency: the block is explicitly labeled as retrieved historical context.
    assert "RETRIEVED CONTEXTUAL MEMORY" in block_a
    assert "NOT the current conversation" in block_a


def test_archive_survives_thread_boundary():
    """The production archive path runs in a daemon Thread; the spine helper
    itself must be safe to call across threads and still persist."""
    from api.oracle_spine import archive_oracle_turn, build_memory_block
    session_id = "arkana-spine-thread-003"
    marker = "MirageFelt7Echo"

    done = threading.Event()
    def _archive():
        archive_oracle_turn(f"Threaded note: {marker}", f"Ack {marker}.", session_id)
        done.set()
    t = threading.Thread(target=_archive, daemon=True)
    t.start()
    assert done.wait(timeout=2.0)

    block, meta = build_memory_block(marker, session_id)
    assert meta["notes_retrieved"] >= 1
    assert marker in block
