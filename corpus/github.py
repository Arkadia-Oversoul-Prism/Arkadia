"""
Arkadia Corpus — GitHub Dynamic Source

Scans a GitHub repository for documents. No hardcoded list.
Any .md (or configured extension) file added to the repo is automatically
picked up on next refresh.

Config env vars:
  CORPUS_GITHUB_REPO          e.g. "Arkadia-Oversoul-Prism/Arkadia"
  CORPUS_GITHUB_TOKEN         Personal access token (optional for public repos)
  CORPUS_GITHUB_BRANCH        default "main"
  CORPUS_GITHUB_EXTENSIONS    default ".md" (comma-sep: ".md,.txt")
  CORPUS_GITHUB_INCLUDE_DIRS  whitelist dirs (comma-sep). If empty = all dirs.
  CORPUS_GITHUB_EXCLUDE_DIRS  blacklist dirs (comma-sep). Default: ".github,node_modules,bot"
  CORPUS_DIR_CATEGORIES       dir→category mapping.
                              e.g. "docs:NEURAL_SPINE,creative:CREATIVE_OS"
                              Unmapped dirs get category = dir.upper()

Optional manifest:
  If "corpus-manifest.json" exists at the repo root, it is fetched and used to
  override label/description/category/priority for specific file paths.

  Format:
  {
    "docs/DOC1_MASTER_WEIGHTS.md": {
      "label": "Master Weights",
      "description": "...",
      "category": "NEURAL_SPINE",
      "priority": 1
    }
  }
"""

import os
import requests
from .base import BaseCorpusSource, CorpusDoc

try:
    import json as _json
except ImportError:
    _json = None


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _prettify_label(path: str) -> str:
    name = path.split("/")[-1]
    if name.lower().endswith(".md"):
        name = name[:-3]
    name = name.replace("_", " ").replace("-", " ")
    return name.title()


class GitHubSource(BaseCorpusSource):
    name = "github"

    def __init__(self):
        self.repo = _env("CORPUS_GITHUB_REPO")
        self.token = _env("CORPUS_GITHUB_TOKEN") or _env("GITHUB_TOKEN")
        self.branch = _env("CORPUS_GITHUB_BRANCH", "main")
        self.extensions = [
            e.strip() for e in _env("CORPUS_GITHUB_EXTENSIONS", ".md").split(",") if e.strip()
        ]
        include_raw = _env("CORPUS_GITHUB_INCLUDE_DIRS")
        self.include_dirs = [d.strip() for d in include_raw.split(",") if d.strip()] if include_raw else []
        exclude_raw = _env("CORPUS_GITHUB_EXCLUDE_DIRS", ".github,node_modules,bot,web,api")
        self.exclude_dirs = [d.strip() for d in exclude_raw.split(",") if d.strip()]
        self._raw_base = f"https://raw.githubusercontent.com/{self.repo}/{self.branch}"
        self._api_base = f"https://api.github.com/repos/{self.repo}"
        self._dir_categories = self._parse_dir_categories()
        self._manifest: dict = {}

    def _parse_dir_categories(self) -> dict:
        raw = _env("CORPUS_DIR_CATEGORIES", "docs:NEURAL_SPINE,creative:CREATIVE_OS,collective:COLLECTIVE,governance:GOVERNANCE")
        mapping = {}
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" in pair:
                d, c = pair.split(":", 1)
                mapping[d.strip()] = c.strip()
        return mapping

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def is_configured(self) -> bool:
        return bool(self.repo)

    def _load_manifest(self):
        try:
            url = f"{self._raw_base}/corpus-manifest.json"
            r = requests.get(url, headers=self._headers(), timeout=10)
            if r.status_code == 200:
                self._manifest = r.json()
                print(f"[GitHub] Manifest loaded — {len(self._manifest)} entries.")
        except Exception as e:
            print(f"[GitHub] No manifest found or error: {e}")
            self._manifest = {}

    def _should_include(self, path: str) -> bool:
        top_dir = path.split("/")[0]
        if top_dir in self.exclude_dirs:
            return False
        if self.include_dirs and top_dir not in self.include_dirs:
            return False
        ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
        return ext in self.extensions

    def _category_for(self, path: str) -> str:
        top_dir = path.split("/")[0]
        return self._dir_categories.get(top_dir, top_dir.upper())

    def _priority_for(self, path: str, manifest_entry: dict) -> int:
        if manifest_entry.get("priority"):
            return int(manifest_entry["priority"])
        top_dir = path.split("/")[0]
        if top_dir in self._dir_categories:
            idx = list(self._dir_categories.keys()).index(top_dir)
            return min(idx + 1, 3)
        return 3

    def discover(self) -> list[CorpusDoc]:
        if not self.is_configured():
            print("[GitHub] CORPUS_GITHUB_REPO not set — source disabled.")
            return []

        self._load_manifest()

        try:
            url = f"{self._api_base}/git/trees/{self.branch}?recursive=1"
            r = requests.get(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            tree = r.json().get("tree", [])
        except Exception as e:
            print(f"[GitHub] Failed to fetch repo tree: {e}")
            return []

        docs = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item["path"]
            if not self._should_include(path):
                continue

            manifest_entry = self._manifest.get(path, {})
            label = manifest_entry.get("label") or _prettify_label(path)
            description = manifest_entry.get("description", "")
            category = manifest_entry.get("category") or self._category_for(path)
            priority = self._priority_for(path, manifest_entry)

            docs.append(CorpusDoc(
                id=path,
                source=self.name,
                label=label,
                description=description,
                category=category,
                priority=priority,
                meta={"path": path, "sha": item.get("sha", ""), "size": item.get("size", 0)},
            ))

        print(f"[GitHub] Discovered {len(docs)} documents in {self.repo}.")
        return docs

    def fetch_content(self, doc: CorpusDoc) -> str:
        path = doc.meta.get("path", doc.id)
        url = f"{self._raw_base}/{path}"
        r = requests.get(url, headers=self._headers(), timeout=12)
        r.raise_for_status()
        return r.text
