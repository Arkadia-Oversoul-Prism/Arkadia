"""
Arkadia Corpus — Google Drive Source

Lists and fetches documents from a Google Drive folder.

Config env vars:
  CORPUS_GDRIVE_FOLDER_ID          The Drive folder ID to scan
  CORPUS_GDRIVE_SERVICE_ACCOUNT    Service account JSON as a string (env var)
  CORPUS_GDRIVE_API_KEY            API key (for public files, simpler setup)
  CORPUS_GDRIVE_CATEGORY           Category to assign all Drive docs (default: GDRIVE)
  CORPUS_GDRIVE_PRIORITY           Priority (default: 2)
  CORPUS_GDRIVE_INCLUDE_TYPES      Comma-sep MIME types to include
                                   Default: Google Docs + plain text + markdown

Setup:
  Option A — Service account (recommended for private Drive):
    1. Create a Google Cloud project, enable Drive API.
    2. Create a service account, download JSON key.
    3. Share the target Drive folder with the service account email.
    4. Set CORPUS_GDRIVE_SERVICE_ACCOUNT to the JSON key content.
    5. Set CORPUS_GDRIVE_FOLDER_ID to the folder ID.

  Option B — API key (public files only):
    1. Create an API key in Google Cloud Console.
    2. Set CORPUS_GDRIVE_API_KEY.
    3. Set CORPUS_GDRIVE_FOLDER_ID.
"""

import os
import json
import requests
from .base import BaseCorpusSource, CorpusDoc


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


GOOGLE_MIME_DOC = "application/vnd.google-apps.document"
INCLUDE_MIME = {
    GOOGLE_MIME_DOC,
    "text/markdown",
    "text/plain",
    "application/octet-stream",
}


class GoogleDriveSource(BaseCorpusSource):
    name = "gdrive"

    def __init__(self):
        self.folder_id = _env("CORPUS_GDRIVE_FOLDER_ID")
        self.service_account_json = _env("CORPUS_GDRIVE_SERVICE_ACCOUNT")
        self.api_key = _env("CORPUS_GDRIVE_API_KEY")
        self.category = _env("CORPUS_GDRIVE_CATEGORY", "GDRIVE")
        self.priority = int(_env("CORPUS_GDRIVE_PRIORITY", "2"))
        self._access_token: str | None = None

    def is_configured(self) -> bool:
        return bool(self.folder_id and (self.service_account_json or self.api_key))

    def _get_access_token(self) -> str | None:
        if not self.service_account_json:
            return None
        if self._access_token:
            return self._access_token
        try:
            import base64, time, hmac, hashlib
            sa = json.loads(self.service_account_json)
            scope = "https://www.googleapis.com/auth/drive.readonly"
            iat = int(time.time())
            exp = iat + 3600
            header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).rstrip(b"=")
            payload = base64.urlsafe_b64encode(json.dumps({
                "iss": sa["client_email"],
                "scope": scope,
                "aud": "https://oauth2.googleapis.com/token",
                "iat": iat,
                "exp": exp,
            }).encode()).rstrip(b"=")
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            private_key = load_pem_private_key(sa["private_key"].encode(), password=None)
            msg = header + b"." + payload
            sig = private_key.sign(msg, padding.PKCS1v15(), hashes.SHA256())
            sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=")
            jwt = (msg + b"." + sig_b64).decode()
            resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt},
                timeout=10,
            )
            resp.raise_for_status()
            self._access_token = resp.json()["access_token"]
            return self._access_token
        except Exception as e:
            print(f"[GDrive] Auth error: {e}")
            return None

    def _drive_headers(self) -> dict:
        h = {}
        token = self._get_access_token()
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _drive_params(self, extra: dict = None) -> dict:
        p = {}
        if self.api_key and not self._get_access_token():
            p["key"] = self.api_key
        if extra:
            p.update(extra)
        return p

    def discover(self) -> list[CorpusDoc]:
        if not self.is_configured():
            print("[GDrive] Not configured — set CORPUS_GDRIVE_FOLDER_ID and credentials.")
            return []
        try:
            q = f"'{self.folder_id}' in parents and trashed=false"
            params = self._drive_params({"q": q, "fields": "files(id,name,mimeType,description)", "pageSize": "200"})
            r = requests.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=self._drive_headers(),
                params=params,
                timeout=15,
            )
            r.raise_for_status()
            files = r.json().get("files", [])
            docs = []
            for f in files:
                mime = f.get("mimeType", "")
                if not any(m in mime for m in ["google-apps.document", "text/", "markdown", "octet-stream"]):
                    continue
                docs.append(CorpusDoc(
                    id=f"gdrive:{f['id']}",
                    source=self.name,
                    label=f["name"],
                    description=f.get("description", ""),
                    category=self.category,
                    priority=self.priority,
                    meta={"file_id": f["id"], "mime_type": mime},
                ))
            print(f"[GDrive] Discovered {len(docs)} documents in folder {self.folder_id}.")
            return docs
        except Exception as e:
            print(f"[GDrive] Discover error: {e}")
            return []

    def fetch_content(self, doc: CorpusDoc) -> str:
        file_id = doc.meta.get("file_id")
        mime = doc.meta.get("mime_type", "")
        if GOOGLE_MIME_DOC in mime:
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
            params = self._drive_params({"mimeType": "text/plain"})
        else:
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
            params = self._drive_params({"alt": "media"})
        r = requests.get(url, headers=self._drive_headers(), params=params, timeout=15)
        r.raise_for_status()
        return r.text
