from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlsplit, urlunsplit


def _run(root: Path, args: list[str]) -> tuple[str | None, str | None]:
    try:
        p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True, timeout=10)
        return p.stdout.strip(), None
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)


# scp-like shorthand (`user@host:path`), which `urlsplit` does not parse.
_SCP_LIKE = re.compile(r"^[^@/\s]+@(?P<host>[^:/\s]+):(?P<path>\S+)$")


class RemoteURL(NamedTuple):
    """A git remote URL with any userinfo removed.

    ``redacted`` is True when the resolved value was altered **or withheld** to
    remove userinfo. A credential must never survive into ``url``; when the form
    cannot be verified the URL is withheld (``url is None``) rather than emitted.
    """

    url: str | None
    redacted: bool


def redact_remote_url(url: Any) -> RemoteURL:
    """Strip `user:password@` / bare `token@` userinfo from a remote URL.

    Git stores a remote URL verbatim, including any credential embedded as
    userinfo, so the raw value must never be surfaced. This is the single place
    that guarantee is made: every consumer of ``repository_state`` receives an
    already-redacted ``remote``.

    Fail-closed: an unparseable or unverifiable form that could contain userinfo
    yields ``url=None``. Credential-free output is returned unchanged.
    """
    if not isinstance(url, str):
        return RemoteURL(None, False)
    raw = url.strip()
    if not raw:
        return RemoteURL(None, False)

    try:
        parts = urlsplit(raw)
    except ValueError:
        # Unparseable (e.g. a malformed IPv6 host) - cannot prove it is
        # credential-free, so withhold rather than guess.
        return RemoteURL(None, True)

    if parts.netloc:
        # userinfo is everything before the final "@" in the authority. A
        # password may itself contain "@", so split on the last one.
        authority = parts.netloc.rsplit("@", 1)[-1]
        if not authority:
            return RemoteURL(None, True)
        cleaned = urlunsplit((parts.scheme, authority, parts.path, parts.query, parts.fragment))
        if not cleaned:
            return RemoteURL(None, True)
        return RemoteURL(cleaned, cleaned != raw)

    match = _SCP_LIKE.match(raw)
    if match:
        return RemoteURL(f"{match.group('host')}:{match.group('path')}", True)

    if "@" in raw:
        # An unparsed form that carries an "@" may hide userinfo; withhold it.
        return RemoteURL(None, True)

    return RemoteURL(raw, False)


def repository_state(repo_root: str = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    branch, err = _run(root, ["branch", "--show-current"])
    head, err2 = _run(root, ["rev-parse", "HEAD"])
    remote, err3 = _run(root, ["remote", "get-url", "origin"])
    status, err4 = _run(root, ["status", "--porcelain"])
    # The raw `get-url` value carries whatever userinfo the environment's remote
    # holds. It is redacted here, once, so that no consumer can surface it.
    redacted = redact_remote_url(remote)
    return {"branch": branch or None, "head": head or None, "clean": status == "", "remote": redacted.url, "remote_redacted": redacted.redacted, "status": "observed" if not (err or err2) else "unavailable", "reason": next((x for x in (err, err2, err3, err4) if x), None)}


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
