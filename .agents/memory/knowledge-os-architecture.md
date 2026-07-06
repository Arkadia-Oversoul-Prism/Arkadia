---
name: Arkadia Knowledge OS Architecture
description: Core architectural decisions, module map, and laws for the Knowledge OS built in GENESIS_V1
---

# Arkadia Knowledge OS — Architecture Memory

## Architectural Laws (immutable)
1. One capability. One implementation. One canonical home.
2. Local First. Cloud sync is additive. Never required.
3. Markdown is the human format. SQLite is the machine format.
4. Oracle retrieves knowledge. Providers generate language.
5. Every subsystem must have a single responsibility.

## Module Map
- `knowledge/db.py` — per-thread SQLite connections (threading.local()), schema auto-apply
- `knowledge/vault.py` — note CRUD, Markdown ↔ SQLite sync, delegates to graph.add_edge
- `knowledge/pipeline.py` — `ingest()` and `ingest_conversation()` — main entry points
- `knowledge/embeddings.py` — Gemini text-embedding-004 + BM25 fallback, cosine similarity
- `knowledge/graph.py` — add_edge (INSERT OR REPLACE), traverse (BFS), find_path, full_graph_export
- `knowledge/context_engine.py` — semantic retrieval, thread_id filtering, ~3000-token budget
- `knowledge/search.py` — 8 modes: semantic, fulltext, tag, timeline, graph, project, people, reference
- `knowledge/timeline.py` — immutable append-only event log (never UPDATE/DELETE rows)
- `knowledge/migrate.py` — one-time: oracle_store.json → timeline, personal_codices → People notes
- `providers/base.py` — BaseProvider ABC (authenticate, send, stream, history, attachments, models, capabilities, health)
- `providers/gemini.py` — Gemini adapter, key resolved per-call via key_manager rotation
- `providers/router.py` — select_provider(), high-level send() with persona resolution

## Critical Rules
- **graph edges**: always use `knowledge/graph.add_edge()` — vault.add_graph_edge() delegates to it. Never write to graph_edges directly.
- **db thread safety**: each OS thread gets its own SQLite connection via threading.local(). Do not share connections across threads.
- **timeline immutability**: append-only. No UPDATE or DELETE on timeline rows. Ever.
- **provider key resolution**: GeminiProvider resolves key per-call (not cached) to support key_manager rotation.
- **vault.py → graph.py**: vault delegates to graph, not the reverse. No circular imports.

**Why:**
The Genesis Protocol mandates that if every AI provider disappeared, the vault remains intact. Markdown + SQLite is the knowledge floor. Providers are stateless reasoning adapters above it.

## API surface
All routes at `/api/knowledge/*` — see `api/knowledge_routes.py`. Thin HTTP skin only.
Key entry: `POST /api/knowledge/providers/send` — assembles context + routes to provider + ingests response.

## SQLite Schema
DB at `knowledge/arkadia.db` (configurable: ARKADIA_DB_PATH env var).
13 tables: notes, chunks, projects, threads, embeddings, tags, note_tags, graph_edges, timeline, references, attachments, providers, personas.
Schema: `knowledge/schema.sql`. Seeded with 6 providers + 8 personas.

## ADRs written
- ADR-010: Knowledge Vault as canonical truth store
- ADR-011: Provider Router — AI providers as replaceable adapters
- ADR-012: Context Engine — semantic retrieval over memory dump

## Phase 2 — Prism Frontend (complete)
- `web/public_prism/src/lib/knowledgeApi.ts` — typed API client for /api/knowledge/*
- `web/public_prism/src/pages/knowledge/KnowledgeGraphView.tsx` — D3 force graph (cleanup on unmount, ResizeObserver)
- `web/public_prism/src/pages/knowledge/TimelineView.tsx` — Recharts AreaChart + event stream, epoch-sorted buckets
- `web/public_prism/src/pages/knowledge/SemanticSearchView.tsx` — 7-mode search UI
- `web/public_prism/src/pages/knowledge/ProjectsView.tsx` — vault stats, providers, personas, projects
- `web/public_prism/src/pages/knowledge/KnowledgeOSPage.tsx` — tab container
- Added `'knowledge-os'` to View type in App.tsx and ArkadiaNavigation.tsx
- Nav item: Intelligence group → "Prism — Knowledge OS" (sigil ◈, color #00D4AA)
- d3 installed in web/public_prism/package.json (required — do not remove)

## Phase 3 — Provider Adapters (complete)
- `providers/claude.py` — Anthropic Claude; system messages filtered from messages[], merged into system= param
- `providers/gpt.py` — OpenAI GPT via official SDK
- `providers/deepseek.py` — DeepSeek via OpenAI-compat API (DEEPSEEK_BASE_URL)
- `providers/local.py` — Ollama local LLM (httpx, fully offline, LAW II)
- `providers/router.py` — all 5 providers registered by priority: gemini→claude→gpt→deepseek→local

## Phase 4 — Android Client
- Not yet built. Target: Flutter + sqflite (shared schema), offline-first, sync to /api/knowledge/*
