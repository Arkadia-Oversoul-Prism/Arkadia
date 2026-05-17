"""
Arkadia Corpus Manager — Enhanced with Manifest Support

Aggregates documents from all configured sources, caches results,
and exposes a unified corpus dict for the API.

NEW: Loads optional corpus-manifest.json for metadata-driven retrieval,
allowing documents to be fetched by name/alias, not just by file path.

Config env vars:
  CORPUS_SOURCES        Comma-sep list of sources to enable.
                        Default: "github"
                        Options: github, gdrive, joplin, obsidian
  CORPUS_CACHE_TTL_HRS  Cache TTL in hours. Default: 6
  CORPUS_CACHE_FILE     Cache file path. Default: arkadia_cache.json
  CORPUS_MANIFEST_PATH  Path to corpus manifest. Default: docs/CORPUS_MANIFEST.json

Adding a new source is as simple as:
  1. Create corpus/mysource.py implementing BaseCorpusSource
  2. Add it to SOURCE_REGISTRY below
  3. Add "mysource" to CORPUS_SOURCES env var
"""

import json
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List

from .base import BaseCorpusSource, CorpusDoc
from .github import GitHubSource
from .gdrive import GoogleDriveSource
from .joplin import JoplinSource
from .obsidian import ObsidianSource


SOURCE_REGISTRY: dict[str, type[BaseCorpusSource]] = {
    "github": GitHubSource,
    "gdrive": GoogleDriveSource,
    "joplin": JoplinSource,
    "obsidian": ObsidianSource,
}


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


class CorpusManager:
    """
    Multi-source corpus aggregator with disk caching and manifest support.
    Discovers documents from all enabled sources, fetches content
    in parallel, caches the result, and enables metadata-driven retrieval.
    """

    def __init__(self):
        self.cache_file = _env("CORPUS_CACHE_FILE", "arkadia_cache.json")
        self.cache_ttl = timedelta(hours=float(_env("CORPUS_CACHE_TTL_HRS", "6")))
        self.manifest_path = _env("CORPUS_MANIFEST_PATH", "docs/CORPUS_MANIFEST.json")
        self._corpus: dict[str, dict] = {}
        self._manifest: dict = {}
        self._sources = self._init_sources()
        self._load_manifest()
        self._load()

    def _init_sources(self) -> list[BaseCorpusSource]:
        raw = _env("CORPUS_SOURCES", "github")
        names = [s.strip() for s in raw.split(",") if s.strip()]
        sources = []
        for name in names:
            cls = SOURCE_REGISTRY.get(name)
            if cls is None:
                print(f"[Corpus Manager] Unknown source '{name}' — skipped.")
                continue
            instance = cls()
            if instance.is_configured():
                sources.append(instance)
                print(f"[Corpus Manager] Source enabled: {name}")
            else:
                print(f"[Corpus Manager] Source '{name}' not configured — skipped.")
        if not sources:
            print("[Corpus Manager] WARNING: No sources configured!")
        return sources

    def _load_manifest(self):
        """Load corpus manifest for metadata-driven retrieval."""
        if not os.path.exists(self.manifest_path):
            print(f"[Corpus Manager] Manifest not found at {self.manifest_path} — skipped.")
            return
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)
            total = self._manifest.get("total_scrolls", 0)
            print(f"[Corpus Manager] Manifest loaded — {total} scrolls registered.")
        except Exception as e:
            print(f"[Corpus Manager] Manifest load error: {e}")

    def _cache_valid(self) -> bool:
        if not os.path.exists(self.cache_file):
            return False
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.cache_file))
        return age < self.cache_ttl

    def _load_cache(self) -> bool:
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._corpus = json.load(f)
            count = len(self._corpus)
            live = sum(1 for d in self._corpus.values() if not d.get("error") and d.get("chars", 0) > 0)
            print(f"[Corpus Manager] Cache loaded — {live}/{count} live documents.")
            return True
        except Exception as e:
            print(f"[Corpus Manager] Cache read error: {e}")
            return False

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._corpus, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Corpus Manager] Cache write error: {e}")

    def _fetch_doc(self, source: BaseCorpusSource, doc: CorpusDoc) -> CorpusDoc:
        try:
            content = source.fetch_content(doc)
            doc.content = content
            doc.fetched_at = source.now_iso()
            doc.error = None
        except Exception as e:
            print(f"[Corpus Manager] Failed to fetch {doc.id}: {e}")
            doc.content = ""
            doc.fetched_at = source.now_iso()
            doc.error = str(e)
        return doc

    def _sync_all_sources(self):
        all_docs: list[tuple[BaseCorpusSource, CorpusDoc]] = []
        for source in self._sources:
            try:
                discovered = source.discover()
                for doc in discovered:
                    all_docs.append((source, doc))
            except Exception as e:
                print(f"[Corpus Manager] Discover failed for {source.name}: {e}")

        if not all_docs:
            print("[Corpus Manager] No documents discovered from any source.")
            return

        print(f"[Corpus Manager] Fetching content for {len(all_docs)} documents...")

        fetched: list[CorpusDoc] = []
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(self._fetch_doc, src, doc): doc for src, doc in all_docs}
            for future in as_completed(futures):
                try:
                    fetched.append(future.result())
                except Exception as e:
                    print(f"[Corpus Manager] Fetch future error: {e}")

        self._corpus = {doc.id: doc.to_dict() for doc in fetched}

        total_chars = sum(d.get("chars", 0) for d in self._corpus.values())
        live = sum(1 for d in self._corpus.values() if not d.get("error") and d.get("chars", 0) > 0)
        print(f"[Corpus Manager] Sync complete — {live}/{len(self._corpus)} live — {total_chars:,} chars.")
        self._save_cache()

    def _load(self):
        if self._cache_valid() and self._load_cache():
            return
        self._sync_all_sources()

    def refresh(self) -> dict:
        print("[Corpus Manager] Force refresh...")
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        self._corpus = {}
        self._sync_all_sources()
        return self._corpus

    def get_full_corpus(self) -> dict:
        return self._corpus

    def get_doc(self, doc_id: str) -> str:
        """Get document content by ID (file path)."""
        return self._corpus.get(doc_id, {}).get("content", "")

    def get_doc_by_name(self, name: str) -> Optional[Dict]:
        """
        NEW: Fetch document by name/alias using manifest metadata.
        Searches manifest for matching title, category, or tags.
        Returns document metadata + content from corpus.
        """
        if not self._manifest:
            return None

        # Flatten manifest hierarchy to search
        all_docs = {}
        for section in self._manifest.values():
            if isinstance(section, dict) and "instructions" not in section:
                for key, doc_meta in section.items():
                    if isinstance(doc_meta, dict):
                        all_docs[key] = doc_meta

        # Search by key, title, or alias
        name_lower = name.lower().replace(" ", "_").replace("-", "_")
        for key, meta in all_docs.items():
            if (
                name_lower in key.lower()
                or name_lower in meta.get("title", "").lower().replace(" ", "_")
                or name_lower in meta.get("path", "").lower().replace("/", "_")
            ):
                doc_id = meta.get("path", key)
                content = self.get_doc(doc_id)
                return {
                    "name": key,
                    "metadata": meta,
                    "content": content,
                    "found": bool(content),
                }

        return None

    def get_by_category(self, category: str) -> dict:
        return {k: v for k, v in self._corpus.items() if v.get("category") == category}

    def get_manifest_overview(self) -> Dict:
        """Return manifest summary for frontend display."""
        if not self._manifest:
            return {}
        
        overview = {
            "version": self._manifest.get("manifest_version", "unknown"),
            "total_scrolls": self._manifest.get("total_scrolls", 0),
            "status": self._manifest.get("status_summary", {}),
            "sections": {},
        }

        for section_name, section_data in self._manifest.items():
            if isinstance(section_data, dict) and section_name not in [
                "manifest_version", "generated", "total_scrolls", "retrieval_logic",
                "initialization_sequence", "continuity_tokens", "status_summary", "note"
            ]:
                docs = [
                    {
                        "name": k,
                        "title": v.get("title"),
                        "function": v.get("function"),
                        "status": v.get("status"),
                        "priority": v.get("priority"),
                    }
                    for k, v in section_data.items()
                    if isinstance(v, dict)
                ]
                if docs:
                    overview["sections"][section_name] = {
                        "count": len(docs),
                        "documents": docs,
                    }

        return overview

    def total_chars(self) -> int:
        return sum(d.get("chars", 0) for d in self._corpus.values())

    def sources_status(self) -> list[dict]:
        return [
            {
                "name": s.name,
                "configured": s.is_configured(),
            }
            for name, cls in SOURCE_REGISTRY.items()
            for s in [cls()]
        ]
