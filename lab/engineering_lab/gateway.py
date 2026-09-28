"""EL-08 — pluggable Model Gateway.

A provider-neutral boundary for model selection. The Engineering Lab is never
hard-coded to one provider. Selection is observable per run: provider, model,
configuration class, and usage are recorded on the run.

Truthfulness rules (directive section 11):

  * A provider that is not configured is reported ``UNCONFIGURED`` or
    ``UNAVAILABLE`` — never as available.
  * For local runtimes (Ollama, llama.cpp, OpenAI-compatible local endpoints)
    the gateway probes reachability and reports the real result.
  * A model is not claimed "free" merely because a provider offers a free tier.

The gateway *selects and records*. It does not grant execution authority.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .contracts import utc_now

#: Provider families the gateway knows how to describe.
LOCAL_PROVIDERS: tuple[str, ...] = (
    "ollama",
    "llama_cpp",
    "openai_compatible_local",
)
REMOTE_PROVIDERS: tuple[str, ...] = (
    "gemini",
    "openai_compatible",
    "anthropic_compatible",
)
AGENT_PROVIDERS: tuple[str, ...] = (
    "native_arkadia_agent",
    "openhands_compatible",
    "acp_compatible",
)

#: Configuration classes. Recorded per run for observability.
CONFIG_CLASSES: dict[str, str] = {
    "ollama": "LOCAL",
    "llama_cpp": "LOCAL",
    "openai_compatible_local": "LOCAL",
    "gemini": "REMOTE",
    "openai_compatible": "REMOTE",
    "anthropic_compatible": "REMOTE",
    "native_arkadia_agent": "AGENT_RUNTIME",
    "openhands_compatible": "AGENT_RUNTIME",
    "acp_compatible": "AGENT_RUNTIME",
}

#: Environment variables that, when present, indicate a provider is configured.
_PROVIDER_ENV: dict[str, tuple[str, ...]] = {
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "openai_compatible": ("OPENAI_API_KEY",),
    "anthropic_compatible": ("ANTHROPIC_API_KEY",),
    "openai_compatible_local": ("LOCAL_MODEL_BASE_URL", "OLLAMA_BASE_URL"),
    "ollama": ("OLLAMA_BASE_URL", "OLLAMA_HOST"),
    "llama_cpp": ("LLAMA_CPP_BASE_URL",),
}


@dataclass(frozen=True)
class ModelDescriptor:
    """A selectable model + its honest configuration status."""

    provider: str
    model: str
    config_class: str
    configured: bool
    status: str  # AVAILABLE | UNCONFIGURED | UNAVAILABLE
    detail: str = ""
    cost_note: str = "cost not asserted; provider tiers are not assumed free"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "config_class": self.config_class,
            "configured": self.configured,
            "status": self.status,
            "detail": self.detail,
            "cost_note": self.cost_note,
        }


@dataclass
class ModelSelection:
    """The observable record of a model choice for a run."""

    provider: str
    model: str
    config_class: str
    status: str
    selected_at: str = field(default_factory=utc_now)
    usage: dict[str, Any] = field(default_factory=dict)
    fallback_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "config_class": self.config_class,
            "status": self.status,
            "selected_at": self.selected_at,
            "usage": self.usage,
            "fallback_from": self.fallback_from,
        }


def _env_configured(provider: str) -> bool:
    return any(os.environ.get(var) for var in _PROVIDER_ENV.get(provider, ()))


def _probe_local(base_url: str, timeout: float = 0.75) -> tuple[bool, str]:
    """Best-effort reachability probe for a local endpoint."""
    for path in ("/api/tags", "/v1/models", "/health"):
        try:
            req = urllib.request.Request(base_url.rstrip("/") + path)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if 200 <= resp.status < 300:
                    return True, f"reachable via {path}"
        except urllib.error.HTTPError:
            # Endpoint responded (even with an error status) => host is reachable.
            return True, f"host reachable via {path}"
        except Exception:
            continue
    return False, "unreachable"


class ModelGateway:
    """Provider-neutral model gateway with truthful configuration reporting."""

    def __init__(self, registry: dict[str, str] | None = None) -> None:
        #: provider -> default model name (implementation artifacts, not normative)
        self._models: dict[str, str] = {
            "gemini": "gemini-1.5-flash",
            "openai_compatible": "gpt-4o",
            "anthropic_compatible": "claude-3-haiku-20240307",
            "ollama": os.environ.get("OLLAMA_MODEL", "llama3"),
            "llama_cpp": "local",
            "openai_compatible_local": "local",
            "native_arkadia_agent": "arkadia-native",
            "openhands_compatible": "openhands",
            "acp_compatible": "acp",
        }
        if registry:
            self._models.update(registry)

    def describe(self, provider: str) -> ModelDescriptor:
        if provider not in CONFIG_CLASSES:
            raise ValueError(f"unknown provider '{provider}'")
        model = self._models.get(provider, "unknown")
        config_class = CONFIG_CLASSES[provider]
        if provider in ("ollama", "llama_cpp", "openai_compatible_local"):
            base = (
                os.environ.get("OLLAMA_BASE_URL")
                or os.environ.get("OLLAMA_HOST")
                or os.environ.get("LLAMA_CPP_BASE_URL")
                or os.environ.get("LOCAL_MODEL_BASE_URL")
            )
            if not base:
                return ModelDescriptor(
                    provider,
                    model,
                    config_class,
                    configured=False,
                    status="UNCONFIGURED",
                    detail="no local endpoint environment variable set",
                )
            reachable, detail = _probe_local(base)
            return ModelDescriptor(
                provider,
                model,
                config_class,
                configured=reachable,
                status="AVAILABLE" if reachable else "UNAVAILABLE",
                detail=detail,
            )
        if provider in ("native_arkadia_agent", "openhands_compatible", "acp_compatible"):
            # Agent runtimes are described but not probed here; a run must be
            # explicitly configured to use one.
            return ModelDescriptor(
                provider,
                model,
                config_class,
                configured=False,
                status="UNCONFIGURED",
                detail="agent runtime requires explicit per-run configuration",
            )
        configured = _env_configured(provider)
        return ModelDescriptor(
            provider,
            model,
            config_class,
            configured=configured,
            status="AVAILABLE" if configured else "UNCONFIGURED",
            detail="api key present" if configured else "no api key in environment",
        )

    def catalog(self) -> list[dict[str, Any]]:
        return [self.describe(p).to_dict() for p in CONFIG_CLASSES]

    def select(
        self, *, preferred: str | None = None, required_class: str | None = None
    ) -> ModelSelection:
        """Select a configured model, honestly reporting unavailability.

        Selection never fabricates availability. If nothing is configured the
        result status is ``UNAVAILABLE`` and the caller must treat model work as
        blocked — not silently substitute a stub.
        """
        candidates: list[str]
        if preferred:
            candidates = [preferred]
        elif required_class:
            candidates = [p for p, c in CONFIG_CLASSES.items() if c == required_class]
        else:
            candidates = list(CONFIG_CLASSES)

        fallback_from = preferred if preferred else None
        for provider in candidates:
            desc = self.describe(provider)
            if desc.configured and desc.status == "AVAILABLE":
                return ModelSelection(
                    provider=desc.provider,
                    model=desc.model,
                    config_class=desc.config_class,
                    status="AVAILABLE",
                    fallback_from=fallback_from if provider != preferred else None,
                )
        return ModelSelection(
            provider=preferred or "none",
            model=self._models.get(preferred or "", "none"),
            config_class=CONFIG_CLASSES.get(preferred or "", "UNKNOWN"),
            status="UNAVAILABLE",
            fallback_from=fallback_from,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_providers": list(LOCAL_PROVIDERS),
            "remote_providers": list(REMOTE_PROVIDERS),
            "agent_providers": list(AGENT_PROVIDERS),
            "catalog": self.catalog(),
        }


_GLOBAL_GATEWAY: ModelGateway | None = None


def get_gateway() -> ModelGateway:
    global _GLOBAL_GATEWAY
    if _GLOBAL_GATEWAY is None:
        _GLOBAL_GATEWAY = ModelGateway()
    return _GLOBAL_GATEWAY


def describe_gateway() -> dict[str, Any]:
    """JSON-safe gateway description for the Lab surface."""
    return get_gateway().to_dict()
