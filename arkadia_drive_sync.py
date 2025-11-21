# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account
# Reads the ARKADIA folder from Drive and caches a corpus snapshot
# for ArkanaBrain to use as context.

import os
import json
import io
from typing import List, Dict, Any
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Env vars on Render:
#   GDRIVE_SERVICE_ACCOUNT_JSON  -> full service account JSON
#   ARKADIA_FOLDER_ID            -> root folder id for /ARKADIA

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
            "Paste your service account JSON into that variable in Render."
        )

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds)


def _fetch_preview(service, file_id: str, mime_type: str, max_chars: int = 1000) -> str:
    """Download a small text preview of a file."""
    try:
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="text/plain",
            )
        else:
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if fh.tell() > max_chars * 4:
                break

        text = fh.getvalue().decode("utf-8", errors="ignore")
        return text[:max_chars]
    except Exception:
        return ""


def _walk_folder(service, folder_id: str, path_prefix: str = "ARKADIA") -> List[Dict[str, Any]]:
    """Recursively walk the Arkadia folder tree and collect file metadata + preview."""
    docs: List[Dict[str, Any]] = []
    page_token = None

    while True:
        resp = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageToken=page_token,
            )
            .execute()
        )

        for f in resp.get("files", []):
            f_id = f["id"]
            name = f["name"]
            mime = f["mimeType"]
            modified = f.get("modifiedTime")

            if mime == "application/vnd.google-apps.folder":
                sub_path = f"{path_prefix}/{name}"
                docs.extend(_walk_folder(service, f_id, sub_path))
            else:
                path = f"{path_prefix}/{name}"
                preview = _fetch_preview(service, f_id, mime)
                docs.append(
                    {
                        "id": f_id,
                        "name": name,
                        "mimeType": mime,
                        "modifiedTime": modified,
                        "path": path,
                        "preview": preview,
                    }
                )

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return docs


def sync_arkadia_folder() -> Dict[str, Any]:
    """
    Sync the Arkadia Drive folder into memory.

    Returns a snapshot with:
      - last_sync
      - error
      - total_documents
      - documents (full list)
    """
    global _ARKADIA_CACHE

    try:
        folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
        if not folder_id:
            raise RuntimeError("ARKADIA_FOLDER_ID env var is not set on Render.")

        service = _build_drive_service()
        docs = _walk_folder(service, folder_id)

        _ARKADIA_CACHE["last_sync"] = datetime.utcnow().isoformat() + "Z"
        _ARKADIA_CACHE["documents"] = docs
        _ARKADIA_CACHE["error"] = None
    except Exception as e:
        _ARKADIA_CACHE["error"] = str(e)

    return {
        "last_sync": _ARKADIA_CACHE["last_sync"],
        "error": _ARKADIA_CACHE["error"],
        "total_documents": len(_ARKADIA_CACHE["documents"]),
        "documents": _ARKADIA_CACHE["documents"],
    }


def get_arkadia_drive_state() -> Dict[str, Any]:
    """Lightweight state summary for /status."""
    return {
        "last_sync": _ARKADIA_CACHE["last_sync"],
        "error": _ARKADIA_CACHE["error"],
        "total_documents": len(_ARKADIA_CACHE["documents"]),
    }


def get_corpus_context(max_docs: int = 6) -> str:
    """
    Return a compact text block summarizing a sample of Arkadia docs
    for ArkanaBrain to use as context.
    """
    if not _ARKADIA_CACHE["documents"]:
        try:
            sync_arkadia_folder()
        except Exception as e:
            _ARKADIA_CACHE["error"] = str(e)

    docs = _ARKADIA_CACHE["documents"]
    if not docs:
        return "▣ ARKADIA CORPUS CONTEXT ▣\n\nNo Arkadia documents are currently cached.\n▣ END CORPUS ▣"

    lines: List[str] = []
    lines.append("▣ ARKADIA CORPUS CONTEXT ▣")
    lines.append(f"(Last Drive sync: {_ARKADIA_CACHE['last_sync']})")
    lines.append("")
    lines.append("— Sample of Arkadia documents —")

    for doc in docs[:max_docs]:
        header = f"* {doc.get('path', doc.get('name'))} [{doc.get('mimeType', '?')}]"
        preview = (doc.get("preview") or "").strip()
        lines.append(header)
        if preview:
            preview_block = "    " + preview.replace("\n", "\n    ")
            lines.append(preview_block)
        lines.append("")

    lines.append("▣ END CORPUS ▣")
    return "\n".join(lines)

