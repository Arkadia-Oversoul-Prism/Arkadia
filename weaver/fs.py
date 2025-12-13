from pathlib import Path
from .logger import get_logger
import os

LOGGER = get_logger()

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__"}
EXCLUDE_SUFFIXES = {".bak"}
MAX_FILE_SIZE_ENV = "REPO_MAX_FILE_SIZE"
DEFAULT_MAX_FILE_SIZE = 1_000_000

def read_repo(root="."):
    files = {}
    for p in Path(root).rglob("*"):
        if p.is_file() and not any(x in str(p) for x in EXCLUDE_DIRS) and not any(str(p).endswith(s) for s in EXCLUDE_SUFFIXES):
            try:
                # skip very large files to avoid memory issues
                try:
                    size = p.stat().st_size
                except Exception:
                    size = 0
                if size > 1_000_000:  # 1MB
                    LOGGER.debug("Skipping large file %s (size=%s)", p, size)
                    continue
                files[str(p)] = p.read_text()
            except Exception:
                LOGGER.debug("Skipping unreadable file: %s", p)
    LOGGER.info("Read %s files from repo", len(files))
    return files


def write_file(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = None
    if p.exists():
        try:
            existing = p.read_text()
        except Exception:
            existing = None
    # Ensure we don't write outside repository root
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    try:
        if not p.resolve().is_relative_to(root):
            raise ValueError(f"Refusing to write outside repo root: {p}")
    except AttributeError:
        # For older Python versions without is_relative_to, fallback
        if str(root) not in str(p.resolve()):
            raise ValueError(f"Refusing to write outside repo root: {p}")

    # Create a backup if the file exists and content differs
    changed = existing != content
    if existing is not None and changed:
        try:
            # Use timestamped .bak to avoid overwriting previous backups, and limit size of backup file
            import time
            ts = int(time.time())
            bak_suffix = f".bak.{ts}"
            bak_path = p.with_suffix(p.suffix + bak_suffix) if p.suffix else Path(str(p) + bak_suffix)
            # if REPO_MAX_FILE_SIZE is set, only create backups for files under the threshold
            try:
                max_size = int(os.environ.get(MAX_FILE_SIZE_ENV, DEFAULT_MAX_FILE_SIZE))
            except Exception:
                max_size = DEFAULT_MAX_FILE_SIZE
            try:
                if p.stat().st_size <= max_size:
                    bak_path.write_text(existing)
                    LOGGER.info("Created backup for %s -> %s", p, bak_path)
                else:
                    LOGGER.info("Skipping backup for %s due to size threshold (%s > %s)", p, p.stat().st_size, max_size)
            except Exception:
                # If we can't stat, write the backup anyway
                bak_path.write_text(existing)
                LOGGER.info("Created backup for %s -> %s", p, bak_path)
        except Exception:
            LOGGER.warning("Failed to write backup for %s", p)
    p.write_text(content)
    LOGGER.info("Wrote file %s (changed=%s)", path, changed)
    return changed

