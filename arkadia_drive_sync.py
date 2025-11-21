# arkadia_drive_sync.py
# Arkadia — Google Drive Codex Binder

import datetime
import json
import os
from typing import Any, Dict, List, Tuple

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    # On local dev without Google libs, we fail gracefully.
    service_account = None
    build = None

# Read-only scope is enough
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# In-memory snapshot of the Arkadia corpus
_SNAPSHOT: Dict[str, Any] = {
    "last_sync": None,
    "error": None,
    "total_documents": 0,
    "documents": [],
}


def _utc_now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _get_folder_id() -> str:
    """
    Support both possible env var names, since we used different ones before.
    """
    folder_id = os.getenv("ARKADIA_DRIVE_FOLDER_ID") or os.getenv(
        "ARKADIA_DRIVE_ROOT_FOLDER_ID"
    )
    if not folder_id:
        raise RuntimeError(
            "Missing ARKADIA_DRIVE_FOLDER_ID (or ARKADIA_DRIVE_ROOT_FOLDER_ID) env var"
        )
    return folder_id


def _build_drive_service():
    """
    Build a Google Drive service using service account credentials
    stored in GOOGLE_SERVICE_ACCOUNT_JSON.
    """
    if service_account is None or build is None:
        raise RuntimeError(
            "google-auth / google-api-python-client not installed in this environment"
        )

    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON env var")

    try:
        info = json.loads(sa_json)
    except Exception as e:
        raise RuntimeError(f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    creds = service_account.Credentials.from_service_account_info(
        info, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return service


def _list_children(
    service: Any, folder_id: str
) -> List[Dict[str, Any]]:
    """
    List direct children of a folder.
    """
    results: List[Dict[str, Any]] = []
    page_token = None

    while True:
        resp = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields=(
                    "nextPageToken, files(id, name, mimeType, modifiedTime)"
                ),
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )
        files = resp.get("files", [])
        results.extend(files)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return results


def _walk_tree(
    service: Any, root_id: str, root_name: str = "ARKADIA"
) -> List[Dict[str, Any]]:
    """
    BFS over the folder tree under ARKADIA root,
    building a flat list of documents with full paths.
    """
    docs: List[Dict[str, Any]] = []

    # Each stack entry: (folder_id, folder_path)
    stack: List[Tuple[str, str]] = [(root_id, root_name)]

    while stack:
        current_id, current_path = stack.pop()
        children = _list_children(service, current_id)

        for f in children:
            mime = f.get("mimeType", "")
            name = f.get("name", "")
            file_id = f.get("id")
            modified = f.get("modifiedTime")

            if mime == "application/vnd.google-apps.folder":
                # Recurse into subfolder
                next_path = f"{current_path}/{name}"
                stack.append((file_id, next_path))
            else:
                docs.append(
                    {
                        "id": file_id,
                        "name": name,
                        "mimeType": mime,
                        "modifiedTime": modified,
                        "path": f"{current_path}/{name}",
                    }
                )

    return docs


def refresh_arkadia_corpus() -> Dict[str, Any]:
    """
    Pull the latest Arkadia snapshot from Google Drive and cache it
    in memory for the current process.

    This is what /arkadia/refresh calls.
    """
    global _SNAPSHOT

    try:
        folder_id = _get_folder_id()
        service = _build_drive_service()
        docs = _walk_tree(service, folder_id, "ARKADIA")

        _SNAPSHOT = {
            "last_sync": _utc_now_iso(),
            "error": None,
            "total_documents": len(docs),
            "documents": docs,
        }
    except Exception as e:
        _SNAPSHOT = {
            "last_sync": _utc_now_iso(),
            "error": f"{type(e).__name__}: {e}",
            "total_documents": 0,
            "documents": [],
        }

    return _SNAPSHOT


def get_arkadia_corpus() -> Dict[str, Any]:
    """
    Return the current in-memory corpus snapshot.

    This is what /arkadia/corpus uses.
    """
    return _SNAPSHOT


def get_arkadia_snapshot() -> Dict[str, Any]:
    """
    Alias used by ArkanaBrain.get_status() to show Drive state in /status.
    """
    return _SNAPSHOT
