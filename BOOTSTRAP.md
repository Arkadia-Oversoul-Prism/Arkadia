# Arkadia — Agent Bootstrap
> Read this file first. Read CURRENT_STATE.md second. Then act.
> Do not read any other governance document unless this file explicitly tells you to.

---

## Current Phase
**Phase 1 — Runtime Stabilization**

Goal: Make the runtime correct before making it capable.
Status: B0.5 complete. B1 ready to begin.

---

## Operating Mode

Read CURRENT_STATE.md to determine which mode applies to this session.

### BUILD MODE (default)
You are implementing one checkpoint. Nothing else.

**May touch:** `kernel/storage/`, `data/`, tests for changed modules, Continuation Ledger.
**Must not touch:** ADRs, ENGINEERING_PRINCIPLES.md, ROADMAP.md, PHASE_GATES.md, ARCHITECTURE_MAP.md, fitness tests, LAYER_MAP.py.

If you notice something wrong in governance, record it in the Continuation Ledger. Do not fix it. Continue with the build objective.

### CALIBRATION MODE (rare)
You are fixing the governance layer or measurement system. No implementation code.

**May touch:** ADRs, fitness tests, LAYER_MAP.py, Ledger, BOOTSTRAP.md, CURRENT_STATE.md.
**Must not touch:** kernel/, api/, providers/, knowledge/, web/, bot/.

---

## Frozen Rules (do not re-derive, just obey)

1. Dependencies point from less stable → more stable layers. `api/ → kernel/` is permitted. `kernel/ → api/` is a violation. See LAYER_MAP.py for layer numbers.
2. The kernel must never import from api/. (ADR-015, Phase 1 Gate E)
3. Every commit must leave the repository deployable. (ADR-014)
4. One checkpoint per session. Stop when the checkpoint is complete.
5. Fitness tests must pass before the Continuation Ledger can be marked complete.
6. Reality overrides documentation. When they disagree, verify the code and update the docs. (Principle 11)

---

## Architectural Debt (current count)

**10 layer violations** + **3 circular import cycles** = 13 registered entries.
All in `tests/architecture/LAYER_MAP.py` (`REGISTERED_ARCHITECTURAL_DEBT`, `REGISTERED_CIRCULAR_DEBT`).
All assigned to Workstream A, Phase 1 Gate E.

**Do not fix any of these during B1.** They are registered. They will be addressed in Workstream A.

---

## B1 Vertical Slice Structure

B1 implements SQLite-backed job and goal persistence. Four independently deployable checkpoints:

| Checkpoint | Objective | Exit Criterion |
|---|---|---|
| **B1.1 — Schema** | Create `kernel/storage/` + SQLite schema from design doc | Schema file exists; migration test passes; nothing else touched |
| **B1.2 — SQLiteJobStore** | Implement `SQLiteJobStore`; `kernel/jobs.py` still uses old store | All unit tests pass; API contract unchanged |
| **B1.3 — Integration** | Replace in-memory queue with `SQLiteJobStore` in `kernel/jobs.py` | Restart sim + concurrency tests pass; repository deployable |
| **B1.4 — Cleanup** | Remove legacy code; update Ledger; close Gate B | `pytest tests/architecture/` green; Gate B closed |

**One checkpoint per session. Stop at the boundary.**

---

## DO NOT THINK ABOUT

- Future phases (2, 3, 4, 5)
- Observability, plugins, knowledge graph, corpus sync
- Refactoring unrelated modules
- The 13 registered debt entries
- The ADR-015 rationale — just obey it
- Architecture improvements outside the current checkpoint

If something outside scope appears worth fixing, add one line to the Continuation Ledger and continue. Do not implement it.

---

## Verification (run once, at the end)

```bash
pytest tests/architecture/ -v          # must be 10/10
pytest tests/test_sqlite_job_store.py  # or relevant test file for this checkpoint
```

Only run tests after the checkpoint implementation is complete. Do not run them between edits.

---

## Silent Operation

Report only when:
- A checkpoint is complete
- You are blocked and cannot continue
- A design decision requires input
- Tests fail unexpectedly

Do not narrate edits, reads, or routine actions.

---

## Consult Only If Needed

| Document | When to read it |
|---|---|
| `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` | B1.1: for the exact schema SQL |
| `docs/phase1/CONTINUATION_LEDGER.md` | End of session: to update it |
| `docs/phase1/PHASE_GATES.md` | When closing a gate |
| `kernel/jobs.py` | B1.2/B1.3: to match the existing public API exactly |
| `tests/architecture/LAYER_MAP.py` | Only if a fitness test fails |
| Any ADR | Only if a design decision requires a constitutional reference |

Do not read ENGINEERING_PRINCIPLES.md, ROADMAP.md, ADR-013, ADR-015, or ARCHITECTURE_MAP.md unless the Continuation Ledger explicitly references them for this checkpoint.
