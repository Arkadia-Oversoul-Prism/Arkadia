# -------------------------------
# arkadia_drive_sync.py (with tree flattening)
# -------------------------------

import os, json, io
from typing import List, Dict, Any
from datetime import datetime

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2 import service_account
    _HAS_GOOGLE = True
except Exception:
    _HAS_GOOGLE = False

SERVICE_ACCOUNT_ENV = "GDRIVE_SERVICE_ACCOUNT_JSON"
FOLDER_ID_ENV = "ARKADIA_FOLDER_ID"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
_ARKADIA_CACHE: Dict[str, Any] = {"last_sync": None, "documents": [], "error": None}

def _build_drive_service():
    if not _HAS_GOOGLE:
        raise RuntimeError("googleapiclient not available")
    sa_json = os.getenv(SERVICE_ACCOUNT_ENV, "").strip()
    if not sa_json:
        raise RuntimeError("GDRIVE_SERVICE_ACCOUNT_JSON env var not set")
    creds = service_account.Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def _walk_folder(service, folder_id: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen = set()
    def _walk(fid: str):
        page_token = None
        q = f"'{fid}' in parents and trashed=false"
        while True:
            resp = service.files().list(
                q=q,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, parents)",
                pageToken=page_token
            ).execute()
            for f in resp.get("files", []):
                fid2 = f.get("id")
                if fid2 in seen:
                    continue
                seen.add(fid2)
                items.append(f)
                if f.get("mimeType") == "application/vnd.google-apps.folder":
                    _walk(fid2)
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    _walk(folder_id)
    return items

def _download_preview(service, file_id: str, mime_type: str, max_chars: int = 600) -> str:
    try:
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, mimeType="text/plain")
        elif mime_type in ("text/plain","text/markdown","text/csv","text/x-markdown"):
            request = service.files().get_media(fileId=file_id)
        else:
            return ""
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue().decode("utf-8","ignore")[:max_chars]
    except Exception as e:
        print("[arkadia_drive_sync] preview error:", e)
        return ""

# --- NEW: build paths map ---
def _build_tree_with_paths(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    id_map = {d["id"]: d for d in docs}
    for d in docs:
        parents = d.get("parents") or []
        full_path = d["name"]
        current = d
        visited = set()
        while parents:
            pid = parents[0]
            if pid in visited or pid not in id_map:
                break
            visited.add(pid)
            parent = id_map[pid]
            full_path = parent["name"] + "/" + full_path
            parents = parent.get("parents") or []
        d["full_path"] = "/" + full_path
    return docs

def refresh_arkadia_cache(force: bool = False) -> Dict[str, Any]:
    global _ARKADIA_CACHE
    folder_id = os.getenv(FOLDER_ID_ENV, "").strip()
    if not folder_id:
        _ARKADIA_CACHE["error"] = "ARKADIA_FOLDER_ID not set"
        return _ARKADIA_CACHE
    if not _HAS_GOOGLE:
        _ARKADIA_CACHE["error"] = "googleapiclient not installed"
        return _ARKADIA_CACHE
    try:
        service = _build_drive_service()
        files = _walk_folder(service, folder_id)
        documents = []
        for f in files:
            preview = _download_preview(service, f.get("id"), f.get("mimeType"), max_chars=800) \
                      if f.get("mimeType") in ("application/vnd.google-apps.document","text/plain","text/markdown","text/csv","text/x-markdown") else ""
            documents.append({
                "id": f.get("id"), "name": f.get("name"), "path": None,
                "mimeType": f.get("mimeType"), "modifiedTime": f.get("modifiedTime"),
                "preview": preview,
                "parents": f.get("parents") or []
            })
        # attach full paths
        _ARKADIA_CACHE = {
            "last_sync": datetime.utcnow().isoformat()+"Z",
            "documents": _build_tree_with_paths(documents),
            "error": None
        }
    except Exception as e:
        _ARKADIA_CACHE["error"] = f"Sync error: {e}"
    return _ARKADIA_CACHE

def get_arkadia_snapshot() -> Dict[str, Any]:
    return _ARKADIA_CACHE

def get_corpus_context(max_documents: int = 6, max_preview_chars: int = 400) -> str:
    snap = _ARKADIA_CACHE
    docs = snap.get("documents") or []
    error = snap.get("error")
    lines = ["▣ ARKADIA CORPUS CONTEXT ▣"]
    if error:
        lines.append(f"(Error: {error})")
    if not docs:
        lines.append("No documents cached")
    else:
        if snap.get("last_sync"):
            lines.append(f"(Last sync: {snap['last_sync']})")
        for d in docs[:max_documents]:
            lines.append(f"* {d.get('name')} [{d.get('mimeType')}]")
            if d.get("preview"):
                lines.extend(d.get("preview").splitlines()[:6])
            lines.append(f"Full path: {d.get('full_path')}")
    lines.append("▣ END CORPUS ▣")
    return "\n".join(lines)

if __name__ == "__main__":
    print("arkadia_drive_sync test run. _HAS_GOOGLE =", _HAS_GOOGLE)
    print(refresh_arkadia_cache(force=True))
