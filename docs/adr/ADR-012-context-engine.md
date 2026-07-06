# ADR-012: Context Engine — Semantic Retrieval, Not Memory Dump

**Status:** Accepted  
**Date:** 2026-07-06  
**Supersedes:** `kernel/memory.py` Phase 8 keyword search; raw prompt prepending

---

## Context

The existing Phase 8 memory system (`kernel/memory.py`) uses keyword matching
against `oracle_store.json` to inject context into the planner prompt.

Problems:
1. Keyword matching misses semantic relationships
2. Injecting a raw memory dump wastes token budget and degrades reasoning quality
3. No graph expansion — related notes are invisible
4. Context is per-session, not persistent across sessions

---

## Decision

Implement a **Context Engine** at `knowledge/context_engine.py` that:

1. **Embeds** the query using Gemini `text-embedding-004` (768-dim)
2. **Scores** all stored chunk embeddings by cosine similarity
3. **Falls back** to BM25 when embeddings are unavailable (offline-first)
4. **Resolves** the top-K relevant notes from chunk scores
5. **Graph-expands** each note one hop to surface related knowledge
6. **Adds** project context (name, description, recent notes)
7. **Appends** recent timeline events for the project
8. **Returns** a typed `ContextPackage` dict — never a raw string dump

**Provider receives:**
```
## Project: <name>
## Relevant Knowledge
### <note_title> (<type>)
<relevant chunk 1>
<relevant chunk 2>
## Related Nodes
- <related note>
## Recent Activity
- [event_type] <timestamp>
```

**Never:**
- A giant flat memory file
- Entire note contents (only relevant chunks)
- More than 8 notes + 6 graph expansions per call

**Why:**
- Token budget discipline: providers get only what's relevant
- Semantic retrieval beats keyword matching for concept-level queries
- Graph expansion surfaces non-obvious but structurally related knowledge
- Offline-first BM25 fallback satisfies LAW II

---

## Upgrade Path for kernel/memory.py

`kernel/memory.py` has been upgraded to:
1. **Try** semantic retrieval first (from Knowledge Vault)
2. **Fall back** to oracle_store keyword scan (backward compat)
3. **Attach** `knowledge_vault` key to context dict when available

The planner contract is unchanged. No planner code was modified.

---

## Consequences

- All new AI interactions should go through `POST /api/knowledge/providers/send`
  which automatically assembles context before routing to a provider
- The oracle_store keyword scan remains as a fallback during the migration period
- Embedding must be triggered after every note ingest (pipeline handles this)
