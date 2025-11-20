# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account
# Reads the ARKADIA folder from Drive and caches a corpus snapshot.

import os
import json
from typing import List, Dict, Any
from datetime import datetime
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SERVICE_ACCOUNT_ENV = "GDRIVE_SERVICE_ACCOUNT_JSON"
FOLDER_ID_ENV = "ARKADIA_FOLDER_ID"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

_ARKADIA_CACHE: Dict[str, Any] = {
    "last_sync": None,
    "documents": [],
    "error": None,
}


def _build_drive_service():
    sa_json = os.getenv(SERVICE_ACCOUNT_ENV, "").strip()
    if not sa_json:
        raise RuntimeError(
            "GDRIVE_SERVICE_ACCOUNT_JSON env var is not set. "
            "Paste your service account JSON into that variable."
        )

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _export_preview_for_doc(service, file_id: str) -> str:
    """Export Google Doc as text and return first ~400 chars."""
    try:
        request = service.files().export(fileId=file_id, mimeType="text/plain")
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        text = fh.getvalue().decode("utf-8", errors="ignore")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text[:600]
    except Exception as e:
        return f"[preview unavailable: {e}]"


def _walk_folder(service, folder_id: str, prefix: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []

    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageToken=page_token,
            )
            .execute()
        )

        for f in resp.get("files", []):
            file_id = f["id"]
            name = f["name"]
            mimeType = f["mimeType"]
            path = f"{prefix}{name}"

            if mimeType == "application/vnd.google-apps.folder":
                sub_docs = _walk_folder(service, file_id, prefix=f"{path}/")
                docs.extend(sub_docs)
            else:
                preview = ""
                if mimeType == "application/vnd.google-apps.document":
                    preview = _export_preview_for_doc(service, file_id)
                doc = {
                    "id": file_id,
                    "name": name,
                    "mimeType": mimeType,
                    "modifiedTime": f.get("modifiedTime"),
                    "path": path,
                    "preview": preview,
                }
                docs.append(doc)

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return docs


def sync_arkadia_folder() -> Dict[str, Any]:
    """Pull latest Arkadia docs from Drive and update cache."""
    global _ARKADIA_CACHE

    folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
    if not folder_id:
        _ARKADIA_CACHE = {
            "last_sync": None,
            "documents": [],
            "error": "ARKADIA_FOLDER_ID env var is not set.",
        }
        return _ARKADIA_CACHE

    try:
        service = _build_drive_service()
        docs = _walk_folder(service, folder_id, prefix="ARKADIA/")
        _ARKADIA_CACHE = {
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "documents": docs,
            "error": None,
        }
    except Exception as e:
        _ARKADIA_CACHE = {
            "last_sync": _ARKADIA_CACHE.get("last_sync"),
            "documents": _ARKADIA_CACHE.get("documents", []),
            "error": str(e),
        }

    return _ARKADIA_CACHE


def refresh_arkadia_cache() -> Dict[str, Any]:
    return sync_arkadia_folder()


def get_arkadia_snapshot() -> Dict[str, Any]:
    return _ARKADIA_CACHE


def get_corpus_context(max_docs: int = 6) -> str:
    snap = get_arkadia_snapshot()
    docs = snap.get("documents") or []
    last_sync = snap.get("last_sync")
    error = snap.get("error")

    lines: List[str] = []
    lines.append("▣ ARKADIA CORPUS CONTEXT ▣")

    if last_sync:
        lines.append(f"(Last Drive sync: {last_sync})")
        lines.append("")
    if error:
        lines.append(f"[Drive error: {error}]")
        lines.append("")

    if not docs:
        lines.append("No Arkadia documents are currently cached.")
        lines.append("▣ END CORPUS ▣")
        return "\n".join(lines)

    lines.append("— Sample of Arkadia documents —")
    for doc in docs[:max_docs]:
        path = doc.get("path") or doc.get("name")
        mime = doc.get("mimeType")
        preview = (doc.get("preview") or "").strip().split("\n")
        lines.append(f"* {path} [{mime}]")
        if preview:
            snippet = "\n    ".join(preview[:3])
            lines.append(f"    {snippet}")
        lines.append("")

    lines.append("▣ END CORPUS ▣")
    return "\n".join(lines)
