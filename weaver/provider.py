"""WEAVER-K2 — governed provider orchestration for Weaver.

Authorization remains PassSpec/K0.1. This module only invokes models.
It must never write files, commit, or push.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .logger import get_logger

LOGGER = get_logger()


class ProviderOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILURE = "AUTH_FAILURE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    TIMEOUT = "TIMEOUT"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


@dataclass
class ProviderRequest:
    provider: str
    prompt: str
    model: str | None = None
    max_key_attempts: int = 4


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
    # redact query keys and long hex/base64-ish secrets
    msg = re.sub(r"(key=)([A-Za-z0-9_\-]{8,})", r"\1***", msg, flags=re.I)
    msg = re.sub(r"\b(AIza[0-9A-Za-z\-_]{10,})\b", "***", msg)
    msg = re.sub(r"\b(sk-[A-Za-z0-9]{10,})\b", "***", msg)
    return msg


def list_available_providers() -> list[str]:
    return ["gemini", "openai", "claude", "deepseek", "local"]


def invoke_provider(req: ProviderRequest) -> ProviderResult:
    """Dispatch a model call. Never mutates the repository."""
    name = (req.provider or "gemini").strip().lower()
    if name not in list_available_providers():
        return ProviderResult(
            outcome=ProviderOutcome.CONFIGURATION_ERROR,
            provider=name,
            error=f"unknown provider: {name}",
        )
    if not (req.prompt or "").strip():
        return ProviderResult(
            outcome=ProviderOutcome.INVALID_REQUEST,
            provider=name,
            error="empty prompt",
        )

    if name == "gemini":
        return _invoke_gemini(req)
    # Other providers: reuse weaver.llm call path without key pool
    try:
        from . import llm as llm_mod

        fn = getattr(llm_mod, name, None)
        if not callable(fn):
            return ProviderResult(
                outcome=ProviderOutcome.PROVIDER_UNAVAILABLE,
                provider=name,
                error=f"provider function missing: {name}",
            )
        text = fn(req.prompt)
        return ProviderResult(
            outcome=ProviderOutcome.SUCCESS,
            text=text or "",
            provider=name,
            attempts=1,
        )
    except Exception as e:
        return ProviderResult(
            outcome=ProviderOutcome.UNKNOWN_FAILURE,
            provider=name,
            error=_mask_secrets(str(e)),
            attempts=1,
        )


def _invoke_gemini(req: ProviderRequest) -> ProviderResult:
    """Gemini via api.key_pool acquire/report when available."""
    import time
    import requests

    MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
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
                text=text or "",
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

    # exhausted
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
