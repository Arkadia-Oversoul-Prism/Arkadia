# Phase 1 — Kernel Responsibility Matrix

**Status:** Analysis complete. No implementation until deliverables are approved.  
**Date:** 2026-07-24  
**Workstream:** A — Kernel Stabilisation

---

## Method

Every module in `kernel/` was read and each public function classified into one of:

| Category | Meaning |
|---|---|
| **orchestration** | Coordinates other components; decides what runs next |
| **planning** | Converts intent into ordered steps (may call LLM) |
| **execution** | Actually runs a capability against real resources |
| **provider** | Interfaces with an external AI or API provider |
| **storage** | Persists or retrieves state |
| **routing** | Maps an intent or message to the correct handler |
| **verification** | Checks whether a result is acceptable |
| **lifecycle** | Starts, stops, or monitors system components |

---

## Module-Level Matrix

| Module | Primary Category | Secondary | Mixed? | Notes |
|---|---|---|---|---|
| `kernel/execution.py` | orchestration | routing + verification + planning | **YES — HIGH CONCERN** | `execute_intent` orchestrates; `classify_input` routes; `plan_task` plans; `verify` verifies; `_execute_planner_intent` delegates to planner. Four distinct responsibilities in one file. |
| `kernel/intent_types.py` | routing | — | no | `ALLOWED_TYPES`, `normalize`. Clean. But hardcodes the capability set — violates Workstream E. |
| `kernel/tools.py` | routing | execution | minor | `BaseTool`, `TOOL_REGISTRY`, `select_tool`. Registry pattern is correct. `_envelope` helper crosses into verification. |
| `kernel/tools_real.py` | execution | — | no | Shell, file, directory, image tools. Each tool is a single capability. Clean single-responsibility. |
| `kernel/agents.py` | execution | — | no | Thin wrappers over `oracle_store` + `api.arkadia_engine`. **Inverted dependency: kernel imports from `api/`.**|
| `kernel/planner.py` | planning | provider + execution | minor | Generates plans via Gemini (provider), validates them, executes chains. Provider call is appropriately abstracted via fallback models. |
| `kernel/jobs.py` | storage | lifecycle | minor | `JobStore`: in-memory dict + `queue.Queue` + JSON snapshot. Persistence is embedded in the store — should eventually be separate. |
| `kernel/goals.py` | storage | — | no | `GoalStore`: same embedded-persistence pattern as `JobStore`. Duplication of pattern. |
| `kernel/worker.py` | lifecycle | orchestration | minor | Daemon threads, goal scheduler. Calls `execute_intent` directly — couples lifecycle to orchestration layer. |
| `kernel/memory.py` | storage | — | no | Context retrieval. Clean: tries Knowledge Vault, falls back to oracle_store. No side effects. |
| `kernel/oracle_store.py` | storage | — | no | JSON file store for transactions, loops, assets, events, balance. Clean single-responsibility. |
| `kernel/metrics.py` | observability | — | no | In-process counters. Thread-safe. Good foundation. Not yet structured logging. |
| `kernel/tts.py` | provider | — | no | Text-to-speech via Edge TTS. |
| `kernel/_piper_fallback.py` | provider | — | no | Piper TTS fallback. |

---

## Responsibility Concentration Heat Map

```
HIGH CONCENTRATION (most concerning — Phase 1 targets):

  kernel/execution.py
  ├── routing         classify_input()
  ├── planning        plan_task()
  ├── execution       execute_steps()
  ├── verification    verify()
  └── orchestration   execute_intent(), _execute_planner_intent()

  kernel/worker.py
  ├── lifecycle       start_workers(), stop_workers()
  ├── lifecycle       start_goal_scheduler()
  └── orchestration   _process_job() → calls execute_intent directly

APPROPRIATE CONCENTRATION (acceptable):

  kernel/jobs.py      storage + queue (co-located by design; extractable)
  kernel/goals.py     storage + schedule-state (same)
  kernel/planner.py   planning + provider (planning strategy owns its provider calls)

CLEAN (single responsibility):

  kernel/intent_types.py   routing only
  kernel/tools_real.py     execution only (5 tools)
  kernel/oracle_store.py   storage only
  kernel/memory.py         retrieval only
  kernel/metrics.py        observability only
```

---

## What the Kernel Should Own (Target State)

Per the Phase 1 brief, the kernel's long-term responsibility set is:

```
KERNEL (target)
├── orchestration     — what runs next; job lifecycle management
├── scheduling        — when goals fire; cadence enforcement
├── lifecycle         — start/stop workers and scheduler
└── events            — observable event emission
```

Everything else should be replaceable:

```
REPLACEABLE (target)
├── planning          → provider-agnostic PlannerInterface
├── routing           → plugin-driven (not hardcoded ALLOWED_TYPES)
├── execution         → tool registry (already exists — keep it)
├── storage           → StorageInterface (SQLite first; Firestore additive)
├── provider          → ProviderInterface (already exists in providers/)
└── verification      → VerifierInterface (currently a pure function — good)
```

---

## Extraction Priority (Phase 1 scope)

| Priority | Module | Action | Why |
|---|---|---|---|
| P1 | `kernel/execution.py` | Split routing (`classify_input`) into `kernel/classifier.py` | Four responsibilities in one file is the highest entropy point |
| P1 | `kernel/agents.py` | Remove `api.arkadia_engine` import; inject dependency | Kernel must not import from API layer |
| P1 | `kernel/jobs.py` | Extract persistence into `StorageInterface`; SQLite first | In-memory queue = data loss on crash |
| P2 | `kernel/intent_types.py` | Replace `ALLOWED_TYPES` frozenset with plugin manifest scan | Compile-time capability registration blocks Workstream E |
| P2 | `kernel/worker.py` | Define `OrchestratorInterface`; decouple from `execute_intent` | Worker should call an interface, not a concrete function |
| P3 | `kernel/planner.py` | Define `PlannerInterface`; current impl becomes `GeminiPlanner` | Makes planner replaceable |

---

*Next document: DEPENDENCY_GRAPH.md*
