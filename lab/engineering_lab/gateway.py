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
        #: provider -> concrete inference adapter (GATE L1). Empty until bound.
        self._adapters: dict[str, ModelAdapter] = {}

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

    # -- GATE L1: generation boundary ----------------------------------------

    def register_adapter(self, provider: str, adapter: "ModelAdapter") -> None:
        """Bind a provider to a concrete inference adapter."""
        if provider not in CONFIG_CLASSES:
            raise ValueError(f"unknown provider '{provider}'")
        self._adapters[provider] = adapter

    def generate(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **options: Any,
    ) -> "ModelResponse":
        """Run one inference turn against *provider*.

        This is the first real call the gateway makes — previously it only
        described models. If no adapter is bound the call fails closed with
        ``ModelUnavailable`` rather than fabricating a response; the caller must
        treat the run as blocked, never silently substitute output.
        """
        adapter = self._adapters.get(provider)
        if adapter is None:
            raise ModelUnavailable(
                f"no inference adapter bound for provider '{provider}'; "
                "the gateway describes models but cannot call them"
            )
        return adapter.generate(model=model, messages=messages, tools=tools, **options)


class ModelUnavailable(RuntimeError):
    """Raised when generation is requested but no adapter can serve it."""


@dataclass
class ModelResponse:
    """One model turn. ``tool_calls`` empty means the model produced text only."""

    provider: str
    model: str
    text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
            "tool_calls": self.tool_calls,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
        }


class ModelAdapter:
    """Inference adapter contract. Stateless; the loop owns no provider detail."""

    provider: str = ""

    def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **options: Any,
    ) -> ModelResponse:  # pragma: no cover - interface
        raise NotImplementedError


class OllamaAdapter(ModelAdapter):
    """Local-first adapter against an Ollama/OpenAI-compatible endpoint.

    Sends to ``/api/chat``. Network access is confined to the configured local
    base URL; nothing here reaches a remote cloud provider.
    """

    provider = "ollama"

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or os.environ.get("OLLAMA_HOST")
            or "http://localhost:11434"
        )
        self._timeout = timeout

    def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **options: Any,
    ) -> ModelResponse:
        body: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if tools:
            body["tools"] = tools
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self._base_url.rstrip("/") + "/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ModelUnavailable(f"local inference call failed: {exc}") from exc

        message = payload.get("message", {}) or {}
        raw_calls = message.get("tool_calls") or []
        tool_calls = [
            {
                "name": (call.get("function") or {}).get("name", ""),
                "arguments": (call.get("function") or {}).get("arguments", {}) or {},
            }
            for call in raw_calls
        ]
        return ModelResponse(
            provider=self.provider,
            model=model,
            text=message.get("content", "") or "",
            tool_calls=tool_calls,
            finish_reason=payload.get("done_reason", "stop"),
            usage={
                "prompt_eval_count": payload.get("prompt_eval_count"),
                "eval_count": payload.get("eval_count"),
            },
        )


_GLOBAL_GATEWAY: ModelGateway | None = None


def get_gateway() -> ModelGateway:
    global _GLOBAL_GATEWAY
    if _GLOBAL_GATEWAY is None:
        _GLOBAL_GATEWAY = ModelGateway()
    return _GLOBAL_GATEWAY


def describe_gateway() -> dict[str, Any]:
    """JSON-safe gateway description for the Lab surface."""
    return get_gateway().to_dict()
