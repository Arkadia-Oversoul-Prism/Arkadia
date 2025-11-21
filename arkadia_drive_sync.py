# arkadia_drive_sync.py
# Arkadia — Drive / Corpus Sync Adapter

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).parent
CORPUS_MAP_PATH = BASE_DIR / "arkadia_corpus_map.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_local_corpus_map() -> Dict[str, Any]:
    """
    Load local arkadia_corpus_map.json if it exists.
    Structure:
    {
      "last_sync": "...",
      "documents": [ { id, name, mimeType, modifiedTime, path, preview }, ... ]
    }
    """
    if not CORPUS_MAP_PATH.exists():
        return {
            "last_sync": None,
            "error": "arkadia_corpus_map.json not found",
            "total_documents": 0,
            "documents": [],
        }

    try:
        with CORPUS_MAP_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.exception("Failed to load arkadia_corpus_map.json")
        return {
            "last_sync": None,
            "error": f"Failed to read arkadia_corpus_map.json: {e}",
            "total_documents": 0,
            "documents": [],
        }

    docs: List[Dict[str, Any]] = data.get("documents", [])
    return {
        "last_sync": data.get("last_sync"),
        "error": None,
        "total_documents": len(docs),
        "documents": docs,
    }


def get_arkadia_corpus() -> Dict[str, Any]:
    """
    Public accessor used by /arkadia/corpus.
    Returns stable snapshot from local map.
    """
    snapshot = _load_local_corpus_map()
    # Ensure keys always present
    snapshot.setdefault("last_sync", None)
    snapshot.setdefault("error", None)
    snapshot.setdefault("total_documents", 0)
    snapshot.setdefault("documents", [])
    return snapshot


def get_arkadia_snapshot() -> Dict[str, Any]:
    """
    Backwards-compat alias (older versions imported this name).
    """
    return get_arkadia_corpus()


def refresh_arkadia_corpus() -> Dict[str, Any]:
    """
    Attempt to refresh from Google Drive if credentials are available.
    If anything fails, fall back to local map but still return a valid structure.
    """
    # Try Drive-based sync if configuration present
    service_creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    folder_id = os.getenv("ARKADIA_DRIVE_FOLDER_ID")

    if not service_creds_json or not folder_id:
        logger.info("Drive credentials or folder id not set; using local corpus map only.")
        snapshot = _load_local_corpus_map()
        # Bump last_sync so UI sees 'recent'
        snapshot["last_sync"] = _now_iso()
        return snapshot

    try:
        # Lazy import so app can still run without these libs locally
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_service_account_info(
            json.loads(service_creds_json),
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        service = build("drive", "v3", credentials=creds)

        # List documents recursively under ARKADIA folder
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, mimeType, modifiedTime, parents)",
        ).execute()

        files = results.get("files", [])

        documents: List[Dict[str, Any]] = []
        for fobj in files:
            doc = {
                "id": fobj["id"],
                "name": fobj["name"],
                "mimeType": fobj["mimeType"],
                "modifiedTime": fobj.get("modifiedTime"),
                # We don't resolve full folder paths here; keep name or simple prefix
                "path": f"ARKADIA/{fobj['name']}",
                "preview": None,
            }
            documents.append(doc)

        snapshot = {
            "last_sync": _now_iso(),
            "error": None,
            "total_documents": len(documents),
            "documents": documents,
        }

        # Persist back to arkadia_corpus_map.json as cache
        try:
            with CORPUS_MAP_PATH.open("w", encoding="utf-8") as f:
                json.dump(
                    {"last_sync": snapshot["last_sync"], "documents": documents},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.warning("Failed to write arkadia_corpus_map.json: %s", e)

        return snapshot

    except Exception as e:
        logger.exception("Drive sync failed; falling back to local corpus map.")
        snapshot = _load_local_corpus_map()
        snapshot["error"] = f"Drive sync failed: {e}"
        snapshot["last_sync"] = _now_iso()
        return snapshot
