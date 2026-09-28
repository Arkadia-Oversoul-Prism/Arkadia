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
        assert repo_root in source["root"].resolve().parents, source["source_provider"]
