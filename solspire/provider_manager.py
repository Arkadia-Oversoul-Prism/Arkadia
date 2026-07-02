"""SolSpire Console — ProviderManager (Milestone 1).

Single interface for all LLM providers. Milestone 1 ships Gemini as the
only real provider; stubs for OpenAI / Anthropic / Ollama keep the
interface stable so Phase 2 can swap them in without touching callers.

Contract:
    manager = ProviderManager()
    manager.select_provider("gemini")
    result = manager.invoke_model("What is sacred geometry?", context={})
    providers = manager.list_providers()
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("solspire.provider_manager")

_PROVIDERS = ["gemini", "openai", "anthropic", "openrouter", "ollama"]
_DEFAULT = "gemini"


class ProviderManager:
    def __init__(self) -> None:
        self._active: str = _DEFAULT
        self._token_usage: dict[str, int] = {p: 0 for p in _PROVIDERS}

    def select_provider(self, name: str) -> None:
        if name not in _PROVIDERS:
            raise ValueError(f"Unknown provider '{name}'. Available: {_PROVIDERS}")
        self._active = name
        logger.info("ProviderManager: switched to '%s'", name)

    def list_providers(self) -> list[str]:
        return list(_PROVIDERS)

    def active_provider(self) -> str:
        return self._active

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        logger.info("ProviderManager.invoke_model provider=%s", self._active)

        if self._active == "gemini":
            return self._invoke_gemini(prompt, ctx)
        elif self._active in ("openai", "anthropic", "openrouter", "ollama"):
            return self._invoke_stub(prompt, ctx)
        else:
            raise ValueError(f"No handler for provider '{self._active}'")

    def token_usage(self) -> dict[str, int]:
        return dict(self._token_usage)

    def _invoke_gemini(self, prompt: str, context: dict[str, Any]) -> str:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            logger.warning("ProviderManager: GOOGLE_API_KEY not set — returning stub")
            return f"[Gemini stub] No API key. Prompt: {prompt[:120]}"
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_name = os.environ.get("SOLSPIRE_LLM_MODEL", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            system_prefix = ""
            if context:
                import json
                system_prefix = f"Context: {json.dumps(context, ensure_ascii=False)[:800]}\n\n"
            resp = model.generate_content(system_prefix + prompt)
            text = resp.text or ""
            self._token_usage["gemini"] += len(prompt.split()) + len(text.split())
            return text
        except Exception as exc:
            logger.error("ProviderManager Gemini error: %s", exc)
            return f"[Gemini error] {exc}"

    def _invoke_stub(self, prompt: str, context: dict[str, Any]) -> str:
        return (
            f"[{self._active.upper()} stub — Milestone 2] "
            f"Prompt received ({len(prompt)} chars). Context keys: {list(context.keys())}"
        )


_GLOBAL_MANAGER = ProviderManager()


def get_manager() -> ProviderManager:
    return _GLOBAL_MANAGER


__all__ = ["ProviderManager", "get_manager"]
