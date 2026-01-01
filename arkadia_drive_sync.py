import os
import json
import time
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache file location
CACHE_FILE = "arkadia_cache.json"

# ---------------------------
# Google Drive Service Setup
# ---------------------------
def _get_drive_service():
    """Get authenticated Google Drive service."""
    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "/run/service_account.json")
    
    # Check if service account JSON exists
    if not creds_path or not os.path.isfile(creds_path):
        logger.warning(f"Service account JSON file not found at: {creds_path}")
        raise FileNotFoundError(f"Service account JSON file not found at: {creds_path}")
    
    # Validate JSON content
    try:
        with open(creds_path, 'r') as f:
            json_content = json.load(f)
            if not json_content.get('type') == 'service_account':
                raise ValueError("Invalid service account JSON format")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid service account JSON: {e}")
        raise ValueError(f"Invalid service account JSON: {e}")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path, 
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        logger.info("Google Drive service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Google Drive service: {e}")
        raise

# ---------------------------
# Recursive Folder Listing
# ---------------------------
def _list_drive_files_recursive(service, folder_id: str) -> List[Dict]:
    """Recursively list all files in a Google Drive folder."""
    documents = []

    def _recurse(current_folder_id, path_prefix=""):
        query = f"'{current_folder_id}' in parents and trashed=false"
        try:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime, size)"
            ).execute()
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            return

        for file in response.get("files", []):
            full_path = os.path.join(path_prefix, file['name']) if path_prefix else file['name']
            documents.append({
                "id": file['id'],
                "name": file['name'],
                "full_path": full_path,
                "mimeType": file['mimeType'],
                "parents": file.get("parents", []),
                "modifiedTime": file.get("modifiedTime"),
                "size": file.get("size", "0")
            })
            
            # Recurse into folders
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                _recurse(file['id'], path_prefix=full_path)

        # Handle pagination
        next_page = response.get("nextPageToken")
        while next_page:
            response = service.files().list(
                q=query,
                spaces='drive',
                pageToken=next_page,
                fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime, size)"
            ).execute()
            
            for file in response.get("files", []):
                full_path = os.path.join(path_prefix, file['name']) if path_prefix else file['name']
                documents.append({
                    "id": file['id'],
                    "name": file['name'],
                    "full_path": full_path,
                    "mimeType": file['mimeType'],
                    "parents": file.get("parents", []),
                    "modifiedTime": file.get("modifiedTime"),
                    "size": file.get("size", "0")
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
    """Build a tree structure from document list."""
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
def get_corpus_context(snapshot: Dict, max_documents: int = 5, max_preview_chars: int = 300) -> str:
    """Generate context summary from document snapshot."""
    documents = snapshot.get("documents", [])
    if not documents:
        return "No documents available in corpus."
    
    # Filter out folders and prioritize by path depth and name length
    file_docs = [doc for doc in documents if doc.get('mimeType') != 'application/vnd.google-apps.folder']
    weighted_docs = sorted(file_docs, key=lambda d: (d['full_path'].count(os.sep), len(d['name'])))
    context_docs = weighted_docs[:max_documents]
    
    context = []
    for doc in context_docs:
        preview_text = doc.get("preview", doc.get("name", ""))[:max_preview_chars]
        context.append(f"[{doc['full_path']}] {preview_text}")
    
    return "\n".join(context)

# ---------------------------
# Main Interface Functions
# ---------------------------
def refresh_arkadia_cache(force: bool = False) -> Dict:
    """Refresh the Arkadia corpus cache from Google Drive."""
    folder_id = os.environ.get("ARKADIA_FOLDER_ID")
    if not folder_id:
        logger.error("ARKADIA_FOLDER_ID environment variable not set")
        return {"last_sync": None, "error": "ARKADIA_FOLDER_ID not set", "documents": []}

    # Check if we should use cached version
    if not force and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                snap = json.load(f)
                logger.info("Cache loaded from file")
                return snap
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}")

    # Fetch fresh data from Google Drive
    try:
        service = _get_drive_service()
        documents = _list_drive_files_recursive(service, folder_id)
        
        snap = {
            "last_sync": datetime.utcnow().isoformat(),
            "error": None,
            "documents": documents,
            "total_documents": len(documents)
        }
        
        # Save to cache
        with open(CACHE_FILE, "w") as f:
            json.dump(snap, f, indent=2)
        
        logger.info(f"Successfully cached {len(documents)} documents")
        return snap
        
    except Exception as e:
        logger.error(f"Failed to fetch drive files: {e}")
        snap = {
            "last_sync": None,
            "error": str(e),
            "documents": [],
            "total_documents": 0
        }
        return snap

def get_arkadia_corpus() -> Dict:
    """Get the cached Arkadia corpus, refreshing if needed."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                snap = json.load(f)
                logger.info("Returning cached corpus")
                return snap
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}")
    
    # No cache exists, refresh
    logger.info("No cache found, refreshing corpus")
    return refresh_arkadia_cache(force=True)
