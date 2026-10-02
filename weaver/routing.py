"""Task-aware provider routing policy for the governed Weaver boundary.

This module is deterministic and side-effect free. It selects only among
providers exposed by the existing providers/router registry. It does not
perform authorization, write files, or execute provider calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

from providers.base import BaseProvider
from providers.router import get_provider


@dataclass(frozen=True)
class RoutingMetadata:
    task_type: str = "general"
    required_capabilities: tuple[str, ...] = ("chat",)
    routing_policy: str = "auto"
    queue_load: Mapping[str, int] = field(default_factory=dict)


# Affinity is a routing preference only. It is not a claim about model quality.
_TASK_AFFINITY: dict[str, tuple[str, ...]] = {
    "coding": ("deepseek", "local", "gpt", "claude", "gemini"),
    "reasoning": ("deepseek", "claude", "gemini", "gpt", "local"),
    "vision": ("gemini", "claude", "gpt", "local", "deepseek"),
    "extraction": ("local", "deepseek", "gemini", "claude", "gpt"),
    "general": ("gemini", "claude", "gpt", "deepseek", "local"),
}


def _names() -> tuple[str, ...]:
    # Keep this aligned with the existing registry rather than introducing a
    # second provider catalogue.
    return ("gemini", "claude", "gpt", "deepseek", "local")


def select_task_provider(
    metadata: RoutingMetadata,
    preferred: Optional[str] = None,
) -> Optional[BaseProvider]:
    """Select an authenticated registry provider deterministically.

    Explicit preference is honored when it is eligible. Auto routing scores
    only declared capability, task affinity, and supplied provider queue load.
    """
    required = tuple(metadata.required_capabilities or ("chat",))
    policy = (metadata.routing_policy or "auto").strip().lower()

    if policy == "explicit":
        if not preferred:
            return None
        provider = get_provider(preferred.strip().lower())
        if provider and provider.authenticate() and all(
            cap in provider.capabilities() for cap in required
        ):
            return provider
        return None

    candidates: list[tuple[int, int, int, str, BaseProvider]] = []
    affinity = _TASK_AFFINITY.get(
        (metadata.task_type or "general").strip().lower(),
        _TASK_AFFINITY["general"],
    )
    affinity_rank = {name: i for i, name in enumerate(affinity)}
    queue_load = metadata.queue_load or {}

    for name in _names():
        provider = get_provider(name)
        if provider is None:
            continue
        try:
            if not provider.authenticate():
                continue
            capabilities = provider.capabilities()
        except Exception:
            continue
        if not all(cap in capabilities for cap in required):
            continue

        load = max(0, int(queue_load.get(name, 0)))
        # Lower queue load wins, then task affinity, then stable registry order.
        candidates.append((load, affinity_rank.get(name, len(affinity)), _names().index(name), name, provider))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[:4])
    return candidates[0][4]
