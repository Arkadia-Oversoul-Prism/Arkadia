# Arkadia — Phase Gate Criteria

**Date:** ARK Y1 · D116 (2026-07-24)  
**Status:** Canonical — update only via Principal Engineer session with ADR reference.

---

## What Phase Gates Are

A phase gate is a set of objective, verifiable exit criteria that must all be satisfied before the next phase begins. Gates prevent phases from being declared complete on vibes — every criterion is either demonstrably true or it is not.

Work inside a phase may overlap with preparation for the next. But **implementation of the next phase does not begin** until all current phase gates are closed.

---

## Phase 0 — Security Hardening

**Status: CLOSED** (verified 2026-07-24)

| Criterion | Verified By | Status |
|---|---|---|
| Shell execution converted to strict allowlist | Read `kernel/tools_real.py` → `ALLOWED_SHELL_COMMANDS` frozenset | ✅ |
| `shell=False` enforced | Read `kernel/tools_real.py` → `subprocess.run(shell=False)` | ✅ |
| Path separator guard implemented | Read `kernel/tools_real.py` → `_check_shell_command` Stage 1 | ✅ |
| Interpreters, package managers, `git`, `find`, `env`, `cp`, `mv` excluded | Read `ALLOWED_SHELL_COMMANDS` | ✅ |
| Canonical write validation (symlink walk + O_NOFOLLOW) | Read `_validate_write_path` | ✅ |
| Production auth fail-fast | Read `api/auth.py` → `_init_firebase()` | ✅ |
| Production sovereign fail-fast | Read `api/main.py` → `SOVEREIGN_KEY` block | ✅ |
| Explicit CORS (no wildcard) | Read `api/main.py` → `_CORS_ORIGINS` | ✅ |
| ADR-013 filed and status=Accepted | `docs/adr/ADR-013-phase0-security-hardening.md` | ✅ |

---

## Phase 1 — Kernel Stabilisation

**Status: IN PROGRESS**

### Gate A: Documentation & Governance

| Criterion | Verified By | Status |
|---|---|---|
| Responsibility Matrix complete | `docs/phase1/RESPONSIBILITY_MATRIX.md` exists + reviewed | ✅ |
| Dependency Graph + Coupling Report complete | `docs/phase1/DEPENDENCY_GRAPH.md` | ✅ |
| Runtime State Diagram complete | `docs/phase1/RUNTIME_STATE_DIAGRAM.md` | ✅ |
| Architecture Map complete | `docs/phase1/ARCHITECTURE_MAP.md` | ✅ |
| SQLite Job Queue Design complete | `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` | ✅ |
| Plugin Registry Spec complete | `docs/phase1/PLUGIN_REGISTRY_SPEC.md` | ✅ |
| Observability Design complete | `docs/phase1/OBSERVABILITY_DESIGN.md` | ✅ |
| Corpus Sync Design complete | `docs/phase1/CORPUS_SYNC_DESIGN.md` | ✅ |
| ADR-014 filed | `docs/adr/ADR-014-*.md` status=Accepted | ✅ |
| ADR-015 filed | `docs/adr/ADR-015-*.md` status=Accepted | ✅ |
| Architecture fitness tests written | `tests/architecture/test_layer_boundaries.py` | ✅ |
| Phase gate criteria documented | This file | ✅ |
| Continuation Ledger updated | `docs/phase1/CONTINUATION_LEDGER.md` | ✅ |

### Gate B: Runtime Durability (Workstream B)

| Criterion | Verified By | Status |
|---|---|---|
| `data/runtime.db` created with correct schema | `sqlite3 data/runtime.db ".schema"` matches design doc | ⬜ |
| `SQLiteJobStore` implements full `JobStore` API | Unit tests pass: `pytest tests/test_sqlite_job_store.py` | ⬜ |
| `SQLiteGoalStore` implements full `GoalStore` API | Unit tests pass: `pytest tests/test_sqlite_goal_store.py` | ⬜ |
| JSON→SQLite migration imports all existing jobs | `pytest tests/test_jobs_migration.py` | ⬜ |
| Two concurrent workers cannot claim the same job | Concurrency test passes | ⬜ |
| RUNNING job resets to PENDING on restart | Restart simulation test passes | ⬜ |
| Firebase sync extracted from `JobStore` | `kernel/jobs.py` contains no `api.firebase_store` import | ⬜ |
| Repository deployable after migration | `uvicorn api.main:app` starts without error | ⬜ |

### Gate C: Observability (Workstream D)

| Criterion | Verified By | Status |
|---|---|---|
| `kernel/observability.py` implemented | File exists, unit tests pass | ⬜ |
| `request_id` in every HTTP response header | `curl -I /api/oracle` → `X-Request-Id` present | ⬜ |
| `execution_id` in every `execute_intent` log | `grep execution_id` in log output | ⬜ |
| JOB_CREATED, JOB_CLAIMED, JOB_COMPLETED events emitted | Log inspection on test job | ⬜ |
| PLAN_GENERATED includes `planner_latency_ms` | Log inspection | ⬜ |
| KNOWLEDGE_RETRIEVED event emitted | Log inspection | ⬜ |
| All log events are valid JSON | `pytest tests/test_observability.py` | ⬜ |

### Gate D: Plugin Registry (Workstream E)

| Criterion | Verified By | Status |
|---|---|---|
| `kernel/plugin_registry.py` implemented | File exists | ⬜ |
| All existing tools registered with manifests | `registry.discover()` returns 5+ manifests | ⬜ |
| `execute_intent` uses `registry.is_allowed()` | `grep ALLOWED_TYPES kernel/execution.py` returns nothing | ⬜ |
| `ALLOWED_TYPES` frozenset removed from `intent_types.py` | `pytest tests/architecture/test_layer_boundaries.py::test_intent_types_allowed_types_is_not_a_frozenset` passes | ⬜ |
| A tool can handle multiple intent types | Registry unit test confirms handles-set routing | ⬜ |

### Gate E: Layer Violations (Workstream A)

| Criterion | Verified By | Status |
|---|---|---|
| `kernel/agents.py` does not import `api.arkadia_engine` | `grep -n "from api" kernel/agents.py` → empty | ⬜ |
| `kernel/planner.py` does not import `api.key_manager` | `grep -n "from api" kernel/planner.py` → empty | ⬜ |
| `kernel/tools_real.py` does not import `api.key_manager` | `grep -n "from api" kernel/tools_real.py` → empty | ⬜ |
| `kernel/jobs.py` does not import `api.firebase_store` | `grep -n "from api" kernel/jobs.py` → empty | ⬜ |
| `kernel/goals.py` does not import `api.firebase_store` | `grep -n "from api" kernel/goals.py` → empty | ⬜ |
| `REGISTERED_ARCHITECTURAL_DEBT` in `LAYER_MAP.py` is empty | File inspection | ⬜ |
| Architecture fitness tests pass with no allowed violations | `pytest tests/architecture/` | ⬜ |

### Gate F: Corpus Sync (Workstream C)

| Criterion | Verified By | Status |
|---|---|---|
| `corpus_sync_state` and `corpus_file_state` tables exist | `sqlite3 data/runtime.db ".tables"` | ⬜ |
| Incremental sync fetches only changed files on second run | Manual test: run twice, observe GitHub API call count | ⬜ |
| Sync is resumable: crash mid-run, re-run picks up from checkpoint | Manual test | ⬜ |
| Rate-limit backoff fires when `X-RateLimit-Remaining: 0` | Unit test with mock response | ⬜ |
| Two stable sync cycles completed without data loss | Log inspection | ⬜ |

### Gate G: Architecture Fitness Tests

| Criterion | Verified By | Status |
|---|---|---|
| All architecture tests pass | `pytest tests/architecture/ -v` | ⬜ |
| `test_kernel_does_not_import_api_directly` passes with empty REGISTERED_ARCHITECTURAL_DEBT | Requires Gate E completion | ⬜ |
| `test_api_main_line_count_within_budget` passes | `wc -l api/main.py` ≤ 2600 | ⬜ |
| No circular imports in kernel | `pytest test_no_circular_imports_in_kernel` | ⬜ |

---

## Phase 1 Exit Declaration

Phase 1 is complete when **all gates A through G are closed**.

The Principal Engineer updates this document to `Status: CLOSED` with the closing date and a reference to the final Continuation Ledger of the phase.

Phase 2 begins immediately after Phase 1 is declared closed.

---

## Phase 2 Preview (Scope Not Final)

Phase 2 gates will be defined at the start of Phase 2 from the Phase 2 brief.
Known candidates based on Phase 1 "what this does not address" lists:

- `api/main.py` decomposition (currently 2506 lines)
- Client-side `isSovereign` flag enforcement
- Frontend Oracle request timeout
- Plugin filesystem discovery / hot-reload
- Canonical domain model definition (ADR-016)
- Oversoul Prism integration design

---

## Operating Rules

1. **Gates are additive** — once a gate is marked ✅ it is not reopened unless a regression is detected.
2. **Gates are objective** — "we think it's probably done" is not a closed gate. The verification method must produce a clear pass/fail result.
3. **New gates can be added within a phase** — but only by Principal Engineer session with ADR update. The gate list is not a to-do list that anyone can extend informally.
4. **The Continuation Ledger tracks gate status** — every session updates the current gate states before closing.
