"""
Arkadia Corpus — Joplin Source

Connects to Joplin via its Data REST API.
Works with Joplin Desktop (local API) or Joplin Server.

Config env vars:
  CORPUS_JOPLIN_URL         Base URL of Joplin API. Default: http://localhost:41184
  CORPUS_JOPLIN_TOKEN       Joplin API token (required).
                            Find it in Joplin → Tools → Options → Web Clipper → Advanced
  CORPUS_JOPLIN_NOTEBOOK    Notebook name to filter (optional). If empty = all notebooks.
  CORPUS_JOPLIN_CATEGORY    Category to assign all Joplin notes (default: JOPLIN)
  CORPUS_JOPLIN_PRIORITY    Priority (default: 2)
  CORPUS_JOPLIN_TAG         Optional tag filter — only notes with this tag are included.

Setup:
  1. Open Joplin Desktop.
  2. Enable the Web Clipper service: Tools → Options → Web Clipper → Enable Web Clipper Service.
  3. Copy your API token.
  4. Set CORPUS_JOPLIN_TOKEN in Replit Secrets.
  5. Set CORPUS_JOPLIN_URL if using Joplin Server (not local desktop).

For Joplin Server:
  CORPUS_JOPLIN_URL = https://your-joplin-server.com
"""

import os
import requests
from .base import BaseCorpusSource, CorpusDoc


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


class JoplinSource(BaseCorpusSource):
    name = "joplin"

    def __init__(self):
        self.base_url = _env("CORPUS_JOPLIN_URL", "http://localhost:41184").rstrip("/")
        self.token = _env("CORPUS_JOPLIN_TOKEN")
        self.notebook_filter = _env("CORPUS_JOPLIN_NOTEBOOK")
        self.tag_filter = _env("CORPUS_JOPLIN_TAG")
        self.category = _env("CORPUS_JOPLIN_CATEGORY", "JOPLIN")
        self.priority = int(_env("CORPUS_JOPLIN_PRIORITY", "2"))

    def is_configured(self) -> bool:
        return bool(self.token)

    def _p(self, extra: dict = None) -> dict:
        p = {"token": self.token}
        if extra:
            p.update(extra)
        return p

    def _get_all_pages(self, url: str, params: dict) -> list:
        results = []
        page = 1
        while True:
            r = requests.get(url, params={**params, "page": page, "limit": 100}, timeout=10)
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            results.extend(items)
            if not data.get("has_more", False):
                break
            page += 1
        return results

    def _get_notebook_id(self) -> str | None:
        if not self.notebook_filter:
            return None
        notebooks = self._get_all_pages(
            f"{self.base_url}/folders",
            self._p({"fields": "id,title"}),
        )
        for nb in notebooks:
            if nb.get("title", "").lower() == self.notebook_filter.lower():
                return nb["id"]
        return None

    def _get_tag_id(self) -> str | None:
        if not self.tag_filter:
            return None
        tags = self._get_all_pages(
            f"{self.base_url}/tags",
            self._p({"fields": "id,title"}),
        )
        for t in tags:
            if t.get("title", "").lower() == self.tag_filter.lower():
                return t["id"]
        return None

    def discover(self) -> list[CorpusDoc]:
        if not self.is_configured():
            print("[Joplin] CORPUS_JOPLIN_TOKEN not set — source disabled.")
            return []
        try:
            tag_id = self._get_tag_id()
            if tag_id:
                notes = self._get_all_pages(
                    f"{self.base_url}/tags/{tag_id}/notes",
                    self._p({"fields": "id,title,parent_id"}),
                )
            else:
                notebook_id = self._get_notebook_id()
                if notebook_id:
                    notes = self._get_all_pages(
                        f"{self.base_url}/folders/{notebook_id}/notes",
                        self._p({"fields": "id,title,parent_id"}),
                    )
                else:
                    notes = self._get_all_pages(
                        f"{self.base_url}/notes",
                        self._p({"fields": "id,title,parent_id"}),
                    )
            docs = []
            for note in notes:
                docs.append(CorpusDoc(
                    id=f"joplin:{note['id']}",
                    source=self.name,
                    label=note.get("title", note["id"]),
                    category=self.category,
                    priority=self.priority,
                    meta={"note_id": note["id"]},
                ))
            print(f"[Joplin] Discovered {len(docs)} notes.")
            return docs
        except Exception as e:
            print(f"[Joplin] Discover error: {e}")
            return []

    def fetch_content(self, doc: CorpusDoc) -> str:
        note_id = doc.meta.get("note_id")
        r = requests.get(
            f"{self.base_url}/notes/{note_id}",
            params=self._p({"fields": "id,title,body"}),
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        return f"# {data.get('title', '')}\n\n{data.get('body', '')}"
