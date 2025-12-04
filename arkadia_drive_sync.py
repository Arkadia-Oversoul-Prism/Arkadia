import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

def _get_drive_service():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    service = build("drive", "v3", credentials=creds)
    return service

def _list_drive_files_recursive(service, folder_id: str):
    results = []
    def _recurse(current_folder_id, path_prefix=""):
        query = f"'{current_folder_id}' in parents and trashed=false"
        page_token = None
        while True:
            response = service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, parents)",
                pageToken=page_token
            ).execute()
            for file in response.get("files", []):
                full_path = f"{path_prefix}{file['name']}"
                results.append({
                    "id": file["id"],
                    "name": file["name"],
                    "full_path": full_path,
                    "mimeType": file["mimeType"],
                })
                if file["mimeType"] == "application/vnd.google-apps.folder":
                    _recurse(file["id"], f"{full_path}/")
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
    _recurse(folder_id)
    return results

def refresh_arkadia_cache(force=False):
    folder_id = os.environ.get("ARKADIA_FOLDER_ID")
    service = _get_drive_service()
    documents = _list_drive_files_recursive(service, folder_id)
    last_sync = datetime.utcnow().isoformat()
    return {
        "documents": documents,
        "last_sync": last_sync,
        "error": None
    }

def build_tree_with_paths(docs):
    tree = {}
    for doc in docs:
        parts = doc["full_path"].split("/")
        current = tree
        for part in parts:
            current = current.setdefault(part, {})
    return tree

def get_corpus_context(max_documents=5, max_preview_chars=300):
    from google.generativeai import text
    # simple smart-weighted context: select first N documents, truncate each to max_preview_chars
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents", [])
    previews = []
    for d in docs[:max_documents]:
        # weight = length of document name as a naive weight example
        weight = len(d["name"])
        preview_text = f"{d['name']}: " + "..." * min(weight, 5)
        previews.append(preview_text[:max_preview_chars])
    return "\n\n".join(previews)
