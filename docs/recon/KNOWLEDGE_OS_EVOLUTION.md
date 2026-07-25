# Knowledge OS Evolution
> Produced from: 21 recon documents + direct code inspection
> Phase: 1 (complete before implementation)
> Status: Design document only — no implementation in this file

---

## 1. Knowledge OS Readiness Report

### The Central Finding

**The Knowledge Layer infrastructure is pre-built and waiting. The Oracle does not use it.**

`knowledge/` contains ~1,124 lines of implemented code: a full ingestion pipeline, a semantic context engine, an 8-mode search system, a typed graph, an immutable timeline, vault CRUD, and Gemini embeddings with BM25 fallback. None of it is wired into the Oracle's request path.

Every Oracle conversation ends like this:

```
User input
  → corpus/manager.py (priority-tier document selection)
  → api/main.py assembles last 12 turns
  → Gemini call
  → Response returned to frontend
  → Response DISCARDED at the knowledge level
```

The Knowledge Layer exists one import away. It has never been called from the Oracle handler.

### What Is Actually Working

**Corpus retrieval:** `corpus/manager.py` supplies document context to the Oracle by priority-tier scoring (1–3 by directory), not true semantic embedding search. This is documented as "TF-IDF semantic relevance" in `replit.md` — the actual mechanism is a priority-tier document filter. Gap between documentation and implementation.

**Kernel memory:** `kernel/memory.py` performs keyword-match retrieval over `data/oracle_store.json` — balance snapshots, open loops, event records. Simple keyword matching, not embeddings. Confirmed by code.

**Knowledge Layer (unconnected):** `knowledge/pipeline.py:ingest()` is a complete 7-step pipeline: duplicate detection → note creation → auto-tag extraction → chunking → Gemini embedding → auto-linking → timeline record. Fully functional. Zero callers in the Oracle path.

**Context engine (unconnected):** `knowledge/context_engine.py:assemble_context()` performs semantic search (cosine similarity over Gemini embeddings, BM25 fallback) → graph expansion → timeline injection → token-budget-tracked assembly. Fully functional. Zero callers in the Oracle handler.

### Architectural Bottlenecks

**1. The Conversation Black Hole**
Every Oracle turn is discarded. No embedding, no graph link, no timeline entry. The system cannot retrieve its own past reasoning. Conversations accumulate in Firestore/localStorage as flat chat logs with no structure.

**2. The Corpus/Knowledge Split**
Two document retrieval systems exist side by side:
- `corpus/` — priority-tier document selection, feeds Oracle today
- `knowledge/` — semantic embedding search, feeds nothing today

The corpus system was built first; the knowledge system was built to replace it. The replacement was never connected.

**3. Three Independent Gemini Call Sites**
`api/main.py` + `kernel/planner.py` / `weaver/llm.py` / `solspire/llm.py` — three separate Gemini client instantiations that share no session context, no key rotation logic, and no retry coordination. The Knowledge OS cannot reason across these call sites.

**4. Phase 1 as Prerequisite**
The Knowledge Layer writes to `knowledge/arkadia.db`. Jobs and goals write to in-memory JSON stores. Until Phase 1 (Workstream B) completes SQLite durability, any conversation archival into `knowledge/arkadia.db` is more durable than the kernel state it describes. This inversion should be resolved before K2 (conversation archival).

### Existing Strengths

- `knowledge/pipeline.py:ingest()` is idempotent (duplicate detection by SHA-256 checksum)
- `knowledge/context_engine.py` has a token budget guard — cannot overflow the provider context window
- `knowledge/embeddings.py` has a BM25 fallback for when the Gemini embedding API is unavailable
- The graph model supports 9 typed relationships — rich enough to model the full entity graph
- The timeline is append-only and typed — 20+ event types already defined

---

## 2. Recon Synthesis

### Already Built (confirmed in code)

| Subsystem | Location | Status |
|---|---|---|
| Knowledge pipeline | `knowledge/pipeline.py` | ✅ Built, unconnected |
| Context engine (semantic) | `knowledge/context_engine.py` | ✅ Built, unconnected |
| 8-mode search | `knowledge/search.py` | ✅ Built, unconnected |
| Graph model | `knowledge/graph.py` + `knowledge/vault.py` | ✅ Built, unconnected |
| Embeddings (Gemini + BM25) | `knowledge/embeddings.py` | ✅ Built, unconnected |
| Immutable timeline | `knowledge/timeline.py` | ✅ Built, unconnected |
| Knowledge DB schema | `knowledge/db.py` + `knowledge/arkadia.db` | ✅ Built, unconnected |
| Corpus retrieval (priority) | `corpus/manager.py` | ✅ Built, connected (Oracle uses this today) |
| Oracle runtime | `api/main.py` + `kernel/` | ✅ Built, connected |
| SolSpire kernel | `kernel/execution.py` + `kernel/planner.py` | ✅ Built, connected |
| Autonomy layer | `weaver/` | ✅ Built, separate call graph |
| Symbolic vector memory | `weaver/echofield/` | ✅ Built (governance only, not Oracle) |
| Discord/Telegram bots | `bot/` | ✅ Built, connected |
| React/Vite frontend | `web/public_prism/` | ✅ Built, connected |

### Duplicated (needs resolution)

| Duplication | Files | Resolution |
|---|---|---|
| Document retrieval | `corpus/manager.py` (priority) vs `knowledge/context_engine.py` (semantic) | K3: replace corpus with context engine |
| Three Gemini call sites | `api/main.py`, `weaver/llm.py`, `solspire/llm.py` | Phase 2: unified provider client |
| IMS Archive rendering | `NexusPage.tsx`, `IMSArchivePage.tsx`, `ShereSanctuary.tsx` | P1 fix (see recon/21) |

### Obsolete (safe to archive)

| Item | Evidence | Action |
|---|---|---|
| `engine/`, `parsers/`, `schemas/` | No confirmed live callers found in recon | Confirm with grep, archive if confirmed |
| `arkana_rasa/` | Rasa NLU — superseded by kernel planner | Archive |
| `sanctum/status.py` | No confirmed callers | Confirm with grep, archive if confirmed |
| `sonata/` (Java) | Superseded by `sonata-android/` (Kotlin) | Archive |
| `attached_assets/arkadia_spirit/GovernanceSpirit/` | Full duplicate nested project (Drizzle, Postgres) | Remove from main tree |

### Should Enter the Knowledge Graph

Once K1–K2 are implemented, these sources should be ingested into `knowledge/arkadia.db`:

- Oracle conversations (K2 — first priority)
- Corpus documents from `corpus/` (K1)
- ADRs and governance documents (K5 — static ingestion)
- SolSpire project conversations (`data/solspire_projects.db` → pipeline)
- Open loops and transactions from `data/oracle_store.json` (K5)
- Vault notes in `vault/` (K5 — already in the right format)
- IMS deliverables from `static/ims/*.html`

---

## 3. Knowledge Domain Model

All types extracted from confirmed code and schema — no invented types.

### knowledge/arkadia.db (SQLite — fully implemented)

| Type | Table | Key fields |
|---|---|---|
| Project | `projects` | `name`, `description`, `status` |
| Thread | `threads` | `project_id`, `title`, `type` |
| Note / KnowledgeEntry | `notes` | `uuid`, `title`, `content`, `note_type`, `checksum`, `embedding_status` |
| Chunk | `chunks` | `note_id`, `content`, `position`, `token_count` |
| Embedding | `embeddings` | `chunk_id`, `vector` (JSON), `model`, `dimensions` |
| Tag | `tags` | `name` |
| NoteTag | `note_tags` | `note_id`, `tag_id` |
| GraphEdge | `graph_edges` | `source_id`, `target_id`, `relationship` |
| TimelineEvent | `timeline_events` | `event_type`, `payload`, `note_id`, `project_id` |
| Provider | `providers` | `name`, `tier`, `capabilities` |
| Persona | `personas` | `name`, `role`, `oracle_identity` |

**Note types** (from `knowledge/vault.py`): `conversation`, `document`, `research`, `task`, `goal`, `event`, `note`, `decision`

**Relationship types** (9): `references`, `elaborates`, `contradicts`, `supports`, `precedes`, `follows`, `spawned`, `resolved_by`, `tagged_with`

**Timeline event types** (20+): `ingest`, `embed_complete`, `search`, `context_assembled`, `note_created`, `note_updated`, `graph_edge_created`, etc.

### data/ — JSON/file-backed (legacy kernel state)

| Type | File | Owner |
|---|---|---|
| Transaction | `data/oracle_store.json[transactions]` | `kernel/oracle_store.py` |
| OpenLoop | `data/oracle_store.json[open_loops]` | `kernel/oracle_store.py` |
| Asset | `data/oracle_store.json[assets]` | `kernel/oracle_store.py` |
| Event | `data/oracle_store.json[events]` | `kernel/oracle_store.py` |
| Job | `data/job_store.json` | `kernel/jobs.py` |
| Goal | `data/goal_store.json` | `kernel/goals.py` |
| Node / Identity | `data/nodes_seed.json` | `api/nodes.py` |
| PersonalCodex | `data/personal_codices/*.json` | `api/main.py` |

### data/solspire_projects.db (SQLite — SolSpire console)

| Type | Table |
|---|---|
| SolSpireProject | `project_conversations` |
| ProjectFile | `project_files` |
| ProjectRepository | `project_repositories` |
| ProjectTask | `project_tasks` |
| ProjectMemory | `project_memory` |
| ProjectEvent | `project_events` |

### governance/ — Weaver autonomy layer

| Type | File |
|---|---|
| GovernanceManifest | `governance/manifest.json` |
| PermissionRule | `governance/permissions.json` |
| RoleDefinition | `governance/roles.json` |
| Boundary | `governance/boundaries.json` |
| Vow | `governance/vows.md` |
| VectorNode | `weaver/echofield/vector_stack.py` (6-axis: identity/function/resonance/structure/mythic/directive) |

---

## 4. Evolution Proposal — Workstream K

### Principle

**Do not build. Connect.**

The Knowledge Layer already exists. The Oracle already exists. Three function calls close the central gap:

```python
pipeline.ingest(...)               # K2: archive conversation turns
pipeline.ingest(...)               # K1: archive corpus documents
context_engine.assemble_context()  # K3: replace corpus retrieval
```

No new abstractions. No redesign. ADR-015 is preserved throughout — all proposed dependencies flow in permitted directions (`api/ → knowledge/` is Layer 4 → Layer N, permitted).

### Workstream K Checkpoints

**K1 — Corpus Document Ingestion**

Connect `github_corpus.py` (incremental fetch) and `corpus/manager.py` (document loading) to `knowledge/pipeline.ingest()`. After each corpus document is fetched/refreshed, ingest it into `knowledge/arkadia.db`.

- Files touched: `corpus/manager.py` or `github_corpus.py`
- Function call: `pipeline.ingest(title=doc.title, content=doc.content, note_type="document", tags=[doc.category])`
- Exit: corpus documents appear in `knowledge/arkadia.db`; search returns them
- Risk: Low — fire-and-forget; existing corpus retrieval unchanged

**K2 — Oracle Conversation Archival** ← First checkpoint, highest value

Add a post-response hook to the Oracle handler (`/api/commune/resonance`) that ingests each completed turn into the Knowledge Pipeline.

- File touched: `api/main.py` (one function, ~5 lines)
- Call site: after the Gemini response is assembled, before it is returned
- Function call: `pipeline.ingest(title=f"Oracle turn {session_id}", content=f"User: {user_input}\n\nArkana: {response}", note_type="conversation", tags=["oracle", "conversation"])`
- Exit: Oracle turns appear in `knowledge/arkadia.db`; they are embedded and retrievable
- Risk: Low — async fire-and-forget; failure silently skipped (never blocks the Oracle response)

**Why K2 first, not K1:**
K2 touches one handler and adds one function call. It is entirely non-blocking (call `pipeline.ingest()` in a background thread). Every future Oracle conversation immediately becomes searchable knowledge. K1 requires understanding corpus fetch timing and is higher-risk.

**K3 — Context Engine Wiring**

Replace `corpus/manager.py`'s priority-tier selection with `knowledge/context_engine.assemble_context()` in the Oracle handler.

- Files touched: `api/main.py` (Oracle handler context assembly section)
- Change: swap `corpus_context = corpus_manager.get_context(query)` for `ctx = context_engine.assemble_context(query=user_input)`
- Exit: Oracle uses semantic search over the embedded Knowledge Graph for context
- Risk: Medium — changes the Oracle's retrieval behavior; requires K2 to have populated the graph first
- Prerequisite: K1 + K2 complete (graph must have content to search)

**K4 — Response Provenance**

Make Oracle responses citable. The context engine already returns note UUIDs alongside text chunks. Surface these as a `sources` array in the Oracle response.

- Files touched: `api/main.py` (response shape), `web/public_prism/src/components/ArkanaCommune.tsx` (render sources)
- Exit: Oracle response includes a `sources` list; frontend shows "Based on: ..." citations
- Risk: Low — additive to response shape; frontend can render conditionally

**K5 — Static Ingestion**

One-time migration: ingest all existing knowledge into the Knowledge Graph.

Sources: `vault/*.md` → `pipeline.ingest(..., note_type="note")` · ADRs + governance docs → `pipeline.ingest(..., note_type="document")` · Open loops from `data/oracle_store.json` → `pipeline.ingest(..., note_type="event")` · SolSpire project conversations → `pipeline.ingest(..., note_type="conversation")`

- Implement as a standalone `scripts/ingest_static.py` — one-time run, not part of the Oracle path
- Exit: Vault, ADRs, open loops, and project conversations searchable via the Knowledge Graph

### Sequencing

```
Phase 1 / Workstream B (SQLite durability)  ←  Must complete first
        ↓
K2 — Conversation Archival                  ←  First K checkpoint (touch one handler)
        ↓
K1 — Corpus Ingestion                       ←  After K2 validated
        ↓
K5 — Static Ingestion                       ←  One-time migration script
        ↓
K3 — Context Engine Wiring                  ←  After K1+K2 populate the graph
        ↓
K4 — Response Provenance                    ←  After K3; user-visible feature
```

### What This Produces

After K1–K3 complete, the Oracle's reasoning loop looks like this:

```
User input
  → knowledge/context_engine.assemble_context(query=input)
       → embed query (Gemini)
       → semantic search over knowledge/arkadia.db
       → graph expansion (1 hop)
       → token-budget-tracked assembly
  → last 12 turns
  → ORACLE_IDENTITY
  → Gemini call
  → Response
  → knowledge/pipeline.ingest(conversation turn)   ← K2 hook
  → Return to user
```

Every conversation deepens the Knowledge Graph. Every future conversation retrieves from it. The system becomes more capable with use — not because the model changed, but because the knowledge substrate grows.

This is the Oversoul Prism architecture from the red notebooks: not a chatbot, but an intelligence substrate where conversations become structure, structure becomes retrieval, and retrieval becomes future reasoning.

---

## Summary for Implementation Agent

The first K checkpoint is **K2 — Conversation Archival**.

**Exact change:** In `api/main.py`, locate the `/api/commune/resonance` handler. After the Oracle response text is assembled and before it is returned, call:

```python
import threading
from knowledge import pipeline

def _archive_turn(user_input: str, response: str, session_id: str):
    try:
        pipeline.ingest(
            title=f"Oracle conversation — {session_id[:8]}",
            content=f"User: {user_input}\n\nArkana: {response}",
            note_type="conversation",
            tags=["oracle", "conversation"],
        )
    except Exception:
        pass  # Never block the Oracle response

threading.Thread(target=_archive_turn, args=(user_input, response, session_id), daemon=True).start()
```

**What this adds:** ~8 lines of code. Every Oracle turn is embedded and stored in `knowledge/arkadia.db` in a background thread. The Oracle response is never delayed or blocked.

**Prerequisites before implementing K2:**
1. Workstream B1 complete (SQLite durability for jobs/goals) — ensures the runtime is stable before wiring Knowledge Layer
2. Architecture fitness tests green (10/10)
3. `knowledge/arkadia.db` initialized (call `knowledge.db.init_db()` on startup if not already)
