"""K4 — Response Provenance.

Arkana must be able to show WHICH retrieved Knowledge OS notes informed a reply.
The invariant under test is provenance, not decoration:

    a source may be cited ONLY if its note was actually part of the context
    package that was injected into the provider for that turn.

The Gemini embedding API is unavailable in the test environment, so
embed_text / store_chunk_embedding are stubbed with deterministic local vectors
(same technique as tests/test_oracle_spine.py). This is strictly necessary to
exercise the REAL retrieval plumbing offline — chunk storage, thread filtering,
scoring, and format_context_for_provider all run unmodified.
"""
from __future__ import annotations

import math

import pytest


# ── Deterministic local embedding stub (replaces unavailable Gemini API) ─────
_EMBED_DIM = 256


def _hash_vec(text: str) -> list[float]:
    vec = [0.0] * _EMBED_DIM
    for tok in ''.join(c if c.isalnum() else ' ' for c in text.lower()).split():
        vec[hash(tok) % _EMBED_DIM] += 1.0
    mag = math.sqrt(sum(v * v for v in vec))
    return [v / mag for v in vec] if mag else vec


def _store_stub(chunk_id, vector, model):
    import json
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
    monkeypatch.setattr(emb, "embed_text", lambda text, task_type="RETRIEVAL_DOCUMENT": _hash_vec(text or ""))
    monkeypatch.setattr(emb, "store_chunk_embedding",
                        lambda chunk_id, vector, model="stub": _store_stub(chunk_id, vector, model))


@pytest.fixture(autouse=True)
def _clean_knowledge_db():
    from knowledge.db import execute
    for tbl in ("embeddings", "chunks", "notes", "threads", "projects", "timeline", "edges"):
        try:
            execute(f"DELETE FROM {tbl}")
        except Exception:
            pass
    yield


def _retrieve(query: str, session_id: str):
    """Drive the REAL spine retrieval and return (block, meta)."""
    from api.oracle_spine import build_memory_block
    return build_memory_block(query, session_id)


# ── Provenance: citations trace to retrieved notes ───────────────────────────

def test_sources_cite_the_note_actually_retrieved():
    """A fact archived into the Knowledge OS is retrieved, injected, AND cited —
    and the citation carries the note's stable uuid, not a synthesised label."""
    from api.oracle_spine import archive_oracle_turn, build_sources

    marker = "ObsidianLattice4Verge"
    session_id = "k4-provenance-001"
    archive_oracle_turn(
        f"The {marker} archive is kept in the western annex.",
        f"Noted: the {marker} archive is in the western annex.",
        session_id,
    )
    import time
    time.sleep(0.05)

    block, meta = _retrieve(f"Where is the {marker} archive kept?", session_id)
    assert meta["notes_retrieved"] >= 1
    assert marker in block, "precondition: the archived fact must be injected"

    sources = build_sources(meta["_context_package"])
    assert sources, "a turn with injected context must cite at least one source"

    # Every citation must resolve to a note present in the injected package.
    package = meta["_context_package"]
    admissible = {
        (n.get("uuid") or n.get("id"))
        for n in package.get("relevant_notes", []) + [
            (e.get("note") or {}) for e in package.get("graph_expansions", [])
        ]
    }
    for src in sources:
        assert src["id"], "a citation must carry a stable identifier"
        assert src["id"] in admissible, "cited source must be part of the injected context"

    # The citation's excerpt must come from text that was actually injected —
    # this is what separates provenance from a decorative label. The excerpt is
    # a whitespace-normalised projection of the chunk (format_context_for_provider
    # injects chunks verbatim), so compare content, not raw bytes.
    excerpt = next(s["excerpt"] for s in sources if s["excerpt"])
    assert excerpt, "a directly-retrieved note must yield an excerpt"
    injected = " ".join(block.split())
    assert excerpt[:40] in injected, "the cited excerpt must derive from the injected block"


def test_sources_are_never_fabricated_without_retrieval():
    """The provenance invariant's negative side: with nothing archived there is
    nothing retrieved, so there is nothing to cite. Empty must stay empty."""
    from api.oracle_spine import build_sources

    block, meta = _retrieve("anything at all", "k4-provenance-empty-002")
    assert meta["notes_retrieved"] == 0
    assert block == ""
    assert build_sources(meta.get("_context_package")) == []


def test_sources_tolerate_absent_or_empty_package():
    """Missing/None/empty context packages yield no citations rather than raising."""
    from api.oracle_spine import build_sources
    assert build_sources(None) == []
    assert build_sources({}) == []
    assert build_sources({"relevant_notes": [], "graph_expansions": []}) == []


def test_sources_deduplicate_and_respect_limit():
    """A note reachable both directly and via graph expansion is cited once,
    and the citation list stays bounded."""
    from api.oracle_spine import build_sources

    package = {
        "relevant_notes": [
            {"uuid": "uuid-a", "title": "Alpha", "note_type": "scroll", "relevant_chunks": ["alpha body"]},
            {"uuid": "uuid-b", "title": "Beta", "note_type": "note", "relevant_chunks": []},
            {"uuid": "uuid-a", "title": "Alpha (duplicate row)", "note_type": "scroll", "relevant_chunks": []},
        ],
        "graph_expansions": [
            {"note": {"uuid": "uuid-a", "title": "Alpha", "note_type": "scroll"}},
            {"note": {"uuid": "uuid-c", "title": "Gamma", "note_type": "note"}},
        ],
    }
    sources = build_sources(package)
    ids = [s["id"] for s in sources]
    assert ids == ["uuid-a", "uuid-b", "uuid-c"], "direct notes first, then linked, deduplicated"
    assert sources[0]["via"] == "note"
    assert sources[2]["via"] == "graph"

    assert len(build_sources(package, limit=2)) == 2


def test_source_excerpt_is_collapsed_and_bounded():
    """Excerpts are whitespace-collapsed and bounded so a citation stays a
    citation — a pointer back to the note, not a copy of the corpus."""
    from api.oracle_spine import build_sources, _EXCERPT_CHARS

    long_body = "word " * 200
    sources = build_sources({
        "relevant_notes": [
            {"uuid": "uuid-long", "title": "Long", "note_type": "note",
             "relevant_chunks": [f"  {long_body}\n\n  trailing  "]},
        ],
        "graph_expansions": [],
    })
    excerpt = sources[0]["excerpt"]
    assert "\n" not in excerpt and "  " not in excerpt
    assert len(excerpt) <= _EXCERPT_CHARS + 1  # +1 for the ellipsis
    assert excerpt.endswith("…")


def test_context_package_stays_internal_to_the_meta_dict():
    """The retained package is an internal diagnostic, never response payload.
    The endpoint must pass it to build_sources and must not serialise it."""
    import inspect
    import api.main as main

    src = inspect.getsource(main)
    assert src.count("_context_package") == 1, (
        "the context package must be referenced only at the citation seam"
    )
    line = [ln for ln in src.splitlines() if "_context_package" in ln][0]
    assert "build_sources(" in line, "the package must only be read to derive citations"

    from api.oracle_spine import retrieve_arkana_context
    meta = retrieve_arkana_context("nothing archived here", "k4-internal-003")[1]
    assert all(not k.startswith("_") for k in meta) or "_context_package" in meta


def test_response_source_preserves_capture_provenance():
    from api.oracle_spine import build_sources

    package = {
        "relevant_notes": [{
            "uuid": "note-1",
            "title": "Captured source",
            "note_type": "document",
            "relevant_chunks": ["evidence"],
            "provenance": {
                "capture_uuid": "cap-1",
                "raw_checksum": "abc123",
                "authored_by": None,
                "source": {"kind": "document", "ref": "test:origin"},
            },
        }],
        "graph_expansions": [],
    }
    sources = build_sources(package)
    assert sources[0]["provenance"]["capture_uuid"] == "cap-1"
    assert sources[0]["provenance"]["source"]["ref"] == "test:origin"


def test_response_source_without_provenance_remains_unknown():
    from api.oracle_spine import build_sources

    package = {
        "relevant_notes": [{
            "uuid": "note-unknown",
            "title": "Legacy",
            "note_type": "note",
            "relevant_chunks": [],
        }],
        "graph_expansions": [],
    }
    sources = build_sources(package)
    assert sources[0]["provenance"] == {"state": "UNKNOWN"}
