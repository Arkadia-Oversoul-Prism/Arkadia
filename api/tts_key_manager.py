"""TTS API key manager.

Stores multiple TTS API keys in a local JSON file (data/tts_keys.json).
Provides:
  • get_active_tts_key() — returns the current active TTS key
  • rotate_tts_key()     — moves to the next key (called on 429)
  • list_tts_keys()     — returns key list (masked) for the UI
  • add_tts_key(key)    — add a new TTS key
  • remove_tts_key()    — remove a TTS key by id
  • set_active_tts_key() — pin a specific key as active
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("arkadia.tts_key_manager")

_DATA_DIR = os.environ.get("SOLSPIRE_DATA_DIR", "data")
_KEYS_PATH = Path(_DATA_DIR) / "tts_keys.json"
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    if _KEYS_PATH.exists():
        try:
            with open(_KEYS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    store: dict[str, Any] = {"active_id": None, "keys": {}}
    return store


def _save(store: dict[str, Any]) -> None:
    _KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_KEYS_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _mask(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


# ── Public API ───────────────────────────────────────────────────────────────

def get_active_key() -> str:
    with _lock:
        store = _load()
        active_id = store.get("active_id")
        if active_id and active_id in store["keys"]:
            entry = store["keys"][active_id]
            if not entry.get("quota_hit"):
                entry["last_used"] = _now()
                _save(store)
                return entry["key"]
        # try to find any non-quota-hit key
        for kid, entry in store["keys"].items():
            if not entry.get("quota_hit"):
                store["active_id"] = kid
                entry["last_used"] = _now()
                _save(store)
                logger.info("[tts_key_manager] switched active key to %s", kid)
                return entry["key"]
        return ""


def rotate_key(exhausted_key: str | None = None) -> str:
    """Mark the current key as quota-hit and return the next available key."""
    with _lock:
        store = _load()
        active_id = store.get("active_id")

        if exhausted_key:
            for kid, entry in store["keys"].items():
                if entry["key"] == exhausted_key:
                    entry["quota_hit"] = True
                    logger.warning("[tts_key_manager] key %s marked quota_hit", kid)
                    break
        elif active_id in store["keys"]:
            store["keys"][active_id]["quota_hit"] = True
            logger.warning("[tts_key_manager] active key %s marked quota_hit", active_id)

        for kid, entry in store["keys"].items():
            if not entry.get("quota_hit"):
                store["active_id"] = kid
                entry["last_used"] = _now()
                _save(store)
                logger.info("[tts_key_manager] rotated to key %s", kid)
                return entry["key"]

        _save(store)
        logger.error("[tts_key_manager] all TTS keys exhausted")
        return ""


def list_keys() -> list[dict[str, Any]]:
    with _lock:
        store = _load()
        active_id = store.get("active_id")
        return [
            {
                "id": kid,
                "label": e.get("label", ""),
                "masked": _mask(e["key"]),
                "added_at": e.get("added_at"),
                "last_used": e.get("last_used"),
                "quota_hit": e.get("quota_hit", False),
                "active": kid == active_id,
            }
            for kid, e in store["keys"].items()
        ]


def add_key(key: str, label: str = "") -> dict[str, Any]:
    key = key.strip()
    if not key:
        raise ValueError("Key cannot be empty")
    with _lock:
        store = _load()
        for e in store["keys"].values():
            if e["key"] == key:
                raise ValueError("Key already exists")
        kid = str(uuid.uuid4())[:8]
        store["keys"][kid] = {
            "id": kid,
            "key": key,
            "label": label or f"TTS Key {len(store['keys'])+1}",
            "added_at": _now(),
            "quota_hit": False,
            "last_used": None,
        }
        if not store.get("active_id"):
            store["active_id"] = kid
        _save(store)
        logger.info("[tts_key_manager] added key %s", kid)
        return {"id": kid, "label": store["keys"][kid]["label"], "masked": _mask(key)}


def remove_key(key_id: str) -> bool:
    with _lock:
        store = _load()
        if key_id not in store["keys"]:
            return False
        del store["keys"][key_id]
        if store.get("active_id") == key_id:
            remaining = [k for k in store["keys"] if not store["keys"][k].get("quota_hit")]
            store["active_id"] = remaining[0] if remaining else (list(store["keys"].keys()) or [None])[0]
        _save(store)
        logger.info("[tts_key_manager] removed key %s", key_id)
        return True


def set_active(key_id: str) -> bool:
    with _lock:
        store = _load()
        if key_id not in store["keys"]:
            return False
        store["active_id"] = key_id
        store["keys"][key_id]["quota_hit"] = False
        _save(store)
        logger.info("[tts_key_manager] manually set active key to %s", key_id)
        return True


def reset_quota(key_id: str) -> bool:
    with _lock:
        store = _load()
        if key_id not in store["keys"]:
            return False
        store["keys"][key_id]["quota_hit"] = False
        _save(store)
        return True
