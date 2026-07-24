# Phase 1 — Dependency Graph & Coupling Report

**Status:** Analysis complete. No implementation until deliverables are approved.  
**Date:** 2026-07-24  
**Workstream:** A — Kernel Stabilisation

---

## Dependency Graph (kernel/ layer)

Arrows show import direction: A → B means "A imports B".

```
                        api/main.py
                            │
                            ▼
              ┌─────────────────────────┐
              │                         │
              ▼                         ▼
        kernel/worker.py          api/firebase_store
              │                         ▲
              │                         │ (lazy import)
              ▼                    ┌────┴────────┐
        kernel/execution.py        │             │
              │                 kernel/jobs.py  kernel/goals.py
              ├─► kernel/agents.py    │
              │        │              │
              │        ▼              │
              │   api/arkadia_engine  │  ← LAYER VIOLATION
              │        │              │
              ├─► kernel/intent_types.py
              ├─► kernel/tools.py
              │        │
              │        ▼
              │   kernel/tools_real.py
              │        │
              │        └─► api/key_manager  ← LAYER VIOLATION
              │
              └─► kernel/planner.py
                       │
                       ├─► kernel/tools.py
                       ├─► kernel/memory.py
                       │        │
                       │        ├─► kernel/oracle_store.py
                       │        └─► knowledge/context_engine.py
                       │
                       └─► api/key_manager  ← LAYER VIOLATION

kernel/metrics.py  ← pure; no upstream kernel deps
```

---

## Layer Violations (Critical)

These are architectural inversions: the kernel depends on the API layer.
The kernel must be testable and runnable without any API layer involvement.

### Violation 1: `kernel/agents.py → api.arkadia_engine`

```python
# kernel/agents.py line 12
from api import arkadia_engine as arkadia
```

**Impact:** Cannot unit-test `generate_verse` without the entire API module loading.  
Cannot run the kernel as a standalone library.  
`api.arkadia_engine` is a large monolith; importing it imports FastAPI, Firebase, etc.

**Extraction plan:** `generate_verse` logic should live in `kernel/` or be injected via a `VerseProvider` interface. `arkadia_engine` is a provider, not a kernel dependency.

---

### Violation 2: `kernel/planner.py → api.key_manager`

```python
# kernel/planner.py line 130-131
from api.key_manager import get_active_key
api_key = get_active_key() or os.environ.get("GOOGLE_API_KEY", "")
```

**Impact:** Planner cannot be instantiated without the API key manager.  
**Extraction plan:** Key resolution belongs in `providers/gemini.py` or a `ProviderConfig`. Planner should receive an `api_key` parameter or a `LLMProvider` interface, not import from `api/`.

---

### Violation 3: `kernel/tools_real.py → api.key_manager` (via `_active_api_key()`)

```python
# kernel/tools_real.py line 539-544
from api.key_manager import get_active_key
```

Same issue as violation 2. `GenerateImageTool` should receive provider configuration, not reach into the API layer.

---

### Violation 4: `kernel/jobs.py → api.firebase_store` (lazy, conditional)

```python
# kernel/jobs.py lines 90, 118
from api.firebase_store import fb_load_jobs
from api.firebase_store import fb_sync_jobs
```

**Impact:** Firebase sync is embedded in the storage layer. Changing the cloud sync strategy requires editing `kernel/jobs.py`. The `JobStore` does two things: persists state and syncs it remotely.  
**Extraction plan:** Define `StorageBackend` interface. `JobStore` writes locally (SQLite/JSON). A separate `FirebaseSyncAdapter` listens for changes and mirrors them — as an optional additive layer, not embedded persistence.

---

### Violation 5: `kernel/goals.py → api.firebase_store` (same pattern)

Same issue as violation 4 — duplicated pattern.

---

## Coupling Map

| Coupling | Type | Severity | Phase 1 target? |
|---|---|---|---|
| `execution.py` mixes classify/plan/execute/verify/orchestrate | Internal concentration | HIGH | YES — split classifier |
| `agents.py → api.arkadia_engine` | Layer inversion (kernel→API) | HIGH | YES |
| `planner.py → api.key_manager` | Layer inversion (kernel→API) | HIGH | YES |
| `tools_real.py → api.key_manager` | Layer inversion (kernel→API) | MEDIUM | YES |
| `jobs.py → api.firebase_store` | Layer inversion (kernel→API) | MEDIUM | YES — extract StorageBackend |
| `goals.py → api.firebase_store` | Same | MEDIUM | YES — same fix |
| `worker.py → execute_intent` (direct fn call) | Tight coupling to implementation | MEDIUM | Defer to P2 (interface extraction) |
| `select_tool()` requires intent.type == tool.name | Routing hardcoded to naming | MEDIUM | YES — Workstream E |
| `ALLOWED_TYPES` frozenset | Compile-time capability registration | MEDIUM | YES — Workstream E |
| `oracle_store.py` read-full-file-on-every-write | Performance + concurrency | LOW | P2 — defer to SQLite migration |
| `api/main.py` 2506 lines | Monolith | LOW | P2 — defer |
| `github_corpus.py` full tree on every sync | Network + time waste | HIGH | YES — Workstream C |

---

## Dependency Inversion Target State

```
api/main.py
    │  depends on
    ▼
kernel/ (pure — no api/ imports)
    │  depends on
    ▼
kernel/ports/  (interfaces only — no implementations)
    ├── StorageBackend     (implemented by: SQLiteStorage, JsonStorage)
    ├── LLMProvider        (implemented by: GeminiProvider, ClaudeProvider)
    ├── VerseProvider      (implemented by: ArkadiaSymbolicEngine)
    └── KeyProvider        (implemented by: EnvKeyProvider, KeyManagerProvider)
```

The API layer provides implementations and wires them into the kernel at startup.
The kernel never imports from `api/`.

---

## What Must Not Change (Phase 1 constraints)

- The `BaseTool` / `TOOL_REGISTRY` interface is correct and must not be replaced.
- The `JobStore` public API (`create`, `get`, `list`, `mark_*`, `requeue_for_retry`) must be preserved — workers, tests, and API routes all depend on it.
- The kernel envelope shape `{success, results, summary, tool_used, handled, intent}` must be preserved.
- Phase 0 security decisions (ADR-013) are constitutional — do not touch `ALLOWED_SHELL_COMMANDS`, write-path validation, or auth fail-fast.

---

*Next document: RUNTIME_STATE_DIAGRAM.md*
