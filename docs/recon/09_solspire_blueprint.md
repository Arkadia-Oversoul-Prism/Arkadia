# 09 — SolSpire Blueprint

Two things share the "SolSpire" name in this repo and must not be conflated:
1. **`kernel/`** — the deterministic execution kernel (Phases 4–8), confirmed live, wired into `api/main.py` startup/shutdown.
2. **`solspire/`** — a separate console/project-management stack (`oracle.py`, `llm.py`, `planner.py`, `execution_runtime.py`, `project_manager.py`, `project_store.py`, `console_router.py`, `tools_fs.py`, `tools_github.py`, `provider_manager.py`, `registry.py`, `intent_router.py`), whose `console_router.py` is mounted into `api/main.py` (per replit.md: "Milestone 1 Kernel API").

## Kernel (`kernel/`) — Subsystem-by-Subsystem
| Subsystem | File | Status |
|---|---|---|
| Intent contract | `intent_types.py` | IMPLEMENTED — 4 strict types (`ALLOWED_TYPES`, `normalize()`) |
| Mutation layer | `oracle_store.py` | IMPLEMENTED — thread-safe JSON CRUD |
| Agent wrappers | `agents.py` | PARTIAL — `call_image_agent()` (line 16) still returns **stubbed** metadata (Phase 4 legacy); real image generation now lives in `tools_real.py`'s `GenerateImageTool` (Gemini Imagen) |
| Classifier/planner/executor | `execution.py` | IMPLEMENTED — `classify_input`, `plan_task`, `execute_intent`, `verify` |
| Async jobs | `jobs.py` | IMPLEMENTED — `JobStore`, FIFO queue, JSON snapshot, `MAX_RETRIES=3` |
| Worker pool | `worker.py` | IMPLEMENTED — daemon threads, exponential backoff, goal scheduler |
| Tool registry | `tools.py` | IMPLEMENTED — `BaseTool`, `TOOL_REGISTRY`, manifest introspection |
| Real tools | `tools_real.py` | IMPLEMENTED — `ExecuteShellTool`, `ReadFileTool`, `WriteFileTool`, `GenerateImageTool` (real, not stubbed) |
| Memory/context | `memory.py` | PARTIAL — keyword-match retrieval only; vector retrieval explicitly noted in-code as "later" (line 14) |
| Goals | `goals.py` | IMPLEMENTED — CRUD, scheduler, safety floors (min 30s cadence, 60/hr cap) |
| Metrics | `metrics.py` | IMPLEMENTED — in-memory sliding-window counters, no persistence |
| Phase 7 planner | `planner.py` | IMPLEMENTED — LLM plan generation with deterministic fallback; **no re-planning mid-run** (explicitly noted as future work, line 27) |
| TTS | `tts.py` (Edge TTS) vs `_piper_fallback.py` | `_piper_fallback.py` appears to be an unused/placeholder local-TTS path — Edge TTS is the active engine (confirmed via prior-session memory) |

## Execution Pipeline (verified trace)
`POST /api/job/create` → `kernel/jobs.py:124` enqueues → `kernel/worker.py:142` worker loop picks up → `kernel/worker.py:46 _process_job` → `execute_intent()` → `kernel/execution.py:59 classify_input` (regex) → if match, deterministic `plan_task`/`execute_steps`/`verify`; if no match, tagged `__plan__` → `kernel/execution.py:239 _execute_planner_intent` → `kernel/planner.py:389 generate_plan` (Gemini) → `validate_plan` (line 207) → `execute_plan` (line 260, resolves `$step_n.field` refs) → each step dispatches via `TOOL_REGISTRY` → `kernel/tools.py:104 _verify` → `kernel/execution.py:345 _summarize` → trace persisted via `kernel/worker.py:101 _record_job_trace`.

## `solspire/` Console — Separate Domain
Not a duplicate of the kernel above; it manages a **different product surface** — SolSpire "projects" (conversations, files, repositories, tasks, memory, events) backed by `data/solspire_projects.db` (SQLite). Confirmed mounted via `console_router.py`. Overlaps conceptually with `kernel/planner.py` (both have an `oracle.py`/`llm.py`-style Gemini planning layer) but operates over project-scoped SQLite state rather than the kernel's global JSON store.

## Implemented / Stub / Broken / Planned Summary
- **Implemented and confirmed live**: intent classification, job queue, worker pool, tool registry, goals, metrics, Phase 7 LLM planner with fallback.
- **Stub**: `kernel/agents.py:call_image_agent` (superseded by real tool, but the stub function still exists — dead code risk).
- **Unimplemented/Planned**: mid-run re-planning (`planner.py`), true vector-based kernel memory (`memory.py`).
- **Unclear/needs confirmation**: whether `engine/task_engine.py` and `parsers/`+`schemas/` are alternate/legacy implementations of the same classify→plan→execute concept, or dead code (see Canonical Architecture Blueprint and Technical Debt Audit).
