# 01 — Repository Map

Evidence-based inventory of the Arkadia repository. Sizes/line counts are approximate as reported by exploration tooling; treat exact figures as indicative, not authoritative to the byte.

## Top-Level Directories

| Directory | Purpose | Status | Key files |
|---|---|---|---|
| `api/` | FastAPI backend — the "Arkadia Mind" | ACTIVE | `main.py` (~88KB, largest single file in repo), `auth.py`, `firebase_store.py`, `ims_products.py`, `pulse.py`, `distribution.py`, `nodes.py`, `arkadia_engine.py`, `key_manager.py` |
| `web/public_prism/` | Production React/Vite frontend ("Public Prism") | ACTIVE | `src/pages/*`, `src/components/*`, `src/contexts/AuthContext.tsx`, `vite.config.ts` |
| `bot/` | Chat platform bridges | ACTIVE | `discord-bot.mjs`, `telegram-bot.mjs`, own `package.json`/`Dockerfile` |
| `kernel/` | SolSpire deterministic execution kernel (Phases 4–8) | ACTIVE | `execution.py`, `jobs.py`, `worker.py`, `tools.py`, `tools_real.py`, `planner.py`, `memory.py`, `goals.py`, `metrics.py`, `oracle_store.py`, `intent_types.py` |
| `weaver/` | Autonomous agent layer ("Echofield" symbolic vector search + autonomy loop) | ACTIVE / EXPERIMENTAL (mixed) | `run_autonomy.py`, `agent.py`, `echofield/`, `autonomy/`, `filters/`, `notes/` (runtime logs) |
| `solspire/` | Separate LLM/project-management console (older or parallel kernel implementation) | PARTIAL — overlaps with `kernel/` | `oracle.py`, `llm.py`, `planner.py`, `execution_runtime.py`, `project_manager.py`, `project_store.py` (SQLite), `console_router.py` (mounted in `api/main.py`), `tools_fs.py`, `tools_github.py`, `provider_manager.py`, `registry.py` |
| `engine/` | Low-level task engine (yet another execution layer) | UNKNOWN / likely LEGACY-or-EXPERIMENTAL — not confirmed wired into `api/main.py` | `task_engine.py`, `subagents.py`, `safety.py`, `state.py` |
| `parsers/` | Standalone intent parsing/routing | UNKNOWN — overlaps conceptually with `kernel/execution.py:classify_input` and `solspire/intent_router.py` | `intent_parser.py`, `routing_engine.py` |
| `schemas/` | Shared intent schema definitions | UNKNOWN — unclear which of `kernel/intent_types.py` / `schemas/intent_schema.py` is canonical | `intent_schema.py` |
| `corpus/` | Multi-source document aggregation for the Oracle's long-term memory | ACTIVE | `manager.py`, `github.py`, `gdrive.py`, `joplin.py`, `obsidian.py` |
| `data/` | JSON/SQLite persistent state | ACTIVE | `oracle_store.json`, `job_store.json`, `goal_store.json`, `nodes_seed.json`, `ims_credentials_sealed.json`, `solspire_projects.db`, `api_keys.json` |
| `governance/` | Declared system rules, permissions, roles, vows, proposals | ACTIVE (as config), enforcement path unconfirmed | `manifest.json`, `permissions.json`, `roles.json`, `boundaries.json`, `autonomy.json`, `vows.md`, `anchors/`, `proposals/` |
| `docs/` | Specs and canonical doctrine documents | ACTIVE | `ARKADIA_SPEC_v3.md`, `DOC1_MASTER_WEIGHTS.md`, `DOC2_OPEN_LOOPS.md`, `DOC3_PRINCIPLES_REGISTRY.md`, `CLOUD_ARCHITECTURE.md`, `CORPUS_MANIFEST.json`, plus `creative/`, `collective/`, `governance/` subfolders (corpus source dirs) |
| `sonata/` | Native Android client (Java) | LEGACY (likely superseded by `sonata-android/`) | `app/`, `build.gradle.kts` |
| `sonata-android/` | Native Android client (Kotlin) | ACTIVE (per prior-session memory: canonical push target) | `app/`, `build.gradle.kts` |
| `arkana_rasa/` | Rasa NLU training config | EXPERIMENTAL — no confirmed caller in `api/main.py` | `data/intents/`, `domain.yml` |
| `arkana_space/` | Standalone FastAPI app, likely for HuggingFace Spaces deployment | PARTIAL / EXPERIMENTAL — separate `Dockerfile`+`requirements.txt`, own `/oracle`, `/webhook/meta` endpoints, unauthenticated | `app.py`, `brain.py`, `Dockerfile`, `requirements.txt` |
| `artifacts/mockup-sandbox/` | Replit Canvas mockup/preview tooling (not part of shipped product) | ACTIVE (tooling) | own `package.json`, `vite.config.ts` |
| `attached_assets/` | Uploaded files, backups, and a **complete nested duplicate project** | Mostly ORPHANED / ARCHIVE | `arkadia_spirit/GovernanceSpirit/` (full separate React+Express+Postgres app with its own `package.json`, `src/`, `server/`, `shared/schema.ts`), large ZIPs/PDFs |
| `gate/` | Static landing page (plain HTML/JS/CSS) | LEGACY — predates the React "Living Gate" flow | `index.html`, `gate.js`, `gate.css` |
| `static/` | Legacy static web assets, incl. real IMS deliverable HTML files | MIXED — `ims/*.html` are ACTIVE/real content still served via `/static` mount; `index.html`/`dashboard.html` are LEGACY pre-React dashboards | `ims/jay_ims.html`, `ims/won_ims.html`, `ims/eduleague.html`, `index.html`, `dashboard.html` |
| `sanctum/` | Health/status tracking | UNKNOWN — not confirmed wired to `api/main.py` | `status.py`, `status.json` |
| `openclaw/` | WhatsApp gateway service (separate Node.js deployable) | ACTIVE (separately deployed, per `docs/DOC1_MASTER_WEIGHTS.md` reference `+2348144942818`) | `gateway.js`, `config.json`, own `package.json`/`Dockerfile`/`render.yaml`/`fly.toml`/`railway.json` |
| `scripts/` | One-off maintenance/deploy scripts | ACTIVE (utility) | `serve-gate.sh`, `github_push.py`, `push-to-sonata.sh` (per memory) |
| `tests/` | Pytest suite | PARTIAL — coverage scope not fully audited | `test_autonomy.py`, `test_llm_providers.py`, `render_test_console.py` |
| `archive/legacy_python/` | Superseded backend implementations | LEGACY (explicitly named) | old `weaver.py`, `brain.py`, `entrypoint.sh` (contains a hardcoded Gemini key — see Security Audit), old `requirements.txt` (references SQLAlchemy/Postgres/`sift-stack-py`, not used by current backend) |

## Root-Level Configuration Files

| File | Purpose |
|---|---|
| `package.json` (root) | Node deps for root-level tooling — **overlaps with, and version-conflicts against**, `web/public_prism/package.json` (see Dependency Audit) |
| `requirements.txt` (root) | Python deps for the main `api/` service |
| `Dockerfile` (root) | Python 3.11-slim container for the main API |
| `.replit` | Replit workflow/environment configuration |
| `vercel.json` (root + `web/public_prism/vercel.json`) | Vercel deployment config for the frontend |
| `firestore.rules` | Firebase security rules |

## Duplicate / Parallel Service Manifests (fragmentation signal)
Four independent Node/Python service trees each carry their own `package.json`/`requirements.txt`/`Dockerfile`, targeting **four different hosts** (Render, Railway, Fly.io, Vercel):
- Root (`/`) → Render (main API)
- `bot/` → Railway (Discord/Telegram)
- `openclaw/` → Render/Fly.io (WhatsApp gateway)
- `arkana_space/` → HuggingFace Spaces

See **12_configuration_audit.md** and **15_redundancy_audit.md** for detail.

## Explicit Uncertainty Markers
- `engine/`, `parsers/`, `schemas/`, `arkana_rasa/`, `sanctum/`: purpose inferred from filenames and directory contents only. **Not confirmed** whether these are imported/called anywhere in the live request path (`api/main.py`, `kernel/`, `weaver/`). Flagged for follow-up in Technical Debt Audit.
- `weaver/notes/*.txt`: numerous timestamped files (e.g. `autonomy_step_1765663664_1.txt`) — confirmed as runtime-generated logs, not source code.
