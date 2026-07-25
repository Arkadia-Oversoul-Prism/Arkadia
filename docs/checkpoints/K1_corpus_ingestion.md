# K1 — Corpus Document Ingestion

**Status:** COMPLETE  
**Date:** ARK Y1 · D117 (2026-07-25)  
**Role:** Implementation Steward  
**Commit:** One commit — see git log  

---

## Objective

Every document entering the corpus must automatically become a Knowledge OS entity — embedded, graph-linked, timeline-recorded, and searchable — without manual syncing.

## Gap Closed

Before K1: corpus documents were served through the RAG layer only. The Knowledge Graph had no awareness of document content.

After K1: every document ingestion path fires `_ingest_to_knowledge_os()` in a daemon thread, which calls `knowledge.pipeline.ingest()`. The pipeline handles embeddings, graph edges, timeline records, and search indexing automatically.

---

## Changes Made

**File:** `api/main.py`

### 1. Added `_ingest_to_knowledge_os()` helper (adjacent to `_archive_oracle_turn()`)

Shared fire-and-forget helper called from all three ingestion entry points. Calls `knowledge.pipeline.ingest()` with `note_type="document"` and source-specific tags. Exceptions are swallowed — callers are never blocked. Duplicate-detection inside `pipeline.ingest()` makes repeated calls idempotent (safe across corpus refreshes).

### 2. Wired into `POST /api/scrolls` — `create_scroll()`

After `_save_direct_scrolls()` and cache bust, spawns a daemon thread with `source="direct_scroll"`.

### 3. Wired into `POST /api/codex/upload` — `upload_file()`

After `_save_direct_scrolls()` and cache bust, spawns a daemon thread with `source="upload"` and `tags=[category, "file"]`.

### 4. Wired into `POST /api/corpus/refresh` — `corpus_refresh()`

After `_get_scrolls(force=True)`, spawns a single background thread that iterates over all live scrolls and calls `_ingest_to_knowledge_os()` for each. The bulk thread is non-blocking for the HTTP response. Duplicate-detection ensures re-refreshes do not create duplicate Knowledge OS entries.

---

## Ingestion Flow (Post K1)

```
User uploads / creates scroll / triggers refresh
        ↓
Corpus layer (RAG, cache, direct scrolls) — unchanged
        ↓  [background daemon thread]
_ingest_to_knowledge_os()
        ↓
knowledge.pipeline.ingest()
        ↓
Embeddings → Knowledge Graph → Timeline → Search Index → SolSpire Console
```

---

## Verification

- `pytest tests/architecture -q` → **10/10 PASS**
- `pytest tests/ -q` → pre-existing collection errors unchanged (`codex_brain` missing — not introduced by this checkpoint)
- Pre-push checklist: no TODO/FIXME/XXX/HACK/arkadia-n26k introduced in workspace source files

## Crystal Triune Scan

No user-facing `Crystal Triune` references found in Python, TypeScript, JavaScript, or Markdown source files. No replacements needed.

## Next Checkpoint

**K5 — Static Ingestion** (vault, ADRs, open loops)
