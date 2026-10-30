"""Unit 1 — Arkana memory ownership containment.

`assemble_context` assembled a package from four channels. Only one of them
applied an ownership filter, and that filter was itself permissive: it ran only
when a `user_id` was bound, so an anonymous caller retrieved *unscoped*. Measured
on the pre-repair tree, a single archived turn owned by one user was reachable
by an anonymous caller through three of the four channels:

    channel          anonymous        another user     owner
    notes            LEAKED           scoped           reached
    graph expansion  unfiltered       unfiltered       reached
    timeline         LEAKED (7 rows)  LEAKED (7 rows)  reached
    project context  LEAKED           LEAKED           reached

The fix scopes every channel to the caller, and the archive path keeps an
ownerless turn out of the shared NULL-owner tier.

These tests drive the real retrieval path against a throwaway database. The
embeddings provider is stubbed because the point under test is *ownership*, not
vector search — a live provider would make the test depend on network state.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import time

import pytest

os.environ["ARKADIA_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="arkadia_memory_ownership_"), "knowledge.db"
)

_DIM = 64


def _hash_vector(text: str) -> list[float]:
    vec = [0.0] * _DIM
    for token in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split():
        vec[hash(token) % _DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def _store_embedding(chunk_id: int, vector: list[float], model: str = "stub") -> int:
    from knowledge.db import execute, execute_one, last_insert_id

    existing = execute_one("SELECT id FROM embeddings WHERE chunk_id = ?", (chunk_id,))
    if existing:
        execute("UPDATE embeddings SET vector = ?, model = ? WHERE chunk_id = ?",
                (json.dumps(vector), model, chunk_id))
        return existing["id"]
    execute("INSERT INTO embeddings (chunk_id, vector, model) VALUES (?, ?, ?)",
            (chunk_id, json.dumps(vector), model))
    return last_insert_id()


@pytest.fixture(autouse=True)
def _stub_embeddings(monkeypatch):
    import knowledge.embeddings as emb

    monkeypatch.setattr(emb, "embed_text",
                        lambda text, task_type="RETRIEVAL_DOCUMENT": _hash_vector(text or ""))
    monkeypatch.setattr(emb, "store_chunk_embedding",
                        lambda chunk_id, vector, model="stub": _store_embedding(chunk_id, vector, model))


@pytest.fixture(autouse=True)
def _clean_knowledge_db():
    from knowledge.db import execute

    for table in ("embeddings", "chunks", "notes", "threads", "projects", "timeline", "graph_edges"):
        try:
            execute(f"DELETE FROM {table}")
        except Exception:
            pass
    yield


OWNER = "firebase-uid-owner-A"
OTHER = "firebase-uid-other-B"
SECRET = "ArkanaMemoryOwnershipCanaryQ7"


def _archive_owned_turn(session_id: str = "owned-session-01") -> None:
    from api.oracle_spine import archive_oracle_turn

    archive_oracle_turn(
        f"Confidential {SECRET} salary data.",
        f"Noted the {SECRET} figures.",
        session_id,
        user_id=OWNER,
    )
    time.sleep(0.05)


def _channels(user_id: str, session_id: str = "", project_id: int | None = None) -> dict:
    from knowledge.context_engine import assemble_context

    pkg = assemble_context(SECRET, thread_id=None, project_id=project_id,
                           user_id=user_id or None)
    return {
        "notes": json.dumps(pkg.get("relevant_notes", [])),
        "graph": json.dumps(pkg.get("graph_expansions", [])),
        "timeline": json.dumps(pkg.get("recent_timeline", [])),
        "project": json.dumps(pkg.get("project_context", {})),
        "timeline_rows": len(pkg.get("recent_timeline", [])),
    }


# ── the exposure itself, one test per channel ────────────────────────────────

def test_anonymous_retrieval_does_not_surface_an_owned_turn():
    """The measured defect: an anonymous caller retrieved another person's turn."""
    _archive_owned_turn()
    got = _channels("")
    assert SECRET not in got["notes"], "anonymous retrieval surfaced an owned conversation note"
    assert SECRET not in got["timeline"], "anonymous retrieval surfaced an owned timeline event"


def test_another_user_retrieval_does_not_surface_an_owned_turn():
    _archive_owned_turn()
    got = _channels(OTHER)
    assert SECRET not in got["notes"], "a different user retrieved the owner's note"
    assert SECRET not in got["timeline"], "a different user retrieved the owner's timeline events"


def test_anonymous_timeline_channel_is_empty_not_merely_unmatched():
    """The timeline channel had no owner filter at all, so it returned every
    event. Scoping must leave an anonymous caller with no rows, not with rows
    that happen to miss the canary."""
    _archive_owned_turn()
    assert _channels("")["timeline_rows"] == 0


def test_anonymous_caller_cannot_read_project_context_by_supplying_project_id():
    """`project_id` is caller-supplied. Resolving it without an owner check let
    an anonymous caller read another owner's project description and note titles."""
    from knowledge.db import execute
    from knowledge.vault import create_note, create_project

    project = create_project("Confidential M&A", user_id=OWNER)
    execute("UPDATE projects SET description = ? WHERE id = ?", (f"Secret {SECRET}", project["id"]))
    create_note(title=f"secret {SECRET} memo", content=SECRET,
                project_id=project["id"], user_id=OWNER)

    got = _channels("", project_id=project["id"])
    assert SECRET not in got["project"], "anonymous caller read an owned project's context"


def test_owner_still_retrieves_their_own_turn():
    """Containment must not break the legitimate workflow it protects."""
    _archive_owned_turn()
    got = _channels(OWNER)
    assert SECRET in got["notes"], "the owner must still retrieve their own archived turn"
    assert got["timeline_rows"] > 0, "the owner must still see their own timeline"


# ── continuity is preserved without becoming world-readable ──────────────────

def test_anonymous_session_continuity_is_preserved():
    """Anonymous turns must remain continuous within their own session. Refusing
    to archive them would remove a product feature, so containment scopes them
    instead: reachable through the caller's own thread, not through the shared tier."""
    from api.oracle_spine import archive_oracle_turn, build_memory_block

    session = "anonymous-continuity-01"
    marker = "AnonContinuityMarkerR4"
    archive_oracle_turn(f"Remember {marker}.", f"Noted {marker}.", session, user_id="")
    time.sleep(0.05)

    block, meta = build_memory_block(f"What about {marker}?", session, user_id="")
    assert meta["notes_retrieved"] >= 1, "anonymous session continuity regressed"
    assert marker in block


def test_anonymous_turn_is_not_reachable_from_another_session():
    """The containment half: the same ownerless turn must not leak to a
    different anonymous session."""
    from api.oracle_spine import archive_oracle_turn, build_memory_block

    marker = "AnonIsolationMarkerT8"
    archive_oracle_turn(f"Private {marker}.", f"Noted {marker}.", "anon-session-A", user_id="")
    time.sleep(0.05)

    block, meta = build_memory_block(f"Tell me about {marker}", "anon-session-B", user_id="")
    assert marker not in (block or ""), "an ownerless turn leaked into another anonymous session"


def test_guessed_session_id_does_not_disclose_an_owned_turn():
    """`session_id` is client-supplied, so addressing a thread is not authority
    over it. An anonymous caller who guesses an owner's session id must not
    receive that owner's exchange."""
    from api.oracle_spine import build_memory_block, resolve_thread_id

    victim_session = "victim-known-session-id"
    _archive_owned_turn(victim_session)

    thread_id = resolve_thread_id(victim_session, user_id="")
    block, meta = build_memory_block(SECRET, victim_session, user_id="")
    assert meta["notes_retrieved"] == 0, "a guessed session id disclosed an owned turn"
    assert SECRET not in (block or "")


def test_public_corpus_stays_readable_anonymously():
    """The NULL-owner tier is the seeded public corpus (scrolls, documents,
    notes). Containment must not close it — only conversation material leaves it."""
    from knowledge.context_engine import assemble_context
    from knowledge.pipeline import ingest

    marker = "PublicCorpusMarkerV1"
    ingest(title=marker, content=f"{marker} is general reference material",
           note_type="document", user_id=None, auto_embed=True)

    pkg = assemble_context(marker, thread_id=None, user_id=None)
    assert any(marker in json.dumps(n) for n in pkg.get("relevant_notes", [])), \
        "the shared public corpus must remain retrievable"


# ── negative control: the harness must be able to detect the defect ──────────

def test_negative_control_detects_a_permissive_scope():
    """A guard that passes on both the defect and its absence proves nothing.

    This drives the *pre-repair* predicate — the permissive `user_id OR
    user_id IS NULL` clause applied only when an owner was bound — and asserts
    the canary is reported as reachable. If this control ever passes silently,
    the tests above have stopped measuring the boundary.
    """
    from knowledge.db import execute

    _archive_owned_turn()

    def pre_repair_retrievable_ids(user_id: str) -> set[int]:
        if user_id:
            rows = execute("SELECT id FROM notes WHERE user_id = ? OR user_id IS NULL", (user_id,))
        else:
            rows = execute("SELECT id FROM notes")  # unscoped anonymous branch
        return {r["id"] for r in rows}

    note_ids = pre_repair_retrievable_ids("")
    leaked = execute(
        f"SELECT content FROM notes WHERE id IN ({','.join('?' * len(note_ids))})",
        tuple(note_ids),
    )
    assert any(SECRET in (row["content"] or "") for row in leaked), \
        "negative control failed: the pre-repair predicate must expose the canary"

    # ...and the repaired predicate, on the same data, must not.
    from knowledge.context_engine import retrievable_note_ids

    fixed = retrievable_note_ids("")
    repaired = execute(
        f"SELECT content FROM notes WHERE id IN ({','.join('?' * len(fixed))})",
        tuple(fixed),
    ) if fixed else []
    assert not any(SECRET in (row["content"] or "") for row in repaired)
