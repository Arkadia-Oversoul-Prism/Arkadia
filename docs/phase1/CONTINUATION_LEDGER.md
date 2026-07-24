# Arkadia — Continuation Ledger

**Session date:** ARK Y1 · D116 (2026-07-24)  
**Principal Engineer session type:** Phase 1 Analysis — NO CODE CHANGES  
**Next session starting point:** → See "Recommended Starting Point" below

---

## Session Summary

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
| SQLite Job Queue Design | `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` | ✅ Complete |
| Plugin Registry Specification | `docs/phase1/PLUGIN_REGISTRY_SPEC.md` | ✅ Complete |
| Observability Design | `docs/phase1/OBSERVABILITY_DESIGN.md` | ✅ Complete |
| Corpus Sync Design | `docs/phase1/CORPUS_SYNC_DESIGN.md` | ✅ Complete |
| ADR-014 (Phase 1 decisions) | `docs/adr/ADR-014-phase1-kernel-stabilisation.md` | ✅ Filed (Proposed) |

**All pre-implementation deliverables are complete. Implementation is blocked pending approval of these documents.**

---

## Outstanding Work (Phase 1 Implementation — Not Started)

### Workstream B — Runtime Durability (Highest Priority)
- [ ] Create `data/runtime.db` with schema from `SQLITE_JOB_QUEUE_DESIGN.md`
- [ ] Implement `kernel/storage/sqlite_job_store.py`
- [ ] Implement `kernel/storage/sqlite_goal_store.py`
- [ ] Migration: JSON → SQLite import on first startup
- [ ] Update `kernel/jobs.py` and `kernel/goals.py` to use new backends
- [ ] Tests: `test_sqlite_job_store.py`, `test_sqlite_goal_store.py`, `test_jobs_migration.py`
- [ ] Extract Firebase sync from `JobStore`/`GoalStore` into separate sync adapter

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

### Workstream C — Corpus Synchronisation (Fifth Priority)
- [ ] Add `corpus_sync_state` and `corpus_file_state` tables to `data/runtime.db`
- [ ] Implement `github_corpus_incremental.py`
- [ ] Validate with two live sync cycles
- [ ] Switch `/api/sync` endpoint to incremental version
- [ ] Remove legacy `github_corpus.py` code (two weeks after stable operation)

---

## Modified Files This Session

**None.** This was an analysis-only session.

---

## Open ADRs

| ADR | Status | Waiting on |
|---|---|---|
| ADR-013 Phase 0 Security | Accepted | Nothing — complete |
| ADR-014 Phase 1 Kernel Stabilisation | **Proposed** | Flamekeeper approval before implementation begins |
| ADR-015 Kernel Port Interfaces | Pending | ADR-014 approval; design in progress |

---

## Architecture Decisions Made This Session (Not Requiring ADR Updates)

1. `data/runtime.db` is the correct SQLite path for job/goal/corpus-sync state — separate from `knowledge/arkadia.db` to avoid coupling runtime state to knowledge state.
2. Firebase sync extraction: implement as a "sync adapter" registered at FastAPI startup via dependency injection — not embedded in `JobStore`.
3. `contextvars.ContextVar` is the correct propagation mechanism for `request_id` / `execution_id` across async routes and daemon worker threads.
4. Workstream priority order: B → E → D → A → C (highest architectural risk first; observability early to support debugging the other workstreams).

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

**Read this file first.** Then:

1. Confirm ADR-014 is approved (status: Accepted) before writing any code.
2. Begin with **Workstream B, Step 1**: create `data/runtime.db` schema.
   - File: `kernel/storage/` (new directory)
   - Reference: `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` → "Schema" section
3. After schema, implement `SQLiteJobStore` — preserve the public API exactly.
4. Run the migration test before touching `kernel/jobs.py`.

**Do not start Workstream E or A until Workstream B tests pass and the repository is verified deployable.**

---

## Architectural Laws (Never Violate)

1. One capability. One implementation. One canonical home.
2. Local First. Cloud sync is additive. Never required.
3. Markdown is the human format. SQLite is the machine format.
4. Oracle retrieves knowledge. Providers generate language.
5. Every subsystem must have a single responsibility.
6. (Phase 0 addition) The kernel must never import from the API layer.
7. (Phase 1 addition) Every commit must leave the repository deployable.
