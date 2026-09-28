"""K5 — static ingestion source coverage."""
from __future__ import annotations

from pathlib import Path

from knowledge.static_ingestion import _SOURCES


def _sources_by_provider() -> dict[str, dict]:
    return {s["source_provider"]: s for s in _SOURCES}


def test_adr_corpus_is_a_declared_source():
    assert "static:adr" in _sources_by_provider()


def test_adr_source_root_resolves_and_holds_the_records():
    adr = _sources_by_provider()["static:adr"]
    assert adr["root"].is_dir(), f"ADR root missing: {adr['root']}"
    assert sorted(p.name for p in adr["root"].glob(adr["glob"])) == [
        "ADR-010-knowledge-vault.md",
        "ADR-011-provider-router.md",
        "ADR-012-context-engine.md",
        "ADR-013-phase0-security-hardening.md",
        "ADR-014-phase1-kernel-stabilisation.md",
        "ADR-015-dependency-direction-rule.md",
    ]


def test_every_declared_source_uses_a_canonical_note_type():
    from knowledge.node_types import NODE_TYPES

    for source in _SOURCES:
        assert source["note_type"] in NODE_TYPES, source["source_provider"]


def test_source_roots_never_escape_the_repository():
    repo_root = Path(__file__).resolve().parent.parent
    for source in _SOURCES:
        if source.get("kind"):  # record source — no filesystem root at all
            assert source["root"] is None, source["source_provider"]
            continue
        assert repo_root in source["root"].resolve().parents, source["source_provider"]


# ── Open loops (records, not files) ──────────────────────────────────────────

def _open_loop_source() -> dict:
    return _sources_by_provider()["static:oracle_open_loops"]


def test_open_loops_are_a_declared_source():
    assert "static:oracle_open_loops" in _sources_by_provider()


def test_open_loop_source_reads_the_canonical_oracle_store():
    """The record source must point at the same store kernel.oracle_store owns."""
    from kernel.oracle_store import _STORE_PATH

    from knowledge import static_ingestion

    assert static_ingestion._ORACLE_STORE_PATH.resolve() == Path(_STORE_PATH).resolve()


def test_open_loop_source_reads_only_loop_rows():
    from knowledge import static_ingestion

    loops = _open_loop_source()
    assert loops["kind"] == "oracle_open_loops"

    rows = static_ingestion._oracle_open_loop_rows()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_missing_oracle_store_yields_no_rows_and_does_not_raise(tmp_path, monkeypatch):
    from knowledge import static_ingestion

    monkeypatch.setattr(static_ingestion, "_ORACLE_STORE_PATH", tmp_path / "absent.json")
    assert static_ingestion._oracle_open_loop_rows() == []
    assert static_ingestion._ingest_oracle_open_loops(_open_loop_source()) == (0, 0, 0)


def test_malformed_oracle_store_yields_no_rows_and_does_not_raise(tmp_path, monkeypatch):
    from knowledge import static_ingestion

    bad = tmp_path / "oracle_store.json"
    bad.write_text("{ not json")
    monkeypatch.setattr(static_ingestion, "_ORACLE_STORE_PATH", bad)
    assert static_ingestion._oracle_open_loop_rows() == []


def test_open_loop_content_is_stable_across_reads(tmp_path, monkeypatch):
    """Dedupe is checksum-scoped, so identical rows must render identically."""
    from knowledge import static_ingestion

    store = tmp_path / "oracle_store.json"
    store.write_text(
        '{"open_loops": [{"id": "loop_abc", "ts": 1777257944.0, '
        '"loop": "ship phase 4", "status": "open", "updated_at": 1777257945.0}]}'
    )
    monkeypatch.setattr(static_ingestion, "_ORACLE_STORE_PATH", store)

    captured: list[dict] = []

    def _fake_ingest(**kwargs):
        captured.append(kwargs)
        return {"uuid": "n/a"}

    import knowledge.pipeline

    monkeypatch.setattr(knowledge.pipeline, "ingest", _fake_ingest, raising=False)

    first = static_ingestion._ingest_oracle_open_loops(_open_loop_source())
    second = static_ingestion._ingest_oracle_open_loops(_open_loop_source())

    assert first == (1, 0, 0)
    assert second == (1, 0, 0)
    assert captured[0]["content"] == captured[1]["content"]
    assert captured[0]["note_type"] == "task"
    assert "ship phase 4" in captured[0]["content"]
