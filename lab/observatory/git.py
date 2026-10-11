from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


def _redact_remote_url(remote: str | None) -> str | None:
    """Remove URL userinfo before a remote is exposed in any read model.

    Git remotes can embed credentials in URL userinfo, for example
    https://user:token@example.invalid/org/repo.git. This value is informational
    only, so preserve the host/path but never the userinfo. The conservative
    fallback also handles malformed URL-like and SCP-style remote forms without
    returning the authority prefix before @.
    """
    if not remote:
        return remote

    try:
        parts = urlsplit(remote)
        if parts.scheme and "@" in parts.netloc:
            host = parts.netloc.rsplit("@", 1)[1]
            return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))
    except ValueError:
        # urlsplit can reject malformed IPv6/authority syntax; redact below.
        pass

    # Fail closed for malformed scheme URLs and SCP-style remotes. Only inspect
    # the authority portion, so an @ in a path/query is preserved.
    if "://" in remote:
        scheme, remainder = remote.split("://", 1)
        authority, separator, suffix = remainder.partition("/")
        if "@" in authority:
            host = authority.rsplit("@", 1)[1]
            return scheme + "://" + host + ("/" + suffix if separator else "")
    else:
        authority, separator, suffix = remote.partition("/")
        if "@" in authority:
            host = authority.rsplit("@", 1)[1]
            return host + ("/" + suffix if separator else "")



def _run(root: Path, args: list[str]) -> tuple[str | None, str | None]:
    try:
        p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True, timeout=10)
        return p.stdout.strip(), None
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)


def repository_state(repo_root: str = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    branch, err = _run(root, ["branch", "--show-current"])
    head, err2 = _run(root, ["rev-parse", "HEAD"])
    remote, err3 = _run(root, ["remote", "get-url", "origin"])
    status, err4 = _run(root, ["status", "--porcelain"])
    return {"branch": branch or None, "head": head or None, "clean": status == "", "remote": _redact_remote_url(remote), "status": "observed" if not (err or err2) else "unavailable", "reason": next((x for x in (err or None, err2 or None, err3 or None, err4 or None) if x), None)}


def commit_history(repo_root: str = ".", limit: int = 250) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(repo_root).resolve()
    fmt = "%H%x1f%P%x1f%aI%x1f%an%x1f%s%x1e"
    out, err = _run(root, ["log", f"-{max(1, min(limit, 1000))}", f"--pretty=format:{fmt}", "--name-only"])
    if err or out is None:
        return [], {"status":"unavailable", "reason":err or "git log unavailable"}
    commits: list[dict[str, Any]] = []
    for block in out.split("\x1e"):
        lines = [x for x in block.strip().splitlines() if x.strip()]
        if not lines: continue
        meta = lines[0].split("\x1f")
        if len(meta) < 5: continue
        files = sorted(set(x.strip() for x in lines[1:] if x.strip()))
        sha, parents, timestamp, author, message = meta[:5]
        commits.append({"sha":sha,"parents":parents.split() if parents else [],"timestamp":timestamp,"author":author,"message":message,"files_changed":files,"directories_touched":sorted(set((x.rsplit("/",1)[0] if "/" in x else "") for x in files))})
    return commits, {"status":"observed", "count":len(commits)}


def python_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return []
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): result.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: result.add(node.module)
    return sorted(result)
