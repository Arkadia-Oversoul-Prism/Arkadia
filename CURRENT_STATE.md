# Arkadia — Current State
> Updated at the end of every session. The next agent reads this before anything else.
> If this file and another document disagree, verify the code. Update this file. (Principle 11)

---

## Phase
Phase 1 — Runtime Stabilization

## Checkpoint
**B1.1 — Schema** (READY TO BEGIN)

## Mode
BUILD

## Objective
Create `kernel/storage/` directory and the SQLite schema for the job/goal runtime database.
Source of truth for schema: `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` → "Schema" section.

## Scope (this checkpoint only)
- Create `kernel/storage/__init__.py`
- Create `kernel/storage/schema.py` (or `kernel/storage/migrations.py`) — schema DDL and `create_tables()` function
- Create `data/runtime.db` (or confirm it is created on first call to `create_tables()`)
- Write `tests/test_sqlite_schema.py` — verifies tables exist with correct columns

## Stop When
Schema file exists. Migration test passes. Nothing else has been touched.

## Do Not Touch
- `kernel/jobs.py` (B1.2)
- `kernel/goals.py` (B1.2)
- `kernel/worker.py` (B1.3)
- `api/` (any file)
- Fitness tests / LAYER_MAP.py
- ADRs / Governance docs

## Blocked By
Nothing.

## Repository Health
- Branch: `main`
- Fitness tests: 10/10 passing
- Registered debt: 10 layer violations + 3 circular imports (all in LAYER_MAP.py — do not touch)
- Workflows: failing (pre-existing — missing secrets, not a B1 blocker)

## Success Criteria (B1.1)
- [ ] `kernel/storage/` directory exists with `__init__.py`
- [ ] Schema DDL matches `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md`
- [ ] `pytest tests/test_sqlite_schema.py` passes
- [ ] `pytest tests/architecture/` still 10/10
- [ ] Repository deployable (no import errors introduced)
- [ ] Continuation Ledger updated

## Last Session
B0.5 — Baseline Integrity complete. Fitness tests fixed, debt registered, registry renamed from ALLOWED_VIOLATIONS → REGISTERED_ARCHITECTURAL_DEBT.

## Next Checkpoints (do not implement yet)
- B1.2 — SQLiteJobStore
- B1.3 — Worker Integration
- B1.4 — Cleanup / Gate B close
