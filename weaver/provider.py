"""WEAVER-K2 — governed provider orchestration for Weaver.

Authorization remains PassSpec/K0.1. This module only invokes models.
It must never write files, commit, or push.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

from .logger import get_logger
from .routing import RoutingMetadata, select_task_provider

LOGGER = get_logger()


class ProviderOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILURE = "AUTH_FAILURE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    TIMEOUT = "TIMEOUT"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


@dataclass
class ProviderRequest:
    # "auto" activates the additive routing policy. Named providers retain
    # explicit-provider semantics and are never silently rerouted.
    provider: str = "auto"
    prompt: str = ""
    model: str | None = None
    max_key_attempts: int = 4
    task_type: str = "general"
    required_capabilities: tuple[str, ...] = ("chat",)
    routing_policy: str = "auto"
    queue_load: Mapping[str, int] = field(default_factory=dict)


@dataclass
class ProviderResult:
    outcome: ProviderOutcome
    text: str = ""
    provider: str = ""
    attempts: int = 0
    error: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.outcome == ProviderOutcome.SUCCESS


def _mask_secrets(msg: str) -> str:
    """Redact long token-like substrings from error strings."""
    import re

    if not msg:
        return msg
    msg = re.sub(r"(key=)([A-Za-z0-9_\-]{8,})", r"\1***", msg, flags=re.I)
    msg = re.sub(r"\b(AIza[0-9A-Za-z\-_]{10,})\b", "***", msg)
    msg = re.sub(r"\b(sk-[A-Za-z0-9]{10,})\b", "***", msg)
    return msg


def list_available_providers() -> list[str]:
    return ["gemini", "openai", "claude", "deepseek", "local"]


def _route(req: ProviderRequest) -> tuple[str | None, dict[str, Any]]:
    requested = (req.provider or "auto").strip().lower()
    if requested != "auto":
        return requested, {"routing": "explicit", "requested_provider": requested}

    selected = select_task_provider(
        RoutingMetadata(
            task_type=req.task_type,
            required_capabilities=tuple(req.required_capabilities or ("chat",)),
            routing_policy=req.routing_policy,
            queue_load=req.queue_load,
        )
    )
    if selected is None:
        return None, {
            "routing": "auto",
            "requested_provider": "auto",
            "routing_reason": "no eligible authenticated provider",
        }
    return selected.name, {
        "routing": "auto",
        "requested_provider": "auto",
        "routing_reason": "capability/task-affinity/queue-load policy",
    }


def invoke_provider(req: ProviderRequest) -> ProviderResult:
    """Dispatch a model call. Never mutates the repository."""
    requested = (req.provider or "auto").strip().lower()
    if requested != "auto" and requested not in list_available_providers():
        return ProviderResult(
            outcome=ProviderOutcome.CONFIGURATION_ERROR,
            provider=requested,
            error=f"unknown provider: {requested}",
        )
    if not (req.prompt or "").strip():
        return ProviderResult(
            outcome=ProviderOutcome.INVALID_REQUEST,
            provider=requested,
            error="empty prompt",
        )

    name, route_meta = _route(req)
    if not name:
        return ProviderResult(
            outcome=ProviderOutcome.PROVIDER_UNAVAILABLE,
            provider="",
            error="no eligible authenticated provider",
            meta=route_meta,
        )

    # Gemini deliberately retains the K2 key-pool path. Routing changes which
    # provider is selected, not how Gemini credentials are acquired/rotated.
    if name == "gemini":
        result = _invoke_gemini(req)
        result.meta.update(route_meta)
        return result

    # All other providers are dispatched through the canonical provider
    # registry, eliminating the old weaver.llm callable-name dependency.
    try:
        from providers.base import ProviderMessage
        from providers.router import get_provider

        adapter = get_provider(name)
        if adapter is None or not adapter.authenticate():
            return ProviderResult(
                outcome=ProviderOutcome.PROVIDER_UNAVAILABLE,
                provider=name,
                error=f"provider unavailable: {name}",
                meta=route_meta,
            )

        messages = [ProviderMessage("user", req.prompt)]
        response = adapter.send(messages, max_tokens=2048)
        text = (response.content or "").strip()
        if not text:
            return ProviderResult(
                outcome=ProviderOutcome.INVALID_RESPONSE,
                provider=name,
                attempts=1,
                error="provider returned empty response",
                meta=route_meta,
            )
        return ProviderResult(
            outcome=ProviderOutcome.SUCCESS,
            text=response.content,
            provider=name,
            attempts=1,
            meta={**route_meta, "model": response.model},
        )
    except Exception as e:
        return ProviderResult(
            outcome=ProviderOutcome.UNKNOWN_FAILURE,
            provider=name,
            error=_mask_secrets(str(e)),
            attempts=1,
            meta=route_meta,
        )


def _invoke_gemini(req: ProviderRequest) -> ProviderResult:
    """Gemini via api.key_pool acquire/report when available."""
    import time
    import requests

    MODEL = req.model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    BASE_URL = "https://generativelanguage.googleapis.com/v1"
    TIMEOUT = int(os.environ.get("WEAVER_PROVIDER_TIMEOUT", "180"))

    acquire: Callable[[], str] | None = None
    report_failure: Callable[..., Any] | None = None
    report_success: Callable[..., Any] | None = None
    try:
        from api.key_pool import acquire_key, report_failure as rf, report_success as rs

        acquire = acquire_key
        report_failure = rf
        report_success = rs
    except Exception:
        acquire = None

    def env_key() -> str:
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

    attempts = 0
    last_error = ""
    max_attempts = max(1, int(req.max_key_attempts))

    while attempts < max_attempts:
        attempts += 1
        key = ""
        try:
            if acquire:
                key = acquire() or ""
            if not key:
                key = env_key()
        except Exception as e:
            last_error = _mask_secrets(str(e))
            return ProviderResult(
                outcome=ProviderOutcome.CONFIGURATION_ERROR,
                provider="gemini",
                attempts=attempts,
                error=last_error or "no key available",
            )
        if not key:
            return ProviderResult(
                outcome=ProviderOutcome.CONFIGURATION_ERROR,
                provider="gemini",
                attempts=attempts,
                error="no Gemini API key available",
            )

        endpoint = f"{BASE_URL}/models/{MODEL}:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": req.prompt}]}]}
        try:
            r = requests.post(
                endpoint,
                json=payload,
                timeout=TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
        except requests.exceptions.Timeout:
            last_error = "timeout"
            if report_failure:
                try:
                    report_failure(key)
                except Exception:
                    pass
            continue
        except requests.exceptions.RequestException as e:
            last_error = _mask_secrets(str(e))
            if report_failure:
                try:
                    report_failure(key)
                except Exception:
                    pass
            continue

        if r.status_code == 200:
            try:
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if not str(text).strip():
                    raise ValueError("empty response")
            except Exception:
                last_error = "malformed response"
                continue
            if report_success:
                try:
                    report_success(key)
                except Exception:
                    pass
            return ProviderResult(
                outcome=ProviderOutcome.SUCCESS,
                text=text,
                provider="gemini",
                attempts=attempts,
            )

        if r.status_code == 429:
            last_error = "rate limited"
            if report_failure:
                try:
                    report_failure(key)
                except Exception:
                    pass
            time.sleep(0.05)
            continue
        if r.status_code in (401, 403):
            last_error = f"auth failure {r.status_code}"
            if report_failure:
                try:
                    report_failure(key)
                except Exception:
                    pass
            return ProviderResult(
                outcome=ProviderOutcome.AUTH_FAILURE,
                provider="gemini",
                attempts=attempts,
                error=last_error,
            )

        last_error = f"status {r.status_code}"
        if report_failure:
            try:
                report_failure(key)
            except Exception:
                pass

    outcome = ProviderOutcome.RATE_LIMITED if "rate" in last_error else ProviderOutcome.PROVIDER_UNAVAILABLE
    return ProviderResult(
        outcome=outcome,
        provider="gemini",
        attempts=attempts,
        error=_mask_secrets(last_error) or "all keys exhausted",
    )


def call_llm_governed(provider: str, prompt: str) -> str:
    """Compatibility wrapper: raises on failure (like legacy call_llm)."""
    result = invoke_provider(ProviderRequest(provider=provider, prompt=prompt))
    if not result.ok:
        raise RuntimeError(f"provider {result.provider} failed: {result.outcome.value}: {result.error}")
    return result.text
