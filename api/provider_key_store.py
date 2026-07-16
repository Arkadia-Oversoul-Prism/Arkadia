"""Multi-provider API key store.

Stores one key per AI provider in data/provider_keys.json.
Each provider entry: {"key": "...", "label": "...", "added_at": "..."}

Providers: gemini, openai, claude, deepseek
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("arkadia.provider_key_store")

_DATA_DIR = os.environ.get("SOLSPIRE_DATA_DIR", "data")
_PATH = Path(_DATA_DIR) / "provider_keys.json"
_lock = threading.Lock()

# Env var fallbacks per provider (checked when no stored key exists)
_ENV_FALLBACKS: dict[str, list[str]] = {
    "gemini":   ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "openai":   ["OPENAI_API_KEY"],
    "claude":   ["ANTHROPIC_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
}

PROVIDERS = ["gemini", "openai", "claude", "deepseek"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    if _PATH.exists():
        try:
            with open(_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(store: dict[str, Any]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _mask(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def get_key(provider: str) -> Optional[str]:
    """Return the stored key for provider, or fall back to env vars.
    
    Skips keys marked as quota_hit, returning the next available key or env fallback.
    """
    with _lock:
        store = _load()
        entry = store.get(provider)
        if entry and entry.get("key"):
            # Skip if quota was hit - fall back to env vars instead
            if entry.get("quota_hit"):
                logger.info("[provider_key_store] %s key marked quota_hit, using env fallback", provider)
            else:
                return entry["key"]
    # env fallback
    for var in _ENV_FALLBACKS.get(provider, []):
        val = os.environ.get(var, "")
        if val:
            return val
    return None


def set_key(provider: str, key: str, label: str = "") -> dict:
    """Store a key for a provider. Overwrites any existing key."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    with _lock:
        store = _load()
        store[provider] = {
            "key": key,
            "label": label or f"{provider.capitalize()} Key",
            "added_at": _now(),
            "quota_hit": False,
        }
        _save(store)
    logger.info("[provider_key_store] set key for %s", provider)
    return {"provider": provider, "label": store[provider]["label"], "masked": _mask(key)}


def remove_key(provider: str) -> bool:
    """Remove the stored key for a provider."""
    with _lock:
        store = _load()
        if provider not in store:
            return False
        del store[provider]
        _save(store)
    logger.info("[provider_key_store] removed key for %s", provider)
    return True


def mark_quota_hit(provider: str) -> bool:
    """Mark a provider's key as quota-hit (rate limited). Falls back to env."""
    with _lock:
        store = _load()
        if provider not in store:
            return False
        store[provider]["quota_hit"] = True
        _save(store)
    logger.warning("[provider_key_store] %s key marked quota_hit", provider)
    return True


def reset_quota(provider: str) -> bool:
    """Reset quota-hit flag for a provider's key."""
    with _lock:
        store = _load()
        if provider not in store:
            return False
        store[provider]["quota_hit"] = False
        _save(store)
    logger.info("[provider_key_store] %s key quota reset", provider)
    return True


def list_keys() -> list[dict]:
    """List all stored provider keys (masked), plus which have env fallbacks."""
    with _lock:
        store = _load()
    result = []
    for provider in PROVIDERS:
        entry = store.get(provider)
        env_key = any(os.environ.get(v) for v in _ENV_FALLBACKS.get(provider, []))
        if entry and entry.get("key"):
            result.append({
                "provider": provider,
                "label": entry.get("label", ""),
                "masked": _mask(entry["key"]),
                "added_at": entry.get("added_at"),
                "source": "stored",
                "quota_hit": entry.get("quota_hit", False),
            })
        elif env_key:
            result.append({
                "provider": provider,
                "label": "Environment variable",
                "masked": "****env****",
                "added_at": None,
                "source": "env",
                "quota_hit": False,
            })
        else:
            result.append({
                "provider": provider,
                "label": None,
                "masked": None,
                "added_at": None,
                "source": "none",
                "quota_hit": False,
            })
    return result
