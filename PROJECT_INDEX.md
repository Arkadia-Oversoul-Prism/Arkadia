# Arkadia — Project Index
> A map of the repository. The agent reads this instead of exploring the tree.
> Update when a new module is added. Never let it drift from the codebase.

---

## Security / Identity
```
api/auth.py              Firebase Admin SDK; dev-mode fallback; fail-fast (ADR-013)
api/nodes.py             Node registry routes + identity (Layer 3 — Identity)
api/user_key_store.py    Per-user API key management (Layer 3 — Identity)
api/firebase_store.py    Firestore sync adapter (Layer 3 — Identity)
data/nodes_seed.json     Node definitions (role, access_level, email_hint)
data/personal_codices/   Per-node private context JSON
firestore.rules          Firestore security rules
```

## API Surface
```
api/main.py              FastAPI app — 2506 lines — DO NOT GROW (budget: 2600)
api/key_manager.py       Gemini API key rotation
api/provider_key_store.py  Per-provider key store
api/knowledge_routes.py  Knowledge OS routes
api/ims_products.py      IMS product routes
api/arkadia_engine.py    Legacy symbolic engine (verse generation)
api/tts_key_manager.py   TTS key management
```

## Runtime Core (kernel/)
```
kernel/execution.py      Orchestration entry point — DO NOT import api/
kernel/planner.py        LLM planning (Gemini) + chain execution
kernel/worker.py         Daemon worker pool + goal scheduler
kernel/jobs.py           JobStore — IN-MEMORY (target: SQLiteJobStore in B1)
kernel/goals.py          GoalStore — IN-MEMORY (target: SQLiteGoalStore in B1)
kernel/tools.py          BaseTool, TOOL_REGISTRY
kernel/tools_real.py     ExecuteShellTool, ReadFileTool, WriteFileTool, etc.
kernel/intent_types.py   ALLOWED_TYPES frozenset (target: plugin registry in E)
kernel/agents.py         Thin execution wrappers (has layer violation — Workstream A)
kernel/metrics.py        In-process counters (p50/p95 per tool)
kernel/memory.py         Context retrieval (Knowledge Vault → oracle_store fallback)
kernel/oracle_store.py   JSON store: transactions, open loops, assets, events
kernel/tts.py            TTS subsystem (has layer violation → api.tts_key_manager)
```

## Runtime Storage (B1 target)
```
kernel/storage/          CREATED IN B1.1 — SQLite schema + stores
  __init__.py
  schema.py              DDL + create_tables()  ← B1.1
  sqlite_job_store.py    SQLiteJobStore         ← B1.2
  sqlite_goal_store.py   SQLiteGoalStore        ← B1.2
data/runtime.db          CREATED IN B1.1 — jobs, goals, corpus sync state
data/jobs.json           Legacy — preserved read-only through B1 (rollback path)
data/goals.json          Legacy — preserved read-only through B1 (rollback path)
```

## Knowledge Layer
```
knowledge/pipeline.py        ingest() — canonical entry point
knowledge/context_engine.py  Semantic retrieval for providers
knowledge/graph.py           Note relationships + traversal
knowledge/search.py          7 search modes
knowledge/timeline.py        Immutable event log
knowledge/embeddings.py      Gemini embed + BM25 fallback
knowledge/arkadia.db         SQLite machine-readable index (SEPARATE from runtime.db)
vault/                       Markdown notes (canonical human format)
github_corpus.py             Corpus sync (incremental version: Workstream C)
```

## Providers
```
providers/router.py      ProviderRouter — selects provider by capability
providers/gemini.py      GeminiProvider (primary)
providers/claude.py      ClaudeProvider
providers/deepseek.py    DeepSeekProvider
providers/gpt.py         GPTProvider
```

## Presentation
```
web/public_prism/        React/Vite SPA — npm run dev on port 5173
  src/components/        UI components
  src/views/             Page views
  src/contexts/          React contexts (voice, oracle, auth)
bot/discord-bot.mjs      Discord bot — needs DISCORD_BOT_TOKEN
bot/telegram-bot.mjs     Telegram bot — needs TELEGRAM_BOT_TOKEN
arkadia-android/         Android shell (WebView-based)
sonata-android/          Android companion app
solspire/                Alternative execution frontend
```

## Governance
```
BOOTSTRAP.md             Agent startup — read first, every session
CURRENT_STATE.md         Live session state — read second, every session
ACTIVE_CONTEXT.md        Session scratchpad — rewrite each session
NEXT_AGENT.md            Auto-generated handoff — copy-paste to next session
DECISION_CACHE.md        Why decisions were made — stops re-litigation
PROJECT_INDEX.md         This file
ENGINEERING_PRINCIPLES.md   11 principles — FROZEN (do not reread unless changed)
ROADMAP.md               Phase sequence — FROZEN (do not reread unless changed)
docs/phase1/CONTINUATION_LEDGER.md   Session history + debt registry
docs/phase1/PHASE_GATES.md           Exit criteria per gate
docs/phase1/ARCHITECTURE_MAP.md      Layer diagram — FROZEN (do not reread unless changed)
docs/adr/                ADR-010 through ADR-015 — FROZEN (do not reread unless changed)
tests/architecture/LAYER_MAP.py      Debt registry — DO NOT EDIT except to add/remove debt
tests/architecture/test_layer_boundaries.py   Fitness tests — DO NOT EDIT in Build mode
```

## Tests
```
tests/architecture/      Architecture fitness tests — 10/10 must pass at all times
tests/                   Unit tests — add alongside each new module
```

## Configuration
```
replit.md                Project overview + user preferences
.replit                  Replit workflow configuration
requirements.txt         Python dependencies
web/public_prism/package.json   Frontend dependencies
```
