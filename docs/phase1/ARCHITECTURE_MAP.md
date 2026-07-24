# Arkadia — Architecture Map

**Version:** 1.0 (Phase 1)  
**Date:** ARK Y1 · D116 (2026-07-24)  
**Status:** Canonical mental model. Update this document whenever a new layer, subsystem, or interface is added. Never let it drift from the codebase.

---

## System Map

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                              A R K A D I A                                  ║
║                     Sovereign Intelligence Architecture                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
  ┌───────────────┐        ┌─────────────────┐        ┌─────────────────┐
  │ CONSTITUTION  │        │  RUNTIME CORE   │        │  PRESENTATION   │
  │               │        │                 │        │                 │
  │ ADRs          │        │ Execution Kernel│        │ Public Prism    │
  │ Arch Laws     │        │ Job Runtime     │        │  (React/Vite)   │
  │ Governance    │        │ Goal Scheduler  │        │ Discord Bot     │
  │ Continuation  │        │ Worker Pool     │        │ Telegram Bot    │
  │   Ledger      │        │ Plugin Registry │        │ Android App     │
  │ Phase Gates   │        │ Observability   │        │ SolSpire        │
  └───────────────┘        └────────┬────────┘        └────────┬────────┘
                                    │                           │
                                    │ governs                   │ consumes
                                    ▼                           ▼
          ┌──────────────────────────────────────────────────────────┐
          │                       API SURFACE                        │
          │                                                          │
          │           Oracle Temple — FastAPI (api/main.py)          │
          │                                                          │
          │  /api/oracle      /api/job/*     /api/knowledge/*        │
          │  /api/sync        /api/goals     /api/nodes              │
          │  /api/forge       /api/spawn     /api/metrics            │
          └───────────────────────────┬──────────────────────────────┘
                                      │
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
               ▼                      ▼                      ▼
  ┌────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐
  │   KNOWLEDGE LAYER  │  │   IDENTITY LAYER     │  │  PROVIDER LAYER   │
  │                    │  │                      │  │                   │
  │ Knowledge Vault    │  │ Firebase Auth        │  │ Provider Router   │
  │  (Markdown)        │  │ Node Registry        │  │ Gemini Adapter    │
  │ SQLite Index       │  │ Sovereign Gate       │  │ (GPT — future)    │
  │ Pipeline / Ingest  │  │ Session Management   │  │ (Claude — future) │
  │ Embeddings (Gemini)│  │ Personal Codex       │  │ (Grok — future)   │
  │ Knowledge Graph    │  │                      │  │                   │
  │ Semantic Search    │  │                      │  │ Key Manager       │
  │ Context Engine     │  │                      │  │                   │
  │ Timeline           │  │                      │  │                   │
  └────────────────────┘  └──────────────────────┘  └───────────────────┘
               │                      │                      │
               └──────────────────────┴──────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │   STORAGE SUBSTRATE    │
                         │                        │
                         │ data/runtime.db        │
                         │  (jobs, goals,         │
                         │   corpus sync state)   │
                         │                        │
                         │ knowledge/arkadia.db   │
                         │  (notes, embeddings,   │
                         │   graph, timeline)     │
                         │                        │
                         │ vault/ (Markdown)      │
                         │  canonical human fmt   │
                         │                        │
                         │ data/*.json (legacy)   │
                         │  → migrating to SQLite │
                         └────────────────────────┘
```

---

## Layer Definitions

### Constitution
Everything that governs how the system is built, not what it does.
- ADRs (`docs/adr/`) — immutable decision records
- Architectural laws (`replit.md`) — the five principles
- Phase gate criteria (`docs/phase1/PHASE_GATES.md`)
- Continuation Ledger (every session)

**Stability:** Highest. Changes here require Principal Engineer + Flamekeeper approval.

---

### Runtime Core
The execution heart of Arkadia. Receives intents, plans steps, executes tools, persists results.

```
kernel/
  execution.py    — orchestration entry point
  planner.py      — LLM planning (Gemini) + chain execution
  worker.py       — daemon worker pool + goal scheduler
  jobs.py         — JobStore (→ SQLite in Phase 1)
  goals.py        — GoalStore (→ SQLite in Phase 1)
  tools.py        — BaseTool, TOOL_REGISTRY
  tools_real.py   — ExecuteShellTool, ReadFileTool, WriteFileTool, ListDirectoryTool, GenerateImageTool
  plugin_registry.py  — (Phase 1 target) PluginManifest, route by handles-set
  observability.py    — (Phase 1 target) StructuredLogger, context vars
  metrics.py      — in-process counters (p50/p95 per tool)
  memory.py       — context retrieval (Knowledge Vault → oracle_store fallback)
  oracle_store.py — JSON store: transactions, open loops, assets, events
  intent_types.py — ALLOWED_TYPES (→ plugin registry in Phase 1)
  agents.py       — thin execution wrappers (layer violation to fix in Phase 1)
```

**Stability:** High. Interface contracts are frozen. Internal implementations are the Phase 1 target.

**Dependency rule:** Runtime Core depends on Knowledge Layer and Provider Layer. It must never depend on API Surface or Presentation. (ADR-015)

---

### API Surface
The translation layer between external callers and the Runtime Core. Owns HTTP concerns: auth, CORS, routing, rate limiting, request/response shaping.

```
api/
  main.py           — FastAPI application (2506 lines — decomposition is Phase 2)
  auth.py           — Firebase token verification, dev-mode fallback
  nodes.py          — Node registry routes
  knowledge_routes.py — Knowledge OS API
  firebase_store.py — Firestore sync adapter
  key_manager.py    — Gemini API key rotation
  arkadia_engine.py — Legacy symbolic engine (verse generation, etc.)
```

**Stability:** Medium. Routes are stable; internal decomposition is Phase 2.

**Dependency rule:** API Surface depends on Runtime Core and Knowledge Layer. It must never depend on Presentation. (ADR-015)

---

### Knowledge Layer
The primary asset of Arkadia. AI providers are replaceable; accumulated knowledge is not.

```
vault/              — Markdown notes (canonical human format)
knowledge/
  pipeline.py       — ingest() — the canonical entry point
  context_engine.py — semantic retrieval for providers
  graph.py          — note relationships + traversal
  search.py         — 7 search modes (semantic, fulltext, tag, ...)
  timeline.py       — immutable event log
  embeddings.py     — Gemini embed + BM25 fallback
  arkadia.db        — SQLite machine-readable index
github_corpus.py    — corpus sync (→ incremental in Phase 1)
```

**Stability:** High. Interfaces are fixed. Implementations (embedding strategy, search modes) can evolve.

**Dependency rule:** Knowledge Layer must expose interfaces only to callers above it. It must not depend on Runtime Core, API Surface, or Presentation. (ADR-015)

---

### Identity Layer
Authentication, authorization, and node identity. Who is allowed to do what.

```
api/
  auth.py           — Firebase Admin SDK, dev-mode fallback, fail-fast (Phase 0)
  nodes.py          — Node registry (node_key, access_level, role)
  user_key_store.py — Per-user API key management
data/
  nodes_seed.json   — Node definitions (role, access_level, email_hint)
  personal_codices/ — Per-node private context JSON
firestore.rules     — Firestore security rules
```

**Stability:** High. Auth contract (fail-fast, sovereign gate) is constitutional (ADR-013).

**Dependency rule:** Identity Layer depends on no other Arkadia layer. It is the leaf — everything else depends on it. (ADR-015)

---

### Provider Layer
AI providers are interchangeable reasoning adapters. The knowledge is the asset; providers generate language.

```
providers/
  router.py    — ProviderRouter: selects provider by capability
  gemini.py    — GeminiProvider: implements BaseProvider
  (future)     — ClaudeProvider, GPTProvider, GrokProvider
```

**Stability:** High at the interface (`BaseProvider`). Low at implementations (provider APIs change constantly).

**Dependency rule:** Provider Layer must not depend on Runtime Core or Knowledge Layer. It must be a pure adapter — input text in, output text out. (ADR-015)

---

### Presentation Layer
Everything the user sees and interacts with. Consumes the API Surface; produces no server-side state directly.

```
web/public_prism/   — React/Vite SPA (Arkadia Prism)
  src/
    components/     — UI components
    views/          — Page views
    contexts/       — React context (voice, oracle, auth)
bot/
  discord-bot.mjs   — Discord integration
  telegram-bot.mjs  — Telegram integration
arkadia-android/    — Android shell (WebView-based)
sonata-android/     — Android companion app
solspire/           — Alternative execution frontend
```

**Stability:** Low — UI evolves fastest. Must be decoupled from knowledge and execution concerns.

**Dependency rule:** Presentation depends on API Surface only. It must never directly import or embed kernel or knowledge logic. (ADR-015)

---

### Storage Substrate
Where state lives. Two databases with distinct concerns.

| Database | Path | Contents | Format |
|---|---|---|---|
| Runtime DB | `data/runtime.db` | Jobs, goals, corpus sync state | SQLite WAL |
| Knowledge DB | `knowledge/arkadia.db` | Notes, embeddings, graph, timeline | SQLite |
| Vault | `vault/` | Canonical Markdown notes | Plain text |
| Legacy | `data/*.json` | oracle_store, old snapshots | JSON → migrating |
| Cloud mirror | Firestore | Job/goal mirror | Firestore |

---

## Dependency Direction (ADR-015)

```
Constitution        (most stable)
      │ ↓ depends on
Runtime Core
      │ ↓
API Surface
      │ ↓
Presentation        (least stable)

Orthogonal:
  Identity Layer   ← leaf; all other layers may depend on it
  Knowledge Layer  ← all layers above API Surface may read from it
  Provider Layer   ← Runtime Core and Knowledge Layer may call it
  Storage Substrate ← Runtime Core and Knowledge Layer write to it
```

**The rule:** Dependencies point downward only. A more stable layer never imports from a less stable layer. Violations are caught by architecture fitness tests (CI).

---

## What This Map Is Not

- It is not a deployment diagram (for that, see `CLOUD_ARCHITECTURE.md` and `DEPLOYMENT_GUIDE.md`)
- It is not a sequence diagram (for those, see `docs/phase1/RUNTIME_STATE_DIAGRAM.md` and `CORPUS_SYNC_DESIGN.md`)
- It is not a data model (for that, see `ARKADIA_KNOWLEDGE_OS.md` and the SQLite schemas)

It is the **canonical mental model**: where does each capability live, what layer owns it, and which direction may it depend.

---

## Future Layers (Read-Only — Do Not Implement in Phase 1)

Per the Knowledge OS Direction (Phase 1 brief — for evaluation only):

```
Oversoul Prism        ← living spine; future unification layer
NovaNet               ← universal operating environment
Canonical Domain      ← unified entity model: identity, relationships, provenance, history
  ├── Public projections:  Homepage, Encyclopedia, Nexus, Spiral Codex, Atlas
  └── Private projections: Mirror World, SolSpire, IMS Archive, VhixNovaCore, Oracle
```

**Nothing implemented in Phase 1 should make these harder to realise.**  
The plugin registry, SQLite storage substrate, and structured observability are all compatible with this future — they are the foundations it requires.
