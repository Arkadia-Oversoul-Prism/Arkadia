# Arkadia — Repository Snapshot
> Regenerate only after major milestones or architectural changes.
> Last generated: Phase 1, B0.5 complete (2026-07-25).
> The agent reads this instead of crawling the repository tree.

---

## What Arkadia Is

A local-first Knowledge OS. Not a chatbot. A personal intelligence substrate that:
- Orchestrates AI reasoning over a structured knowledge vault
- Persists goals, jobs, conversations, and research across sessions
- Exposes multiple views (web SPA, Discord bot, Telegram bot, Android) over a single knowledge graph
- Routes reasoning across LLM providers (Gemini primary, Claude/GPT/DeepSeek fallback)

Vision: *conversations become structure; structure becomes retrieval; retrieval becomes intelligence.*

---

## Architecture Overview

```
Layer 0 — Infrastructure
  data/            SQLite databases, JSON snapshots, seed files
  vault/           Markdown notes (canonical human format)

Layer 1 — Kernel (most stable — never imports api/)
  kernel/          Orchestration, planning, workers, job/goal stores, tools, memory

Layer 2 — Knowledge (orthogonal to kernel — peer layer)
  knowledge/       Pipeline, graph, context engine, embeddings, timeline, search

Layer 3 — Providers + Identity (orthogonal — peer layers)
  providers/       GeminiProvider, ClaudeProvider, GPTProvider, DeepSeekProvider
  api/nodes.py     Node registry (identity)
  api/user_key_store.py, api/firebase_store.py

Layer 4 — API (least stable — orchestrates everything)
  api/main.py      FastAPI app (~2506 lines; budget: 2600)

Layer 5 — Presentation (views)
  web/public_prism/    React/Vite SPA
  bot/                 Discord + Telegram bots
  arkadia-android/     Android WebView shell
  sonata-android/      Android companion
  solspire/            Alternative frontend
```

**Dependency rule:** dependencies point from Layer 4 → Layer 1. Reverse is a violation.

---

## Module Map

### Security / Identity
| File | Purpose |
|---|---|
| `api/auth.py` | Firebase Admin SDK; dev-mode fallback; fail-fast (ADR-013) |
| `api/nodes.py` | Node registry routes + identity |
| `api/user_key_store.py` | Per-user API key management |
| `api/firebase_store.py` | Firestore sync adapter |
| `data/nodes_seed.json` | Node definitions (role, access_level, email_hint) |
| `firestore.rules` | Firestore security rules |

### API Surface
| File | Purpose |
|---|---|
| `api/main.py` | FastAPI app — **2506 lines — DO NOT GROW past 2600** |
| `api/key_manager.py` | Gemini API key rotation |
| `api/provider_key_store.py` | Per-provider key store |
| `api/knowledge_routes.py` | Knowledge OS routes |
| `api/tts_key_manager.py` | TTS key management |
| `api/arkadia_engine.py` | Legacy symbolic engine (verse generation) |

### Runtime Core
| File | Purpose |
|---|---|
| `kernel/execution.py` | Orchestration entry point — **DO NOT import api/** |
| `kernel/planner.py` | LLM planning (Gemini) + chain execution |
| `kernel/worker.py` | Daemon worker pool + goal scheduler |
| `kernel/jobs.py` | JobStore — **in-memory** (B1.2 target: SQLiteJobStore) |
| `kernel/goals.py` | GoalStore — **in-memory** (B1.2 target: SQLiteGoalStore) |
| `kernel/tools.py` | BaseTool, TOOL_REGISTRY |
| `kernel/tools_real.py` | ExecuteShellTool, ReadFileTool, WriteFileTool, etc. |
| `kernel/intent_types.py` | ALLOWED_TYPES frozenset (Workstream E target) |
| `kernel/agents.py` | Thin execution wrappers (layer violation — Workstream A) |
| `kernel/metrics.py` | In-process counters (p50/p95 per tool) |
| `kernel/memory.py` | Context retrieval (Knowledge Vault → oracle_store fallback) |
| `kernel/oracle_store.py` | JSON store: transactions, open loops, assets, events |
| `kernel/tts.py` | TTS subsystem (layer violation → api.tts_key_manager — Workstream A) |

### Runtime Storage (B1 target — does not exist yet)
| File | Purpose |
|---|---|
| `kernel/storage/__init__.py` | Package init — **created in B1.1** |
| `kernel/storage/schema.py` | DDL + `create_tables()` — **created in B1.1** |
| `kernel/storage/sqlite_job_store.py` | SQLiteJobStore — **created in B1.2** |
| `kernel/storage/sqlite_goal_store.py` | SQLiteGoalStore — **created in B1.2** |
| `data/runtime.db` | SQLite runtime database — **created on first run in B1.1** |
| `data/jobs.json` | Legacy in-memory snapshot — preserved read-only through B1 |
| `data/goals.json` | Legacy in-memory snapshot — preserved read-only through B1 |

### Knowledge Layer
| File | Purpose |
|---|---|
| `knowledge/pipeline.py` | `ingest()` — canonical entry point |
| `knowledge/context_engine.py` | Semantic retrieval for providers |
| `knowledge/graph.py` | Note relationships + traversal |
| `knowledge/search.py` | 7 search modes |
| `knowledge/timeline.py` | Immutable event log |
| `knowledge/embeddings.py` | Gemini embed + BM25 fallback |
| `knowledge/arkadia.db` | SQLite machine-readable index (**separate from runtime.db**) |
| `vault/` | Markdown notes (canonical human format) |
| `github_corpus.py` | Corpus sync (Workstream C target: incremental) |

### Providers
| File | Purpose |
|---|---|
| `providers/router.py` | ProviderRouter — selects by capability (**orthogonal cross-dep violation — Workstream A**) |
| `providers/gemini.py` | GeminiProvider (primary) |
| `providers/claude.py` | ClaudeProvider |
| `providers/deepseek.py` | DeepSeekProvider |
| `providers/gpt.py` | GPTProvider |

---

## Phase & Workstream Status

### Phase 1 — Runtime Stabilization

| Workstream | Name | Status |
|---|---|---|
| **B** | Durable Persistence | 🔄 In progress — B1.1 ready |
| C | Corpus Sync (incremental) | ⬜ Not started |
| D | Observability | ⬜ Not started |
| E | Plugin Registry | ⬜ Not started |
| A | Layer Violation Remediation | ⬜ Not started — depends on E |

### B1 Checkpoints
| Checkpoint | Status |
|---|---|
| B1.1 — SQLite Schema | ✅ Ready to begin |
| B1.2 — SQLiteJobStore + SQLiteGoalStore | ⬜ After B1.1 |
| B1.3 — Worker Integration | ⬜ After B1.2 |
| B1.4 — Cleanup / Gate B close | ⬜ After B1.3 |

---

## Architectural Debt (13 registered entries)

All entries in `tests/architecture/LAYER_MAP.py`. All assigned Workstream A, Gate E exit criterion.

### Layer Inversions (10)
| Importer | Imported module | Workstream |
|---|---|---|
| kernel/agents.py | api (multiple) | A |
| kernel/tts.py | api.tts_key_manager | A |
| kernel/planner.py | api (multiple) | A |
| kernel/execution.py | api (multiple) | A |
| providers/router.py | knowledge.db | A |

*(See LAYER_MAP.py for exact module paths and exit criteria)*

### Circular Imports (3)
| Cycle | Workstream |
|---|---|
| kernel.execution ↔ kernel.planner | A |
| kernel.execution ↔ kernel.tools | A |
| kernel.planner ↔ kernel.tools | A |

**Do not fix any of these in B1.** They are registered and scheduled.

---

## ADR Status

| ADR | Title | Status |
|---|---|---|
| ADR-013 | Authentication & Security Hardening | ✅ Accepted |
| ADR-014 | Phase 1 Runtime Stabilization | ✅ Accepted |
| ADR-015 | Layer Boundary Enforcement | ✅ Accepted |

All ADRs frozen. See `02_DECISIONS.md` for the decisions extracted from them.

---

## Fitness Tests

```bash
pytest tests/architecture/ -v    # must be 10/10 at all times
```

Tests:
1. `test_no_layer_inversions` — no unregistered layer inversions
2. `test_no_orthogonal_cross_dependencies` — orthogonal subsystems isolated
3. `test_registered_debt_is_documented` — every debt entry has a reason
4. `test_registered_debt_references_remediation` — every debt entry has a timeline
5. `test_kernel_does_not_import_api_directly` — fast-path guard
6. `test_providers_do_not_import_kernel` — provider leaf adapter rule
7. `test_knowledge_does_not_import_api` — knowledge layer isolation
8. `test_no_circular_imports_in_kernel` — unregistered cycles blocked
9. `test_api_main_line_count_within_budget` — api/main.py ≤ 2600 lines
10. `test_intent_types_allowed_types_is_not_a_frozenset` — plugin registry readiness

---

## Runtime Dependencies

```
Python:  see requirements.txt (FastAPI, uvicorn, google-generativeai, edge-tts, ...)
Node.js: web/public_prism/package.json (React, Vite, Tailwind v3)
```

**Secrets required to run** (all missing — pre-existing, not a B1 concern):
- `GEMINI_API_KEY` — LLM provider
- `SOVEREIGN_KEY` — authentication gate
- `SESSION_SECRET` — session signing (present)
- `DISCORD_BOT_TOKEN` — Discord bot
- `TELEGRAM_BOT_TOKEN` — Telegram bot

---

## Governance Files

| File | Read when |
|---|---|
| `.bootstrap/00_BOOT.md` | Session start — always |
| `.bootstrap/01_STATE.md` | Session start — always |
| `.bootstrap/02_DECISIONS.md` | Before asking "why was X decided?" |
| `.bootstrap/03_SCOPE.md` | Before touching any file |
| `.bootstrap/04_SUCCESS.md` | Before declaring session done |
| `NEXT_AGENT.md` | Copy-paste to start the next session |
| `PARKING_LOT.md` | When noticing issues outside scope |
| `REPOSITORY_SNAPSHOT.md` | This file — replaces tree exploration |
| `docs/phase1/CONTINUATION_LEDGER.md` | End of session only — to update it |
| `docs/phase1/PHASE_GATES.md` | When closing a gate |
