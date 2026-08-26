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
    """Initialise the Firebase Admin SDK.

    Security contract (Phase 0):
      • In production (ENVIRONMENT=production): any failure — missing credentials
        OR failed initialisation — is a hard startup error. The process must not
        start in an unauthenticated state silently.
      • In development: missing credentials falls back to dev-mode with unsigned
        JWT decoding so the app remains runnable locally without secrets.
        A failed initialisation (credentials present but invalid) is always fatal
        regardless of environment — if you set the variable it must work.
    """
    global _firebase_app, _dev_mode

    _is_production = os.environ.get("ENVIRONMENT", "").strip().lower() == "production"
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()

    if not sa_json:
        if _is_production:
            raise RuntimeError(
                "[AUTH] FIREBASE_SERVICE_ACCOUNT_JSON is required in production. "
                "The server will not start without valid Firebase credentials. "
                "Set FIREBASE_SERVICE_ACCOUNT_JSON or remove ENVIRONMENT=production "
                "for local/dev use."
            )
        logger.warning(
            "[AUTH] FIREBASE_SERVICE_ACCOUNT_JSON not set — running in dev-mode "
            "(token signatures are NOT verified; local development only)"
        )
        _dev_mode = True
        return

    # Credentials are present — initialise or die. Never silently downgrade.
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
        # Credentials were present but initialisation failed — this is always
        # a hard error. A misconfigured credential is worse than a missing one
        # because it signals a deployment error that must be surfaced immediately.
        raise RuntimeError(
            f"[AUTH] Firebase Admin SDK initialisation failed: {e}. "
            "Fix FIREBASE_SERVICE_ACCOUNT_JSON or remove it to run in dev-mode."
        ) from e


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


def _profiles_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data", "user_profiles")


import re as _re_handle

_HANDLE_RE = _re_handle.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")


def normalize_handle(raw: str | None) -> str:
    """Canonical handle: strip optional @, lowercase, validate format.

    Format: [a-z0-9][a-z0-9._-]{1,31}  (length 2–32 inclusive).
    Raises ValueError on invalid input.
    """
    if raw is None:
        raise ValueError("Handle is required")
    h = str(raw).strip()
    if h.startswith("@"):
        h = h[1:]
    h = h.lower().strip()
    if not h or not _HANDLE_RE.match(h):
        raise ValueError("Invalid handle format")
    return h


def _username_index_path() -> str:
    return os.path.join(_profiles_dir(), "_username_index.json")


def _load_username_index() -> dict[str, str]:
    path = _username_index_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_username_index(index: dict[str, str]) -> None:
    os.makedirs(_profiles_dir(), exist_ok=True)
    path = _username_index_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, sort_keys=True)


def resolve_uid_by_handle(handle: str) -> str | None:
    """Server-side only: normalized handle → Firebase UID. Returns None if unknown."""
    try:
        key = normalize_handle(handle)
    except ValueError:
        return None
    return _load_username_index().get(key) or None


def public_profile_by_handle(handle: str) -> dict[str, Any] | None:
    """Safe public discovery payload (no UID). None if unknown."""
    uid = resolve_uid_by_handle(handle)
    if not uid:
        return None
    stored = load_user_profile_store(uid)
    try:
        canon = normalize_handle(stored.get("username") or handle)
    except ValueError:
        return None
    return {
        "username": canon,
        "handle": canon,
        "display_name": (stored.get("display_name") or "").strip() or canon,
        "avatar_url": (stored.get("avatar_url") or "").strip() or None,
    }


def load_user_profile_store(uid: str) -> dict[str, Any]:
    """User-created product profile (P1-A). Empty dict if none."""
    path = os.path.join(_profiles_dir(), f"{uid}.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_user_profile_store(uid: str, patch: dict[str, Any]) -> dict[str, Any]:
    """Merge and persist user-owned profile fields. Returns full stored profile.

    Username/handle is normalized and uniqueness-enforced via _username_index.json.
    Raises ValueError on invalid handle or collision (caller maps to HTTP 400).
    """
    os.makedirs(_profiles_dir(), exist_ok=True)
    current = load_user_profile_store(uid)
    allowed = ("display_name", "username", "bio", "avatar_url")
    prev_username = (current.get("username") or "").strip()
    for k in allowed:
        if k in patch and patch[k] is not None:
            val = patch[k]
            if isinstance(val, str):
                val = val.strip()[:500]
            current[k] = val
    if "username" in patch and patch["username"] is not None:
        raw = patch["username"]
        if isinstance(raw, str) and raw.strip():
            canon = normalize_handle(raw)
            index = _load_username_index()
            owner = index.get(canon)
            if owner and owner != uid:
                raise ValueError("Handle already taken")
            if prev_username:
                try:
                    prev_key = normalize_handle(prev_username)
                    if index.get(prev_key) == uid and prev_key != canon:
                        del index[prev_key]
                except ValueError:
                    pass
            index[canon] = uid
            _save_username_index(index)
            current["username"] = canon
        else:
            if prev_username:
                try:
                    prev_key = normalize_handle(prev_username)
                    index = _load_username_index()
                    if index.get(prev_key) == uid:
                        del index[prev_key]
                        _save_username_index(index)
                except ValueError:
                    pass
            current["username"] = ""
    current["uid"] = uid
    path = os.path.join(_profiles_dir(), f"{uid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current


def build_user_profile(uid: str, firebase_claims: dict | None, email: str = "") -> dict[str, Any]:
    """Construct product profile: user-created store first; IMS node only with explicit claim.

    P1-A: email-hint matching no longer populates display identity. Canonical/IMS
    nodes apply only when Firebase custom claim node_key is set by admin.
    """
    node = None
    if firebase_claims:
        node_key = firebase_claims.get("node_key") or firebase_claims.get("arkadia_node")
        if node_key:
            node = get_node_by_key(node_key)

    access_level = 0
    role = "Guest"
    node_key = None

    if node:
        access_level = node.get("access_level", 1)
        role = node.get("role", "Authenticated Node")
        node_key = node.get("node_key")

    resolved_email = email or (firebase_claims or {}).get("email", "") or ""
    stored = load_user_profile_store(uid)

    # Product identity priority: user-created profile > Firebase name > email local-part
    # Node display_name only when explicit node_key claim (initiated IMS nodes)
    display_name = (
        (stored.get("display_name") or "").strip()
        or ((node or {}).get("display_name") if node_key else None)
        or (firebase_claims or {}).get("name")
        or (resolved_email.split("@")[0] if resolved_email else "")
        or uid[:8]
    )

    return {
        "uid":          uid,
        "email":        resolved_email,
        "node_key":     node_key,
        "display_name": display_name,
        "username":     (stored.get("username") or "").strip() or None,
        "bio":          (stored.get("bio") or "").strip() or None,
        "avatar_url":   (stored.get("avatar_url") or "").strip() or None,
        "role":         role,
        "role_sigil":   (node or {}).get("role_sigil", "◈") if node else "◈",
        "ims_id":       (node or {}).get("ims_id") if node else None,
        "access_level": access_level,
        "status":       (node or {}).get("status", "authenticated") if node else "authenticated",
        "access_tools": (node or {}).get("access_tools", []) if node else [],
        "profile_complete": bool((stored.get("display_name") or "").strip()),
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
    "build_user_profile", "load_user_profile_store", "save_user_profile_store", "get_node_by_key", "get_personal_codex",
    "normalize_handle", "resolve_uid_by_handle", "public_profile_by_handle",
    "_nodes_by_key",
]
