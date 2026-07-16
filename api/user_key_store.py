"""Per-User API Key Storage — Firestore-backed, auth-protected.

Stores API keys per authenticated user in Firestore.
Keys are stored encrypted and only masked values are ever sent to the frontend.

Collections:
  • users/{user_id}/api_keys — stores the user's API keys

Usage:
    from api.user_key_store import (
        get_user_keys, add_user_key, remove_user_key,
        set_active_user_key, get_active_key_for_user
    )
"""
from __future__ import annotations

import base64
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("arkadia.user_key_store")

_db = None
_available = False
_lock = threading.Lock()


def _init() -> None:
    global _db, _available
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        logger.info("[USER_KEY_STORE] FIREBASE_SERVICE_ACCOUNT_JSON not set — using in-memory fallback")
        _available = False
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore as fs

        if not firebase_admin._apps:
            cred_data = json.loads(sa_json) if sa_json.startswith("{") else sa_json
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)

        _db = fs.client()
        _available = True
        logger.info("[USER_KEY_STORE] Firestore-backed user key store active")
    except Exception as e:
        logger.warning(f"[USER_KEY_STORE] Firestore init failed — using in-memory fallback: {e}")
        _available = False


_init()

# In-memory fallback for when Firestore is not available
_memory_store: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _encrypt_key(key: str) -> str:
    """Simple XOR encryption with base64 encoding. For production, use proper encryption."""
    # Use a combination of environment secret and the key itself for basic obfuscation
    secret = os.environ.get("SOVEREIGN_KEY", "arkadia-default-secret")
    encrypted = ""
    for i, char in enumerate(key):
        encrypted += chr(ord(char) ^ ord(secret[i % len(secret)]))
    return base64.b64encode(encrypted.encode()).decode()


def _decrypt_key(encrypted: str) -> str:
    """Decrypt a key that was encrypted with _encrypt_key."""
    secret = os.environ.get("SOVEREIGN_KEY", "arkadia-default-secret")
    try:
        decoded = base64.b64decode(encrypted.encode()).decode()
        decrypted = ""
        for i, char in enumerate(decoded):
            decrypted += chr(ord(char) ^ ord(secret[i % len(secret)]))
        return decrypted
    except Exception:
        return ""


# ── Public API ───────────────────────────────────────────────────────────────

def get_user_keys(user_id: str) -> list[dict[str, Any]]:
    """Get all keys for a user (masked). Returns list of key info dicts."""
    with _lock:
        if _available and _db:
            try:
                docs = _db.collection("users").document(user_id).collection("api_keys").stream()
                keys = []
                active_id = None
                for doc in docs:
                    data = doc.to_dict()
                    keys.append({
                        "id": doc.id,
                        "label": data.get("label", ""),
                        "masked": _mask(data.get("key", "")),
                        "added_at": data.get("added_at"),
                        "last_used": data.get("last_used"),
                        "quota_hit": data.get("quota_hit", False),
                        "active": data.get("active", False),
                    })
                    if data.get("active"):
                        active_id = doc.id
                # Also get the stored active_id if not set
                if active_id is None:
                    user_doc = _db.collection("users").document(user_id).get()
                    if user_doc.exists:
                        active_id = user_doc.to_dict().get("active_api_key_id")
                        for k in keys:
                            k["active"] = k["id"] == active_id
                return keys
            except Exception as e:
                logger.warning(f"[USER_KEY_STORE] Failed to get keys for {user_id}: {e}")
        
        # Fallback to memory store
        if user_id in _memory_store:
            store = _memory_store[user_id]
            return [
                {
                    "id": kid,
                    "label": e.get("label", ""),
                    "masked": _mask(e.get("key", "")),
                    "added_at": e.get("added_at"),
                    "last_used": e.get("last_used"),
                    "quota_hit": e.get("quota_hit", False),
                    "active": e.get("active", False),
                }
                for kid, e in store.get("keys", {}).items()
            ]
        return []


def add_user_key(user_id: str, key: str, label: str = "") -> dict[str, Any]:
    """Add a new API key for a user."""
    key = key.strip()
    if not key:
        raise ValueError("Key cannot be empty")
    
    with _lock:
        kid = str(uuid.uuid4())[:8]
        key_data = {
            "key": _encrypt_key(key),
            "label": label or f"Key {kid}",
            "added_at": _now(),
            "quota_hit": False,
            "last_used": None,
            "active": False,
        }
        
        if _available and _db:
            try:
                user_ref = _db.collection("users").document(user_id)
                keys_ref = user_ref.collection("api_keys")
                
                # Check for duplicates
                for doc in keys_ref.stream():
                    existing = doc.to_dict()
                    if _decrypt_key(existing.get("key", "")) == key:
                        raise ValueError("Key already exists for this user")
                
                keys_ref.document(kid).set(key_data)
                
                # If no active key, set this one as active
                user_doc = user_ref.get()
                if not user_doc.exists or not user_doc.to_dict().get("active_api_key_id"):
                    user_ref.update({"active_api_key_id": kid})
                    key_data["active"] = True
                
                logger.info(f"[USER_KEY_STORE] Added key {kid} for user {user_id}")
                return {"id": kid, "label": key_data["label"], "masked": _mask(key)}
            except ValueError:
                raise
            except Exception as e:
                logger.warning(f"[USER_KEY_STORE] Failed to add key for {user_id}: {e}")
        
        # Memory fallback
        if user_id not in _memory_store:
            _memory_store[user_id] = {"keys": {}, "active_id": None}
        
        # Check duplicates
        for e in _memory_store[user_id]["keys"].values():
            if e.get("key") == key:
                raise ValueError("Key already exists for this user")
        
        _memory_store[user_id]["keys"][kid] = key_data
        if not _memory_store[user_id].get("active_id"):
            _memory_store[user_id]["active_id"] = kid
            key_data["active"] = True
        
        return {"id": kid, "label": key_data["label"], "masked": _mask(key)}


def remove_user_key(user_id: str, key_id: str) -> bool:
    """Remove an API key for a user."""
    with _lock:
        if _available and _db:
            try:
                key_ref = _db.collection("users").document(user_id).collection("api_keys").document(key_id)
                key_doc = key_ref.get()
                if not key_doc.exists:
                    return False
                
                key_ref.delete()
                
                # If this was the active key, switch to another
                user_ref = _db.collection("users").document(user_id)
                user_doc = user_ref.get()
                if user_doc.exists and user_doc.to_dict().get("active_api_key_id") == key_id:
                    remaining = list(user_ref.collection("api_keys").limit(1).stream())
                    new_active = remaining[0].id if remaining else None
                    user_ref.update({"active_api_key_id": new_active})
                
                logger.info(f"[USER_KEY_STORE] Removed key {key_id} for user {user_id}")
                return True
            except Exception as e:
                logger.warning(f"[USER_KEY_STORE] Failed to remove key {key_id} for {user_id}: {e}")
        
        # Memory fallback
        if user_id in _memory_store and key_id in _memory_store[user_id]["keys"]:
            del _memory_store[user_id]["keys"][key_id]
            return True
        return False


def set_active_user_key(user_id: str, key_id: str) -> bool:
    """Set the active API key for a user."""
    with _lock:
        if _available and _db:
            try:
                # Verify key exists
                key_ref = _db.collection("users").document(user_id).collection("api_keys").document(key_id)
                if not key_ref.get().exists:
                    return False
                
                # Update user's active key reference
                _db.collection("users").document(user_id).update({"active_api_key_id": key_id})
                
                # Update the key's active flag
                key_ref.update({"active": True})
                
                # Unset other keys' active flag
                batch = _db.batch()
                keys_ref = _db.collection("users").document(user_id).collection("api_keys")
                for doc in keys_ref.stream():
                    if doc.id != key_id:
                        batch.update(doc.reference, {"active": False})
                batch.commit()
                
                logger.info(f"[USER_KEY_STORE] Set active key to {key_id} for user {user_id}")
                return True
            except Exception as e:
                logger.warning(f"[USER_KEY_STORE] Failed to set active key {key_id} for {user_id}: {e}")
        
        # Memory fallback
        if user_id in _memory_store and key_id in _memory_store[user_id]["keys"]:
            for kid, e in _memory_store[user_id]["keys"].items():
                e["active"] = (kid == key_id)
            _memory_store[user_id]["active_id"] = key_id
            return True
        return False


def get_active_key_for_user(user_id: str) -> str | None:
    """Get the active API key for a user (decrypted). Returns None if no key."""
    with _lock:
        if _available and _db:
            try:
                user_ref = _db.collection("users").document(user_id)
                user_doc = user_ref.get()
                if not user_doc.exists:
                    return None
                
                active_id = user_doc.to_dict().get("active_api_key_id")
                if not active_id:
                    return None
                
                key_doc = user_ref.collection("api_keys").document(active_id).get()
                if not key_doc.exists:
                    return None
                
                encrypted = key_doc.to_dict().get("key", "")
                return _decrypt_key(encrypted)
            except Exception as e:
                logger.warning(f"[USER_KEY_STORE] Failed to get active key for {user_id}: {e}")
        
        # Memory fallback
        if user_id in _memory_store:
            active_id = _memory_store[user_id].get("active_id")
            if active_id and active_id in _memory_store[user_id]["keys"]:
                return _memory_store[user_id]["keys"][active_id].get("key")
        return None


def rotate_user_key(user_id: str, exhausted_key: str) -> str | None:
    """Mark a key as quota-hit and return the next available key."""
    with _lock:
        if _available and _db:
            try:
                # Mark exhausted
                keys_ref = _db.collection("users").document(user_id).collection("api_keys")
                for doc in keys_ref.stream():
                    key_data = doc.to_dict()
                    stored_key = _decrypt_key(key_data.get("key", ""))
                    if stored_key == exhausted_key:
                        doc.reference.update({"quota_hit": True})
                    elif not key_data.get("quota_hit") and not key_data.get("active"):
                        # Make this the new active key
                        user_ref = _db.collection("users").document(user_id)
                        user_ref.update({"active_api_key_id": doc.id})
                        doc.reference.update({"active": True})
                        return stored_key
                
                # Find any non-quota-hit key
                for doc in keys_ref.stream():
                    if not doc.to_dict().get("quota_hit"):
                        return _decrypt_key(doc.to_dict().get("key", ""))
            except Exception as e:
                logger.warning(f"[USER_KEY_STORE] Failed to rotate key for {user_id}: {e}")
        
        # Memory fallback
        if user_id in _memory_store:
            for kid, e in _memory_store[user_id]["keys"].items():
                if e.get("key") == exhausted_key:
                    e["quota_hit"] = True
                elif not e.get("quota_hit") and not e.get("active"):
                    e["active"] = True
                    _memory_store[user_id]["active_id"] = kid
                    return e.get("key")
        return None
