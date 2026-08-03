# Checkpoint K3-C — Knowledge Graph Enrichment

**Date:** ARK Y1 · D136 (2026-08-03)
**Role:** Arkadia Implementation Steward
**Session type:** Workstream K — Checkpoint K3-C (semantic enrichment + graph intelligence)

---

## Objective

Make the Knowledge Graph intelligent — turn isolated facts into a self-linking
semantic network by discovering relationships that already exist in the data.

The canonical ontology from K3-A is **frozen and untouched**.
The infrastructure from K3-B is **extended, not replaced**.

---

## Progression

| Checkpoint | Layer |
|---|---|
| K3-A | Canonical ontology (schema) |
| K3-B | Operational graph (infrastructure) |
| **K3-C** | **Semantic enrichment (intelligence)** |

---

## Deliverables

### Created

| File | Purpose |
|---|---|
| `knowledge/edge_migration.py` | Legacy edge migration utility (Task 1) |
| `knowledge/enrichment.py` | Semantic enrichment engine (Task 2) |
| `knowledge/embedding_queue.py` | Embedding completion queue (Task 6) |
| `web/public_prism/src/pages/knowledge/NodeInspector.tsx` | Node inspector component (Task 5) |

### Modified

| File | Change |
|---|---|
| `knowledge/pipeline.py` | Auto-link step now calls `enrichment.schedule_enrichment()` with tag-heuristic fallback |
| `api/main.py` | Added embedding pass + orphan enrichment to `lifespan()` startup sequence |
| `api/knowledge_routes.py` | 10 new endpoints (Tasks 1, 2, 4, 6, 7); extended `/status` growth metrics |
| `web/public_prism/src/lib/knowledgeApi.ts` | Added `NodeDetail`, `EdgeDetail`, `NeighborResult`, `PathResult`, `EmbeddingStatus`, `MigrationReport` types + 8 new API call functions |
| `web/public_prism/src/pages/knowledge/KnowledgeGraphView.tsx` | Selected-node panel replaced with `NodeInspector` |

---

## Task Summary

### Task 1 — Legacy Edge Migration (`knowledge/edge_migration.py`)

- `scan_violations()` — find all non-canonical edge types (read-only)
- `build_migration_report()` — full report without changes
- `apply_migration(dry_run=True)` — migrate mappable types using INSERT OR IGNORE + DELETE; unmappable types reported and left unchanged; never auto-deletes data
- 40-entry `LEGACY_TO_CANONICAL` map covering all known pre-K3-A identifiers
- CLI: `python3 -m knowledge.edge_migration --report | --dry-run | --apply`
- Exposed at: `GET /api/knowledge/migrate/edges/report`, `POST /api/knowledge/migrate/edges/apply`

### Task 2 — Semantic Enrichment Engine (`knowledge/enrichment.py`)

Five evidence scorers, each returning `(target_id, relationship, weight, reason)` tuples:

| Scorer | Relationship | Threshold |
|---|---|---|
| `_shared_tag_links` | `relates_to` / `references` | confidence ≥ 0.25 |
| `_shared_project_links` | `relates_to` | fixed 0.4 |
| `_conversation_thread_links` | `replies_to` | 0.9 (thread predecessor) |
| `_type_affinity_links` | `follows` / `references` | sequence / title overlap |
| `_source_provider_links` | `connected_to` | 0.3 (same provider) |

- `enrich_note(note_id)` — enrich one note; returns edges_created count
- `enrich_batch(note_ids)` — batch processing
- `enrich_all_orphans(limit)` — find and enrich nodes with no outbound edges
- `schedule_enrichment(note_id)` — background daemon thread (called from pipeline)
- `schedule_orphan_enrichment()` — background daemon thread (called at startup)
- Never fabricates links — confidence threshold gate on all edges
- Idempotent — `INSERT OR REPLACE` on `graph_edges` UNIQUE constraint

Exposed at: `POST /api/knowledge/enrich/{note_id}`, `POST /api/knowledge/enrich/orphans`

### Task 3 — Knowledge Object Identity

Notes already have stable UUIDs via `notes.uuid` (set at creation in `vault.create_note()`).
The `NodeInspector` now surfaces this UUID prominently as "STABLE ID".
The new `/api/knowledge/node/{id}` endpoint returns `node.uuid` explicitly.
Identity survives: re-indexing (checksum-based dedup), embedding refresh, migration (UUID never changes), startup ingestion.
No schema change required — the existing UUID column is the persistent identity.

### Task 4 — Graph Explorer API

New endpoints in `api/knowledge_routes.py`:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/knowledge/node/{id}` | Full node with outbound + inbound edge metadata |
| `GET` | `/api/knowledge/neighbors/{id}` | BFS traversal up to 3 hops; relationship filter supported |
| `GET` | `/api/knowledge/path` | Shortest path between two nodes (`from_id`, `to_id`, `max_depth`) |

All three power: Arkana context retrieval, SolSpire explorer, Encyclopedia drill-down, Spiral Codex linking.

### Task 5 — SolSpire Graph Explorer (`NodeInspector.tsx`)

- Full node metadata (type badge, title, creation date)
- Stable UUID display
- Degree summary (outbound / inbound / total in three mini-stat cards)
- Scrollable edge list with relationship type, direction arrow, weight, and target/source title
- "Explore Neighbors" drill-down button
- Wired into `KnowledgeGraphView` — replaces the minimal text card that existed before
- No layout or tab changes to `KnowledgeOSPage`

### Task 6 — Embedding Completion Queue (`knowledge/embedding_queue.py`)

- `get_embedding_status()` — progress snapshot (total / complete / pending / partial / failed / coverage / backlog)
- `process_pending_batch(n)` — embed up to n notes in one call
- `run_full_embedding_pass()` — loop until backlog is clear (max 20 passes, 50 notes/pass)
- `schedule_embedding_pass()` — background daemon thread; called from `lifespan()` after K5 ingestion
- Exposed at: `GET /api/knowledge/embeddings/status`, `POST /api/knowledge/embeddings/process`

### Task 7 — Knowledge Growth Metrics (extended `/api/knowledge/status`)

New fields in `growth` block:

| Field | Description |
|---|---|
| `notes_today` | Notes created in last 24 h |
| `edges_today` | Edges created in last 24 h |
| `avg_node_degree` | 2 × edges / nodes |
| `semantic_links` | Count of relates_to + references + connected_to + mentions + derived_from edges |
| `embed_coverage` | complete / total ratio (0.0 – 1.0) |

`indexing_status` block now includes `coverage` field.

---

## New API Surface (K3-C additions)

```
GET  /api/knowledge/node/{id}
GET  /api/knowledge/neighbors/{id}
GET  /api/knowledge/path
POST /api/knowledge/enrich/{note_id}
POST /api/knowledge/enrich/orphans
GET  /api/knowledge/migrate/edges/report
POST /api/knowledge/migrate/edges/apply
GET  /api/knowledge/embeddings/status
POST /api/knowledge/embeddings/process
```

---

## Startup Sequence (updated)

```
lifespan():
  1. Background corpus sync daemon
  2. Kernel workers + goal scheduler
  3. Real tool registration
  4. Node registry load
  5. K5 Static ingestion (background)      ← K3-B
  6. Embedding completion pass (background) ← K3-C
  7. Orphan enrichment pass (background)    ← K3-C
```

---

## Verification

```
pytest tests/architecture -q   → 10/10 PASSED
npm run build                  → ✓ zero errors
Canonical ontology untouched   → node_types.py + relationship_types.py unmodified
Semantic links idempotent      → UNIQUE constraint on graph_edges
Migration report: clean DB     → { "summary": { "clean": true } }
Embedding status               → GET /api/knowledge/embeddings/status → 200
Graph Explorer                 → GET /api/knowledge/node/1 → 200
```

---

## Hard Rules Compliance

- ✅ `node_types.py` not modified
- ✅ `relationship_types.py` not modified
- ✅ No new databases
- ✅ No competing pipelines — all enrichment flows through `pipeline.ingest()` → `enrichment.py` → `graph.add_edge()`
- ✅ No UI redesign — `NodeInspector` extends the existing side-panel slot
- ✅ No ADR edits
- ✅ No ROADMAP edits

---

## Stop Condition Met

- ✅ 10/10 architecture tests
- ✅ Build passes
- ✅ Legacy migration utility with report
- ✅ Semantic enrichment engine with confidence thresholds
- ✅ Stable Knowledge Object identity (UUID surfaced)
- ✅ Graph Explorer endpoints (`/node`, `/neighbors`, `/path`)
- ✅ SolSpire Node Inspector with edge browser
- ✅ Embedding completion queue with progress tracking
- ✅ Extended growth metrics in `/api/knowledge/status`
- ✅ Documentation updated
