"""Distributed Gemini API key pool — load-balanced selection across surfaces.

Problem: Oracle Chat, ReasoMate, SolSpire, and Knowledge OS each resolve a
Gemini key independently. With a single "active key" model they all pin the
SAME key, so parallel processes hammer one key and burn its quota/time budget
before any rotation happens.

Solution: a process-local key pool that round-robins (weighted) across all
configured keys so concurrent callers naturally spread across the pool. On a
429/quota error the offending key is cooled down for a window and the next
caller picks a different key — without waiting for an explicit rotate.

Key sources (union, deduped, order preserved):
  1. provider_key_store["gemini"]   (Settings → AI Provider Keys)
  2. key_manager store              (Settings → legacy Gemini multi-key)
  3. GEMINI_API_KEY / GOOGLE_API_KEY env fallbacks

This module is the single source of truth for "which key should a Gemini
caller use right now". Both `api/main.py::_gemini_chat` and
`solspire/provider_manager.py` should route through `acquire_key()` /
`report_failure()` so load is distributed, not duplicated.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from typing import Optional

logger = logging.getLogger("arkadia.key_pool")

# Cool-down applied to a key after a quota/rate-limit failure (seconds).
# Short enough that a transient burst doesn't permanently retire a key, long
# enough that parallel callers naturally migrate to a fresh key mid-burst.
DEFAULT_COOLDOWN = float(os.environ.get("ARKADIA_KEY_COOLDOWN", "45"))

_lock = threading.Lock()

# key -> expiry epoch (0 = available). Survives across calls within the
# process so concurrent threads cooperate without a coordinator service.
_cooldowns: dict[str, float] = {}

# Round-robin cursor per "pool" so distribute weights fairly. The cursor is a
# deque of keys ordered by preference; we rotate so the least-recently-used
# available key is served next.
_cursor: deque[str] = deque()


def _collect_keys() -> list[str]:
    """Union of all configured Gemini keys, deduped, order preserved."""
    seen: set[str] = set()
    keys: list[str] = []

    def add(k: Optional[str]) -> None:
        if not k:
            return
        k = k.strip()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)

    # 1. Multi-provider store (Settings → AI Provider Keys → Gemini)
    try:
        from api.provider_key_store import _load as _load_provider
        store = _load_provider()
        entry = store.get("gemini")
        if entry and entry.get("key") and not entry.get("quota_hit"):
            add(entry["key"])
        elif entry and entry.get("key") and entry.get("quota_hit"):
            # Still collect, but it's pre-cooled below via the quota_hit flag.
            add(entry["key"])
    except Exception:
        pass

    # 2. Legacy multi-key manager (Settings → Gemini keys with rotation)
    try:
        from api.key_manager import _load as _load_km
        km = _load_km()
        for kid, entry in km.get("keys", {}).items():
            add(entry.get("key"))
    except Exception:
        pass

    # 3. Env fallbacks
    add(os.environ.get("GEMINI_API_KEY"))
    add(os.environ.get("GOOGLE_API_KEY"))

    return keys


def _available(keys: list[str], now: float) -> list[str]:
    """Filter to keys not currently in cooldown."""
    out = []
    for k in keys:
        exp = _cooldowns.get(k, 0)
        if exp and now < exp:
            continue
        out.append(k)
    return out


def pool_snapshot() -> dict:
    """Return a diagnostic view of the current pool (no secrets)."""
    with _lock:
        now = time.time()
        keys = _collect_keys()
        return {
            "size": len(keys),
            "available": sum(1 for k in keys if not _cooldowns.get(k, 0) or now >= _cooldowns[k]),
            "cooled": [
                {"masked": _mask(k), "expires_in": max(0, int(_cooldowns[k] - now))}
                for k in keys
                if _cooldowns.get(k, 0) and now < _cooldowns.get(k, 0)
            ],
        }


def _mask(k: str) -> str:
    return k[:4] + "****" + k[-4:] if len(k) > 8 else "****"


def acquire_key() -> str:
    """Return the best available Gemini key, distributing load across the pool.

    Selection: round-robin over available (non-cooled) keys so concurrent
    callers naturally spread. Falls back to any key (even cooled) if every key
    is in cooldown — a cooled key is still preferable to no key.
    """
    with _lock:
        return _acquire_key_locked()


def _acquire_key_locked() -> str:
    """Lock-held implementation — caller must already own `_lock`."""
    keys = _collect_keys()
    now = time.time()
    avail = _available(keys, now)

    if not avail:
        if keys:
            # Everything is cooled — return the soonest-to-recover key.
            avail = [min(keys, key=lambda k: _cooldowns.get(k, 0))]
            logger.warning("[key_pool] all keys in cooldown — reusing soonest key")
        else:
            return ""

    # Maintain cursor so the same caller doesn't always get key[0].
    # Rotate cursor to align with available set, then pick + rotate.
    target = avail[0]
    if _cursor and _cursor[0] in avail:
        target = _cursor[0]
    # Advance cursor to the next available key for fairness.
    try:
        idx = avail.index(target)
        _cursor.clear()
        _cursor.extend(avail[idx + 1:] + avail[:idx + 1])
    except ValueError:
        pass
    return target


def report_failure(key: str, cooldown: float = DEFAULT_COOLDOWN) -> str:
    """Mark `key` as rate-limited and return the next available key.

    Called when a Gemini call gets 429/403/RESOURCE_EXHAUSTED. Cools the key
    for `cooldown` seconds so subsequent acquire_key() calls skip it.
    """
    with _lock:
        now = time.time()
        if key:
            _cooldowns[key] = now + cooldown
            logger.warning("[key_pool] key %s cooled for %.0fs", _mask(key), cooldown)
        return _acquire_key_locked()


def report_success(key: str) -> None:
    """Clear any cooldown on a key after a successful call."""
    with _lock:
        _cooldowns.pop(key, None)


def reset_key(key: str) -> None:
    """Manually clear a key's cooldown (e.g. from Settings UI)."""
    with _lock:
        _cooldowns.pop(key, None)


def reset_all() -> None:
    """Clear all cooldowns — used by admin/reset endpoints."""
    with _lock:
        _cooldowns.clear()
        _cursor.clear()
