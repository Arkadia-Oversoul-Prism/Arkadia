# Session Handoff — K1
> Copy this file as the opening message to the next session.

---

## Completed
- Phase 0 — Endpoint migration: all active `arkadia-n26k` → `arkadia-kw64` references updated ✅
- Workstream B — SQLite durability complete; Gate B CLOSED ✅
- Backend LIVE: https://arkadia-kw64.onrender.com ✅
- Knowledge OS recon complete: `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` ✅
- K2 — Oracle Conversation Archival: daemon thread archives every Oracle turn into the Knowledge Layer ✅

## ⚠ One manual action still pending (does not block K1)
`web/public_prism/.env.production` → `VITE_API_URL` must be updated to `https://arkadia-kw64.onrender.com` by the user in Vercel dashboard before next frontend deploy.

## This Session: K1 — Corpus Document Ingestion
**Read `MISSION.md` first.** It has everything.

Quick version: After corpus documents are stored/synced, call `knowledge/pipeline.ingest()` in a daemon thread so the Knowledge Graph becomes aware of document content. The duplicate-detection inside `pipeline.ingest()` makes this idempotent.

---

## Your Startup (Maximum 5 minutes)

1. Read `MISSION.md`
2. Read `.bootstrap/01_STATE.md`
3. Read `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` → "K1" section only
4. Run `pytest tests/architecture -q` — confirm 10/10
5. Read `corpus/manager.py` (find where documents are stored after upload/sync)
6. Read `api/main.py` corpus upload/sync endpoint(s)
7. Implement K1
8. Run pre-push checklist (see MISSION.md)
9. Run verification
10. Update `MISSION.md`, `.bootstrap/01_STATE.md`, `NEXT_AGENT.md`
11. Commit and push
12. Stop

## Do NOT Open
- ENGINEERING_PRINCIPLES.md, ROADMAP.md, ARCHITECTURE_MAP.md, PHASE_GATES.md, any ADR
- CONTINUATION_LEDGER.md at startup (update it at session end only)

## Architecture is frozen. Connect, don't rebuild.
