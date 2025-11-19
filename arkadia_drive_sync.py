# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account
# Reads the ARKADIA folder from Drive and caches a corpus snapshot,
# plus helpers for raw corpus export (for compression).

import os
import json
import io
from typing import List, Dict, Any
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Env vars on Render / local
SERVICE_ACCOUNT_ENV = "GDRIVE_SERVICE_ACCOUNT_JSON"
FOLDER_ID_ENV = "ARKADIA_FOLDER_ID"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# In-memory cache so we don't hit Drive on every /status or /sync
_ARKADIA_CACHE: Dict[str, Any] = {
    "last_sync": None,
    "documents": [],
    "error": None,
}

# On-disk snapshot for full-text corpus (used by compression scripts)
CORPUS_SNAPSHOT_FILE = "arkadia_corpus_raw.json"


# ---------------------------------------------------------
# Core Drive helpers
# ---------------------------------------------------------

def _build_drive_service():
    """
    Build an authenticated Drive service from the service account
    JSON stored in the GDRIVE_SERVICE_ACCOUNT_JSON env var.
    """
    sa_json = os.getenv(SERVICE_ACCOUNT_ENV, "").strip()
    if not sa_json:
        raise RuntimeError(
            "GDRIVE_SERVICE_ACCOUNT_JSON env var is not set. "
            "Paste your service account JSON into that variable in Render secrets."
        )

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=SCOPES
    )
    # cache_discovery=False to avoid disk writes in serverless envs
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _list_folder_children(folder_id: str) -> List[Dict[str, Any]]:
    """
    List all non-trashed files directly under the given folder.
    """
    service = _build_drive_service()
    q = f"'{folder_id}' in parents and trashed = false"
    fields = "nextPageToken, files(id,name,mimeType,modifiedTime)"
    page_token = None
    files: List[Dict[str, Any]] = []

    while True:
        resp = (
            service.files()
            .list(
                q=q,
                spaces="drive",
                fields=fields,
                pageToken=page_token,
                pageSize=1000,
                orderBy="folder,name",
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def export_doc_as_text(file_id: str) -> str:
    """
    Export a Google Doc as plain text via Drive API.
    Used for previews and raw corpus export.
    """
    try:
        service = _build_drive_service()
        request = service.files().export(
            fileId=file_id,
            mimeType="text/plain",
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print("[ArkadiaDriveSync] export_doc_as_text error:", e)
        return ""


# ---------------------------------------------------------
# Live cache sync (used by /arkadia/refresh & /arkadia/sync)
# ---------------------------------------------------------

def refresh_arkadia_cache() -> Dict[str, Any]:
    """
    Refresh the in-memory Arkadia Drive cache from the ARKADIA_FOLDER_ID.
    Returns the updated cache structure.
    """
    global _ARKADIA_CACHE

    folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
    if not folder_id:
        _ARKADIA_CACHE["error"] = "ARKADIA_FOLDER_ID env var not set"
        print("[ArkadiaDriveSync] ARKADIA_FOLDER_ID not set.")
        return _ARKADIA_CACHE

    try:
        children = _list_folder_children(folder_id)
        docs = []

        for f in children:
            file_id = f.get("id")
            name = f.get("name")
            mime = f.get("mimeType")
            modified = f.get("modifiedTime")
            preview = ""

            # For Google Docs, pull a short preview snippet
            if mime == "application/vnd.google-apps.document":
                txt = export_doc_as_text(file_id)
                if txt:
                    # Normalize newlines for JSON/log safety
                    preview = txt.replace("\r", "").replace("\n", "\\n")
                    if len(preview) > 320:
                        preview = preview[:320]

            docs.append(
                {
                    "id": file_id,
                    "name": name,
                    "mimeType": mime,
                    "modifiedTime": modified,
                    "preview": preview,
                }
            )

        _ARKADIA_CACHE = {
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "documents": docs,
            "error": None,
        }

    except Exception as e:
        print("[ArkadiaDriveSync] refresh failed:", e)
        _ARKADIA_CACHE["error"] = str(e)

    return _ARKADIA_CACHE


def get_cached_corpus() -> Dict[str, Any]:
    """
    Return the current cached snapshot (used by /arkadia/sync).
    """
    return {
        "last_sync": _ARKADIA_CACHE.get("last_sync"),
        "documents": _ARKADIA_CACHE.get("documents", []),
        "error": _ARKADIA_CACHE.get("error"),
    }


def get_corpus_context(max_docs: int = 2) -> str:
    """
    Build a human-readable context block from the cached Drive listing.
    This is what you saw printed at /arkadia/corpus.
    """
    docs = _ARKADIA_CACHE.get("documents", [])
    if not docs:
        return (
            "▣ ARKADIA CORPUS CONTEXT ▣\n"
            "(no Drive documents cached)\n"
            "▣ END CORPUS ▣"
        )

    lines: List[str] = []
    lines.append("▣ ARKADIA CORPUS CONTEXT ▣")
    if _ARKADIA_CACHE.get("last_sync"):
        lines.append(f"(Last Drive sync: {_ARKADIA_CACHE['last_sync']})")
    lines.append("")
    lines.append("— Top Arkadia documents —")

    for d in docs[:max_docs]:
        lines.append(f"* {d.get('name')} [{d.get('mimeType')}]")
        preview = (d.get("preview") or "").strip()
        if preview:
            lines.append("    " + preview[:260])
        lines.append("")

    lines.append("▣ END CORPUS ▣")
    return "\n".join(lines)


# ---------------------------------------------------------
# Raw corpus snapshot (for compression pipeline)
# ---------------------------------------------------------

def build_corpus_snapshot(map_path: str = "arkadia_corpus_map.json") -> Dict[str, Any]:
    """
    Build a raw full-text corpus snapshot based on arkadia_corpus_map.json.

    arkadia_corpus_map.json structure example:
    {
      "A01": {
        "drive_id": "DRIVE_FILE_ID",
        "category": "core_paper"
      },
      "HEART_NODE_ACTIVATION": {
        "drive_id": "1UwvMa4VG_ZnwBPgaIc5UEP32TQpYdZJjMmxStosA7wQ",
        "category": "scroll"
      }
    }
    """
    try:
        with open(map_path, "r", encoding="utf-8") as f:
            corpus_map = json.load(f)
    except Exception as e:
        print("[ArkadiaDriveSync] cannot load corpus map:", e)
        return {}

    docs: List[Dict[str, Any]] = []

    for key, info in corpus_map.items():
        file_id = info.get("drive_id")
        if not file_id:
            continue

        full_text = export_doc_as_text(file_id)
        if not full_text:
            continue

        docs.append(
            {
                "key": key,
                "drive_id": file_id,
                "category": info.get("category", "unknown"),
                "full_text": full_text,
            }
        )

    snapshot = {
        "last_build": datetime.utcnow().isoformat() + "Z",
        "docs": docs,
    }

    try:
        with open(CORPUS_SNAPSHOT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        print("[ArkadiaDriveSync] wrote raw corpus snapshot to", CORPUS_SNAPSHOT_FILE)
    except Exception as e:
        print("[ArkadiaDriveSync] failed to write snapshot:", e)

    return snapshot
