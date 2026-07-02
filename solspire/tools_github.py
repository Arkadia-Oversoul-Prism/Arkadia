"""SolSpire Console — GitHub Tool (Milestone 1).

Provides GitHub operations: list repos, get file tree, read file content.
Uses GITHUB_TOKEN env var when available for higher rate limits.
Does NOT execute git clone (no shell in the kernel) — uses GitHub REST API.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("solspire.tools_github")

_API = "https://api.github.com"
_TIMEOUT = 15.0


def _headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN", "")
    h: dict[str, str] = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def list_repos(owner: str) -> dict[str, Any]:
    try:
        url = f"{_API}/users/{owner}/repos"
        resp = httpx.get(url, headers=_headers(), timeout=_TIMEOUT, params={"per_page": 50, "sort": "updated"})
        if resp.status_code != 200:
            return {"ok": False, "error": f"GitHub API {resp.status_code}: {resp.text[:200]}"}
        repos = [{"name": r["name"], "full_name": r["full_name"], "url": r["html_url"],
                  "description": r.get("description"), "language": r.get("language"),
                  "stars": r["stargazers_count"], "updated_at": r["updated_at"]}
                 for r in resp.json()]
        return {"ok": True, "owner": owner, "repos": repos, "count": len(repos)}
    except Exception as e:
        logger.error("tools_github.list_repos error: %s", e)
        return {"ok": False, "error": str(e)}


def get_tree(owner: str, repo: str, branch: str = "main") -> dict[str, Any]:
    try:
        url = f"{_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        resp = httpx.get(url, headers=_headers(), timeout=_TIMEOUT)
        if resp.status_code != 200:
            return {"ok": False, "error": f"GitHub API {resp.status_code}: {resp.text[:200]}"}
        data = resp.json()
        files = [{"path": item["path"], "type": item["type"], "size": item.get("size")}
                 for item in data.get("tree", []) if item["type"] in ("blob", "tree")]
        return {"ok": True, "owner": owner, "repo": repo, "branch": branch,
                "files": files, "count": len(files)}
    except Exception as e:
        logger.error("tools_github.get_tree error: %s", e)
        return {"ok": False, "error": str(e)}


def read_file(owner: str, repo: str, path: str, branch: str = "main") -> dict[str, Any]:
    try:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        resp = httpx.get(url, headers=_headers(), timeout=_TIMEOUT)
        if resp.status_code == 404:
            return {"ok": False, "error": f"File not found: {path} in {owner}/{repo}@{branch}"}
        if resp.status_code != 200:
            return {"ok": False, "error": f"GitHub {resp.status_code}: {resp.text[:200]}"}
        content = resp.text
        if len(content) > 64 * 1024:
            content = content[:64 * 1024] + "\n[...truncated]"
        return {"ok": True, "owner": owner, "repo": repo, "path": path,
                "branch": branch, "content": content, "size": len(content)}
    except Exception as e:
        logger.error("tools_github.read_file error: %s", e)
        return {"ok": False, "error": str(e)}


def commit_file(owner: str, repo: str, path: str, content: str,
                message: str, branch: str = "main") -> dict[str, Any]:
    """Create or update a file via the GitHub Contents API.

    Requires GITHUB_TOKEN with repo write scope.
    Automatically fetches the current file SHA when updating an existing file.
    """
    import base64
    try:
        contents_url = f"{_API}/repos/{owner}/{repo}/contents/{path}"
        sha: str | None = None

        # Fetch existing SHA (needed for update; absent for create)
        existing = httpx.get(contents_url, headers=_headers(),
                             params={"ref": branch}, timeout=_TIMEOUT)
        if existing.status_code == 200:
            sha = existing.json().get("sha")
        elif existing.status_code not in (404,):
            return {"ok": False, "error": f"GitHub {existing.status_code}: {existing.text[:200]}"}

        encoded = base64.b64encode(content.encode()).decode()
        payload: dict[str, Any] = {
            "message": message or f"chore: update {path}",
            "content": encoded,
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        resp = httpx.put(contents_url, headers=_headers(), json=payload, timeout=_TIMEOUT)
        if resp.status_code not in (200, 201):
            return {"ok": False, "error": f"GitHub {resp.status_code}: {resp.text[:300]}"}

        action = "updated" if sha else "created"
        return {
            "ok": True,
            "action": action,
            "path": path,
            "branch": branch,
            "commit_sha": resp.json().get("commit", {}).get("sha", ""),
            "html_url": resp.json().get("content", {}).get("html_url", ""),
        }
    except Exception as e:
        logger.error("tools_github.commit_file error: %s", e)
        return {"ok": False, "error": str(e)}


def get_repo_info(owner: str, repo: str) -> dict[str, Any]:
    try:
        url = f"{_API}/repos/{owner}/{repo}"
        resp = httpx.get(url, headers=_headers(), timeout=_TIMEOUT)
        if resp.status_code != 200:
            return {"ok": False, "error": f"GitHub API {resp.status_code}: {resp.text[:200]}"}
        r = resp.json()
        return {
            "ok": True,
            "name": r["name"],
            "full_name": r["full_name"],
            "description": r.get("description"),
            "language": r.get("language"),
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "default_branch": r["default_branch"],
            "url": r["html_url"],
            "clone_url": r["clone_url"],
            "updated_at": r["updated_at"],
        }
    except Exception as e:
        logger.error("tools_github.get_repo_info error: %s", e)
        return {"ok": False, "error": str(e)}


__all__ = ["list_repos", "get_tree", "read_file", "get_repo_info"]
