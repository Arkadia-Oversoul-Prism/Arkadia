---
name: Phase 1 Analysis
description: Phase 1 pre-implementation deliverables — all complete, pending Flamekeeper approval before any implementation begins.
---

# Phase 1 Analysis — Durable Notes

## Status
All seven Phase 1 deliverables written. ADR-014 filed (Proposed). Zero code changes made.

## Key Architectural Findings

**Highest entropy point:** `kernel/execution.py` — mixes classify/plan/execute/verify/orchestrate.

**Layer violations (kernel imports from api/):**
- `kernel/agents.py` → `api.arkadia_engine` (generate_verse)
- `kernel/planner.py` → `api.key_manager` (Gemini key lookup)
- `kernel/tools_real.py` → `api.key_manager` (GenerateImageTool)
- `kernel/jobs.py` + `kernel/goals.py` → `api.firebase_store` (sync)

**In-memory queue gap:** `kernel/jobs.py` uses `queue.Queue` — pending jobs lost on crash. JSON snapshot is soft-restart only. Fix: SQLite WAL (data/runtime.db, separate from knowledge/arkadia.db).

**ALLOWED_TYPES:** Hardcoded frozenset in `kernel/intent_types.py`. Fix: `PluginRegistry` with `PluginManifest` — tools declare what intent types they handle.

**Corpus sync:** `github_corpus.py` fetches full tree on every run — no SHA comparison, no state, no resumability. Fix: incremental sync with `corpus_sync_state` + `corpus_file_state` tables.

**Metrics:** `kernel/metrics.py` is a good foundation but in-memory only, no request_id correlation. Fix: `kernel/observability.py` with StructuredLogger + contextvars.

## Workstream Priority Order
B (SQLite durability) → E (plugin registry) → D (observability) → A (layer violations) → C (corpus sync)

## ADR-014 Rule
Every Phase 1 commit must: reduce coupling, increase testability, preserve deployability, include tests, update ADRs.

## Documents Written
All in docs/phase1/:
- RESPONSIBILITY_MATRIX.md
- DEPENDENCY_GRAPH.md
- RUNTIME_STATE_DIAGRAM.md
- SQLITE_JOB_QUEUE_DESIGN.md
- PLUGIN_REGISTRY_SPEC.md
- OBSERVABILITY_DESIGN.md
- CORPUS_SYNC_DESIGN.md
- ../adr/ADR-014-phase1-kernel-stabilisation.md
- CONTINUATION_LEDGER.md

## Why: What Not to Repeat
Phase 0 is constitutional — verified complete, do not revisit.
Implementation is blocked until ADR-014 is approved (status: Proposed).
Do not start Workstream E or A until Workstream B tests pass.
