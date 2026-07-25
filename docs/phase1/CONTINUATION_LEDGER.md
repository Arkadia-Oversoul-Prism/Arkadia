# Arkadia — Continuation Ledger

---

## Session: B0.5 — Baseline Integrity

**Session date:** ARK Y1 · D116 (2026-07-24)  
**Role:** Architecture Steward  
**Session type:** Workstream B0.5 — Calibration and Debt Registration (NO implementation code changed)  
**Next session starting point:** Begin Workstream B1 — Persistence Foundation

### Session Summary

This session executed the three-commit B0.5 plan:

1. **Commit 1 — Calibration:** Fixed the inverted enforcement condition in `test_no_layer_inversions` (`imported_layer > importer_layer` → `imported_layer < importer_layer`). Added `REGISTERED_CIRCULAR_DEBT` debt-registry mechanism to `LAYER_MAP.py` and `test_no_circular_imports_in_kernel`. Fixed internally inconsistent dependency-direction docstring in `LAYER_MAP.py`. Added `ENGINEERING_PRINCIPLES.md` Principle 11: "Reality Overrides Documentation."

2. **Commit 2 — Debt Registration:** Registered all discovered architectural violations in `REGISTERED_ARCHITECTURAL_DEBT` and `REGISTERED_CIRCULAR_DEBT` with owner, workstream, and exit criterion. Four violations were newly discovered that were not in the original calibration report (see Debt Registry below).

3. **Post-acceptance refinement:** Renamed `ALLOWED_VIOLATIONS` → `REGISTERED_ARCHITECTURAL_DEBT` and `ALLOWED_CIRCULAR_IMPORTS` → `REGISTERED_CIRCULAR_DEBT` throughout `LAYER_MAP.py` and `test_layer_boundaries.py`. Added explicit freeze rule to `LAYER_MAP.py`. Language now reflects intent: these entries are scheduled liabilities, not granted permissions.

3. **Commit 3 — Governance Synchronization:** Updated this Ledger; corrected the Open ADRs table; froze the baseline.

**Architecture fitness tests: 10/10 passing.**  
**No implementation code was touched.**

---

## Session: Phase 1 Analysis

**Session date:** ARK Y1 · D116 (2026-07-24)  
**Role:** Architecture Steward (elevated from Principal Engineer at Phase 1 implementation inflection)  
**Session type:** Phase 1 Analysis — NO CODE CHANGES  
**Next session starting point:** → See "Recommended Starting Point" below

### Session Summary

This session:
1. Verified Phase 0 security hardening (ADR-013) is fully implemented and matches spec.
2. Produced all seven Phase 1 pre-implementation deliverables.
3. Filed ADR-014 (Phase 1 constitutional decisions).

**No code was changed. No new features were added. The repository is in the same state as at session start.**

---

## Phase 0 Verification Status

| Decision | File | Status |
|---|---|---|
| Shell allowlist + path-separator guard + `shell=False` | `kernel/tools_real.py` | ✅ Verified |
| Excluded: `env`, `find`, `git`, `python`, `pip`, `cp`, `mv` | `kernel/tools_real.py` | ✅ Verified |
| Write path: canonical validation + symlink walk + O_NOFOLLOW | `kernel/tools_real.py` | ✅ Verified |
| Auth fail-fast — production startup error if Firebase missing | `api/auth.py` | ✅ Verified |
| Sovereign fail-fast — `RuntimeError` at module load if production | `api/main.py` | ✅ Verified |
| CORS explicit origins — wildcard banned, production locked | `api/main.py` | ✅ Verified |
| ADR-013 filed and status=Accepted | `docs/adr/ADR-013-*.md` | ✅ Verified |

**Phase 0 is complete and intact. Do not revisit.**

---

## Phase 1 Deliverables Status

| Deliverable | File | Status |
|---|---|---|
| Responsibility Matrix | `docs/phase1/RESPONSIBILITY_MATRIX.md` | ✅ Complete |
| Dependency Graph + Coupling Report | `docs/phase1/DEPENDENCY_GRAPH.md` | ✅ Complete |
| Runtime State Diagram | `docs/phase1/RUNTIME_STATE_DIAGRAM.md` | ✅ Complete |
| Architecture Map | `docs/phase1/ARCHITECTURE_MAP.md` | ✅ Complete |
| SQLite Job Queue Design | `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` | ✅ Complete |
| Plugin Registry Specification | `docs/phase1/PLUGIN_REGISTRY_SPEC.md` | ✅ Complete |
| Observability Design | `docs/phase1/OBSERVABILITY_DESIGN.md` | ✅ Complete |
| Corpus Sync Design | `docs/phase1/CORPUS_SYNC_DESIGN.md` | ✅ Complete |
| Architecture Fitness Tests | `tests/architecture/test_layer_boundaries.py` | ✅ Complete |
| Layer Map | `tests/architecture/LAYER_MAP.py` | ✅ Complete |
| Phase Gates | `docs/phase1/PHASE_GATES.md` | ✅ Complete |
| ADR-014 (Phase 1 decisions) | `docs/adr/ADR-014-phase1-kernel-stabilisation.md` | ✅ Filed (Accepted) |
| ADR-015 (Dependency Direction Rule) | `docs/adr/ADR-015-dependency-direction-rule.md` | ✅ Filed (Accepted) |

**All pre-implementation deliverables are complete. Phase 0 and Phase 1 Analysis approved by Flamekeeper (2026-07-24). Implementation may begin.**

---

## Session: Infrastructure — Railway Migration

**Session date:** ARK Y1 · D117 (2026-07-25)
**Role:** Infrastructure Steward
**Session type:** Infrastructure — Railway deployment configuration (NO application code changed)
**Next session starting point:** Begin C1.2 — Incremental Sync Engine

### Session Summary

Render free-tier allocation exhausted. Backend migrated to Railway.

**Files created:**
- `railway.json` (root) — DOCKERFILE builder, `healthcheckPath: /api/heartbeat`, restart-on-failure policy
- `docs/deployment/RAILWAY.md` — full operator guide: env vars, persistent volume setup, migration from Render, rollback procedure

**No application code was modified.** `entrypoint.sh`, `Dockerfile`, `api/main.py`, and all kernel files are untouched.

**Architecture fitness tests: 10/10 passing (unchanged).**

### Operator Actions Still Required

The following must be completed by the project operator in the Railway dashboard before the backend is live:

1. Create a Railway service from this GitHub repo (Railway detects `railway.json` automatically).
2. Set required environment variables: `ENVIRONMENT`, `SOVEREIGN_KEY`, `GOOGLE_API_KEY`, `CORS_ALLOWED_ORIGINS`.
3. Add a persistent volume mounted at `/arkadia-data`.
4. Set `SOLSPIRE_DATA_DIR=/arkadia-data` and `ARKADIA_DB_PATH=/arkadia-data/arkadia.db`.
5. Update frontend `ORACLE_URL` references from the old Render domain to the new Railway domain.

See `docs/deployment/RAILWAY.md` for full steps.

---

## Session: B1.1 — SQLite Schema

**Session date:** ARK Y1 · D116 (2026-07-24)
**Role:** Architecture Steward
**Session type:** Workstream B1.1 — Persistence Foundation, Schema checkpoint
**Next session starting point:** Begin B1.2 — SQLiteJobStore

### Session Summary

Created the `kernel/storage/` package and the SQLite runtime database schema.

**Files created:**
- `kernel/storage/__init__.py` — package marker
- `kernel/storage/schema.py` — DDL constants + `create_tables(db_path)` (idempotent, WAL mode)
- `tests/test_sqlite_schema.py` — 11 tests covering table existence, all columns, all indexes, WAL mode, idempotency, CHECK constraints, and return value

**Verification:**
- `pytest tests/test_sqlite_schema.py` — **11/11 passing**
- `pytest tests/architecture/` — **10/10 passing** (unchanged)

**No other files were touched.** `kernel/jobs.py`, `kernel/goals.py`, `kernel/worker.py`, and all API files are unmodified.

---

## Outstanding Work (Phase 1 Implementation)

### Workstream B — Runtime Durability (Highest Priority)
- [x] **B1.1 CLOSED** — `kernel/storage/` + schema (commit `1a38633`; 21/21 tests; see `docs/checkpoints/B1.1.md`)
- [ ] **B1.2** — Implement `kernel/storage/sqlite_job_store.py` + `kernel/storage/sqlite_goal_store.py`
- [ ] **B1.3** — Migration: JSON → SQLite import on first startup; update `kernel/jobs.py` and `kernel/goals.py`
- [ ] **B1.4** — Remove legacy code; close Gate B; extract Firebase sync adapter

### Workstream E — Plugin Architecture (Second Priority)
- [ ] Implement `kernel/plugin_registry.py` (PluginRegistry, PluginManifest)
- [ ] Update `register_tool()` to accept optional manifest
- [ ] Add manifests to all existing tool registrations
- [ ] Update `execute_intent()` to use `registry.is_allowed()` instead of `ALLOWED_TYPES`
- [ ] Update `select_tool()` to delegate to registry
- [ ] Test: `test_plugin_registry.py`
- [ ] Remove `ALLOWED_TYPES` after all callers migrated

### Workstream D — Observability (Third Priority)
- [ ] Implement `kernel/observability.py` (StructuredLogger, context vars)
- [ ] Add `request_id` middleware to `api/main.py`
- [ ] Instrument `execute_intent()` with JOB_STARTED/COMPLETED/FAILED events
- [ ] Instrument `kernel/planner.py` with PLAN_STARTED/GENERATED/PROVIDER_CALLED events
- [ ] Instrument `kernel/memory.py` with KNOWLEDGE_RETRIEVED event
- [ ] Instrument `kernel/worker.py` with JOB_CLAIMED event
- [ ] Tests: `test_observability.py`

### Workstream A — Layer Violation Remediation (Fourth Priority)
- [ ] Remove `kernel/agents.py → api.arkadia_engine` dependency
- [ ] Remove `kernel/planner.py → api.key_manager` dependency
- [ ] Remove `kernel/tools_real.py → api.key_manager` dependency
- [ ] Extract Firebase sync adapters from kernel layer
- [ ] Verify: `import kernel.execution` does not load any `api/` module

### Workstream C — Corpus Synchronisation (Active)
- [x] **C1.1 CLOSED** — schema extension: `corpus_sync_state` + `corpus_file_state` tables (13 tests; see `docs/checkpoints/C1.1.md`)
- [ ] **C1.2** — Implement `github_corpus_incremental.py` (SHA comparison, rate-limit backoff, per-file checkpoint)
- [ ] **C1.3** — Switch `/api/sync` endpoint to `incremental_sync()`
- [ ] **C1.4** — Cleanup: remove `github_corpus.py` after two stable cycles; close Gate F

---

## Modified Files This Session

**None.** This was an analysis-only session.

---

## Open ADRs

| ADR | Status | Waiting on |
|---|---|---|
| ADR-013 Phase 0 Security | Accepted | Nothing — complete |
| ADR-014 Phase 1 Kernel Stabilisation | **Accepted** | Nothing — approved by Flamekeeper 2026-07-24 |
| ADR-015 Dependency Direction Rule | **Accepted** | Nothing — approved by Flamekeeper 2026-07-24 |

*(Note: the previous version of this table incorrectly showed ADR-014 as "Proposed" and ADR-015 as "Pending". Both ADR files show Accepted. Corrected in B0.5 governance sync per Principle 11.)*

---

## Architecture Decisions Made This Session (Not Requiring ADR Updates)

1. `data/runtime.db` is the correct SQLite path for job/goal/corpus-sync state — separate from `knowledge/arkadia.db` to avoid coupling runtime state to knowledge state.
2. Firebase sync extraction: implement as a "sync adapter" registered at FastAPI startup via dependency injection — not embedded in `JobStore`.
3. `contextvars.ContextVar` is the correct propagation mechanism for `request_id` / `execution_id` across async routes and daemon worker threads.
4. Workstream priority order: B → E → D → A → C (highest architectural risk first; observability early to support debugging the other workstreams).

---

## Architectural Debt Registry (B0.5 Baseline)

All entries are registered in `tests/architecture/LAYER_MAP.py` (`REGISTERED_ARCHITECTURAL_DEBT` or `REGISTERED_CIRCULAR_DEBT`). Each entry has an owner, workstream, and exit criterion. Removing an entry from the registry is the exit criterion — not just fixing the code.

### Layer Inversions (registered in REGISTERED_ARCHITECTURAL_DEBT)

| Importer | Imported | Violation | Workstream | Exit Criterion |
|---|---|---|---|---|
| `kernel/agents.py` | `api` | kernel→api: generate_verse | A | `grep "from api" kernel/agents.py` empty |
| `kernel/planner.py` | `api` | kernel→api: key_manager | A | `grep "from api" kernel/planner.py` empty |
| `kernel/tools_real.py` | `api` | kernel→api: key_manager | A | `grep "from api" kernel/tools_real.py` empty |
| `kernel/jobs.py` | `api` | kernel→api: firebase_store | A | `grep "from api" kernel/jobs.py` empty |
| `kernel/goals.py` | `api` | kernel→api: firebase_store | A | `grep "from api" kernel/goals.py` empty |
| `kernel/tts.py` | `api` | kernel→api: tts_key_manager *(new — B0.5)* | A | `grep "from api" kernel/tts.py` empty |
| `api/nodes.py` | `kernel` | identity→runtime: kernel.tools *(new — B0.5)* | A | `grep "from kernel" api/nodes.py` empty |
| `api/main.py` | `solspire` | api→presentation: console_router *(new — B0.5)* | A | `grep "solspire" api/main.py` empty |
| `providers/` | `api` | provider→api: key_manager/provider_key_store *(new — B0.5)* | A | `grep -rn "from api" providers/` empty |
| `providers/router.py` | `knowledge` | orthogonal: provider→knowledge *(new — B0.5)* | A | `grep "knowledge" providers/router.py` empty |

### Circular Imports (registered in REGISTERED_CIRCULAR_DEBT)

| Cycle | Notes | Workstream | Exit Criterion |
|---|---|---|---|
| `kernel.execution → kernel.tools → kernel.execution` | *(new — B0.5)* | A | Test passes with entry removed |
| `kernel.execution → kernel.planner → kernel.execution` | *(new — B0.5)* | A | Test passes with entry removed |

**Total registered debt:** 10 layer violations + 2 circular import cycles = **12 entries**  
**Previously documented:** 5 | **Newly discovered in B0.5:** 7  
**All assigned to:** Workstream A, Phase 1 Gate E

---

## Known Risks

| Risk | Severity | Mitigation |
|---|---|---|
| SQLite migration: JSON import data integrity | HIGH | Dedicated migration test (`test_jobs_migration.py`) required before cutover |
| `api/main.py` is 2506 lines — any large edit is high-risk | HIGH | Do not touch main.py for anything other than the middleware addition (Workstream D) and Firebase sync extraction (Workstream A) |
| Daemon threads have no graceful drain on shutdown | LOW | Acceptable for current scale; document and defer |
| `ALLOWED_TYPES` alias period: two authoritative sources temporarily | MEDIUM | Set a deadline — remove within the same PR sprint as the plugin registry ships |
| Corpus first run after migration fetches all files (no prior SHA state) | LOW | Expected and acceptable; log clearly |

---

## Environment State

- **Three workflows are failing** (`Arkadia Oracle Temple`, `Arkadia Frontend`, `Arkadia Discord Bot`). This is a pre-existing condition unrelated to this session. No code was changed. The workflows require secrets (`GOOGLE_API_KEY`, `DISCORD_BOT_TOKEN`, etc.) which are not set.
- **No secrets are configured** beyond `SESSION_SECRET`. The backend will fail with `ImportError` or missing-key warnings on start. This does not block Phase 1 analysis work.

---

## Recommended Starting Point for Next Session

**The next session operates under the Architecture Steward framework.** The full charter is at `.agents/memory/architecture-steward.md`. Key rules:
- First responsibility: protecting the architecture. Second: delivering working software. Never reverse.
- Session start checklist is mandatory before writing any code.
- Change budget: one bounded context, one ADR, one migration, one deployable checkpoint.
- Session end: all 8 deliverables required. Architecture fitness tests must pass before Continuation Ledger can be marked complete.

**Session start checklist:**
1. Read this Continuation Ledger.
2. Read ADR-013, ADR-014, ADR-015.
3. Read `docs/phase1/PHASE_GATES.md`.
4. Run `pytest tests/architecture/` — confirm no new regressions (10 entries in REGISTERED_ARCHITECTURAL_DEBT + 3 in REGISTERED_CIRCULAR_DEBT are expected and documented).
5. Restate the session objective in one paragraph.

**Then begin Workstream B — structured as four independently mergeable checkpoints:**

### B1 — Persistence Foundation
- Create `kernel/storage/` directory
- Write SQLite schema from `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` → "Schema" section
- Write and run migration tests
- **Exit criteria:** schema exists, migrations pass, nothing else touched

### B2 — SQLiteJobStore
- Implement `SQLiteJobStore` — preserve the public API of `kernel/jobs.py` exactly
- Atomic job claiming (UPDATE … WHERE status='pending' RETURNING)
- Crash-safe persistence, restart recovery
- All lifecycle transitions tested
- **Exit criteria:** SQLiteJobStore tests pass; `kernel/jobs.py` still uses the old store

### B3 — Worker Integration
- Replace `kernel/jobs.py` in-memory queue with `SQLiteJobStore`
- Run restart simulation
- Run concurrent claim simulation
- **Exit criteria:** worker uses SQLite; restart/concurrency tests pass; repository deployable

### B4 — Cleanup
- Remove legacy in-memory queue code
- Update ADR-014 (if schema differed from design)
- Update `docs/phase1/ARCHITECTURE_MAP.md`
- Update this Continuation Ledger
- Run all architecture fitness tests; REGISTERED_ARCHITECTURAL_DEBT must not have grown
- **Exit criteria:** Gate B closed per `PHASE_GATES.md`

Each checkpoint is deployable, testable, and independently reversible.

**Standing question:** "What is the smallest architectural change that unlocks the next phase?"

**Do not start Workstream E or A until B4 is complete and Gate B is closed.**

---

## Architectural Laws (Never Violate)

1. One capability. One implementation. One canonical home.
2. Local First. Cloud sync is additive. Never required.
3. Markdown is the human format. SQLite is the machine format.
4. Oracle retrieves knowledge. Providers generate language.
5. Every subsystem must have a single responsibility.
6. (Phase 0 addition) The kernel must never import from the API layer.
7. (Phase 1 addition) Every commit must leave the repository deployable.
