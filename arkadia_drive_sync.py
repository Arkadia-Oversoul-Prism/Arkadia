# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account
# Reads the ARKADIA folder from Drive and caches a corpus snapshot.

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from googleapiclient.discovery import build
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
    """Build an authenticated Drive service from the service account JSON in env."""
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
    return build("drive", "v3", credentials=creds)


def _list_folder_recursive(
    service,
    root_folder_id: str,
    root_prefix: str = "ARKADIA",
) -> List[Dict[str, Any]]:
    """
    Recursively list everything under the root Arkadia folder.
    Returns a flat list of {id, name, mimeType, modifiedTime, path, preview}.
    """
    docs: List[Dict[str, Any]] = []

    stack = [(root_folder_id, root_prefix)]
    while stack:
        folder_id, prefix = stack.pop()

        page_token: Optional[str] = None
        while True:
            resp = (
                service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                    pageToken=page_token,
                )
                .execute()
            )
            for f in resp.get("files", []):
                f_id = f["id"]
                f_name = f["name"]
                mime = f.get("mimeType", "")
                modified = f.get("modifiedTime")
                path = f"{prefix}/{f_name}"

                # Folder → recurse
                if mime == "application/vnd.google-apps.folder":
                    stack.append((f_id, path))
                    docs.append(
                        {
                            "id": f_id,
                            "name": f_name,
                            "mimeType": mime,
                            "modifiedTime": modified,
                            "path": path,
                            "preview": "",
                        }
                    )
                    continue

                preview = ""
                # For Google Docs, export a small text preview
                if mime == "application/vnd.google-apps.document":
                    try:
                        content = (
                            service.files()
                            .export(fileId=f_id, mimeType="text/plain")
                            .execute()
                        )
                        if isinstance(content, bytes):
                            content = content.decode("utf-8", errors="ignore")
                        preview = str(content)[:800]
                    except Exception:
                        preview = ""

                docs.append(
                    {
                        "id": f_id,
                            "name": f_name,
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


def sync_arkadia_folder() -> None:
    """
    Pull a fresh snapshot from Drive into in-memory cache.
    """
    global _ARKADIA_CACHE

    folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
    if not folder_id:
        _ARKADIA_CACHE["error"] = "ARKADIA_FOLDER_ID env var is not set"
        return

    try:
        service = _build_drive_service()
        docs = _list_folder_recursive(service, folder_id, root_prefix="ARKADIA")
        _ARKADIA_CACHE["documents"] = docs
        _ARKADIA_CACHE["last_sync"] = datetime.utcnow().isoformat() + "Z"
        _ARKADIA_CACHE["error"] = None
    except Exception as e:
        _ARKADIA_CACHE["error"] = str(e)


def get_arkadia_corpus() -> Dict[str, Any]:
    """
    Return raw cached Arkadia corpus: documents + last_sync + error.
    If empty, attempt a sync.
    """
    if not _ARKADIA_CACHE["documents"] and not _ARKADIA_CACHE["error"]:
        # Try lazy sync
        try:
            sync_arkadia_folder()
        except Exception as e:
            _ARKADIA_CACHE["error"] = str(e)

    return {
        "last_sync": _ARKADIA_CACHE["last_sync"],
        "documents": _ARKADIA_CACHE["documents"],
        "error": _ARKADIA_CACHE["error"],
    }


def get_drive_status() -> Dict[str, Any]:
    """
    Lightweight status (for /status).
    """
    corpus = get_arkadia_corpus()
    docs = corpus.get("documents") or []
    return {
        "last_sync": corpus.get("last_sync"),
        "total_documents": len(docs),
        "error": corpus.get("error"),
    }


def get_corpus_context() -> str:
    """
    Build a compressed textual context string for ArkanaBrain and /arkadia/corpus.
    """
    corpus = get_arkadia_corpus()
    last_sync = corpus.get("last_sync")
    error = corpus.get("error")
    docs: List[Dict[str, Any]] = corpus.get("documents") or []

    lines: List[str] = []
    lines.append("▣ ARKADIA CORPUS CONTEXT ▣")
    if last_sync:
        lines.append(f"(Last Drive sync: {last_sync})")
    lines.append("")

    if error:
        lines.append(f"Drive Error: {error}")
        lines.append("▣ END CORPUS ▣")
        return "\n".join(lines)

    if not docs:
        lines.append("No Arkadia documents are currently cached.")
        lines.append("▣ END CORPUS ▣")
        return "\n".join(lines)

    lines.append("— Sample of Arkadia documents —")

    # Show up to six non-folder docs
    shown = 0
    for d in docs:
        if d.get("mimeType") == "application/vnd.google-apps.folder":
            continue
        path = d.get("path") or d.get("name") or "Unknown"
        mime = d.get("mimeType") or "application/octet-stream"
        preview = (d.get("preview") or "").replace("\r", " ").replace("\n", " ")
        snippet = (preview[:220] + "…") if preview and len(preview) > 220 else preview

        lines.append(f"* {path} [{mime}]")
        if snippet:
            lines.append(f"    {snippet}")
        lines.append("")
        shown += 1
        if shown >= 6:
            break

    lines.append("▣ END CORPUS ▣")
    return "\n".join(lines)
