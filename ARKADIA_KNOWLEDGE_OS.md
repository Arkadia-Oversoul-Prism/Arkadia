# Arkadia Knowledge OS
## Architecture Document — GENESIS_V1

**Codename:** ARKADIA_GENESIS_V1  
**Continuity Token:** GENESIS-JUL6-117  
**Date:** 2026-07-06

---

## Core Principle

> Knowledge is the source of truth. AI conversations are transient interfaces to that knowledge.

Arkadia is not a chatbot. It is not an AI wrapper. It is a local-first Knowledge Operating System where knowledge is the primary asset and AI providers become interchangeable reasoning adapters.

---

## Architectural Laws

| Law | Statement |
|-----|-----------|
| I | One capability. One implementation. One canonical home. |
| II | Local First. Cloud sync is additive. Never required. |
| III | Markdown is the human format. SQLite is the machine format. |
| IV | Oracle retrieves knowledge. Providers generate language. |
| V | Every subsystem must have a single responsibility. |

---

## System Map

```
┌─────────────────────────────────────────────────────────┐
│                    PRISM (Visualization)                 │
│         Knowledge Graph · Timeline · Projects            │
│         People · Books · Research · AI Activity         │
└───────────────────────┬─────────────────────────────────┘
                        │  HTTP (FastAPI)
┌───────────────────────▼─────────────────────────────────┐
│                 ORACLE (Orchestration)                   │
│   Semantic Search · Context Assembly · Auto-Linking     │
│   Tag Generation · Conflict Detection · Graph Traversal │
│              /api/knowledge/* routes                    │
└──────┬─────────────────────────┬────────────────────────┘
       │                         │
┌──────▼──────┐         ┌───────▼──────────────────────┐
│  KNOWLEDGE   │         │      PROVIDER ROUTER          │
│  PIPELINE    │         │  Gemini · Claude · GPT · ...  │
│  Ingest →    │         │  One interface. Swappable.    │
│  Chunk →     │         │  Business logic stays out.    │
│  Embed →     │         └──────────────────────────────┘
│  Graph →     │
│  Timeline    │
└──────┬───────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│                  KNOWLEDGE VAULT                         │
│                                                         │
│  vault/Projects/   vault/Books/     vault/People/       │
│  vault/Ideas/      vault/Daily/     vault/Research/     │
│  vault/Archive/    vault/Templates/ vault/Attachments/  │
│                                                         │
│         Every note = Markdown + SQLite + Graph          │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│              SQLite — knowledge/arkadia.db               │
│                                                         │
│  notes · chunks · embeddings · projects · threads       │
│  graph_edges · timeline · tags · references             │
│  attachments · providers · personas                     │
└─────────────────────────────────────────────────────────┘
```

---

## Knowledge Pipeline

Every conversation flows through this pipeline. Nothing is discarded.

```
Conversation
     ↓
Markdown Note (vault/)
     ↓
Chunking (knowledge/pipeline.py)
     ↓
Embedding (Gemini text-embedding-004 / BM25 fallback)
     ↓
SQLite Index (knowledge/arkadia.db)
     ↓
Knowledge Graph (graph_edges table)
     ↓
Timeline Entry (immutable)
     ↓
Search Index (available for retrieval)
```

**Entry point:** `POST /api/knowledge/ingest`  
**Conversation entry point:** `POST /api/knowledge/ingest/conversation`  
**Send with automatic knowledge context:** `POST /api/knowledge/providers/send`

---

## Context Engine

The provider receives ONLY relevant context, never a memory dump.

```
User Query
     ↓
Embed Query (text-embedding-004)
     ↓
Cosine Similarity → Top-K Chunks
     ↓
Resolve Notes from Chunks
     ↓
Graph Expand (1–2 hops)
     ↓
Add Project Context
     ↓
Add Recent Timeline
     ↓
Context Package (typed dict)
     ↓
Format for Provider (token-efficient string)
     ↓
Provider
```

**Offline fallback:** BM25 keyword scoring (no API required).

---

## Provider Router

```python
# Adding a new provider = 2 steps only:
# 1. Implement BaseProvider in providers/<name>.py
# 2. Register in providers/router.py

class BaseProvider(ABC):
    def authenticate(self) -> bool
    def send(messages, system_prompt, ...) -> ProviderResponse
    def stream(messages, ...) -> AsyncIterator[str]
    def history(thread_id) -> list[dict]
    def attachments(file_path) -> Optional[dict]
    def models() -> list[str]
    def capabilities() -> list[str]
    def health() -> dict
```

Current adapters: **Gemini** (active). Claude, GPT, DeepSeek, Grok, Local (stubs — implement when needed).

---

## Knowledge Graph

Every note is a graph node. Relationships are typed and directional.

| Relationship | Meaning |
|-------------|---------|
| references | This note cites another |
| extends | This note builds on another |
| contradicts | This note disputes another |
| summarizes | This note compresses another |
| implements | This note operationalises another |
| belongs_to | This note is part of another |
| generated_by | Created by a specific process |
| reviewed_by | Validated by a specific node |
| derived_from | Derived from a source note |

**Graph traversal:** `GET /api/knowledge/graph/{note_id}/traverse?depth=2`  
**Full export (for Prism):** `GET /api/knowledge/graph`  
**Path finding:** `GET /api/knowledge/graph/{note_id}/path/{target_id}`

---

## Timeline Engine

Every event is immutable. The timeline is append-only.

```
Conversation → Prompt → Response → Knowledge Created → Knowledge Modified
→ Review → Decision → Sync → Error → Pipeline Run → Embed Complete
→ Graph Link → Search Query → Provider Call
```

**Replay:** `GET /api/knowledge/timeline/replay/{project_id}`  
**Query:** `GET /api/knowledge/timeline`

---

## Search Engine

Six search modes, all accessible via `POST /api/knowledge/search`:

| Mode | How It Works |
|------|-------------|
| semantic | Embedding cosine similarity (BM25 fallback) |
| fulltext | SQLite LIKE across title + content |
| tag | Exact tag match via note_tags junction |
| timeline | Event log search with date filtering |
| project | Project name + description search |
| people | Person notes search |
| reference | External URL and citation search |

---

## SQLite Schema Summary

**Tables:** notes, chunks, projects, threads, embeddings, tags, note_tags, graph_edges, timeline, references, attachments, providers, personas  
**Schema:** `knowledge/schema.sql`  
**DB path:** `knowledge/arkadia.db` (configurable via `ARKADIA_DB_PATH`)

---

## Persona System

Personas belong to Arkadia, not providers. Any provider can assume any persona.

| Persona | Role |
|---------|------|
| Architect | Systems thinking, structural design |
| Reviewer | Critical reading, gap detection |
| Editor | Clarity, compression, precision |
| Researcher | Source tracing, signal/noise |
| Critic | Steel-manning, challenge |
| Teacher | Pedagogy, bridge-building |
| Planner | Decomposition, dependency mapping |
| Summarizer | Compression without distortion |

**API:** `GET /api/knowledge/personas`  
**Use in send:** `POST /api/knowledge/providers/send` with `"persona": "Architect"`

---

## API Surface

```
# Knowledge Pipeline
POST /api/knowledge/ingest
POST /api/knowledge/ingest/conversation

# Notes
GET  /api/knowledge/notes
GET  /api/knowledge/notes/{uuid}

# Search
POST /api/knowledge/search
GET  /api/knowledge/search/semantic
GET  /api/knowledge/search/fulltext

# Context
POST /api/knowledge/context

# Knowledge Graph
GET  /api/knowledge/graph
GET  /api/knowledge/graph/{note_id}/traverse
GET  /api/knowledge/graph/{note_id}/path/{target_id}
POST /api/knowledge/graph/edge

# Timeline
GET  /api/knowledge/timeline
GET  /api/knowledge/timeline/recent
GET  /api/knowledge/timeline/replay/{project_id}

# Projects
GET  /api/knowledge/projects
POST /api/knowledge/projects
GET  /api/knowledge/projects/{name_or_uuid}

# Providers
GET  /api/knowledge/providers
GET  /api/knowledge/providers/health
POST /api/knowledge/providers/send

# Personas
GET  /api/knowledge/personas
GET  /api/knowledge/personas/{name}

# Status
GET  /api/knowledge/status
```

---

## Migration

Run once to port existing data into the Knowledge OS:

```bash
python -m knowledge.migrate
```

Migrates:
1. `data/oracle_store.json` → SQLite timeline events
2. `data/personal_codices/*.json` → People notes in vault

---

## Synchronisation Priority

```
Markdown (vault/)
     ↓
SQLite (knowledge/arkadia.db)
     ↓
Knowledge Graph
     ↓
Firebase (additive sync)
     ↓
Git (version history)
```

Never reverse this order. Markdown is the source of truth.

---

## Android Architecture

Target: Flutter, offline-first, shared architecture with web.

**Recommended stack:**
- Flutter + Dart
- SQLite via `sqflite` package (same schema as knowledge/arkadia.db)
- HTTP client to Oracle Temple (`/api/knowledge/*`)
- Local vault sync via file system + background HTTP sync
- Firebase for auth + cloud sync

**Architecture pattern:**
```
Flutter UI
     ↓
Local SQLite (offline-first)
     ↓ (sync when online)
Oracle Temple API (/api/knowledge/*)
     ↓
Knowledge Vault (server-side)
```

**Priority:** Local SQLite writes always succeed. Server sync is additive.

See `sonata-android/` for the existing Android project (Sonata music player).
Knowledge OS Android client to be built as a separate artifact.

---

## Implementation Roadmap

### Phase 1: Foundation (Complete ✓)
- [x] Knowledge Vault (`vault/`)
- [x] SQLite schema (`knowledge/schema.sql`)
- [x] Database layer (`knowledge/db.py`)
- [x] Note CRUD + Markdown write (`knowledge/vault.py`)
- [x] Knowledge Pipeline (`knowledge/pipeline.py`)
- [x] Embeddings layer (`knowledge/embeddings.py`)
- [x] Knowledge Graph (`knowledge/graph.py`)
- [x] Context Engine (`knowledge/context_engine.py`)
- [x] Search Engine (`knowledge/search.py`)
- [x] Timeline Engine (`knowledge/timeline.py`)
- [x] Provider Base Interface (`providers/base.py`)
- [x] Gemini Provider Adapter (`providers/gemini.py`)
- [x] Provider Router (`providers/router.py`)
- [x] Knowledge API Routes (`api/knowledge_routes.py`)
- [x] Oracle upgrade (kernel/memory.py uses semantic retrieval)
- [x] Migration script (`knowledge/migrate.py`)
- [x] ADR-010, ADR-011, ADR-012

### Phase 2: Prism Visualization (Next)
- [ ] Knowledge Graph view (D3.js force graph in React)
- [ ] Timeline view (chronological event replay)
- [ ] Project dashboard (notes, graph, activity)
- [ ] Semantic search UI

### Phase 3: Provider Adapters
- [ ] Claude adapter (`providers/claude.py`)
- [ ] GPT adapter (`providers/gpt.py`)
- [ ] DeepSeek adapter (`providers/deepseek.py`)
- [ ] Grok adapter (`providers/grok.py`)
- [ ] Local LLM adapter (`providers/local.py` — Ollama)

### Phase 4: Android Client
- [ ] Flutter project scaffold
- [ ] Local SQLite with shared schema
- [ ] Offline-first sync
- [ ] Knowledge OS API integration

### Phase 5: Advanced Intelligence
- [ ] Automatic conflict detection between notes
- [ ] Duplicate detection across semantic similarity
- [ ] Knowledge integrity audit
- [ ] Daily review generator
- [ ] Project summary generator
- [ ] Relationship strength scoring (weighted graph)

---

## File Index

```
knowledge/
├── __init__.py          # Package marker
├── db.py                # SQLite connection manager
├── schema.sql           # Canonical schema (13 tables)
├── vault.py             # Note CRUD + Markdown I/O
├── pipeline.py          # Knowledge pipeline (ingest entry point)
├── embeddings.py        # Gemini embed + BM25 fallback + cosine similarity
├── graph.py             # Knowledge graph (traversal, path finding, auto-link)
├── context_engine.py    # Context assembly for providers
├── search.py            # 7 search modes + unified search
├── timeline.py          # Immutable event log
└── migrate.py           # One-time data migration

providers/
├── __init__.py          # Package marker
├── base.py              # BaseProvider interface (all adapters must implement)
├── gemini.py            # Gemini adapter (active)
└── router.py            # Provider selection + high-level send()

vault/
├── Projects/            # Project-scoped notes
├── Books/               # Book notes
├── People/              # Person profiles
├── Ideas/               # Ideas and concepts
├── Daily/               # Daily notes
├── Research/            # Research and citations
├── Attachments/         # Binary assets
├── Templates/           # Note templates
├── Archive/             # Soft-deleted notes
└── Index/               # Auto-generated indexes

docs/adr/
├── ADR-010-knowledge-vault.md     # Vault as canonical truth store
├── ADR-011-provider-router.md     # Providers as replaceable adapters
└── ADR-012-context-engine.md      # Semantic retrieval over memory dump

api/
└── knowledge_routes.py  # /api/knowledge/* HTTP routes (thin skin)
```
