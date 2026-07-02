"""SolSpire Console — ProviderManager (Milestone 1, upgraded).

Multi-key support: multiple API keys per provider stored in data/provider_keys.json.
Auto-fallback: on quota/rate-limit errors, automatically rotates to the next key.
Manual switching: set active key or provider via the console UI.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger("solspire.provider_manager")

_PROVIDERS = ["gemini", "openai", "anthropic", "openrouter", "ollama"]
_DEFAULT_PROVIDER = "gemini"
_DEFAULT_MODELS: dict[str, str] = {
    "gemini":     "gemini-1.5-flash",
    "openai":     "gpt-4o",
    "anthropic":  "claude-3-haiku-20240307",
    "openrouter": "openai/gpt-4o-mini",
    "ollama":     "llama3",
}

_QUOTA_SIGNALS = ("quota", "rate", "limit", "429", "resource_exhausted", "too many requests")

_DATA_DIR = Path(__file__).parent.parent / "data"
_KEYS_FILE = _DATA_DIR / "provider_keys.json"


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(sig in msg for sig in _QUOTA_SIGNALS)


class ProviderManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._active_provider: str = _DEFAULT_PROVIDER
        self._token_usage: dict[str, int] = {p: 0 for p in _PROVIDERS}
        self._store: dict[str, Any] = self._load()

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        if _KEYS_FILE.exists():
            try:
                return json.loads(_KEYS_FILE.read_text())
            except Exception:
                pass
        return {"auto_fallback": True, "keys": [], "models": dict(_DEFAULT_MODELS)}

    def _save(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _KEYS_FILE.write_text(json.dumps(self._store, indent=2))

    # ── Provider selection ─────────────────────────────────────────────────

    def select_provider(self, name: str) -> None:
        if name not in _PROVIDERS:
            raise ValueError(f"Unknown provider '{name}'. Available: {_PROVIDERS}")
        with self._lock:
            self._active_provider = name
        logger.info("ProviderManager: switched provider to '%s'", name)

    def list_providers(self) -> list[str]:
        return list(_PROVIDERS)

    def active_provider(self) -> str:
        return self._active_provider

    def token_usage(self) -> dict[str, int]:
        return dict(self._token_usage)

    # ── Key management ────────────────────────────────────────────────────

    def add_key(self, provider: str, label: str, key_value: str) -> str:
        if provider not in _PROVIDERS:
            raise ValueError(f"Unknown provider '{provider}'")
        if not key_value.strip():
            raise ValueError("Key value cannot be empty")
        with self._lock:
            key_id = str(uuid.uuid4())[:16]
            existing = [k for k in self._store["keys"] if k["provider"] == provider and k["active"]]
            entry: dict[str, Any] = {
                "id": key_id,
                "provider": provider,
                "label": label or f"Key {len(existing) + 1}",
                "key": key_value.strip(),
                "active": len(existing) == 0,
                "created_at": int(time.time()),
            }
            self._store["keys"].append(entry)
            self._save()
            logger.info("ProviderManager: added key '%s' for %s (id=%s)", entry["label"], provider, key_id)
            return key_id

    def remove_key(self, key_id: str) -> bool:
        with self._lock:
            before = len(self._store["keys"])
            self._store["keys"] = [k for k in self._store["keys"] if k["id"] != key_id]
            if len(self._store["keys"]) < before:
                self._save()
                return True
            return False

    def set_active_key(self, provider: str, key_id: str) -> bool:
        with self._lock:
            found = False
            for k in self._store["keys"]:
                if k["provider"] == provider:
                    k["active"] = k["id"] == key_id
                    if k["active"]:
                        found = True
            if found:
                self._save()
            return found

    def list_keys(self, provider: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            keys = self._store["keys"]
            if provider:
                keys = [k for k in keys if k["provider"] == provider]
            return [
                {
                    "id": k["id"],
                    "provider": k["provider"],
                    "label": k["label"],
                    "key_masked": k["key"][:6] + "••••••••" + k["key"][-3:] if len(k["key"]) > 9 else "••••••",
                    "active": k["active"],
                    "created_at": k["created_at"],
                }
                for k in keys
            ]

    def _get_active_key(self, provider: str) -> str | None:
        for k in self._store["keys"]:
            if k["provider"] == provider and k["active"]:
                return k["key"]
        return None

    def _get_all_keys_for_provider(self, provider: str) -> list[str]:
        """Return all keys for a provider — active first."""
        keys = [k for k in self._store["keys"] if k["provider"] == provider]
        keys.sort(key=lambda k: 0 if k["active"] else 1)
        return [k["key"] for k in keys]

    # ── Model management ──────────────────────────────────────────────────

    def get_model(self, provider: str) -> str:
        return self._store["models"].get(provider, _DEFAULT_MODELS.get(provider, ""))

    def set_model(self, provider: str, model: str) -> None:
        with self._lock:
            self._store["models"][provider] = model
            self._save()

    def get_models(self) -> dict[str, str]:
        return dict(self._store.get("models", _DEFAULT_MODELS))

    # ── Auto-fallback ─────────────────────────────────────────────────────

    def get_auto_fallback(self) -> bool:
        return bool(self._store.get("auto_fallback", True))

    def set_auto_fallback(self, enabled: bool) -> None:
        with self._lock:
            self._store["auto_fallback"] = enabled
            self._save()

    # ── Invoke ────────────────────────────────────────────────────────────

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        provider = self._active_provider

        if provider == "gemini":
            return self._invoke_with_fallback_gemini(prompt, ctx)
        else:
            return self._invoke_stub(prompt, ctx)

    def _invoke_with_fallback_gemini(self, prompt: str, ctx: dict[str, Any]) -> str:
        key_env = os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        stored_keys = self._get_all_keys_for_provider("gemini")

        candidates = stored_keys if stored_keys else ([key_env] if key_env else [])
        if not candidates:
            logger.warning("ProviderManager: no Gemini API keys configured")
            return "[Gemini stub] No API key. Configure one in the Keys tab."

        last_err: Exception | None = None
        for api_key in candidates:
            try:
                return self._call_gemini(api_key, prompt, ctx)
            except Exception as exc:
                last_err = exc
                if self.get_auto_fallback() and _is_quota_error(exc):
                    logger.warning("ProviderManager: Gemini key exhausted (%s), trying next key", exc)
                    continue
                raise
        logger.error("ProviderManager: all Gemini keys exhausted. Last error: %s", last_err)
        return f"[Gemini error — all keys exhausted] {last_err}"

    def _call_gemini(self, api_key: str, prompt: str, ctx: dict[str, Any]) -> str:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_name = self.get_model("gemini") or "gemini-1.5-flash"
        model = genai.GenerativeModel(model_name)
        system_prefix = ""
        if ctx:
            system_prefix = f"Context: {json.dumps(ctx, ensure_ascii=False)[:800]}\n\n"
        resp = model.generate_content(system_prefix + prompt)
        text = resp.text or ""
        self._token_usage["gemini"] += len(prompt.split()) + len(text.split())
        logger.info("ProviderManager: Gemini OK model=%s tokens~=%d", model_name, len(text.split()))
        return text

    def _invoke_stub(self, prompt: str, context: dict[str, Any]) -> str:
        return (
            f"[{self._active_provider.upper()} — Milestone 2 stub] "
            f"Prompt received ({len(prompt)} chars). Context keys: {list(context.keys())}"
        )


_GLOBAL_MANAGER = ProviderManager()


def get_manager() -> ProviderManager:
    return _GLOBAL_MANAGER


__all__ = ["ProviderManager", "get_manager"]
