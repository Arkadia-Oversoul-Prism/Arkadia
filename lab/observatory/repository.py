from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from ..model import Observation, observed_now

EXCLUDED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build", ".next", "coverage", ".cache"}
SECRET_NAMES = {".env", ".env.local", ".env.production", "service-account.json", "firebase-adminsdk.json"}
SECRET_PARTS = ("secret", "credential", "token", "password", "private_key", "api_key")


def _secret_path(path: Path) -> bool:
    name = path.name.lower()
    return name in SECRET_NAMES or any(part in name for part in SECRET_PARTS)


def _language(path: Path) -> str | None:
    return {".py":"python", ".ts":"typescript", ".tsx":"tsx", ".js":"javascript", ".jsx":"jsx", ".json":"json", ".md":"markdown", ".yml":"yaml", ".yaml":"yaml", ".toml":"toml"}.get(path.suffix.lower())


def discover_files(repo_root: str = ".") -> list[dict[str, Any]]:
    root = Path(repo_root).resolve()
    rows: list[dict[str, Any]] = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".git"))
        for name in sorted(files):
            path = Path(base) / name
            if _secret_path(path):
                continue
            try:
                rel = path.relative_to(root).as_posix()
                stat = path.stat()
                digest = hashlib.sha256(path.read_bytes()).hexdigest() if stat.st_size <= 2_000_000 else None
                rows.append({"path": rel, "extension": path.suffix.lower(), "size": stat.st_size, "hash": digest, "language": _language(path), "directory": path.parent.relative_to(root).as_posix() if path.parent != root else ""})
            except (OSError, UnicodeError):
                continue
    return rows


def repository_observation(repo_root: str = ".") -> Observation:
    root = Path(repo_root).resolve()
    value = {"name": root.name, "path": str(root)}
    return Observation(id="obs:repository", type="repository", subject="Arkadia", source="filesystem", confidence=1.0, observed_at=observed_now(), value=value, provenance={"source_file": str(root)})
