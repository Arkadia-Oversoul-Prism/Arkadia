"""
arkadia_drive_sync.py

Robust Google Drive sync helper for Arkadia.

- Reads GOOGLE_SERVICE_ACCOUNT_JSON env var (expected as JSON string).
- Reads ARKADIA_FOLDER_ID env var for the top-level folder.
- Recursively lists files and folders under the folder id.
- Fetches text previews for Google Docs and plaintext files.
- Exposes:
    refresh_arkadia_cache(force=False) -> { last_sync, documents, error }
    build_tree_with_paths(docs) -> list-like tree structure
    get_corpus_context(max_documents=5, max_preview_chars=300) -> str
"""

import os
import json
import io
from datetime import datetime
from typing import List, Dict, Any, Optional

# These imports may fail in environments without the packages; we handle that gracefully.
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account
    _HAS_GOOGLE = True
except Exception:
    _HAS_GOOGLE = False

# Public cache (module-level)
_ARKADIA_CACHE: Dict[str, Any] = {"last_sync": None, "documents": [], "error": None}


def _get_drive_service():
    """
    Build a Drive service client using the JSON stored in GOOGLE_SERVICE_ACCOUNT_JSON.
    Raise RuntimeError with a clear message if missing/invalid.
    """
    if not _HAS_GOOGLE:
        raise RuntimeError("googleapiclient / google oauth libraries are not installed in this environment.")

    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON env var is not set.")
    try:
        info = json.loads(sa_json)
    except Exception as e:
        raise RuntimeError(f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON: {e}") from e

    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def _list_drive_files_recursive(service, folder_id: str) -> List[Dict[str, Any]]:
    """
    Recursively walk the Drive folder and return a flat list of file dicts with fields:
    id, name, mimeType, parents, full_path
    Uses a stack recursion that builds full_path using path_prefix.
    """
    items: List[Dict[str, Any]] = []
    seen = set()

    def _recurse(current_folder_id: str, path_prefix: str = ""):
        page_token = None
        q = f"'{current_folder_id}' in parents and trashed = false"
        while True:
            resp = service.files().list(
                q=q,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, parents)",
                pageToken=page_token,
            ).execute()
            for f in resp.get("files", []):
                fid = f.get("id")
                if fid in seen:
                    continue
                seen.add(fid)
                name = f.get("name")
                mime = f.get("mimeType")
                full_path = f"{path_prefix}{name}"
                items.append(
                    {
                        "id": fid,
                        "name": name,
                        "mimeType": mime,
                        "parents": f.get("parents") or [],
                        "full_path": full_path,
                    }
                )
                # If folder, recurse into it
                if mime == "application/vnd.google-apps.folder":
                    _recurse(fid, path_prefix=f"{full_path}/")
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    _recurse(folder_id, path_prefix="")
    return items


def _download_doc_preview(service, file_id: str, mime_type: str, max_chars: int = 600) -> str:
    """
    Download small text preview for Google Docs (export plain text) or plaintext files.
    Returns empty string on unsupported mime or error.
    """
    try:
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, mimeType="text/plain")
        elif mime_type in ("text/plain", "text/markdown", "text/csv", "text/x-markdown"):
            request = service.files().get_media(fileId=file_id)
        else:
            return ""
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        text = fh.getvalue().decode("utf-8", errors="ignore")
        # normalize whitespace a little
        text = text.replace("\r\n", "\n").strip()
        return text[:max_chars]
    except HttpError as e:
        # Drive may return transient 500 / 404 etc — surface limited message
        print(f"[arkadia_drive_sync] preview HttpError for {file_id}: {e}")
        return ""
    except Exception as e:
        print(f"[arkadia_drive_sync] preview error for {file_id}: {e}")
        return ""


def refresh_arkadia_cache(force: bool = False) -> Dict[str, Any]:
    """
    Refresh the in-memory Arkadia snapshot from Drive.
    Returns: dict with keys: last_sync, documents (list), error (None or message).
    Does not raise — always returns a dict so callers can continue running.
    """
    global _ARKADIA_CACHE

    folder_id = os.getenv("ARKADIA_FOLDER_ID", "").strip()
    if not folder_id:
        _ARKADIA_CACHE = {"last_sync": None, "documents": [], "error": "ARKADIA_FOLDER_ID env var is not set."}
        return _ARKADIA_CACHE

    if not _HAS_GOOGLE:
        _ARKADIA_CACHE = {"last_sync": None, "documents": [], "error": "googleapiclient not installed in environment."}
        return _ARKADIA_CACHE

    try:
        service = _get_drive_service()
    except Exception as e:
        _ARKADIA_CACHE = {"last_sync": None, "documents": [], "error": f"Drive auth/build error: {e}"}
        return _ARKADIA_CACHE

    try:
        flat_files = _list_drive_files_recursive(service, folder_id)
        documents: List[Dict[str, Any]] = []
        for f in flat_files:
            mime = f.get("mimeType")
            fid = f.get("id")
            name = f.get("name")
            path = f.get("full_path")
            preview = ""
            # Only attempt preview for text-like files and Google Docs
            if mime in ("application/vnd.google-apps.document", "text/plain", "text/markdown", "text/csv", "text/x-markdown"):
                preview = _download_doc_preview(service, fid, mime, max_chars=1200)
            documents.append(
                {
                    "id": fid,
                    "name": name,
                    "mimeType": mime,
                    "full_path": path,
                    "preview": preview,
                }
            )

        _ARKADIA_CACHE = {"last_sync": datetime.utcnow().isoformat() + "Z", "documents": documents, "error": None}
        return _ARKADIA_CACHE

    except HttpError as e:
        _ARKADIA_CACHE = {"last_sync": None, "documents": [], "error": f"Drive API HttpError: {e}"}
        return _ARKADIA_CACHE
    except Exception as e:
        _ARKADIA_CACHE = {"last_sync": None, "documents": [], "error": f"Unexpected error: {e}"}
        return _ARKADIA_CACHE


def get_arkadia_snapshot() -> Dict[str, Any]:
    """Return the cached Arkadia snapshot."""
    return _ARKADIA_CACHE


def build_tree_with_paths(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build a simple tree (list of top-level nodes) where each node is:
      { "id","name","mimeType","preview","children": [...], "full_path" }
    This returns a list of top-level node dicts. Useful for console tree UI.
    """
    # Build a nested dict of dicts keyed by path segments
    root = {}
    meta = {}  # map full_path -> doc
    for d in docs:
        full = d.get("full_path") or d.get("name")
        meta[full] = d

    for full in meta.keys():
        parts = full.split("/")
        node = root
        for p in parts:
            node = node.setdefault(p, {})

    # Convert nested dict into list structure recursively
    def convert(node_dict, prefix=""):
        nodes = []
        for name, subtree in sorted(node_dict.items()):
            full_path = (prefix + name) if prefix else name
            doc_meta = meta.get(full_path)
            entry = {
                "name": name,
                "full_path": full_path,
                "mimeType": doc_meta.get("mimeType") if doc_meta else ("application/vnd.google-apps.folder" if subtree else "unknown"),
                "preview": (doc_meta.get("preview") if doc_meta else "") if doc_meta else "",
                "children": convert(subtree, prefix=(full_path + "/") if subtree else "")
            }
            nodes.append(entry)
        return nodes

    return convert(root, prefix="")

def get_corpus_context(max_documents: int = 5, max_preview_chars: int = 300) -> str:
    """
    Produce a compact human-readable corpus context string.
    Truncates previews to max_preview_chars and selects the first max_documents entries.
    """
    snap = _ARKADIA_CACHE
    last_sync = snap.get("last_sync")
    docs: List[Dict[str, Any]] = snap.get("documents") or []
    error = snap.get("error")

    if error:
        return f"▣ ARKADIA CORPUS CONTEXT ▣\n(Error: {error})\n▣ END CORPUS ▣"

    if not docs:
        return "▣ ARKADIA CORPUS CONTEXT ▣\n\nNo Arkadia documents are currently cached.\n▣ END CORPUS ▣"

    lines = ["▣ ARKADIA CORPUS CONTEXT ▣"]
    if last_sync:
        lines.append(f"(Last Drive sync: {last_sync})")
    lines.append("")
    lines.append("— Sample of Arkadia documents —")

    for d in docs[:max_documents]:
        name = d.get("name", "")
        path = d.get("full_path", name)
        mime = d.get("mimeType", "")
        preview = (d.get("preview") or "")[:max_preview_chars]
        lines.append(f"* {path} [{mime}]")
        if preview:
            plines = preview.splitlines()
            for pl in plines[:6]:
                lines.append(f"    {pl}")
        lines.append("")

    lines.append("▣ END CORPUS ▣")
    return "\n".join(lines)
