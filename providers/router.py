"""
Arkadia Knowledge OS — Provider Router
=======================================
Selects and dispatches to the correct provider adapter.
Business logic NEVER leaks into provider adapters.
The rest of Arkadia never depends on provider-specific behaviour.
Adding a new provider = implement BaseProvider + register here.
"""

import json
import os
from typing import Optional

from providers.base import BaseProvider, ProviderMessage, ProviderResponse
from providers.gemini import GeminiProvider


# ─────────────────────────────────────────────────────────────────────────────
# Provider registry
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, BaseProvider] = {}
_INITIALISED = False


def _init_registry() -> None:
    global _INITIALISED
    if _INITIALISED:
        return
    # Register all available providers
    # Future providers: add an import + register call here only
    _REGISTRY["gemini"] = GeminiProvider(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    )
    # Placeholder stubs — replace with real adapters when implementing
    # _REGISTRY["claude"]   = ClaudeProvider()
    # _REGISTRY["gpt"]      = GPTProvider()
    # _REGISTRY["deepseek"] = DeepSeekProvider()
    # _REGISTRY["grok"]     = GrokProvider()
    # _REGISTRY["local"]    = LocalLLMProvider()
    _INITIALISED = True


def get_provider(name: str) -> Optional[BaseProvider]:
    _init_registry()
    return _REGISTRY.get(name)


def list_providers() -> list[dict]:
    _init_registry()
    result = []
    for name, provider in _REGISTRY.items():
        result.append({
            "name": name,
            "display_name": provider.display_name,
            "capabilities": provider.capabilities(),
            "authenticated": provider.authenticate(),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Auto-selection
# ─────────────────────────────────────────────────────────────────────────────

def select_provider(
    required_capabilities: Optional[list[str]] = None,
    preferred: Optional[str] = None,
) -> Optional[BaseProvider]:
    """
    Select the best available provider:
    1. If preferred is specified and available, use it.
    2. Otherwise, select the first authenticated provider that satisfies required_capabilities.
    Priority order matches the `providers` table priority column.
    """
    _init_registry()
    required_capabilities = required_capabilities or ["chat"]

    if preferred and preferred in _REGISTRY:
        p = _REGISTRY[preferred]
        if p.authenticate():
            caps = p.capabilities()
            if all(c in caps for c in required_capabilities):
                return p

    for name, provider in _REGISTRY.items():
        if not provider.authenticate():
            continue
        caps = provider.capabilities()
        if all(c in caps for c in required_capabilities):
            return provider

    return None


# ─────────────────────────────────────────────────────────────────────────────
# High-level send (used by Oracle and Kernel)
# ─────────────────────────────────────────────────────────────────────────────

def send(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    persona_name: Optional[str] = None,
    provider_name: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> ProviderResponse:
    """
    High-level send. Resolves persona system prompt, selects provider, dispatches.
    messages: list of {"role": "user"|"assistant", "content": str}
    """
    # Resolve persona system prompt
    if persona_name and not system_prompt:
        system_prompt = _resolve_persona_prompt(persona_name)

    provider = select_provider(preferred=provider_name)
    if not provider:
        raise RuntimeError("No authenticated provider available. Configure at least one provider API key.")

    canonical_msgs = [ProviderMessage(m["role"], m["content"]) for m in messages]

    return provider.send(
        canonical_msgs,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _resolve_persona_prompt(persona_name: str) -> Optional[str]:
    try:
        from knowledge.db import execute_one
        row = execute_one("SELECT system_prompt FROM personas WHERE name = ?", (persona_name,))
        return row["system_prompt"] if row else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Health check (all registered providers)
# ─────────────────────────────────────────────────────────────────────────────

def health_all() -> list[dict]:
    _init_registry()
    results = []
    for name, provider in _REGISTRY.items():
        h = provider.health()
        h["provider"] = name
        results.append(h)
    return results
