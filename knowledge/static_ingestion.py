"""
Arkadia Knowledge OS — K5 Static Ingestion
==========================================
One-time startup pass that seeds the Knowledge OS with static knowledge that
already exists in the repository but has never been ingested.

Two source kinds are declared in `_SOURCES`:

  * ``file`` (default) — a ``root`` + ``glob`` over markdown on disk. One
    ingest per file.
  * ``oracle_open_loops`` — the loop rows inside the canonical oracle store
    (``data/oracle_store.json``). One ingest per open loop. Declared here
    because K5 names "open loops" explicitly; they are records, not files, so
    they cannot be reached by a markdown glob.

LAW I: One pipeline. Ingest always calls pipeline.ingest().

Idempotency is checksum-scoped and therefore *per source*: the same bytes always
dedupe, but two sources whose content differs only in incidental whitespace are
two different checksums. Because a ``vault`` projection of a note is the note's
content wrapped in frontmatter, file bodies are normalised with
``_normalize_body`` so re-reading a projection yields the original checksum.

What this does NOT and cannot fix: a note created from source A is still a real
second object when source B *scans the same bytes*. In production cwd, note
projections land in ``vault/`` — the ``static:vault`` scan root — so a
first-pass ingestion can be re-read from the vault on a later pass. That is
cross-source duplication driven by the ingestion order, not a normalisation bug.

Called from api/main.py lifespan() — runs once at startup in a background thread.
Never duplicates existing objects (checksum-based deduplication).
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("arkadia.static_ingestion")

# ─────────────────────────────────────────────────────────────────────────────
# Source definitions
# Each entry: (root, glob, note_type, tags, source_provider)
# `glob` is None for non-file sources, which are dispatched by `kind`.
# ─────────────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent

# Canonical oracle store. Same path kernel/oracle_store.py resolves by default
# (`SOLSPIRE_DATA_DIR` or "data"); env override honoured so a relocated store is
# still seeded rather than silently skipped.
_ORACLE_STORE_PATH = Path(os.environ.get("SOLSPIRE_DATA_DIR", str(_REPO_ROOT / "data"))) / "oracle_store.json"

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
    # Architecture Decision Records — named explicitly in the K5 objective
    {
        "root": _REPO_ROOT / "docs" / "adr",
        "glob": "*.md",
        "note_type": "document",
        "tags": ["adr", "architecture", "static-corpus"],
        "source_provider": "static:adr",
    },
    # Vault notes already on disk (written by create_note but may predate ingestion)
    {
        "root": _REPO_ROOT / "vault",
        "glob": "**/*.md",
        "note_type": "note",
        "tags": ["vault", "static-corpus"],
        "source_provider": "static:vault",
    },
    # Open loops — records, not files. K5 names them explicitly; they live in the
    # canonical oracle store and are dispatched by kind, not by glob.
    {
        "kind": "oracle_open_loops",
        "root": None,
        "glob": None,
        "note_type": "task",
        "tags": ["open-loop", "oracle-store", "static-corpus"],
        "source_provider": "static:oracle_open_loops",
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


def _normalize_body(text: str) -> str:
    """Canonicalise a note body for checksum-stable duplicate detection.

    ``create_note`` persists ``frontmatter + content`` verbatim while
    ``pipeline.ingest`` checksums ``content`` alone. A caller that appends a
    trailing newline (or a blank line) before ingest therefore writes a file
    whose re-read body never matches its own stored checksum, so re-reading that
    file ingests a spurious duplicate. Trailing whitespace is presentation, not
    content: strip it on both write and read so the round-trip converges.
    """
    return text.strip()


def _title_from_path(path: Path) -> str:
    """Derive a human-readable title from the file path."""
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    # Capitalise first letter of each word
    return " ".join(w.capitalize() for w in stem.split())


def _iso(ts: float | int | None) -> str:
    """Render an epoch timestamp as an ISO-8601 UTC string."""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return "unknown"


def _oracle_open_loop_rows() -> list[dict]:
    """Read the open-loop rows from the canonical oracle store.

    Read-only. A missing or malformed store yields no rows rather than raising:
    a singleton runtime artefact must never abort the startup ingestion pass.
    """
    try:
        raw = _ORACLE_STORE_PATH.read_text(encoding="utf-8")
        store = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug(f"[K5] Oracle store unreadable ({_ORACLE_STORE_PATH}): {exc}")
        return []

    loops = store.get("open_loops") or []
    return [loop for loop in loops if isinstance(loop, dict)]


def _ingest_oracle_open_loops(source: dict) -> tuple[int, int, int]:
    """Ingest each oracle-store open loop as a ``task`` note.

    Stable per-loop content (id, loop text, status, created, updated) keeps the
    checksum dedupe deterministic across runs. Repeat-barren records — looped
    more than once with only `updated_at` moving — are deduped by including the
    update timestamp, which is the loop's own last-write marker, not a clock
    read taken here.
    """
    from knowledge.pipeline import ingest as _ingest

    ingested = skipped = errors = 0

    for loop in _oracle_open_loop_rows():
        loop_id = str(loop.get("id") or "").strip()
        text = str(loop.get("loop") or "").strip()
        if not text:
            skipped += 1
            continue

        status = str(loop.get("status") or "open").strip() or "open"
        updated = _iso(loop.get("updated_at") or loop.get("ts"))
        content = _normalize_body(
            f"Open loop\n"
            f"ID: {loop_id or 'unidentified'}\n"
            f"Loop: {text}\n"
            f"Status: {status}\n"
            f"Created: {_iso(loop.get('ts'))}\n"
            f"Updated: {updated}"
        )
        try:
            result = _ingest(
                title=f"Open loop: {text}"[:200],
                content=content,
                note_type=source["note_type"],
                tags=source["tags"],
                source_provider=source["source_provider"],
                auto_tag=True,
                auto_embed=False,
                auto_link=False,
            )
            if result.get("duplicate"):
                skipped += 1
            else:
                ingested += 1
        except Exception as exc:
            logger.warning(f"[K5] Open-loop ingest failed for {loop_id or text[:40]}: {exc}")
            errors += 1

    return ingested, skipped, errors


def run_static_ingestion() -> dict:
    """
    Scan all configured static sources and ingest any record not already
    present in the Knowledge OS (idempotent via checksum deduplication).

    Returns a summary dict for logging.
    """
    from knowledge.pipeline import ingest as _ingest

    ingested = 0
    skipped  = 0
    errors   = 0

    for source in _SOURCES:
        if source.get("kind") == "oracle_open_loops":
            _i, _s, _e = _ingest_oracle_open_loops(source)
            ingested += _i
            skipped  += _s
            errors   += _e
            continue

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
            content = _normalize_body(body if body else raw)
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
