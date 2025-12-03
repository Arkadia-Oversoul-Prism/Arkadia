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
CORPUS_MAP_FILE = "arkadia_corpus_map.json"

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

def _build_tree_with_paths(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Build a simple id->doc map so we can walk parents to make full_path
    id_map = {d["id"]: d for d in docs}
    for d in docs:
        parents = d.get("parents") or []
        # reconstruct path by walking up first-parent chain (best-effort)
        name = d.get("name") or ""
        parts = [name]
        visited = set()
        cur_parents = parents
        while cur_parents:
            pid = cur_parents[0]
            if pid in visited or pid not in id_map:
                break
            visited.add(pid)
            parent = id_map.get(pid)
            if not parent:
                break
            parts.insert(0, parent.get("name",""))
            cur_parents = parent.get("parents") or []
        d["full_path"] = "/" + "/".join([p for p in parts if p])
    return docs

def _write_corpus_map(docs: List[Dict[str, Any]]) -> None:
    """
    Write a flat path -> metadata map to CORPUS_MAP_FILE.
    Only include non-folder documents (text/docs).
    """
    flat = {}
    for d in docs:
        mime = d.get("mimeType","")
        if mime == "application/vnd.google-apps.folder":
            continue
        path = d.get("full_path") or d.get("name") or d.get("id")
        flat[path] = {
            "id": d.get("id"),
            "name": d.get("name"),
            "mimeType": mime,
            "modifiedTime": d.get("modifiedTime"),
            "preview": d.get("preview") or ""
        }
    try:
        with open(CORPUS_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(flat, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[arkadia_drive_sync] error writing corpus map:", e)

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
                "id": f.get("id"),
                "name": f.get("name"),
                "mimeType": f.get("mimeType"),
                "modifiedTime": f.get("modifiedTime"),
                "preview": preview,
                "parents": f.get("parents") or []
            })
        docs_with_paths = _build_tree_with_paths(documents)
        # save cache
        _ARKADIA_CACHE = {
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "documents": docs_with_paths,
            "error": None
        }
        # write flat corpus map for fast path lookup
        _write_corpus_map(docs_with_paths)
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
