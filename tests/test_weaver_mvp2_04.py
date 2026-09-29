"""MVP2-04 — project-scoped embedding provider seam."""
from __future__ import annotations

from solspire.embedding_provider import (
    EmbeddingResult,
    configure_embedding_provider,
    get_embedding_provider,
)
from solspire.project_knowledge import build_knowledge_summary


class FakeEmbeddingProvider:
    def embed(self, texts, *, project_id):
        return EmbeddingResult(
            status="AVAILABLE",
            vectors=[[0.1, 0.2] for _ in texts],
            provider="test-fixture",
            dimensions=2,
            note="deterministic test provider",
        )

    def describe(self, *, project_id):
        return {
            "status": "AVAILABLE",
            "provider": "test-fixture",
            "coverage": "fixture",
            "dimensions": 2,
            "project_id": project_id,
            "note": "deterministic test provider",
        }


def test_default_embedding_state_is_honestly_unavailable():
    configure_embedding_provider(None)
    state = get_embedding_provider().describe(project_id="p-mvp204")
    assert state["status"] == "NOT_AVAILABLE"
    assert state["provider"] is None
    assert state["dimensions"] is None
    assert state["coverage"] is None


def test_provider_can_be_injected_without_authorizing_execution():
    configure_embedding_provider(FakeEmbeddingProvider())
    try:
        state = build_knowledge_summary("p-mvp204", embedding_provider=get_embedding_provider())
        assert state["embeddings"]["status"] == "AVAILABLE"
        assert state["embeddings"]["provider"] == "test-fixture"
        assert state["authorization"]["Execution"] == "LOCKED"
        result = get_embedding_provider().embed(["hello"], project_id="p-mvp204")
        assert result.status == "AVAILABLE"
        assert result.vectors == [[0.1, 0.2]]
    finally:
        configure_embedding_provider(None)


def test_embedding_seam_does_not_claim_semantic_graph_or_authority():
    configure_embedding_provider(None)
    state = build_knowledge_summary("p-mvp204")
    assert state["authorization"]["PassSpec"] == "NONE"
    assert state["authorization"]["PatchApproval"] == "NONE"
    assert state["authorization"]["Execution"] == "LOCKED"
