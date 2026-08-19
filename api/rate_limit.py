"""
Arkadia Phase 1 — minimal in-memory rate limiting.

Zero external deps. Suitable for single-instance Render free tier.
Limits are env-configurable. Health/status paths are exempt.

Keying:
  - Authenticated: uid from Bearer JWT payload (unsigned decode is enough for
    rate-keying; verification still happens in auth layer)
  - Anonymous: client IP (X-Forwarded-For first hop, else client host)

Returns 429 + Retry-After when exceeded.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Optional

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
except ImportError:  # unit tests of pure helpers without starlette
    BaseHTTPMiddleware = object  # type: ignore
    Request = object  # type: ignore
    JSONResponse = dict  # type: ignore
    Response = object  # type: ignore

logger = logging.getLogger("arkadia.rate_limit")

# Default free-tier envelopes (requests per window seconds)
DEFAULT_LIMITS = {
    # path prefix → (max_requests, window_seconds)
    "/api/commune/resonance": (20, 60),       # LLM-expensive
    "/api/personal/": (15, 60),               # write path
    "/api/knowledge/ingest": (20, 60),
    "/api/knowledge/search": (60, 60),
    "/api/knowledge/": (90, 60),              # general knowledge reads
    "/api/": (120, 60),                       # catch-all API
}

EXEMPT_PREFIXES = (
    "/health",
    "/api/knowledge/status",
    "/api/scrolls",
    "/docs",
    "/openapi",
    "/redoc",
    "/assets",
    "/favicon",
)

_lock = threading.Lock()
# key → deque of request timestamps
_buckets: dict[str, Deque[float]] = defaultdict(deque)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)).strip())
    except (TypeError, ValueError):
        return default


def load_limits() -> dict[str, tuple[int, int]]:
    """Allow override via env without code changes.

    ARKADIA_RL_RESONANCE=20/60
    ARKADIA_RL_PERSONAL=15/60
    ARKADIA_RL_SEARCH=60/60
    ARKADIA_RL_KNOWLEDGE=90/60
    ARKADIA_RL_API=120/60
    """
    mapping = {
        "ARKADIA_RL_RESONANCE": "/api/commune/resonance",
        "ARKADIA_RL_PERSONAL": "/api/personal/",
        "ARKADIA_RL_INGEST": "/api/knowledge/ingest",
        "ARKADIA_RL_SEARCH": "/api/knowledge/search",
        "ARKADIA_RL_KNOWLEDGE": "/api/knowledge/",
        "ARKADIA_RL_API": "/api/",
    }
    limits = dict(DEFAULT_LIMITS)
    for env_name, path in mapping.items():
        raw = os.environ.get(env_name, "").strip()
        if not raw or "/" not in raw:
            continue
        try:
            n_s, w_s = raw.split("/", 1)
            limits[path] = (int(n_s), int(w_s))
        except ValueError:
            logger.warning("[RL] ignoring invalid %s=%s", env_name, raw)
    return limits


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _uid_from_authorization(request: Request) -> Optional[str]:
    """Best-effort uid extraction for rate-keying only (not auth)."""
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    parts = token.split(".")
    if len(parts) < 2:
        return None
    try:
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        return payload.get("user_id") or payload.get("sub") or payload.get("uid")
    except Exception:
        return None


def _match_limit(path: str, limits: dict[str, tuple[int, int]]) -> Optional[tuple[str, int, int]]:
    # longest prefix wins
    best = None
    best_len = -1
    for prefix, (n, w) in limits.items():
        if path.startswith(prefix) and len(prefix) > best_len:
            best = (prefix, n, w)
            best_len = len(prefix)
    return best


def _is_exempt(path: str) -> bool:
    return any(path.startswith(p) for p in EXEMPT_PREFIXES)


def check_rate_limit(key: str, max_requests: int, window: int) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds)."""
    now = time.time()
    with _lock:
        bucket = _buckets[key]
        cutoff = now - window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_requests:
            retry = int(window - (now - bucket[0])) + 1
            return False, max(retry, 1)
        bucket.append(now)
        return True, 0


def reset_rate_limit_state() -> None:
    """Test helper — clear all buckets."""
    with _lock:
        _buckets.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limits: Optional[dict[str, tuple[int, int]]] = None):
        super().__init__(app)
        self.limits = limits or load_limits()
        self.enabled = os.environ.get("ARKADIA_RATE_LIMIT", "1").strip() != "0"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        path = request.url.path or "/"
        if _is_exempt(path):
            return await call_next(request)

        matched = _match_limit(path, self.limits)
        if not matched:
            return await call_next(request)

        prefix, max_req, window = matched
        uid = _uid_from_authorization(request)
        identity = f"uid:{uid}" if uid else f"ip:{_client_ip(request)}"
        key = f"{identity}|{prefix}"

        allowed, retry_after = check_rate_limit(key, max_req, window)
        if not allowed:
            logger.warning("[RL] 429 key=%s path=%s retry=%s", key[:48], path, retry_after)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Slow down and retry.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
