# ADR-010: Knowledge Vault as Canonical Truth Store

**Status:** Accepted  
**Date:** 2026-07-06  
**Supersedes:** (N/A — new capability)

---

## Context

Arkadia previously stored knowledge as:
- Transient AI conversation history (lost on session end)
- A flat `data/oracle_store.json` for transactions, loops, and events
- Personal codices as JSON blobs
- No semantic indexing or graph relationships

This violates the Genesis Protocol principle:
> Knowledge is the source of truth. AI conversations are transient interfaces to that knowledge.

---

## Decision

Implement a canonical **Knowledge Vault** at `vault/` with the following structure:

```
vault/
├── Projects/     # Project-scoped notes and decisions
├── Books/        # Book notes and highlights
├── People/       # Person profiles
├── Ideas/        # Freeform ideas and concepts
├── Daily/        # Daily notes (YYYY-MM-DD)
├── Research/     # Deep research and citations
├── Attachments/  # Binary assets
├── Templates/    # Note templates
├── Archive/      # Soft-deleted notes
└── Index/        # Auto-generated search indexes
```

Every note is:
1. A Markdown file with YAML frontmatter (human-readable, portable)
2. An SQLite record in `knowledge/arkadia.db` (machine-indexed)
3. A graph node in the knowledge graph
4. An entry in the immutable timeline
5. Chunked and embedded for semantic search

**Why:**
- Markdown survives any provider change, any framework migration, any API shutdown.
- If every current AI provider disappeared tomorrow, the vault remains intact.
- SQLite provides fast machine-readable indexing without a server.
- The combination satisfies LAW II (Local First) and LAW III (Markdown is human format).

---

## Note Schema

Every note includes these metadata fields:

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Globally unique identifier |
| title | string | Human-readable title |
| created | ISO-8601 | Creation timestamp |
| updated | ISO-8601 | Last modification timestamp |
| project | UUID | Owning project (optional) |
| thread | UUID | Conversation thread (optional) |
| type | enum | note/conversation/research/book/person/idea/decision/daily |
| participants | list[str] | Node names involved |
| tags | list[str] | Semantic tags |
| links | list[UUID] | Explicit note links |
| embedding_status | enum | pending/complete/failed |
| graph_nodes | list | Related graph node IDs |
| checksum | SHA-256 | Content hash for change detection |
| source_provider | str | Provider that generated the content |

---

## Consequences

- Every AI response MUST be ingested through `knowledge/pipeline.py`
- Direct writes to oracle_store.json are deprecated (still readable for migration)
- The migration script `knowledge/migrate.py` ports existing data
- Orphan notes (without type/project) are not permitted
