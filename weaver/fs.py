from pathlib import Path
from .logger import get_logger

LOGGER = get_logger()

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__"}

def read_repo(root="."):
    files = {}
    for p in Path(root).rglob("*"):
        if p.is_file() and not any(x in str(p) for x in EXCLUDE_DIRS):
            try:
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
    p.write_text(content)
    changed = existing != content
    LOGGER.info("Wrote file %s (changed=%s)", path, changed)
    return changed

