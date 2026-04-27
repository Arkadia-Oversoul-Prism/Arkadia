# Arkadia — Living Intelligence Framework

## Overview
Arkadia is a sovereign human-AI distributed intelligence framework. ARKANA (Gemini-powered Oracle) serves Zahrune Nova's architecture through a React/Vite frontend and FastAPI backend.

## Architecture

### Backend — Arkadia Oracle Temple
- **Entry:** `api/main.py` — FastAPI app (Cycle 15+)
- **Identity:** ORACLE_IDENTITY constitutional layer injected into every Gemini call
- **Corpus:** Dynamic multi-source system — discovers documents automatically
- **Scoring:** TF-IDF semantic relevance (Neural Spine always injected; others scored per query)
- **History:** Conversation history + summarization + pattern extraction
- **Run:** `uvicorn api.main:app --host 0.0.0.0 --port 8000`

### Corpus Engine — `corpus/` module
- **`corpus/manager.py`** — Multi-source aggregator, parallel fetch, 6hr disk cache
- **`corpus/github.py`** — GitHub API dynamic scanner (no hardcoded doc list)
- **`corpus/gdrive.py`** — Google Drive source (configure with CORPUS_GDRIVE_* vars)
- **`corpus/joplin.py`** — Joplin Data REST API source
- **`corpus/obsidian.py`** — Obsidian Local REST API source
- **`github_corpus.py`** — Backward-compat shim, delegates to corpus module

### Frontend — Public Prism
- **Location:** `web/public_prism/`
- **Run:** `cd web/public_prism && npm run dev` (port 5000)
- **Framework:** React + Vite + TypeScript + Tailwind + Framer Motion
- **Pages:** Home, Gate (LivingGate), Oracle (ArkanaCommune), Reset (CoherenceReset), Vault (SpiralVault), Sanctuary

### Spiral Codex Live Console (`SpiralVault.tsx`)
The Vault page is the central living feed:
- Fetches `/api/codex` — all docs with label, description, category, source, preview
- Dynamic category tabs derived from actual data (not hardcoded)
- Source chips per card (GitHub, Drive, Joplin, Obsidian with branded colors)
- ARKANA heartbeat beacon + sources status row
- Re-sync button → POST `/api/corpus/refresh`
- Arc state progress bar (Feb 16 – Mar 31, 2026)
- Expand/collapse full scroll content per card

### SolSpire Phase 4 — Execution Kernel (`kernel/`)
Strict, deterministic closed-loop execution layer beneath Arkana. Wires into `/api/commune/resonance` (classify-first, fall through to Arkana on no match) and exposes direct endpoints. **Pipeline:** `classify_input → plan_task → execute_steps → verify → summary`. No LLM in the kernel itself.

- **`kernel/intent_types.py`** — strict 4-type contract: `generate_images | log_transaction | update_open_loops | generate_verse`
- **`kernel/oracle_store.py`** — JSON-file Mutation Layer (`data/oracle_store.json`), thread-safe, atomic writes, sections: `transactions / open_loops / assets / balance / events`
- **`kernel/agents.py`** — internal agent functions, all return `{status: ...}` envelopes for `verify()`
- **`kernel/execution.py`** — regex-based classifier (recognizes `$/₦/€/£`, currency words, image/loop/verse verbs), planner, executor, verifier, master `execute_intent(intent)`

### SolSpire Phase 5 — Async Job Orchestration (`kernel/jobs.py`, `kernel/worker.py`)
Wraps the Phase 4 kernel in a background worker pool. Decouples execution from response. Existing sync endpoints remain unchanged.

- **`kernel/jobs.py`** — thread-safe `JobStore` with FIFO `queue.Queue`, JSON snapshot at `data/job_store.json` (jobs survive soft restart, in-flight jobs re-enqueue), `MAX_RETRIES=3`
- **`kernel/worker.py`** — N daemon worker threads (default 2, configurable via `SOLSPIRE_WORKERS`), exponential backoff (0.5s → 1s → 2s) between retries, soft-failure detection (kernel `success=False` triggers retry)
- **Lifecycle:** workers start via FastAPI `on_event("startup")`, shut down on `on_event("shutdown")`
- **Bot integration:** opt-in via `TELEGRAM_ASYNC_JOBS=true` — kernel-classified messages go through `/api/job/create`, bot replies "Task received…" then polls until completion. Default off, sync behavior preserved

### SolSpire Phase 6 — Tool Registry + Dynamic Routing (`kernel/tools.py`)
Replaces the if/elif dispatch inside `execute_steps` with a pluggable tool catalog. Adding a new capability = subclass `BaseTool`, set `name`/`description`/`payload_schema`, implement `run(payload)`, call `register_tool()`. Zero edits to the kernel.

- **`BaseTool`** contract — `name`, `description`, `payload_schema`, `run(payload) -> envelope`. `manifest()` for introspection
- **`TOOL_REGISTRY`** — module-level dict, `register_tool / unregister_tool / get_tool / select_tool / list_tools`
- **Built-ins** (auto-registered on import) — `GenerateImagesTool`, `LogTransactionTool`, `UpdateOpenLoopsTool`, `GenerateVerseTool` — each wraps the existing `kernel.agents` functions, no behavior change
- **`execute_intent`** now dispatches via `select_tool(intent)` → `tool.run(payload)`; returns the same Phase 4 envelope shape with new `tool_used` field appended (Phase 5 worker + bot rendering unchanged)
- **Endpoints:** `GET /api/tools` (catalog), `POST /api/tools/{name}/run` (direct invocation, accepts `{payload: {...}}` or raw payload as body)
- **Bot commands:** `/tools` (list registered tools), `/run <name> {json}` (invoke directly with optional JSON payload)
- **Phase 7 hook:** `select_tool()` is the single seam where an LLM router will replace literal type-matching with reasoning-based selection

### Arkadia Symbolic Engine (`api/arkadia_engine.py`)
Deterministic, no-LLM stylistic generator running inside the same FastAPI service:
- `generate_verse()` — 4-line shaped output (invocation → symbolic movement → fracture → seal), passed through a 10-syllable cap (`pronouncing` lib + vowel-cluster fallback) and an optional 40% rhyme tag.
- `compress(text)` / `expand(text)` — small Arkadian lexicon lookup (`flame↔F3, spiral↔S9, codex↔C4, field↔FD6, archive↔A7`); pass-through for tokens not in the dict.
- Exposed two ways:
  1. **HTTP routes** — `POST /arkadia/generate`, `POST /arkadia/compress`, `POST /arkadia/expand`. Same Render service, no second deployment.
  2. **Chat commands** — `⟐ generate`, `⟐ compress <text>`, `⟐ expand <text>` parsed inside `/api/commune/resonance` and short-circuited before the Gemini call. Returns the standard Oracle response shape so the existing chat UI renders engine output without any frontend change.

## Key API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/heartbeat` | GET | Status beacon |
| `/api/commune/resonance` | POST | Oracle chat (with history) |
| `/api/codex` | GET | Full corpus — labels, descriptions, categories, source, content |
| `/api/corpus` | GET | Lightweight corpus metadata |
| `/api/corpus/refresh` | POST | Force re-sync from all sources (background) |
| `/api/sources` | GET | Which sources are configured |
| `/api/coherence-reset` | POST | Somatic reset protocol |
| `/arkadia/generate` | POST | Symbolic engine: 4-line shaped verse (deterministic, no LLM) |
| `/arkadia/compress` | POST | Symbolic engine: lexicon-based compression (`{text}` → `{compressed}`) |
| `/arkadia/expand` | POST | Symbolic engine: reverse compression (`{text}` → `{expanded}`) |

## Corpus Configuration
Sources activated by environment variables:

```
CORPUS_SOURCES=github,gdrive,joplin,obsidian  # comma-sep, only configured ones activate

# GitHub (default, public repo)
CORPUS_GITHUB_REPO=Arkadia-Oversoul-Prism/Arkadia
CORPUS_GITHUB_BRANCH=main
CORPUS_GITHUB_INCLUDE_DIRS=docs,creative,collective,governance
CORPUS_GITHUB_EXCLUDE_DIRS=.github,node_modules,bot,web,api
CORPUS_DIR_CATEGORIES=docs:NEURAL_SPINE,creative:CREATIVE_OS,collective:COLLECTIVE,governance:GOVERNANCE
CORPUS_GITHUB_EXTENSIONS=.md

# Google Drive
CORPUS_GDRIVE_FOLDER_ID=<folder_id>
CORPUS_GDRIVE_SERVICE_ACCOUNT=<service_account_json>

# Joplin
CORPUS_JOPLIN_TOKEN=<api_token>
CORPUS_JOPLIN_URL=http://localhost:41184

# Obsidian Local REST API
CORPUS_OBSIDIAN_TOKEN=<api_key>
CORPUS_OBSIDIAN_URL=http://127.0.0.1:27123
```

## Optional: corpus-manifest.json
Add to repo root to override labels/descriptions/categories for specific files:
```json
{
  "docs/DOC1_MASTER_WEIGHTS.md": {
    "label": "Master Weights",
    "description": "...",
    "category": "NEURAL_SPINE",
    "priority": 1
  }
}
```

## Deployment
- **Backend:** Render — `https://arkadia-n26k.onrender.com`
- **Frontend:** Vercel — `https://arkadia-prism.vercel.app`
- **Telegram Bot:** Railway (`bot/` directory)
- **Dev:** Replit (this environment)

## Secrets Required
| Secret | Used For |
|---|---|
| `GEMINI_API_KEY` | Oracle (Gemini) |
| `GITHUB_TOKEN` | Git push + private corpus repos |
| `VITE_FIREBASE_API_KEY` | Firebase auth |
| `VITE_FIREBASE_APP_ID` | Firebase auth |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase auth |
| `VITE_FIREBASE_PROJECT_ID` | Firebase auth |

### Phase 8 — Memory-Aware Planning, Goals, Observability
- **`kernel/memory.py`** — keyword-match retrieval over `data/oracle_store.json`; injected into planner as `context`
- **`kernel/goals.py`** — persistent long-running directives (`data/goals.json`); CRUD + scheduler enqueues due goals every 15s (env: `SOLSPIRE_GOAL_TICK_SECONDS`); safety floors: min cadence 30s, hourly cap 60
- **`kernel/metrics.py`** — sliding-window per-tool counters (success rate, p50/p95) + plan/goal counters
- **Worker:** spawns goal scheduler thread on startup; persists per-job execution `trace` (input, plan, plan_source, context, per-step timings/summaries)
- **API endpoints:** `GET/POST/PATCH/DELETE /api/goals`, `GET /api/job/{id}/trace`, `GET /api/metrics`

### Operational Dashboard — `web/public_prism/src/pages/dashboard/`
Mounted as a top-level View ("Dashboard") in the existing Arkadia navigation. Same gold/teal palette, same state-driven nav pattern (no URL routing).
- **`Dashboard.tsx`** — sidebar shell + sub-page state machine
- **`Overview.tsx`** — live stats + Recharts line chart (client-side ring buffer, 60 samples max)
- **`Jobs.tsx`** — table with auto-refresh (3s), click-to-expand detail pane, "View Trace" jump
- **`Goals.tsx`** — full CRUD with pause/resume/complete/delete
- **`Traces.tsx`** — execution breakdown: input, plan JSON, retrieved context, per-step timings, final result
- **`Tools.tsx`** — registry view (name, description, input schema)
- **`System.tsx`** — queue depth, success rate, avg latency, per-tool metrics table
- **`lib/dashboardApi.ts`** — typed fetch client; uses `VITE_API_BASE_URL` (empty in dev → Vite proxies `/api` to `:8000`)
- **`main.tsx`** — wraps app in `QueryClientProvider`; React Query handles all polling + cache invalidation
- **Vite config:** added `server.proxy['/api'] → http://localhost:8000` for dev

### Vercel Deployment Notes
- Frontend deploys from `web/public_prism/` (existing `vercel.json`, framework auto-detected as Vite)
- For dashboard to reach Render backend in prod, set Vercel env var: `VITE_API_BASE_URL=https://arkadia-n26k.onrender.com`
- If unset, the dashboard makes same-origin requests (which fail on Vercel since the backend is on Render — set the env var)

## Cycle History
- **Cycle 13:** ARKANA identity, 20-scroll corpus, /api/codex, SpiralVault feed UI (Weaver)
- **Cycle 14:** Firebase memory layer — anonymous auth, Firestore conversation persistence
- **Cycle 15:** Conversation summarization, pattern extraction, textarea UX, react-markdown
- **Cycle 16:** Dynamic multi-source corpus engine, Spiral Codex Live Console Feed
- **Phase 7:** LLM planner + multi-tool chaining (Gemini-driven plans with deterministic fallback)
- **Phase 8:** Memory-aware planning, persistent goals, observability + operational dashboard
