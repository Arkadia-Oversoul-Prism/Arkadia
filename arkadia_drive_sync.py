# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account
# Reads the ARKADIA folder from Drive and caches a corpus snapshot.

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from googleapiclient.discovery import build
from google.oauth2 import service_account

# Environment variable names on Render
SERVICE_ACCOUNT_ENV = "GDRIVE_SERVICE_ACCOUNT_JSON"
FOLDER_ID_ENV = "ARKADIA_FOLDER_ID"

# Drive scopes
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Where we store the local cache in the container
CACHE_PATH = "arkadia_drive_cache.json"

# In-memory cache so we don't hit Drive on every request
_ARKADIA_CACHE: Dict[str, Any] = {
    "last_sync": None,
    "documents": [],
    "error": None,
}


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------


def _load_cache_from_disk() -> None:
    global _ARKADIA_CACHE
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _ARKADIA_CACHE.update(data)
        except Exception:
            # If cache is corrupted, keep default in-memory structure
            pass


def _save_cache_to_disk() -> None:
    global _ARKADIA_CACHE
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_ARKADIA_CACHE, f, indent=2, ensure_ascii=False)
    except Exception:
        # If we cannot write, just ignore; in-memory still works
        pass


def _build_drive_service():
    """Build an authenticated Drive service from the service account JSON."""
    sa_json = os.getenv(SERVICE_ACCOUNT_ENV, "").strip()
    if not sa_json:
        raise RuntimeError(
            "GDRIVE_SERVICE_ACCOUNT_JSON env var is not set. "
            "Paste your service account JSON into that variable in Render."
        )

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    return service


def _list_files_recursive(service, folder_id: str) -> List[Dict[str, Any]]:
    """List all files/folders directly under the given folder_id."""
    results: List[Dict[str, Any]] = []

    page_token: Optional[str] = None
    while True:
        response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                pageSize=1000,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            )
            .execute()
        )

        files = response.get("files", [])
        for f in files:
            results.append(f)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def _get_preview_for_doc(service, file_id: str, max_chars: int = 500) -> str:
    """
    For Google Docs, export as text/plain and take a short preview.
    If anything fails, return empty string.
    """
    try:
        content = (
            service.files()
            .export(fileId=file_id, mimeType="text/plain")
            .execute()
        )
        if isinstance(content, bytes):
            text = content.decode("utf-8", errors="ignore")
        else:
            text = str(content)
        text = text.replace("\r\n", "\n")
        return text[:max_chars]
    except Exception:
        return ""


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------


def refresh_arkadia_cache() -> Dict[str, Any]:
    """
    Hit Google Drive with the service account, walk the ARKADIA_FOLDER_ID,
    and populate the in-memory + on-disk cache with:
      - documents: [{id, name, mimeType, modifiedTime, preview}]
      - last_sync: ISO timestamp
      - error: None or string
    """
    global _ARKADIA_CACHE

    folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
    if not folder_id:
        _ARKADIA_CACHE["error"] = (
            "ARKADIA_FOLDER_ID env var is not set. "
            "Set it to the root Arkadia Drive folder ID."
        )
        _ARKADIA_CACHE["documents"] = []
        _ARKADIA_CACHE["last_sync"] = None
        _save_cache_to_disk()
        return _ARKADIA_CACHE

    try:
        service = _build_drive_service()
    except Exception as e:
        _ARKADIA_CACHE["error"] = f"Failed to build Drive service: {e}"
        _ARKADIA_CACHE["documents"] = []
        _ARKADIA_CACHE["last_sync"] = None
        _save_cache_to_disk()
        return _ARKADIA_CACHE

    docs: List[Dict[str, Any]] = []
    error_msg: Optional[str] = None

    try:
        # First level under the Arkadia root
        items = _list_files_recursive(service, folder_id)

        for item in items:
            file_id = item.get("id")
            name = item.get("name")
            mime = item.get("mimeType")
            modified = item.get("modifiedTime")

            preview = ""
            if mime == "application/vnd.google-apps.document":
                preview = _get_preview_for_doc(service, file_id=file_id)

            docs.append(
                {
                    "id": file_id,
                    "name": name,
                    "mimeType": mime,
                    "modifiedTime": modified,
                    "preview": preview,
                }
            )

        _ARKADIA_CACHE["last_sync"] = datetime.utcnow().isoformat() + "Z"
        _ARKADIA_CACHE["documents"] = docs
        _ARKADIA_CACHE["error"] = None

    except Exception as e:
        _ARKADIA_CACHE["error"] = f"Drive sync failed: {e}"
        _ARKADIA_CACHE["documents"] = []
        _ARKADIA_CACHE["last_sync"] = None

    _save_cache_to_disk()
    return _ARKADIA_CACHE


def get_arkadia_snapshot() -> Dict[str, Any]:
    """
    Return the current snapshot of the Arkadia Drive state.
    This is used by:
      - /arkadia/sync endpoint
      - ArkanaBrain._build_corpus_context()
    """
    # If we've never loaded from disk, try now
    if _ARKADIA_CACHE["last_sync"] is None and not _ARKADIA_CACHE["documents"]:
        _load_cache_from_disk()
    return _ARKADIA_CACHE
