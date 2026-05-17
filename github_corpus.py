"""
Arkadia Living Corpus — Auto-Discovery Engine
Crawls the GitHub repo tree at startup and ingests every document it finds.
No hardcoded file list. Add a file to the repo → next sync picks it up.
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta


REPO = "Arkadia-Oversoul-Prism/Arkadia"
BRANCH = "main"
BASE_RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
GITHUB_API = "https://api.github.com"

# Directories to crawl. Add any new directory here to include it as a category.
# The directory name becomes the category label automatically.
CORPUS_DIRS = {
    "docs",
    "creative",
    "collective",
    "governance",
    "codex",
    "rituals",
    "protocols",
    "transmissions",
    "archive_active",
}

# Directories and path prefixes to never ingest (code, tooling, etc.)
SKIP_PREFIXES = {
    "web/", "api/", "bot/", "weaver/", "archive/",
    ".github/", "node_modules/", "__pycache__/",
}

# Individual filenames to skip regardless of location
SKIP_FILENAMES = {
    "README.md", "readme.md", "CHANGELOG.md", "LICENSE.md",
    ".gitignore", ".gitkeep", "package.json", "package-lock.json",
}

# File extensions to ingest
CORPUS_EXTENSIONS = {".md", ".txt"}

# Category → display priority (lower = injected first into Oracle context)
CATEGORY_PRIORITY = {
    "NEURAL_SPINE": 1,
    "CREATIVE_OS": 2,
    "CODEX": 2,
    "COLLECTIVE": 2,
    "GOVERNANCE": 3,
}

# Directory name → category name
DIR_TO_CATEGORY = {
    "docs": "NEURAL_SPINE",
    "creative": "CREATIVE_OS",
    "collective": "COLLECTIVE",
    "governance": "GOVERNANCE",
    "codex": "CODEX",
}


def _infer_category(path: str) -> str:
    """Map a file path to its corpus category. New dirs get uppercased dir name."""
    top = path.split("/")[0] if "/" in path else ""
    return DIR_TO_CATEGORY.get(top, top.upper().replace("-", "_") if top else "GENERAL")


def _infer_priority(category: str) -> int:
    return CATEGORY_PRIORITY.get(category, 3)


def _infer_label(path: str, content: str = "") -> str:
    """
    Extract a human-readable label.
    First tries the first H1 heading in the content.
    Falls back to cleaning the filename.
    """
    if content:
        for line in content.strip().split("\n")[:10]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()[:80]

    filename = path.split("/")[-1]
    name = os.path.splitext(filename)[0]
    # Strip common prefixes like DOC1_, P-008-
    name = re.sub(r"^(DOC\d+_|P-\d{3}-)", "", name)
    name = re.sub(r"[-_]", " ", name)
    return name.title().strip() or filename


def _infer_description(content: str, max_len: int = 220) -> str:
    """
    Extract a short description from the document.
    Uses the first non-heading, non-empty, non-separator line.
    """
    if not content:
        return ""
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(("#", "---", "===", "```", "|")):
            continue
        # Strip markdown bold/italic
        line = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", line)
        line = re.sub(r"_{1,2}(.*?)_{1,2}", r"\1", line)
        return line[:max_len]
    return ""


def _path_to_key(path: str) -> str:
    """Convert file path to a stable corpus key. Unique per file."""
    filename = path.split("/")[-1]
    name = os.path.splitext(filename)[0]
    # Preserve the full path-derived key to avoid collisions across dirs
    dir_prefix = path.replace("/", "__").replace("-", "_").upper()
    key = re.sub(r"[^A-Z0-9_]", "_", dir_prefix)
    return key.strip("_")


class GitHubCorpus:
    """
    Auto-discovering corpus engine.
    Crawls the full GitHub repo tree, ingests every eligible document,
    caches results. No hardcoded file list — add files to the repo and
    they are picked up on the next sync.
    """

    def __init__(self, cache_file="arkadia_cache.json", cache_ttl_hours=6):
        self.cache_file = cache_file
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        self.corpus_data: dict = {}
        self._load_corpus()

    def _auth_headers(self) -> dict:
        h = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            h["Authorization"] = f"token {self.token}"
        return h

    def _is_cache_valid(self) -> bool:
        if not os.path.exists(self.cache_file):
            return False
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.cache_file))
        return age < self.cache_ttl

    def _load_from_cache(self) -> bool:
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.corpus_data = json.load(f)
            count = len(self.corpus_data)
            cats = len({v.get("category") for v in self.corpus_data.values()})
            print(f"[Corpus] Cache loaded: {count} scrolls across {cats} categories.")
            return True
        except Exception as e:
            print(f"[Corpus] Cache read error: {e}")
            return False

    def _save_to_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.corpus_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Corpus] Cache write error: {e}")

    def _discover_paths(self) -> list[str]:
        """
        Use the GitHub recursive tree API to discover all corpus-eligible files.
        One API call returns the entire repo tree.
        """
        url = f"{GITHUB_API}/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
        try:
            resp = requests.get(url, headers=self._auth_headers(), timeout=20)
            resp.raise_for_status()
            tree = resp.json().get("tree", [])
        except Exception as e:
            print(f"[Corpus] Tree API error: {e}")
            return []

        discovered = []
        for item in tree:
            if item.get("type") != "blob":
                continue

            path: str = item["path"]
            filename = path.split("/")[-1]
            ext = os.path.splitext(filename)[1].lower()

            # Extension filter
            if ext not in CORPUS_EXTENSIONS:
                continue

            # Skip non-corpus paths
            if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
                continue

            # Skip specific filenames
            if filename in SKIP_FILENAMES:
                continue

            # Only ingest from known corpus directories (or root-level .md files)
            top_dir = path.split("/")[0] if "/" in path else ""
            if top_dir and top_dir not in CORPUS_DIRS:
                continue

            discovered.append(path)

        discovered.sort()
        return discovered

    def _fetch_content(self, path: str) -> str | None:
        url = f"{BASE_RAW}/{path}"
        try:
            resp = requests.get(url, timeout=12)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"[Corpus] Fetch error ({path}): {e}")
            return None

    def _load_corpus(self):
        if self._is_cache_valid() and self._load_from_cache():
            return

        print(f"[Corpus] Discovering documents in {REPO}...")
        paths = self._discover_paths()
        print(f"[Corpus] Found {len(paths)} documents. Fetching content...")

        self.corpus_data = {}
        for path in paths:
            content = self._fetch_content(path)
            key = _path_to_key(path)
            category = _infer_category(path)
            self.corpus_data[key] = {
                "content": content or "",
                "category": category,
                "priority": _infer_priority(category),
                "label": _infer_label(path, content or ""),
                "description": _infer_description(content or ""),
                "path": path,
                "fetched_at": datetime.now().isoformat(),
                "error": None if content else "Fetch failed",
            }

        live = sum(1 for v in self.corpus_data.values() if v["content"])
        cats = {v["category"] for v in self.corpus_data.values() if v["content"]}
        print(f"[Corpus] {live}/{len(paths)} scrolls live across {len(cats)} categories: {sorted(cats)}")
        self._save_to_cache()

    def refresh(self) -> dict:
        """Force full re-discovery and re-fetch from GitHub."""
        print("[Corpus] Force refresh — re-discovering all documents...")
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        self.corpus_data = {}
        self._load_corpus()
        return self.corpus_data

    def get_full_corpus(self) -> dict:
        return self.corpus_data

    def get_doc(self, key: str) -> str:
        return self.corpus_data.get(key, {}).get("content", "")

    def get_by_category(self, category: str) -> dict:
        return {k: v for k, v in self.corpus_data.items() if v.get("category") == category}

    def inject_document(self, key: str, data: dict):
        """Inject an external document directly into the live corpus."""
        self.corpus_data[key] = data

    def total_chars(self) -> int:
        return sum(len(v.get("content", "")) for v in self.corpus_data.values())

    def categories(self) -> set[str]:
        return {v["category"] for v in self.corpus_data.values() if v.get("content")}


# ── Module-level singleton ────────────────────────────────────────────────────

_corpus: GitHubCorpus | None = None


def _get() -> GitHubCorpus:
    global _corpus
    if _corpus is None:
        _corpus = GitHubCorpus()
    return _corpus


def get_full_corpus() -> dict:
    return _get().get_full_corpus()


def refresh_corpus() -> dict:
    return _get().refresh()


def get_doc(key: str) -> str:
    return _get().get_doc(key)


def get_by_category(category: str) -> dict:
    return _get().get_by_category(category)


def inject_document(key: str, data: dict):
    """Inject a document directly into the live in-memory corpus."""
    _get().inject_document(key, data)


def total_chars() -> int:
    return _get().total_chars()


def corpus_categories() -> set[str]:
    return _get().categories()
