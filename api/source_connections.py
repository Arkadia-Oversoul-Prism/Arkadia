"""Governed SolSpire source connections.

Connection secrets live only on the server and are encrypted at rest. The
store is deliberately a small configuration file, not another database or
knowledge authority. Source documents continue through CorpusManager and the
existing Knowledge OS ingest pipeline.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("arkadia.source_connections")
_LOCK = threading.Lock()
_PATH = Path(os.environ.get("SOLSPIRE_DATA_DIR", "data")) / "source_connections.json"

SOURCES: dict[str, dict[str, Any]] = {
    "github": {
        "label": "GitHub",
        "kind": "token",
        "fields": ["token", "repository"],
        "description": "Repositories and source files already supported by the corpus layer.",
    },
    "gdrive": {
        "label": "Google Drive",
        "kind": "service_account",
        "fields": ["folder_id", "service_account_json", "api_key"],
        "description": "Read documents from a Drive folder through the existing Google Drive corpus adapter.",
    },
    "joplin": {
        "label": "Joplin",
        "kind": "api",
        "fields": ["url", "token", "notebook", "tag"],
        "description": "Read Joplin notes through the Joplin Data API.",
    },
    "obsidian": {
        "label": "Obsidian",
        "kind": "local_rest",
        "fields": ["url", "token", "vault_dir", "tag"],
        "description": "Read an Obsidian vault through its Local REST API endpoint.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fernet() -> Fernet:
    """Derive the encryption key from the existing server secret.

    No new secret authority is introduced. Production requires SOVEREIGN_KEY,
    which already gates sensitive server operations.
    """
    secret = os.environ.get("SOVEREIGN_KEY", "").strip()
    if not secret:
        raise RuntimeError("SOVEREIGN_KEY is required to store source credentials")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _load() -> dict[str, dict]:
    if not _PATH.exists():
        return {}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[sources] connection store read failed: %s", exc)
        return {}


def _save(store: dict[str, dict]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=2), encoding="utf-8")
    os.replace(tmp, _PATH)
    try:
        os.chmod(_PATH, 0o600)
    except OSError:
        pass


def _uid(user: dict) -> str:
    uid = str(user.get("uid") or user.get("user_id") or user.get("sub") or "").strip()
    if not uid:
        raise ValueError("Authenticated user has no stable uid")
    return uid


def _encrypt(value: dict) -> str:
    return _fernet().encrypt(json.dumps(value).encode("utf-8")).decode("ascii")


def _decrypt(value: str) -> dict:
    try:
        return json.loads(_fernet().decrypt(value.encode("ascii")).decode("utf-8"))
    except InvalidToken as exc:
        raise RuntimeError("Stored source credential cannot be decrypted") from exc


def list_connections(user: dict) -> list[dict]:
    uid = _uid(user)
    with _LOCK:
        store = _load()
        owned = store.get(uid, {})
    result = []
    for name, meta in SOURCES.items():
        entry = owned.get(name)
        result.append({
            "source": name,
            "label": meta["label"],
            "description": meta["description"],
            "configured": bool(entry),
            "status": entry.get("status", "disconnected") if entry else "disconnected",
            "connected_at": entry.get("connected_at") if entry else None,
            "last_sync": entry.get("last_sync") if entry else None,
            "last_sync_count": entry.get("last_sync_count", 0) if entry else 0,
            "kind": meta["kind"],
        })
    return result


def get_connection(user: dict, source: str) -> dict | None:
    uid = _uid(user)
    with _LOCK:
        entry = _load().get(uid, {}).get(source)
    if not entry:
        return None
    return _decrypt(entry["secret"])


def connect(user: dict, source: str, config: dict) -> dict:
    uid = _uid(user)
    if source not in SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    clean = {k: str(v).strip() for k, v in config.items() if v is not None and str(v).strip()}
    if source == "gdrive" and not clean.get("folder_id"):
        raise ValueError("Google Drive folder_id is required")
    if source == "gdrive" and not (clean.get("service_account_json") or clean.get("api_key")):
        raise ValueError("Google Drive requires a service-account JSON credential or API key")
    if source in {"joplin", "obsidian"} and not clean.get("token"):
        raise ValueError(f"{SOURCES[source]['label']} requires an API token")
    if source == "github" and not clean.get("token"):
        raise ValueError("GitHub requires a token")

    with _LOCK:
        store = _load()
        user_store = store.setdefault(uid, {})
        previous = user_store.get(source, {})
        user_store[source] = {
            "secret": _encrypt(clean),
            "status": "connected",
            "connected_at": previous.get("connected_at") or _now(),
            "last_sync": previous.get("last_sync"),
            "last_sync_count": previous.get("last_sync_count", 0),
        }
        _save(store)
    return next(x for x in list_connections(user) if x["source"] == source)


def disconnect(user: dict, source: str) -> bool:
    uid = _uid(user)
    with _LOCK:
        store = _load()
        user_store = store.get(uid, {})
        removed = user_store.pop(source, None) is not None
        if not user_store:
            store.pop(uid, None)
        _save(store)
    return removed


def record_sync(user: dict, source: str, count: int) -> None:
    uid = _uid(user)
    with _LOCK:
        store = _load()
        entry = store.get(uid, {}).get(source)
        if not entry:
            return
        entry["last_sync"] = _now()
        entry["last_sync_count"] = int(count)
        entry["status"] = "connected"
        _save(store)


def build_corpus_source(source: str, config: dict):
    """Build an existing corpus adapter from a decrypted connection config."""
    from corpus.github import GitHubSource
    from corpus.gdrive import GoogleDriveSource
    from corpus.joplin import JoplinSource
    from corpus.obsidian import ObsidianSource

    classes = {"github": GitHubSource, "gdrive": GoogleDriveSource, "joplin": JoplinSource, "obsidian": ObsidianSource}
    obj = classes[source]()
    if source == "github":
        if "token" in config:
            obj.token = config["token"]
        if config.get("repository"):
            obj.repository = config["repository"]
    elif source == "gdrive":
        obj.folder_id = config.get("folder_id", "")
        obj.service_account_json = config.get("service_account_json", "")
        obj.api_key = config.get("api_key", "")
    elif source == "joplin":
        obj.base_url = config.get("url", obj.base_url).rstrip("/")
        obj.token = config.get("token", "")
        obj.notebook_filter = config.get("notebook", "")
        obj.tag_filter = config.get("tag", "")
    elif source == "obsidian":
        obj.base_url = config.get("url", obj.base_url).rstrip("/")
        obj.token = config.get("token", "")
        obj.vault_dir = config.get("vault_dir", "")
        obj.tag_filter = config.get("tag", "")
    return obj
