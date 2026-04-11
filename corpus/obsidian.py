"""
Arkadia Corpus — Obsidian Source

Connects to Obsidian via the Local REST API community plugin.

Config env vars:
  CORPUS_OBSIDIAN_URL       Base URL of the Obsidian REST API.
                            Default: http://127.0.0.1:27123
  CORPUS_OBSIDIAN_TOKEN     API key from the plugin settings (required).
  CORPUS_OBSIDIAN_VAULT_DIR Subdirectory within vault to scan (optional).
                            If empty = entire vault.
  CORPUS_OBSIDIAN_CATEGORY  Category for all Obsidian notes (default: OBSIDIAN)
  CORPUS_OBSIDIAN_PRIORITY  Priority (default: 2)
  CORPUS_OBSIDIAN_TAG       Optional tag filter (e.g. "arkadia"). Only notes
                            with this tag are included.

Setup:
  1. Install the "Local REST API" plugin from the Obsidian community plugins.
  2. Enable it and copy the API key.
  3. Set CORPUS_OBSIDIAN_TOKEN in Replit Secrets.
  4. If running remotely (not localhost), set CORPUS_OBSIDIAN_URL to the
     exposed URL (e.g. via ngrok or Tailscale).

Obsidian Sync / Remote access:
  If your vault is not on the same machine as the server, use ngrok or
  Tailscale to expose the REST API securely.
  Then set CORPUS_OBSIDIAN_URL to the tunnel URL.
"""

import os
import requests
from .base import BaseCorpusSource, CorpusDoc


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


class ObsidianSource(BaseCorpusSource):
    name = "obsidian"

    def __init__(self):
        self.base_url = _env("CORPUS_OBSIDIAN_URL", "http://127.0.0.1:27123").rstrip("/")
        self.token = _env("CORPUS_OBSIDIAN_TOKEN")
        self.vault_dir = _env("CORPUS_OBSIDIAN_VAULT_DIR", "")
        self.tag_filter = _env("CORPUS_OBSIDIAN_TAG")
        self.category = _env("CORPUS_OBSIDIAN_CATEGORY", "OBSIDIAN")
        self.priority = int(_env("CORPUS_OBSIDIAN_PRIORITY", "2"))

    def is_configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}

    def discover(self) -> list[CorpusDoc]:
        if not self.is_configured():
            print("[Obsidian] CORPUS_OBSIDIAN_TOKEN not set — source disabled.")
            return []
        try:
            dir_path = self.vault_dir.strip("/") if self.vault_dir else ""
            url = f"{self.base_url}/vault/{dir_path}/" if dir_path else f"{self.base_url}/vault/"
            r = requests.get(url, headers=self._headers(), timeout=10)
            r.raise_for_status()
            files = r.json().get("files", [])

            md_files = [f for f in files if str(f).endswith(".md")]

            if self.tag_filter:
                md_files = self._filter_by_tag(md_files)

            docs = []
            for path in md_files:
                label = str(path).split("/")[-1].replace(".md", "").replace("_", " ").replace("-", " ").title()
                docs.append(CorpusDoc(
                    id=f"obsidian:{path}",
                    source=self.name,
                    label=label,
                    category=self.category,
                    priority=self.priority,
                    meta={"vault_path": str(path)},
                ))
            print(f"[Obsidian] Discovered {len(docs)} notes.")
            return docs
        except Exception as e:
            print(f"[Obsidian] Discover error: {e}")
            return []

    def _filter_by_tag(self, paths: list) -> list:
        filtered = []
        for path in paths:
            try:
                url = f"{self.base_url}/vault/{path}"
                r = requests.get(url, headers={**self._headers(), "Accept": "application/json"}, timeout=8)
                if r.ok:
                    meta = r.json()
                    tags = meta.get("frontmatter", {}).get("tags", [])
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.split(",")]
                    if self.tag_filter.lower() in [t.lower() for t in tags]:
                        filtered.append(path)
            except Exception:
                pass
        return filtered

    def fetch_content(self, doc: CorpusDoc) -> str:
        path = doc.meta.get("vault_path")
        url = f"{self.base_url}/vault/{path}"
        r = requests.get(url, headers={**self._headers(), "Accept": "text/markdown"}, timeout=12)
        r.raise_for_status()
        return r.text
