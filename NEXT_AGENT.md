# Session Handoff
> Copy this entire file as the opening message to the next agent session.
> This file is rewritten at the end of every session.

---

## Completed This Session
- Infrastructure: Railway deployment configuration
  - `railway.json` (root) — DOCKERFILE builder, healthcheck `/api/heartbeat`, restart policy
  - `docs/deployment/RAILWAY.md` — full deployment guide: env vars, volume config, Render migration, rollback
  - No application code modified; 81/81 tests passing; architecture fitness 10/10

## Not Started
- C1.2 — Incremental Sync Engine (`github_corpus_incremental.py`)

---

## Your Startup (maximum 3 minutes, follow exactly)

1. Read `MISSION.md`
2. Read `BOOTSTRAP.md`
3. Read `CURRENT_STATE.md`
4. Run `python3 -m pytest tests/architecture/ -q` — confirm 10/10
5. Implement the objective in `CURRENT_STATE.md`
6. Run verification once
7. Update `MISSION.md`, `CURRENT_STATE.md`, `NEXT_AGENT.md`
8. Stop

## Do NOT Reopen
- ENGINEERING_PRINCIPLES.md, ROADMAP.md, ARCHITECTURE_MAP.md, PHASE_GATES.md
- Any ADR (ADR-010 through ADR-015)
- CONTINUATION_LEDGER.md (except to update at session end)
- ACTIVE_CONTEXT.md (superseded by MISSION.md)
- DECISION_CACHE.md (unless blocked by a design question)

## Key Files for C1.2
- `docs/phase1/CORPUS_SYNC_DESIGN.md` — full algorithm, schema, rate-limit spec
- `github_corpus.py` — existing full-tree sync; read to understand `should_ingest()` and `ingest_document()` signatures
- `kernel/storage/schema.py` — column reference for `corpus_sync_state` + `corpus_file_state`
- Pass `ARKADIA_DB_PATH` env var in tests to use a temp database

## Stop When
`pytest tests/test_corpus_sync_incremental.py` passes.
`pytest tests/architecture/` is 10/10.
`MISSION.md` updated to C1.3.
`CURRENT_STATE.md` updated to C1.3 ready.
This file rewritten for the C1.3 session.
