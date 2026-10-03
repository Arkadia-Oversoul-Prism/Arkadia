"""Project-scoped, read-only workspace snapshots for the SolSpire agentic canvas.

The canonical files remain in project_store. This module materializes a bounded
snapshot for the existing Engineering Lab Sandbox; it does not introduce a
second file database or persist agent-written output as canonical project data.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

_MAX_FILES = 100
_MAX_FILE_BYTES = 2_000_000
_MAX_TOTAL_BYTES = 10_000_000


def _safe_relative_name(name: str) -> PurePosixPath | None:
    raw = (name or "").replace("\\", "/").strip()
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    if any(":" in part for part in path.parts):
        return None
    return path


def _clear_workspace(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for child in root.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def prepare_project_workspace(
    subject_uid: str,
    project_id: str,
    *,
    base_root: str | Path | None = None,
) -> dict[str, Any]:
    """Refresh an owner/project-derived workspace from canonical project files.

    The path never contains a caller-supplied UID or project ID. File names are
    validated as relative POSIX paths and all resolved targets must stay below
    the derived root. Only bounded text already stored in the canonical project
    file table is materialized.
    """
    uid = (subject_uid or "").strip()
    pid = (project_id or "").strip()
    if not uid or not pid:
        raise ValueError("subject_uid and project_id are required")

    base = Path(
        base_root
        or os.environ.get("SOLSPIRE_CANVAS_ROOT")
        or (Path(tempfile.gettempdir()) / "arkadia-solspire-canvas")
    ).expanduser().resolve()
    key = hashlib.sha256(f"{uid}\0{pid}".encode("utf-8")).hexdigest()[:32]
    root = (base / key).resolve()
    root.relative_to(base)
    _clear_workspace(root)

    from solspire.project_store import get_file, list_files

    seeded: list[str] = []
    skipped: list[dict[str, str]] = []
    total_bytes = 0
    records = list_files(pid)[:_MAX_FILES]
    for record in records:
        file_id = str(record.get("id") or "")
        name = str(record.get("name") or "")
        relative = _safe_relative_name(name)
        if not file_id or relative is None:
            skipped.append({"name": name or "(unnamed)", "reason": "unsafe_or_missing_name"})
            continue
        file_record = get_file(file_id)
        if not file_record or file_record.get("project_id") != pid:
            skipped.append({"name": name, "reason": "canonical_file_unavailable"})
            continue
        text = str(file_record.get("content") or "")
        size = len(text.encode("utf-8"))
        if size > _MAX_FILE_BYTES or total_bytes + size > _MAX_TOTAL_BYTES:
            skipped.append({"name": name, "reason": "snapshot_size_limit"})
            continue
        target = root.joinpath(*relative.parts)
        resolved = target.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            skipped.append({"name": name, "reason": "path_escape"})
            continue
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(text, encoding="utf-8")
        total_bytes += size
        seeded.append(str(relative))

    return {
        "root": str(root),
        "source": "canonical_project_files",
        "read_only": True,
        "seeded_files": seeded,
        "skipped_files": skipped,
        "file_count": len(seeded),
        "bytes_materialized": total_bytes,
        "limits": {
            "max_files": _MAX_FILES,
            "max_file_bytes": _MAX_FILE_BYTES,
            "max_total_bytes": _MAX_TOTAL_BYTES,
        },
    }


__all__ = ["prepare_project_workspace"]
