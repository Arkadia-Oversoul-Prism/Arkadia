"""
Arkadia Knowledge OS — Provider Router
=======================================
Selects and dispatches to the correct provider adapter.
Business logic NEVER leaks into provider adapters.
The rest of Arkadia never depends on provider-specific behaviour.
Adding a new provider = implement BaseProvider + register here. That's all.
"""

import os
from typing import Optional

from providers.base import BaseProvider, ProviderMessage, ProviderResponse
from providers.gemini import GeminiProvider
from providers.claude import ClaudeProvider
from providers.gpt import GPTProvider
from providers.deepseek import DeepSeekProvider
from providers.local import LocalLLMProvider


# ─────────────────────────────────────────────────────────────────────────────
# Provider registry — ordered by priority (lower = higher priority)
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, BaseProvider] = {}
_INITIALISED = False


def _init_registry() -> None:
    global _INITIALISED
    if _INITIALISED:
        return
    _REGISTRY["gemini"]   = GeminiProvider(model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"))
    _REGISTRY["claude"]   = ClaudeProvider(model=os.environ.get("CLAUDE_MODEL", "claude-opus-4-5"))
    _REGISTRY["gpt"]      = GPTProvider(model=os.environ.get("GPT_MODEL", "gpt-4o"))
    _REGISTRY["deepseek"] = DeepSeekProvider(model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"))
    _REGISTRY["local"]    = LocalLLMProvider(model=os.environ.get("LOCAL_LLM_MODEL", "llama3"))
    _INITIALISED = True


def get_provider(name: str) -> Optional[BaseProvider]:
    _init_registry()
    return _REGISTRY.get(name)


def list_providers() -> list[dict]:
    _init_registry()
    return [
        {
            "name": name,
            "display_name": provider.display_name,
            "capabilities": provider.capabilities(),
            "authenticated": provider.authenticate(),
        }
        for name, provider in _REGISTRY.items()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Auto-selection
# ─────────────────────────────────────────────────────────────────────────────

# Priority order for auto-selection (matches DB priority column)
_PRIORITY_ORDER = ["gemini", "claude", "gpt", "deepseek", "local"]


def select_provider(
    required_capabilities: Optional[list[str]] = None,
    preferred: Optional[str] = None,
) -> Optional[BaseProvider]:
    """
    Select the best available provider:
    1. If preferred is specified and can satisfy required_capabilities, use it.
    2. Otherwise walk _PRIORITY_ORDER, return first authenticated match.
    """
    _init_registry()
    required_capabilities = required_capabilities or ["chat"]

    if preferred and preferred in _REGISTRY:
        p = _REGISTRY[preferred]
        if p.authenticate() and all(c in p.capabilities() for c in required_capabilities):
            return p

    for name in _PRIORITY_ORDER:
        if name not in _REGISTRY:
            continue
        provider = _REGISTRY[name]
        if not provider.authenticate():
            continue
        if all(c in provider.capabilities() for c in required_capabilities):
            return provider

    return None


# ─────────────────────────────────────────────────────────────────────────────
# High-level send (used by Oracle, Kernel, and API routes)
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
    messages: list of {"role": "user"|"assistant"|"system", "content": str}
    """
    if persona_name and not system_prompt:
        system_prompt = _resolve_persona_prompt(persona_name)

    provider = select_provider(preferred=provider_name)
    if not provider:
        raise RuntimeError(
            "No authenticated AI provider available. "
            "Set at least one of: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, "
            "or start Ollama locally."
        )

    canonical_msgs = [ProviderMessage(m["role"], m["content"]) for m in messages]
    return provider.send(canonical_msgs, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)


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
        try:
            h = provider.health()
        except Exception as e:
            h = {"status": "error", "model": "unknown", "latency_ms": 0, "reason": str(e)}
        h["provider"] = name
        results.append(h)
    return results
