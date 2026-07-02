"""SolSpire Console — File System Tool (Milestone 1).

Safe, sandboxed file system operations. All paths are restricted to the
workspace root — no escaping outside the project directory.
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
    try:
        if len(content.encode("utf-8")) > _MAX_WRITE_BYTES:
            return {"ok": False, "error": f"Content too large (max {_MAX_WRITE_BYTES} bytes)"}
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(target.relative_to(_WORKSPACE)), "bytes_written": len(content.encode())}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.error("tools_fs.write_file error: %s", e)
        return {"ok": False, "error": str(e)}


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
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"ok": False, "error": f"File not found: {path}"}
        if not target.is_file():
            return {"ok": False, "error": "Only files can be deleted via this tool"}
        target.unlink()
        return {"ok": True, "path": path, "deleted": True}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.error("tools_fs.delete_file error: %s", e)
        return {"ok": False, "error": str(e)}


__all__ = ["read_file", "write_file", "list_directory", "delete_file"]
