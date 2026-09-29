"""Project-scoped embedding provider seam.

This module defines the adapter boundary without inventing a live provider.
The default provider is explicit NOT_AVAILABLE until a real provider is bound.
Embeddings remain contextual data and never authorize execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class EmbeddingResult:
    status: str
    vectors: list[list[float]] | None
    provider: str | None
    dimensions: int | None
    note: str


class EmbeddingProvider(Protocol):
    """Minimal adapter contract for a project-scoped embedding provider."""

    def embed(self, texts: Sequence[str], *, project_id: str) -> EmbeddingResult:
        ...

    def describe(self, *, project_id: str) -> dict[str, object]:
        ...


class UnavailableEmbeddingProvider:
    """Honest default until a concrete provider is configured."""

    def embed(self, texts: Sequence[str], *, project_id: str) -> EmbeddingResult:
        del texts, project_id
        return EmbeddingResult(
            status="NOT_AVAILABLE",
            vectors=None,
            provider=None,
            dimensions=None,
            note="No project-scoped embedding provider is configured.",
        )

    def describe(self, *, project_id: str) -> dict[str, object]:
        return {
            "status": "NOT_AVAILABLE",
            "provider": None,
            "coverage": None,
            "dimensions": None,
            "project_id": project_id,
            "note": "No project-scoped embedding provider is configured.",
        }


_default_provider: EmbeddingProvider = UnavailableEmbeddingProvider()


def configure_embedding_provider(provider: EmbeddingProvider | None) -> None:
    """Bind an explicit provider adapter; None restores the honest default."""
    global _default_provider
    _default_provider = provider or UnavailableEmbeddingProvider()


def get_embedding_provider() -> EmbeddingProvider:
    return _default_provider
