"""
Arkadia Knowledge OS — K5 Static Ingestion
==========================================
One-time startup pass that seeds the Knowledge OS with static corpus files
that already exist in the repository but have never been ingested.

LAW I: One pipeline. Ingest always calls pipeline.ingest().
        Duplicate-detection in pipeline.ingest() makes this fully idempotent.

Called from api/main.py lifespan() — runs once at startup in a background thread.
Never duplicates existing objects (checksum-based deduplication).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

logger = logging.getLogger("arkadia.static_ingestion")

# ─────────────────────────────────────────────────────────────────────────────
# Source definitions
# Each entry: (glob_pattern_root, glob_pattern, note_type, tags, description)
# ─────────────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent

_SOURCES: list[dict] = [
    # Spiral Codex scrolls
    {
        "root": _REPO_ROOT / "static",
        "glob": "**/*.md",
        "note_type": "scroll",
        "tags": ["spiral-codex", "static-corpus"],
        "source_provider": "static:spiral_codex",
    },
    # Canonical docs — project-level principles, specs, node maps
    {
        "root": _REPO_ROOT / "docs",
        "glob": "*.md",
        "note_type": "document",
        "tags": ["canonical-doc", "static-corpus"],
        "source_provider": "static:docs",
    },
    # Collective / community layer
    {
        "root": _REPO_ROOT / "docs" / "collective",
        "glob": "*.md",
        "note_type": "document",
        "tags": ["collective", "community", "static-corpus"],
        "source_provider": "static:collective",
    },
    # Creative layer
    {
        "root": _REPO_ROOT / "docs" / "creative",
        "glob": "*.md",
        "note_type": "document",
        "tags": ["creative", "static-corpus"],
        "source_provider": "static:creative",
    },
    # Vault notes already on disk (written by create_note but may predate ingestion)
    {
        "root": _REPO_ROOT / "vault",
        "glob": "**/*.md",
        "note_type": "note",
        "tags": ["vault", "static-corpus"],
        "source_provider": "static:vault",
    },
]

# Files to skip regardless of source (governance artefacts, boilerplate)
_SKIP_FILENAMES: frozenset[str] = frozenset({
    "README.md",
    "NODE_TEMPLATE.md",
})

# Minimum content length to be worth ingesting (bytes)
_MIN_CONTENT_BYTES = 64


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

def _strip_frontmatter(text: str) -> tuple[str, str]:
    """Return (title_hint, body) with YAML frontmatter stripped."""
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            fm_block = text[3:end]
            body = text[end + 5:].strip()
            # Try to extract title from frontmatter
            for line in fm_block.splitlines():
                if line.lower().startswith("title:"):
                    return line.partition(":")[2].strip(), body
            return "", body
    return "", text.strip()


def _title_from_path(path: Path) -> str:
    """Derive a human-readable title from the file path."""
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    # Capitalise first letter of each word
    return " ".join(w.capitalize() for w in stem.split())


def run_static_ingestion() -> dict:
    """
    Scan all configured static sources and ingest any file not already
    present in the Knowledge OS (idempotent via checksum deduplication).

    Returns a summary dict for logging.
    """
    from knowledge.pipeline import ingest as _ingest

    ingested = 0
    skipped  = 0
    errors   = 0

    for source in _SOURCES:
        root: Path = source["root"]
        if not root.exists():
            logger.debug(f"[K5] Source root missing, skipping: {root}")
            continue

        for path in sorted(root.glob(source["glob"])):
            if not path.is_file():
                continue
            if path.name in _SKIP_FILENAMES:
                continue

            try:
                raw = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                logger.warning(f"[K5] Cannot read {path}: {exc}")
                errors += 1
                continue

            if len(raw.encode()) < _MIN_CONTENT_BYTES:
                skipped += 1
                continue

            title_from_fm, body = _strip_frontmatter(raw)
            content = body if body else raw
            title   = title_from_fm or _title_from_path(path)

            try:
                result = _ingest(
                    title=title,
                    content=content,
                    note_type=source["note_type"],
                    tags=source["tags"],
                    source_provider=source["source_provider"],
                    auto_tag=True,
                    auto_embed=False,   # embeddings done lazily to keep startup fast
                    auto_link=False,    # links built lazily
                )
                if result.get("duplicate"):
                    skipped += 1
                else:
                    ingested += 1
                    logger.debug(f"[K5] Ingested: {title[:60]}")
            except Exception as exc:
                logger.warning(f"[K5] Ingest failed for {path}: {exc}")
                errors += 1

    summary = {"ingested": ingested, "skipped": skipped, "errors": errors}
    logger.info(f"[K5] Static ingestion complete — {summary}")
    return summary


def schedule_static_ingestion() -> None:
    """
    Launch static ingestion in a background daemon thread.
    Startup is not blocked. Any failure is logged but not fatal.
    """
    def _run() -> None:
        try:
            run_static_ingestion()
        except Exception as exc:
            logger.error(f"[K5] Static ingestion thread error: {exc}", exc_info=True)

    t = threading.Thread(target=_run, name="k5-static-ingestion", daemon=True)
    t.start()
    logger.info("[K5] Static ingestion thread launched")
