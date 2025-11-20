# arkadia_drive_sync.py
# Arkadia — Google Drive Sync using Service Account (Recursive, Full-Corpus Mode)
# Reads the ARKADIA folder (and all subfolders) from Drive and caches a corpus snapshot.

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Env vars on Render
SERVICE_ACCOUNT_ENV = "GDRIVE_SERVICE_ACCOUNT_JSON"
FOLDER_ID_ENV = "ARKADIA_FOLDER_ID"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class ArkadiaDriveSync:
    """
    Central interface for Arkadia <-> Google Drive.
    - sync_arkadia_folder(): refresh cache from Drive
    - get_arkadia_snapshot(): raw JSON of documents
    - get_corpus_context(): pretty-printed summary for prompting
    """

    _CACHE: Dict[str, Any] = {
        "last_sync": None,
        "documents": [],   # list of {id,name,mimeType,modifiedTime,preview,path}
        "error": None,
    }

    # ---------------------------------------------------------
    # LOW-LEVEL HELPERS
    # ---------------------------------------------------------

    @classmethod
    def _build_drive_service(cls):
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

    @classmethod
    def _list_children(cls, service, folder_id: str) -> List[Dict[str, Any]]:
        """List direct children of a folder."""
        results: List[Dict[str, Any]] = []
        page_token: Optional[str] = None

        while True:
            resp = (
                service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields=(
                        "nextPageToken, files(id, name, mimeType, modifiedTime)"
                    ),
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

    @classmethod
    def _extract_google_doc_text(cls, service, file_id: str) -> str:
        """Export a Google Doc as plain text and return its contents."""
        try:
            request = service.files().export_media(
                fileId=file_id, mimeType="text/plain"
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            content_bytes = fh.read()
            try:
                return content_bytes.decode("utf-8", errors="replace")
            except Exception:
                return content_bytes.decode("latin-1", errors="replace")
        except Exception as e:
            return f"[ERROR exporting Google Doc: {e}]"

    @classmethod
    def _extract_binary_preview(cls, service, file_info: Dict[str, Any]) -> str:
        """
        For non-Google-Doc files.
        Option D: we at least index them with a placeholder preview.
        (Later we can add PDF text extraction or OCR here.)
        """
        mime = file_info.get("mimeType", "")
        name = file_info.get("name", "")

        # For now, don't download binaries — just describe them.
        # This avoids heavy traffic and keeps Render lightweight.
        return f"[{mime} asset: {name}]"

    @classmethod
    def _walk_folder(
        cls,
        service,
        folder_id: str,
        path_prefix: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Recursively walk a folder and collect docs.
        Each entry includes:
        - id, name, mimeType, modifiedTime, preview, path
        """
        items: List[Dict[str, Any]] = []

        children = cls._list_children(service, folder_id)

        for f in children:
            fid = f.get("id")
            name = f.get("name", "")
            mime = f.get("mimeType", "")
            modified = f.get("modifiedTime", "")
            # Build a logical path like "00_Master/Arkadia_Codex_Master_Index.md"
            current_path = f"{path_prefix}/{name}".lstrip("/")

            if mime == "application/vnd.google-apps.folder":
                # Recurse into subfolder
                sub_items = cls._walk_folder(service, fid, current_path)
                items.extend(sub_items)
                # Also store the folder itself as a node (no preview)
                items.append(
                    {
                        "id": fid,
                        "name": name,
                        "mimeType": mime,
                        "modifiedTime": modified,
                        "preview": "",
                        "path": current_path + "/",
                    }
                )
            else:
                # Document / asset
                if mime == "application/vnd.google-apps.document":
                    text = cls._extract_google_doc_text(service, fid)
                    preview = text[:600] if text else ""
                else:
                    # Non-doc file (pdf, json, images, etc.) — just mark presence
                    preview = cls._extract_binary_preview(service, f)

                items.append(
                    {
                        "id": fid,
                        "name": name,
                        "mimeType": mime,
                        "modifiedTime": modified,
                        "preview": preview,
                        "path": current_path,
                    }
                )

        return items

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    @classmethod
    def sync_arkadia_folder(cls) -> Dict[str, Any]:
        """
        Refresh the in-memory cache from Google Drive.
        Walks the full ARKADIA folder tree recursively (option D).
        """
        root_id = os.getenv(FOLDER_ID_ENV, "").strip()
        if not root_id:
            cls._CACHE["error"] = (
                "ARKADIA_FOLDER_ID env var is not set. "
                "Set it to your Arkadia root Drive folder ID."
            )
            cls._CACHE["documents"] = []
            cls._CACHE["last_sync"] = None
            return cls._CACHE

        try:
            service = cls._build_drive_service()
            docs = cls._walk_folder(service, root_id, path_prefix="ARKADIA")

            cls._CACHE["last_sync"] = datetime.utcnow().isoformat() + "Z"
            cls._CACHE["documents"] = docs
            cls._CACHE["error"] = None
        except Exception as e:
            cls._CACHE["error"] = str(e)
            cls._CACHE["documents"] = []
            cls._CACHE["last_sync"] = None

        return cls._CACHE

    @classmethod
    def get_arkadia_snapshot(cls) -> Dict[str, Any]:
        """
        Return the raw cache (for /arkadia/sync endpoint).
        If never synced, perform a sync once.
        """
        if cls._CACHE["last_sync"] is None and cls._CACHE["error"] is None:
            cls.sync_arkadia_folder()

        # Light copy
        return {
            "last_sync": cls._CACHE["last_sync"],
            "documents": cls._CACHE["documents"],
            "error": cls._CACHE["error"],
        }

    @classmethod
    def get_corpus_context(cls, max_docs: int = 6) -> str:
        """
        Produce a compact text block for prompting / diagnostics.
        This is what ArkanaBrain uses as CORPUS CONTEXT.
        """
        snapshot = cls.get_arkadia_snapshot()
        docs = snapshot.get("documents", [])
        last_sync = snapshot.get("last_sync")
        error = snapshot.get("error")

        lines: List[str] = []
        lines.append("▣ ARKADIA CORPUS CONTEXT ▣")

        if error:
            lines.append("")
            lines.append(f"[Drive Sync Error] {error}")
            lines.append("▣ END CORPUS ▣")
            return "\n".join(lines)

        if not docs:
            lines.append("")
            lines.append("No Arkadia documents are currently cached.")
            lines.append("▣ END CORPUS ▣")
            return "\n".join(lines)

        if last_sync:
            lines.append(f"(Last Drive sync: {last_sync})")
        lines.append("")
        lines.append("— Sample of Arkadia documents —")

        # Prefer non-folder docs with real previews
        def sort_key(d: Dict[str, Any]):
            # Folders last, docs with preview first
            is_folder = d.get("mimeType") == "application/vnd.google-apps.folder"
            has_preview = bool(d.get("preview", "").strip())
            # sort by: not folder, has_preview, name
            return (is_folder, not has_preview, d.get("path", d.get("name", "")))

        sorted_docs = sorted(docs, key=sort_key)
        count = 0

        for d in sorted_docs:
            if count >= max_docs:
                break
            name = d.get("name", "")
            mime = d.get("mimeType", "")
            path = d.get("path", name)
            preview = (d.get("preview") or "").strip().replace("\r", " ")
            if len(preview) > 280:
                preview = preview[:277] + "..."

            lines.append(f"* {path} [{mime}]")
            if preview:
                for line in preview.split("\n")[:3]:
                    if line.strip():
                        lines.append(f"    {line.strip()}")
            count += 1

        lines.append("")
        lines.append("▣ END CORPUS ▣")
        return "\n".join(lines)
