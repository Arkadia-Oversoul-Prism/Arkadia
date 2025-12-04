import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Google Drive Service Setup
# ---------------------------
def _get_drive_service():
    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_FILE")
    if not creds_path or not os.path.isfile(creds_path):
        raise FileNotFoundError("Service account JSON file not found at: {}".format(creds_path))
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=["https://www.googleapis.com/auth/drive"])
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return service

# ---------------------------
# Recursive Folder Listing
# ---------------------------
def _list_drive_files_recursive(service, folder_id: str):
    documents = []

    def _recurse(current_folder_id, path_prefix=""):
        query = f"'{current_folder_id}' in parents and trashed=false"
        try:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields="nextPageToken, files(id, name, mimeType, parents)"
            ).execute()
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            return

        for file in response.get("files", []):
            full_path = os.path.join(path_prefix, file['name'])
            documents.append({
                "id": file['id'],
                "name": file['name'],
                "full_path": full_path,
                "mimeType": file['mimeType'],
                "parents": file.get("parents", [])
            })
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                _recurse(file['id'], path_prefix=full_path)

        # handle pagination
        next_page = response.get("nextPageToken")
        while next_page:
            response = service.files().list(
                q=query,
                spaces='drive',
                pageToken=next_page,
                fields="nextPageToken, files(id, name, mimeType, parents)"
            ).execute()
            for file in response.get("files", []):
                full_path = os.path.join(path_prefix, file['name'])
                documents.append({
                    "id": file['id'],
                    "name": file['name'],
                    "full_path": full_path,
                    "mimeType": file['mimeType'],
                    "parents": file.get("parents", [])
                })
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    _recurse(file['id'], path_prefix=full_path)
            next_page = response.get("nextPageToken")

    _recurse(folder_id)
    return documents

# ---------------------------
# Build Tree Data
# ---------------------------
def build_tree_with_paths(docs: List[Dict]):
    tree = {}
    path_map = {}
    for doc in docs:
        parts = doc['full_path'].split(os.sep)
        current = tree
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = doc
        path_map[doc['full_path']] = doc
    return tree, path_map

# ---------------------------
# Corpus Context & Smart Weighted Query
# ---------------------------
def get_corpus_context(documents: List[Dict], max_documents: int = 5, max_preview_chars: int = 300):
    # simple weighted approach: prioritize docs with shorter paths and recent first (simulation)
    weighted_docs = sorted(documents, key=lambda d: (d['full_path'].count(os.sep), len(d['name'])))
    context_docs = weighted_docs[:max_documents]
    context = []
    for doc in context_docs:
        preview_text = doc.get("preview", "")[:max_preview_chars]
        context.append(f"[{doc['full_path']}] {preview_text}")
    return "\n".join(context)

# ---------------------------
# Refresh Arkadia Cache
# ---------------------------
def refresh_arkadia_cache(force=False):
    folder_id = os.environ.get("ARKADIA_FOLDER_ID")
    if not folder_id:
        raise ValueError("ARKADIA_FOLDER_ID environment variable not set")

    cache_file = "arkadia_cache.json"
    snap = {}
    if not force and os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            snap = json.load(f)
            logger.info("Cache loaded from file")
            return snap

    service = _get_drive_service()
    try:
        documents = _list_drive_files_recursive(service, folder_id)
    except Exception as e:
        logger.error(f"Failed to fetch drive files: {e}")
        snap = {"last_sync": None, "error": str(e), "documents": []}
    else:
        snap = {"last_sync": str(json.dumps(os.times())), "error": None, "documents": documents}
        with open(cache_file, "w") as f:
            json.dump(snap, f, indent=2)
        logger.info(f"{len(documents)} documents cached")
    return snap
