# ADR-014: Phase 1 — Kernel Stabilisation

**Status:** Proposed  
**Date:** ARK Y1 · D116 (2026-07-24)  
**Decider:** Flamekeeper + Principal Engineer  
**Supersedes:** None  
**References:** ADR-013 (Phase 0 Security), ADR-010/011/012 (Knowledge OS)

---

## Context

Phase 0 closed five critical security vulnerabilities. The architecture is now safe to refactor. Phase 1 is a stabilisation phase — no new features, no UI changes. Its objective is to reduce architectural entropy to the point where new capabilities can be added without increasing technical debt.

The Phase 1 analysis (2026-07-24) produced seven documents identifying the highest-entropy points in the current implementation. These decisions govern how Phase 1 implementation work proceeds.

Ref docs: `docs/phase1/RESPONSIBILITY_MATRIX.md`, `DEPENDENCY_GRAPH.md`, `RUNTIME_STATE_DIAGRAM.md`, `SQLITE_JOB_QUEUE_DESIGN.md`, `PLUGIN_REGISTRY_SPEC.md`, `OBSERVABILITY_DESIGN.md`, `CORPUS_SYNC_DESIGN.md`

---

## Decisions

### Decision 1: Workstream B — SQLite-Backed Job and Goal Queue

**Replace** the in-memory `queue.Queue` + JSON snapshot persistence in `kernel/jobs.py` and `kernel/goals.py` with SQLite-backed storage.

**Rationale:** The current implementation loses all in-flight jobs on process crash. The JSON snapshot is a best-effort recovery mechanism, not a durability guarantee. SQLite WAL mode provides crash-safe atomic writes with no external dependencies.

**Constraints:**
- The public `JobStore` API is frozen: `create`, `get`, `list`, `mark_running`, `mark_completed`, `mark_failed`, `requeue_for_retry`, `stats`. No changes to callers.
- Firebase sync remains additive and optional. It is not removed. It is extracted from the `JobStore` into a separate sync adapter.
- Migration is incremental: JSON → SQLite import on first startup; JSON files preserved as read-only backup.
- Database file: `data/runtime.db` (separate from `knowledge/arkadia.db`)
- Every intermediate commit must leave the repository deployable.

**Rollback:** Single `git revert` of the migration commit restores JSON behaviour. JSON files are preserved throughout.

---

### Decision 2: Workstream E — Plugin Registry Replaces ALLOWED_TYPES

**Replace** the `ALLOWED_TYPES` frozenset in `kernel/intent_types.py` with a `PluginRegistry` in `kernel/plugin_registry.py` that discovers capabilities from registered tool manifests.

**Rationale:** Hardcoding the capability set at the module level means adding any new capability requires editing the kernel. The existing `BaseTool`/`TOOL_REGISTRY` pattern in `kernel/tools.py` is already pluggable at the execution level; the routing layer must match.

**Constraints:**
- `BaseTool` interface is unchanged. Existing tools require no modification.
- `register_tool()` accepts an optional `PluginManifest`; when not provided, a default manifest is generated from the tool's attributes.
- `ALLOWED_TYPES` becomes a compatibility alias during transition; removed after all callers are migrated.
- Migration is incremental (6 independently-deployable steps — see `PLUGIN_REGISTRY_SPEC.md`).

**Not in scope:** Plugin file-system discovery, plugin versioning enforcement, dependency resolution. These are Phase 2.

---

### Decision 3: Workstream D — Structured Observability

**Add** `kernel/observability.py` providing a `StructuredLogger` that emits JSON events to stdout. Add `request_id` and `execution_id` context propagation via `contextvars.ContextVar`.

**Rationale:** Currently there is no way to correlate log lines across a full request/job lifecycle. `kernel/metrics.py` provides counters but they reset on restart and have no per-request identity. Structured logs are the minimum observability floor before further complexity is added.

**Constraints:**
- No external metrics backend (no Prometheus, Datadog, OpenTelemetry) in Phase 1.
- No log file writes — stdout only.
- No user content in logs (lengths, counts, and hashes only).
- `kernel/metrics.py` is not replaced — the structured logger calls into it as a side effect.
- FastAPI middleware adds `X-Request-Id` header to all responses.

---

### Decision 4: Workstream A — Kernel Layer Violation Remediation

**Remove** all imports of `api/` modules from `kernel/` modules. The kernel must be runnable without any API layer involvement.

**Specific violations to fix (in priority order):**
1. `kernel/agents.py` → `api.arkadia_engine`: extract `generate_verse` logic into `kernel/verse.py` or accept a `VerseProvider` interface
2. `kernel/planner.py` → `kernel/tools_real.py` → `api.key_manager`: move key resolution to a `KeyProvider` interface injected at startup
3. `kernel/jobs.py` + `kernel/goals.py` → `api.firebase_store`: extract Firebase sync into a `SyncAdapter` registered at startup

**Rationale:** Layer inversions prevent the kernel from being tested in isolation, create circular import risks as the codebase grows, and couple the execution core to deployment-specific infrastructure.

**Constraints:**
- API surface (routes, response shapes) is unchanged.
- The `api/` layer provides concrete implementations and wires them into the kernel at FastAPI startup.
- `kernel/` never imports from `api/`.

---

### Decision 5: Workstream C — Incremental Corpus Synchronisation

**Replace** the full-tree-on-every-sync behaviour in `github_corpus.py` with an incremental sync that compares blob SHAs.

**Rationale:** The current implementation re-fetches and re-ingests every file on every sync, regardless of changes. This wastes GitHub API quota, increases sync latency, and provides no resumability on failure.

**Constraints:**
- Sync state persisted in `data/runtime.db` (two new tables: `corpus_sync_state`, `corpus_file_state`)
- `ingest()` API is unchanged
- Legacy `github_corpus.py` preserved until incremental version is proven stable (two sync cycles)
- Rate-limit handling: exponential backoff, respect `X-RateLimit-Remaining`

---

## Scope Boundaries (Phase 1 Exclusions)

The following are explicitly **out of scope for Phase 1** and must not be implemented until Phase 2 or later:

- `api/main.py` decomposition (2506-line monolith) — Phase 2
- Client-side `isSovereign` flag security — Phase 2
- Frontend Oracle request timeout — Phase 2 (low effort but not Phase 1 scope)
- Plugin filesystem discovery / hot-reload — Phase 2
- Distributed tracing (OpenTelemetry) — Phase 3
- Redis, Kafka, Kubernetes, microservices — explicitly excluded (see Phase 1 brief)
- UI changes of any kind — explicitly excluded
- New capabilities / features — explicitly excluded
- `curl`/`wget` SSRF in automated pipelines — only relevant if approval-gate is removed

---

## Engineering Rules (Constitutional for Phase 1)

Every pull request implementing Phase 1 work must:
1. Reduce coupling (measurable: fewer cross-layer imports)
2. Increase testability (measurable: each changed module can be unit-tested in isolation)
3. Preserve deployability (every commit: `uvicorn api.main:app` starts without error)
4. Include tests for changed behaviour
5. Update this ADR or create a new ADR for sub-decisions that were not anticipated here

No implementation may increase architectural debt. If a change cannot satisfy all four constraints, it must be redesigned.

---

## Consequences

### Positive
- In-flight jobs survive process crashes (SQLite durability)
- New capabilities can be added without editing the kernel (plugin registry)
- Full request lifecycle is observable from log output alone (structured logging)
- Corpus sync is bounded, resumable, and respects API limits
- Kernel layer is testable in isolation (no api/ imports)

### Risks to Monitor
- SQLite migration: JSON import must be validated for data integrity before cutover
- Plugin registry: `ALLOWED_TYPES` alias must be removed promptly — leaving both indefinitely creates confusion about which is authoritative
- Structured logging: log volume may increase significantly; monitor for performance impact on slow I/O paths
- Incremental corpus sync: first run after migration fetches all files (no prior SHA state); subsequent runs are incremental

---

## Related ADRs

- ADR-010: Knowledge Vault as canonical truth store
- ADR-011: Provider Router — AI providers as replaceable adapters
- ADR-012: Context Engine — semantic retrieval, not memory dump
- ADR-013: Phase 0 — Security Hardening (prerequisite; constitutional)
- ADR-015 (pending): Kernel Port Interfaces — `StorageBackend`, `LLMProvider`, `KeyProvider`
