# Session Handoff
> Copy this file as the opening message to the next session.
> Rewrite it at the end of every session.

---

## Completed
- B0.5 — Baseline Integrity (fitness tests fixed, debt registered)
- Infrastructure: `railway.json` + `docs/deployment/RAILWAY.md` (Railway deploy config)
- Analysis: `DEPLOYMENT_OPTIONS.md` (Fly.io ⭐ vs Koyeb vs Local+Cloudflare Tunnel comparison)
- Analysis: `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` (Knowledge OS synthesis — Workstream K plan)
- Session infrastructure: `.bootstrap/`, `PARKING_LOT.md`, `REPOSITORY_SNAPSHOT.md`

## Awaiting User Decision
- **Deployment platform**: Fly.io (recommended), Koyeb, or Local + Cloudflare Tunnel — user must choose before running infrastructure agent
- **Workstream K start**: K2 (Oracle Conversation Archival) is ready after B1 complete

## Not Started
- **B1.1 — SQLite Schema** ← implement this session

---

## Your Startup (follow exactly, in order)

1. Read `.bootstrap/00_BOOT.md`
2. Read `.bootstrap/01_STATE.md`
3. Read `.bootstrap/03_SCOPE.md`
4. Run: `pytest tests/architecture/ -v` — confirm 10/10
5. Implement B1.1 (see `03_SCOPE.md`)
6. Run verification once (see `.bootstrap/04_SUCCESS.md`)
7. Update `.bootstrap/01_STATE.md`, `03_SCOPE.md`, `04_SUCCESS.md`
8. Rewrite `NEXT_AGENT.md` for B1.2
9. Stop

## Do NOT Open
- ENGINEERING_PRINCIPLES.md, ROADMAP.md, ARCHITECTURE_MAP.md, PHASE_GATES.md, any ADR
- CONTINUATION_LEDGER.md (update it at session end, don't read it at start)
- `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` (already internalized — check DECISION_CACHE.md)

## Architecture is frozen. Do not challenge it. Obey it.

## Begin In
`kernel/storage/` — create directory, `__init__.py`, `schema.py`
Schema DDL source: `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md`

## Stop When
All items in `.bootstrap/04_SUCCESS.md` are checked.
