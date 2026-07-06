# 17 — Functionality Matrix

| Feature | Status | Evidence |
|---|---|---|
| Oracle chat (`/api/commune/resonance`) | WORKING | Confirmed live route, Gemini integration, corpus context injection |
| CEO chat with tool-calling (`/api/ceo/chat`) | WORKING | ORACLE_IDENTITY + tool registry injection confirmed in `api/main.py` |
| Corpus multi-source aggregation | WORKING | `corpus/manager.py` confirmed live; workflow logs this session show "corpus syncing 29 scrolls" |
| Spiral Codex Live Console | WORKING | `/api/codex`, `SpiralVault.tsx` confirmed per replit.md and file presence |
| SolSpire kernel job orchestration (Phases 4-6) | WORKING | Full execution trace confirmed end-to-end (classify → plan → execute → verify → summary) |
| SolSpire async jobs + worker pool (Phase 5) | WORKING | `kernel/jobs.py`, `kernel/worker.py` confirmed with retry/backoff |
| SolSpire tool registry (Phase 6) | WORKING | `kernel/tools.py`, `/api/tools` endpoints confirmed |
| SolSpire Phase 7 LLM planner | WORKING (with deterministic fallback) | `kernel/planner.py` confirmed, fallback path verified |
| SolSpire Phase 8 memory/goals/observability | PARTIALLY WORKING | Goals + metrics fully implemented; memory retrieval is keyword-match only, not the richer "memory-aware planning" implied by naming |
| Operational Dashboard (`web/public_prism/src/pages/dashboard/`) | WORKING | Confirmed pages (Overview, Jobs, Goals, Traces, Tools, System) exist and match replit.md description |
| Image generation (`/api/forge`) | WORKING | Real Gemini Imagen tool (`tools_real.py:GenerateImageTool`) confirmed; older `kernel/agents.py` stub is dead code, not the active path |
| Arkadia Symbolic Engine (verse/compress/expand) | WORKING | Deterministic, no-LLM implementation confirmed in `api/arkadia_engine.py` |
| IMS diagnostic/product engine | WORKING | `api/ims_products.py` confirmed with Gemini analysis + Paystack purchase flow |
| IMS Archive (standalone page) | **PARTIALLY WORKING / BROKEN (inconsistent)** | Confirmed to show only 3 of 6 real IMS documents depending on entry point (see Redundancy Audit) — under active repair elsewhere in this session |
| Living Gate calibration tool (lyric timestamp sync) | WORKING (single-track only, not yet generalized) | Confirmed built in prior session; generalization to reusable multi-track feature is planned but not yet implemented per this session's in-progress task |
| Discord bot | BROKEN (in this dev environment) | Workflow status shows "failed" per system log this session — pre-existing, not addressed this session per user's prior instruction |
| Telegram bot (async jobs) | WORKING (opt-in) | `TELEGRAM_ASYNC_JOBS` flag confirmed, default off |
| WhatsApp gateway (OpenClaw) | UNKNOWN / not runtime-verified this session | Code and deploy configs exist; not confirmed reachable/healthy from this environment |
| Mockup sandbox (Canvas tooling) | BROKEN (in this dev environment) | Workflow status shows "failed" per system log this session — tooling only, not shipped product |
| Node/personal codex registry | WORKING | `api/nodes.py` confirmed with public/sovereign-gated endpoints |
| Music distribution flow | WORKING (upload/covenant/submit) | `api/distribution.py`, `DistributePage.tsx` confirmed |
| Living Larder orders | WORKING | `/api/orders` confirmed (sovereign-gated GET) |
| Firestore conversation persistence | WORKING | `conversationService.ts` confirmed |
| True semantic/embedding search over corpus | **UNIMPLEMENTED** (despite replit.md wording) | No embedding provider found anywhere; retrieval is priority-tier based |
| Conversation summarization (active) | **UNIMPLEMENTED** (despite replit.md's Cycle 15 claim) | Only exists in `archive/legacy_python/` (explicitly legacy) |
| Kernel vector-based memory | **UNIMPLEMENTED** (explicitly noted "later" in code) | `kernel/memory.py:14` |
| Mid-run re-planning (Phase 7 planner) | **UNIMPLEMENTED** (explicitly noted as future work in code) | `kernel/planner.py:27` |
| `engine/task_engine.py` intent execution | STUB/UNKNOWN | No confirmed live caller found this session |
| `parsers/`+`schemas/` intent parsing | STUB/UNKNOWN | No confirmed live caller found this session |
| Rasa NLU (`arkana_rasa/`) | STUB/EXPERIMENTAL | No confirmed live caller found this session |
| `sanctum/` health monitoring | STUB/UNKNOWN | No confirmed live caller found this session |
| GovernanceSpirit sub-app (attached_assets) | LEGACY | Confirmed isolated, not part of live product |
| `sonata/` (Java Android) | LEGACY (per prior memory, superseded by `sonata-android/`) | Not re-verified this session |

## Evidence Standard
Every "WORKING" classification above traces to a specific file/line/endpoint confirmed by this session's exploration passes. Every "UNIMPLEMENTED"/"STUB"/"UNKNOWN" classification is based on either an explicit in-code comment admitting the gap, or the absence of a confirmed caller — not inference from naming alone.
