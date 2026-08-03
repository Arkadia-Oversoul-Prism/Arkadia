# Arkadia Knowledge Graph Specification

> **Constitutional document.** This file governs every decision about the Knowledge Graph.  
> Do not implement graph features that contradict this document.  
> Update this document through the checkpoint process when a decision changes.

---

## Purpose

The Knowledge Graph is the shared substrate of the entire Arkadia ecosystem.

Every product — NovaNet, ReasoMate, Spiral Codex, Encyclopedia Galactica, Nexus, SolSpire — is a **lens over the same underlying knowledge model**. Products do not own data. They visualise nodes and edges.

```
Everything
  ↓
Knowledge Graph
  ↓
Views (NovaNet · Spiral Codex · Encyclopedia · SolSpire · ReasoMate)
```

---

## Node Types

Every object ingested into the Knowledge OS is stored as a `note` row with a canonical `note_type`.

| Type | Description | Vault Directory |
|---|---|---|
| `document` | Imported or uploaded document | `Documents/` |
| `conversation` | Oracle conversation exchange | `Projects/` |
| `person` | Individual — author, participant, historical figure | `People/` |
| `project` | A defined body of work | `Projects/` |
| `organization` | Company, institution, community body | `Organizations/` |
| `community` | Social or knowledge community | `Communities/` |
| `concept` | Abstract idea, principle, or doctrine | `Ideas/` |
| `scroll` | Curated Spiral Codex article | `Scrolls/` |
| `chapter` | Encyclopedia Galactica chapter | `Encyclopedia/` |
| `place` | Geographic or cosmological location | `Places/` |
| `timeline_event` | Historical or projected event | `Timeline/` |
| `media` | Audio, video, image asset | `Media/` |
| `task` | Actionable item or open loop | `Projects/` |
| `note` | General catch-all note | `Ideas/` |

### Legacy Types (preserved for backward compatibility)

| Legacy Type | Canonical Equivalent |
|---|---|
| `research` | `document` |
| `book` | `document` |
| `idea` | `concept` |
| `decision` | `note` |
| `daily` | `note` |

---

## Relationship Types

Edges in the `graph_edges` table must use a type from this list.

### Semantic Relationships

| Type | Meaning |
|---|---|
| `references` | A cites or points to B |
| `derived_from` | A is built on or sourced from B |
| `contradicts` | A directly opposes or disputes B |
| `supported_by` | A is validated or backed by B |
| `inspired_by` | A was creatively or intellectually motivated by B |
| `mentions` | A contains a reference to B without deep dependency |

### Structural Relationships

| Type | Meaning |
|---|---|
| `belongs_to` | A is a member of collection B |
| `part_of` | A is a sub-element of B |
| `child_of` | A descends from B in a hierarchy |
| `parent_of` | A contains B as a child element |
| `follows` | A comes after B in sequence |
| `precedes` | A comes before B in sequence |

### Authorship / Provenance

| Type | Meaning |
|---|---|
| `authored_by` | A was written or created by person B |
| `generated_by` | A was produced by a system or tool B |
| `reviewed_by` | A was evaluated or approved by B |

### General

| Type | Meaning |
|---|---|
| `relates_to` | A and B are semantically connected (catch-all) |
| `extends` | A builds upon or expands B |
| `summarizes` | A is a condensed version of B |
| `implements` | A is a concrete realisation of B |

---

## Identity Rules

### Duplicate Detection

- Duplicate detection is **content-based**: SHA-256 checksum of the raw content string.
- Two objects with identical content checksums are the same object; the second write is a no-op.
- Title changes alone do not create duplicates.

### UUIDs

- Every node has a stable UUID assigned at creation.
- UUIDs are the cross-system identity. Never use integer IDs in external references.

### Merge Policy

- Merging two nodes (e.g. two person records for the same individual) is a **manual operation**.
- Automated linking via tag similarity does not merge; it only creates edges.

---

## Lifecycle Rules

### Creation

1. Content enters via `knowledge.pipeline.ingest()` — the only canonical entry point.
2. `ingest()` creates a `note` row, chunks the content, queues embeddings, runs auto-link, records a `knowledge_created` timeline event.
3. **All creation paths must go through `pipeline.ingest()`.**

### Update

- Content updates reset `embedding_status` to `pending`.
- The timeline receives a `knowledge_modified` event.
- Checksum is recomputed; a content change that produces the same checksum is a no-op.

### Archival

- Nodes are never deleted from the Knowledge Graph.
- A `status` field (to be added in a future checkpoint) will allow `active | archived` filtering.
- Archival produces a `knowledge_archived` timeline event.

---

## Ownership Rules

| Source | Owner | Access |
|---|---|---|
| Oracle conversations | User session | Private by default |
| Corpus documents | System | Public (Spiral Codex) |
| Encyclopedia chapters | System | Public |
| Static ingestion (docs/, ADRs) | System | Internal |
| User-created notes | User | Private by default |

Ownership semantics are stored in `source_provider` and will be expanded with an `owner_id` field in a future checkpoint.

---

## Retrieval Semantics

### Context Assembly (Arkana / Oracle)

Entry point: `knowledge.context_engine.assemble_context(query, project_id, thread_id, ...)`

Steps:
1. Semantic search over embedded chunks
2. Full-text fallback
3. Graph expansion (BFS depth-1 from top results)
4. Project context injection
5. Timeline history (most recent N events)
6. Token budget enforcement

### Search (SolSpire / Crystal Triune)

Entry point: `knowledge.search.unified_search(query, modes, top_k, ...)`

Modes: `semantic`, `fulltext`, `tag`, `timeline`, `graph`, `project`, `people`, `references`

### Graph Traversal (Visualisation)

Entry point: `knowledge.graph.traverse(start_id, max_depth, relationship_filter)`

Full export: `knowledge.graph.full_graph_export()`

---

## The One Pipeline Law

> **LAW I: One pipeline. One canonical home.**

There is exactly one entry point for knowledge ingestion: `knowledge.pipeline.ingest()`.

There is exactly one entry point for context retrieval: `knowledge.context_engine.assemble_context()`.

There is exactly one canonical type vocabulary: `knowledge.node_types`.

Any code that bypasses these entry points is a defect.

---

## File Map

| File | Role |
|---|---|
| `knowledge/node_types.py` | **Canonical type vocabulary** — single source of truth |
| `knowledge/pipeline.py` | Ingestion pipeline — ingest(), ingest_conversation() |
| `knowledge/graph.py` | Graph operations — add_edge, traverse, find_path, full_graph_export |
| `knowledge/vault.py` | Note CRUD — create_note, update_note, list_notes |
| `knowledge/search.py` | Multi-mode search — unified_search() |
| `knowledge/timeline.py` | Immutable event log — record(), query() |
| `knowledge/context_engine.py` | RAG context assembly — assemble_context() |
| `knowledge/embeddings.py` | Vector embedding — embed_text(), store_chunk_embedding() |
| `knowledge/db.py` | Thread-safe SQLite connection |
| `knowledge/schema.sql` | Canonical DDL |

---

*Last updated: ARK Y1 · D183 (2026-08-02) — K3 Knowledge Graph Foundation*
