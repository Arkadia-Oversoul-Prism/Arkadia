---
name: Session Infrastructure
description: The 6-file startup system that replaces the 10-document session ritual. How agents orient and hand off efficiently.
---

# Session Infrastructure

## The Startup Protocol

Every agent session reads exactly these, in order:
1. `BOOTSTRAP.md` — frozen rules, operating mode, thinking budget, immutable doc list
2. `CURRENT_STATE.md` — current checkpoint, objective, scope, stop condition
3. `ACTIVE_CONTEXT.md` — session scratchpad: files to create, files to read, stop condition
4. `pytest tests/architecture/ -v` — verify 10/10
5. Implement. Verify once. Stop.

## True Current State (as of 2026-07-25)
- Railway deployment done: `railway.json` + `docs/deployment/RAILWAY.md`
- All 21 recon docs exist in `docs/recon/`
- `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` written (K workstream plan)
- `DEPLOYMENT_OPTIONS.md` written (Fly.io ⭐ recommended; awaiting user decision)
- Next implementation: B1.1 — SQLite Schema

## The 6 Files

| File | Purpose | Updated when |
|---|---|---|
| `BOOTSTRAP.md` | Immutable rules + operating modes + thinking budget | ADR changes or new phase |
| `CURRENT_STATE.md` | Live checkpoint state | End of every session |
| `ACTIVE_CONTEXT.md` | Session scratchpad | Rewritten every session |
| `NEXT_AGENT.md` | Auto-generated handoff prompt | End of every session |
| `DECISION_CACHE.md` | Why decisions were made — stops re-litigation | When a new ADR is filed |
| `PROJECT_INDEX.md` | Repository map — prevents tree exploration | When a new module is added |

## Immutable Documents (never reread unless changed)

These are frozen. BOOTSTRAP.md summarizes them. Skip unless git shows a diff:
- ENGINEERING_PRINCIPLES.md
- ROADMAP.md
- docs/phase1/ARCHITECTURE_MAP.md
- docs/adr/ADR-013, ADR-014, ADR-015

## Operating Modes

**Build mode** (default): implement one checkpoint. Cannot touch ADRs, fitness tests, governance docs.
**Calibration mode** (rare): fix governance or measurement system. Cannot touch runtime code.

**Why:** Prevents governance work from bleeding into implementation sessions and vice versa.

## Thinking Budget

Architecture 5% / Coding 80% / Testing 10% / Documentation 5%.
If architecture thinking exceeds 5%, the session is off-track.
