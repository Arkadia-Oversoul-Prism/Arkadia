import requests
import json
import os
from datetime import datetime, timedelta

class GitHubCorpus:
    """
    Fetches and manages Arkadia corpus from GitHub public repository.
    Replaces arkadia_drive_sync.py with simpler GitHub-based approach.
    """
    
    def __init__(self, cache_file="arkadia_cache.json", cache_ttl_hours=24):
        self.base_url = "https://raw.githubusercontent.com/Arkadia-Oversoul-Prism/Arkadia/main/docs"
        self.doc_files = {
            "DOC1_MASTER_WEIGHTS": f"{self.base_url}/DOC1_MASTER_WEIGHTS.md",
            "DOC2_OPEN_LOOPS": f"{self.base_url}/DOC2_OPEN_LOOPS.md",
            "DOC3_PRINCIPLES_REGISTRY": f"{self.base_url}/DOC3_PRINCIPLES_REGISTRY.md",
            "DOC4_NODE_MAP": f"{self.base_url}/DOC4_NODE_MAP.md",
            "DOC5_REVENUE_BREATH": f"{self.base_url}/DOC5_REVENUE_BREATH.md",
        }
        self.cache_file = cache_file
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.corpus_data = {}
        self._load_corpus()
    
    def _is_cache_valid(self):
        if not os.path.exists(self.cache_file):
            return False
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.cache_file))
        return file_age < self.cache_ttl
    
    def _load_from_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.corpus_data = json.load(f)
            return True
        except Exception as e:
            print(f"[GitHubCorpus] Error loading cache: {e}")
            return False
    
    def _save_to_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.corpus_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[GitHubCorpus] Error saving cache: {e}")
            return False
    
    def _fetch_doc(self, doc_key, doc_url):
        try:
            response = requests.get(doc_url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[GitHubCorpus] Error fetching {doc_key}: {e}")
            return None
    
    def _load_corpus(self):
        if self._is_cache_valid():
            if self._load_from_cache():
                return
        
        print("[GitHubCorpus] Fetching docs from GitHub...")
        self.corpus_data = {}
        
        for doc_key, doc_url in self.doc_files.items():
            content = self._fetch_doc(doc_key, doc_url)
            if content:
                self.corpus_data[doc_key] = {
                    "url": doc_url,
                    "content": content,
                    "fetched_at": datetime.now().isoformat(),
                }
            else:
                self.corpus_data[doc_key] = {
                    "url": doc_url,
                    "content": "",
                    "error": "Failed to fetch",
                    "fetched_at": datetime.now().isoformat(),
                }
        
        self._save_to_cache()
    
    def refresh(self):
        print("[GitHubCorpus] Refreshing corpus from GitHub...")
        self.corpus_data = {}
        for doc_key, doc_url in self.doc_files.items():
            content = self._fetch_doc(doc_key, doc_url)
            if content:
                self.corpus_data[doc_key] = {
                    "url": doc_url,
                    "content": content,
                    "fetched_at": datetime.now().isoformat(),
                }
            else:
                self.corpus_data[doc_key] = {
                    "url": doc_url,
                    "content": "",
                    "error": "Failed to fetch",
                    "fetched_at": datetime.now().isoformat(),
                }
        self._save_to_cache()
        return self.corpus_data
    
    def get_full_corpus(self):
        return self.corpus_data
    
    def get_corpus_context(self, query=None):
        context = {
            "timestamp": datetime.now().isoformat(),
            "source": "GitHub public repository",
            "repository": "Arkadia-Oversoul-Prism/Arkadia",
            "docs": self.corpus_data,
        }
        if query:
            context["query"] = query
        return context
    
    def get_doc(self, doc_key):
        return self.corpus_data.get(doc_key, {}).get("content", "")


_corpus_instance = None

def init_corpus(cache_file="arkadia_cache.json", cache_ttl_hours=24):
    global _corpus_instance
    _corpus_instance = GitHubCorpus(cache_file=cache_file, cache_ttl_hours=cache_ttl_hours)
    return _corpus_instance

def get_corpus_context(query=None):
    global _corpus_instance
    if _corpus_instance is None:
        _corpus_instance = GitHubCorpus()
    return _corpus_instance.get_corpus_context(query)

def get_full_corpus():
    global _corpus_instance
    if _corpus_instance is None:
        _corpus_instance = GitHubCorpus()
    return _corpus_instance.get_full_corpus()

def refresh_corpus():
    global _corpus_instance
    if _corpus_instance is None:
        _corpus_instance = GitHubCorpus()
    return _corpus_instance.refresh()

def get_doc(doc_key):
    global _corpus_instance
    if _corpus_instance is None:
        _corpus_instance = GitHubCorpus()
    return _corpus_instance.get_doc(doc_key)
