# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account
# Reads the ARKADIA folder from Drive and caches a corpus snapshot.

import os
import json
from typing import List, Dict, Any
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io

# Env vars on Render
SERVICE_ACCOUNT_ENV = "GDRIVE_SERVICE_ACCOUNT_JSON"
FOLDER_ID_ENV = "ARKADIA_FOLDER_ID"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# In-memory cache so we don't hit Drive on every request
_ARKADIA_CACHE: Dict[str, Any] = {
    "last_sync": None,
    "documents": [],
    "error": None,
}


def _build_drive_service():
    """Build an authenticated Drive service from the service account JSON in env."""
    sa_json = os.getenv(SERVICE_ACCOUNT_ENV, "").strip()
    if not sa_json:
        raise RuntimeError(
            "GDRIVE_SERVICE_ACCOUNT_JSON env var is not set. "
            "Paste your service account JSON into that variable on Render."
        )

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service


def _fetch_arkadia_files(service) -> List[Dict[str, Any]]:
    """Fetch metadata for all files in the ARKADIA folder."""
    folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
    if not folder_id:
        raise RuntimeError("ARKADIA_FOLDER_ID env var is not set.")

    files: List[Dict[str, Any]] = []
    page_token = None

    while True:
        response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def _download_file_content(service, file_id: str, mime_type: str) -> str:
    """
    Downloads content for supported file types.
    - Google Docs -> export as plain text
    - text/*      -> raw download
    - application/json -> raw download
    Everything else returns an empty string for now.
    """
    # Google Docs
    if mime_type == "application/vnd.google-apps.document":
        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
    # Plain text / JSON
    elif mime_type.startswith("text/") or mime_type == "application/json":
        request = service.files().get_media(fileId=file_id)
    else:
        return ""

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read().decode("utf-8", errors="ignore")


def sync_arkadia_folder() -> Dict[str, Any]:
    """
    Syncs the ARKADIA folder from Drive into the in-memory cache.
    Returns the raw cache dict.
    """
    global _ARKADIA_CACHE

    try:
        service = _build_drive_service()
        files = _fetch_arkadia_files(service)

        documents: List[Dict[str, Any]] = []
        for f in files:
            file_id = f["id"]
            name = f.get("name", "Untitled")
            mime_type = f.get("mimeType", "")
            modified = f.get("modifiedTime")

            text = _download_file_content(service, file_id, mime_type)

            documents.append(
                {
                    "id": file_id,
                    "name": name,
                    "mimeType": mime_type,
                    "modifiedTime": modified,
                    "text": text,
                }
            )

        _ARKADIA_CACHE = {
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "documents": documents,
            "error": None,
        }
    except Exception as e:
        _ARKADIA_CACHE["error"] = str(e)

    return _ARKADIA_CACHE


def get_arkadia_snapshot() -> Dict[str, Any]:
    """
    Returns a lightweight view of the current cache:
    counts + top 20 docs + short previews.
    """
    docs = _ARKADIA_CACHE.get("documents", []) or []
    return {
        "last_sync": _ARKADIA_CACHE.get("last_sync"),
        "error": _ARKADIA_CACHE.get("error"),
        "total_documents": len(docs),
        "documents": [
            {
                "id": d["id"],
                "name": d["name"],
                "mimeType": d["mimeType"],
                "modifiedTime": d["modifiedTime"],
                "preview": (d.get("text") or "")[:250],
            }
            for d in docs[:20]
        ],
    }
