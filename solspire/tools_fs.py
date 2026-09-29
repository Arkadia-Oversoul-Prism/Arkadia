"""SolSpire Console — File System Tool (Milestone 1).

Safe, sandboxed file system operations. All paths are restricted to the
workspace root — no escaping outside the project directory.

Architecture boundary:
    SolSpire may inspect its workspace here, but engineering mutation is
    governed by Weaver → K15 → K3. This module therefore refuses direct
    filesystem writes. Weaver has its own governed filesystem implementation
    and does not depend on this module for mutation.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("solspire.tools_fs")

_WORKSPACE = Path(os.environ.get("SOLSPIRE_WORKSPACE_ROOT", ".")).resolve()
_MAX_READ_BYTES = 64 * 1024  # 64 KB
_MAX_WRITE_BYTES = 256 * 1024


def _safe_path(relative: str) -> Path:
    p = (_WORKSPACE / relative).resolve()
    if not str(p).startswith(str(_WORKSPACE)):
        raise PermissionError(f"Path escapes workspace: {relative}")
    return p


def read_file(path: str) -> dict[str, Any]:
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"ok": False, "error": f"File not found: {path}"}
        if not target.is_file():
            return {"ok": False, "error": f"Not a file: {path}"}
        size = target.stat().st_size
        if size > _MAX_READ_BYTES:
            return {"ok": False, "error": f"File too large ({size} bytes, max {_MAX_READ_BYTES})"}
        content = target.read_text(encoding="utf-8", errors="replace")
        return {"ok": True, "path": str(target.relative_to(_WORKSPACE)), "content": content, "size": size}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.error("tools_fs.read_file error: %s", e)
        return {"ok": False, "error": str(e)}


def write_file(path: str, content: str) -> dict[str, Any]:
    """Refuse direct SolSpire filesystem mutation.

    Engineering writes belong to Weaver's governed K15 → K3 transaction path.
    Keeping this function as an explicit BLOCKED terminal path preserves the
    legacy API surface without leaving a second mutation authority behind.
    """
    logger.warning("Blocked direct SolSpire filesystem write: %s", path)
    return {
        "ok": False,
        "status": "BLOCKED",
        "error": "Direct filesystem mutation is disabled; use the governed Weaver K15 → K3 path.",
        "path": path,
    }


def list_directory(path: str = ".") -> dict[str, Any]:
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"ok": False, "error": f"Directory not found: {path}"}
        if not target.is_dir():
            return {"ok": False, "error": f"Not a directory: {path}"}
        entries = []
        for item in sorted(target.iterdir()):
            rel = str(item.relative_to(_WORKSPACE))
            if item.name.startswith(".") or item.name == "node_modules":
                continue
            entries.append({
                "name": item.name,
                "path": rel,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"ok": True, "path": str(target.relative_to(_WORKSPACE)), "entries": entries, "count": len(entries)}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.error("tools_fs.list_directory error: %s", e)
        return {"ok": False, "error": str(e)}


def delete_file(path: str) -> dict[str, Any]:
    logger.warning("Blocked direct SolSpire filesystem delete: %s", path)
    return {
        "ok": False,
        "status": "BLOCKED",
        "error": "Direct filesystem mutation is disabled; use the governed Weaver K15 → K3 path.",
        "path": path,
    }


__all__ = ["read_file", "write_file", "list_directory", "delete_file"]
