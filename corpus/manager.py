"""
Arkadia Corpus Manager

Aggregates documents from all configured sources, caches results,
and exposes a unified corpus dict for the API.

Config env vars:
  CORPUS_SOURCES        Comma-sep list of sources to enable.
                        Default: "github"
                        Options: github, gdrive, joplin, obsidian
  CORPUS_CACHE_TTL_HRS  Cache TTL in hours. Default: 6
  CORPUS_CACHE_FILE     Cache file path. Default: arkadia_cache.json

Adding a new source is as simple as:
  1. Create corpus/mysource.py implementing BaseCorpusSource
  2. Add it to SOURCE_REGISTRY below
  3. Add "mysource" to CORPUS_SOURCES env var
"""

import json
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    Multi-source corpus aggregator with disk caching.
    Discovers documents from all enabled sources, fetches content
    in parallel, and caches the result.
    """

    def __init__(self):
        self.cache_file = _env("CORPUS_CACHE_FILE", "arkadia_cache.json")
        self.cache_ttl = timedelta(hours=float(_env("CORPUS_CACHE_TTL_HRS", "6")))
        self._corpus: dict[str, dict] = {}
        self._sources = self._init_sources()
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
            doc.fetched_at = doc.now_iso()
            doc.error = None
        except Exception as e:
            print(f"[Corpus Manager] Failed to fetch {doc.id}: {e}")
            doc.content = ""
            doc.fetched_at = doc.now_iso()
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
        return self._corpus.get(doc_id, {}).get("content", "")

    def get_by_category(self, category: str) -> dict:
        return {k: v for k, v in self._corpus.items() if v.get("category") == category}

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
