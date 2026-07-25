# Session Handoff — B1.1
> Copy this entire file as the opening message to the next session.
> This file is rewritten at the end of every session.

---

## Completed
- B0.5 — Baseline Integrity (fitness tests fixed, debt registered, registry renamed)
- Session infrastructure: `.bootstrap/`, PARKING_LOT.md, REPOSITORY_SNAPSHOT.md

## Not Started
- **B1.1 — SQLite Schema** (this is what you implement)

---

## Your Startup (follow exactly, in order)

1. Read `.bootstrap/00_BOOT.md`
2. Read `.bootstrap/01_STATE.md`
3. Read `.bootstrap/03_SCOPE.md`
4. Run: `pytest tests/architecture/ -v` — confirm 10/10
5. Implement the schema (see `03_SCOPE.md`)
6. Run verification (see `.bootstrap/04_SUCCESS.md`)
7. Update `.bootstrap/01_STATE.md`, `03_SCOPE.md`, `04_SUCCESS.md`
8. Rewrite `NEXT_AGENT.md` for B1.2
9. Stop

## Do NOT Open
- ENGINEERING_PRINCIPLES.md
- ROADMAP.md
- ARCHITECTURE_MAP.md
- PHASE_GATES.md
- Any ADR
- CONTINUATION_LEDGER.md (except to update at session end)

## Architecture is frozen. Do not challenge it. Obey it.

## Begin In
`kernel/storage/` — create the directory and schema file.
Schema DDL: `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md`

## Stop When
All items in `.bootstrap/04_SUCCESS.md` are checked.
