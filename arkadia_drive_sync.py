import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

ARKADIA_FOLDER_ID = os.getenv("ARKADIA_FOLDER_ID")
SERVICE_ACCOUNT_JSON_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_FILE")

_cache_snap = {}

def _get_drive_service():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON_FILE)
    return build("drive", "v3", credentials=creds)

def _list_drive_files_recursive(service, folder_id: str):
    """Recursively list all files in a folder, including subfolders."""
    all_files = []

    def _recurse(current_folder_id, path_prefix=""):
        query = f"'{current_folder_id}' in parents and trashed = false"
        page_token = None
        while True:
            resp = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageSize=1000,
                pageToken=page_token
            ).execute()
            for f in resp.get("files", []):
                full_path = f"{path_prefix}/{f['name']}".lstrip("/")
                if f['mimeType'] == "application/vnd.google-apps.folder":
                    _recurse(f['id'], path_prefix=full_path)
                else:
                    all_files.append({
                        "id": f["id"],
                        "name": f["name"],
                        "mimeType": f["mimeType"],
                        "modifiedTime": f.get("modifiedTime"),
                        "full_path": full_path,
                        "preview": ""
                    })
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    _recurse(folder_id)
    return all_files

def refresh_arkadia_cache(force=False):
    global _cache_snap
    if _cache_snap and not force:
        return _cache_snap

    snap = {"last_sync": datetime.utcnow().isoformat(), "documents": [], "error": None}
    if not ARKADIA_FOLDER_ID or not SERVICE_ACCOUNT_JSON_FILE:
        snap["error"] = "ARKADIA_FOLDER_ID or SERVICE_ACCOUNT_JSON_FILE not set"
        _cache_snap = snap
        return snap

    try:
        service = _get_drive_service()
        snap["documents"] = _list_drive_files_recursive(service, ARKADIA_FOLDER_ID)
    except Exception as e:
        snap["error"] = str(e)

    _cache_snap = snap
    return snap

def build_tree_with_paths(docs):
    """Build nested tree nodes from flat list using full_path"""
    tree = {}
    for d in docs:
        parts = d["full_path"].split("/")
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = d
    return tree

def get_corpus_context(max_documents=5, max_preview_chars=300):
    from random import sample
    docs = _cache_snap.get("documents", [])
    if not docs:
        return []
    selected = sample(docs, min(len(docs), max_documents))
    for d in selected:
        # Here you can implement smart preview generation or weighting later
        d["preview"] = d.get("preview")[:max_preview_chars]
    return selected
