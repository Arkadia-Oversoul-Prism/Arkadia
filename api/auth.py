"""Arkadia Auth Layer — Firebase Admin SDK token verification.

Provides:
  • verify_firebase_token(token) -> dict  (the decoded Firebase claims)
  • get_current_user(request) -> dict     (FastAPI dependency, optional)
  • require_auth(request) -> dict         (FastAPI dependency, raises 401)
  • require_sovereign(request) -> dict    (FastAPI dependency, access_level=3)

On startup the module tries to initialise the Firebase Admin SDK using
FIREBASE_SERVICE_ACCOUNT_JSON (full JSON string) or falls back to
GOOGLE_APPLICATION_CREDENTIALS (path to a JSON file).  If neither is
present the module operates in *dev-mode*: token verification is skipped
and a synthetic guest profile is returned so the app stays runnable
locally without credentials.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger("arkadia.auth")

# ── Firebase Admin SDK init ──────────────────────────────────────────────────

_firebase_app = None
_dev_mode = False


def _init_firebase() -> None:
    global _firebase_app, _dev_mode

    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        if os.environ.get("ENVIRONMENT", "").strip().lower() == "production":
            raise RuntimeError(
                "[AUTH] FIREBASE_SERVICE_ACCOUNT_JSON is not set while ENVIRONMENT=production. "
                "Refusing to start in unsigned-JWT dev-mode auth fallback in production. "
                "Set FIREBASE_SERVICE_ACCOUNT_JSON (or unset ENVIRONMENT=production for local/dev use)."
            )
        logger.warning("[AUTH] FIREBASE_SERVICE_ACCOUNT_JSON not set — running in dev-mode (no token verification)")
        _dev_mode = True
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            return

        if sa_json.startswith("{"):
            cred = credentials.Certificate(json.loads(sa_json))
        else:
            cred = credentials.Certificate(sa_json)

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("[AUTH] Firebase Admin SDK initialised")
    except Exception as e:
        logger.warning(f"[AUTH] Firebase Admin init failed — dev-mode: {e}")
        _dev_mode = True


_init_firebase()


# ── Token verification ───────────────────────────────────────────────────────

def _decode_jwt_payload_unsafe(token: str) -> dict[str, Any] | None:
    """Decode JWT payload without signature verification (dev-mode only)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None


def verify_firebase_token(token: str) -> dict[str, Any] | None:
    """Return decoded Firebase claims dict, or None on failure."""
    if _dev_mode:
        return None
    try:
        from firebase_admin import auth as fb_auth
        return fb_auth.verify_id_token(token)
    except Exception as e:
        logger.debug(f"[AUTH] Token verification failed: {e}")
        return None


# ── Node registry helpers ────────────────────────────────────────────────────

_NODES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "nodes_seed.json")
_CODEX_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "personal_codices")

_nodes_by_key: dict[str, dict] = {}

def _load_nodes() -> None:
    global _nodes_by_key
    try:
        with open(_NODES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _nodes_by_key = {n["node_key"]: n for n in data.get("nodes", [])}
        logger.info(f"[AUTH] Loaded {len(_nodes_by_key)} nodes from registry")
    except Exception as e:
        logger.warning(f"[AUTH] Failed to load node registry: {e}")

_load_nodes()


def get_node_by_key(node_key: str) -> dict | None:
    return _nodes_by_key.get(node_key)


def get_node_by_email_hint(email: str) -> dict | None:
    """Find a node whose email_hint appears in the given email address."""
    email_lower = email.lower()
    for node in _nodes_by_key.values():
        hint = (node.get("email_hint") or "").lower()
        if hint and hint in email_lower:
            return node
    return None


def get_personal_codex(node_key: str) -> dict | None:
    """Load personal codex JSON for a node, if it exists."""
    try:
        path = os.path.join(_CODEX_DIR, f"{node_key}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def build_user_profile(uid: str, firebase_claims: dict | None, email: str = "") -> dict[str, Any]:
    """Construct a user profile dict from Firebase claims + node registry."""
    node = None

    # 1. Try custom claim node_key (set by admin)
    if firebase_claims:
        node_key = firebase_claims.get("node_key") or firebase_claims.get("arkadia_node")
        if node_key:
            node = get_node_by_key(node_key)
        # 2. Fall back to email-hint matching
        if not node:
            email = email or firebase_claims.get("email", "")
            if email:
                node = get_node_by_email_hint(email)

    access_level = 0
    role = "Guest"
    node_key = None

    if node:
        access_level = node.get("access_level", 1)
        role = node.get("role", "Authenticated Node")
        node_key = node.get("node_key")

    return {
        "uid":          uid,
        "email":        email or (firebase_claims or {}).get("email", ""),
        "node_key":     node_key,
        "display_name": (node or {}).get("display_name") or (firebase_claims or {}).get("name", ""),
        "role":         role,
        "role_sigil":   (node or {}).get("role_sigil", "◈"),
        "ims_id":       (node or {}).get("ims_id"),
        "access_level": access_level,
        "status":       (node or {}).get("status", "authenticated"),
        "access_tools": (node or {}).get("access_tools", []),
    }


# ── FastAPI dependencies ─────────────────────────────────────────────────────

def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


async def get_current_user(request: Request) -> dict[str, Any] | None:
    """Optional auth dependency. Returns user profile if token present + valid,
    None if no token or invalid (does not raise).

    In dev-mode (no Firebase service account) the JWT signature is NOT verified —
    the payload is decoded just to identify the user by email/uid so that the
    node-registry lookup still works locally.
    """
    token = _extract_token(request)
    if not token:
        return None
    if _dev_mode:
        claims = _decode_jwt_payload_unsafe(token)
        if not claims:
            return None
        uid = claims.get("user_id") or claims.get("sub") or "dev-user"
        email = claims.get("email", "")
        logger.debug(f"[AUTH] dev-mode — decoded token for uid={uid} email={email}")
        return build_user_profile(uid, claims, email)
    claims = verify_firebase_token(token)
    if not claims:
        return None
    return build_user_profile(claims.get("uid", ""), claims, claims.get("email", ""))


async def require_auth(request: Request) -> dict[str, Any]:
    """Dependency that raises 401 if user is not authenticated."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_sovereign(request: Request) -> dict[str, Any]:
    """Dependency that requires access_level >= 3 (Sovereign)."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.get("access_level", 0) < 3:
        raise HTTPException(status_code=403, detail="Sovereign access required")
    return user


__all__ = [
    "verify_firebase_token",
    "get_current_user", "require_auth", "require_sovereign",
    "build_user_profile", "get_node_by_key", "get_personal_codex",
    "_nodes_by_key",
]
