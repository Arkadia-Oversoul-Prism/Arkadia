# Arkadia Implementation Steward — Next Session Brief

## Status

| Item | State |
|---|---|
| CS1 — Conversational Spine (Oracle/Arkana) | **COMPLETE** |
| K3-A — Canonical Ontology | **COMPLETE** |
| K3-B — Operational Graph | **COMPLETE** |
| K3-C — Semantic Enrichment | **COMPLETE** |
| Architecture tests | **10/10 PASSING** |
| Spine continuity tests | **4/4 PASSING** (`tests/test_oracle_spine.py`) |
| Frontend typecheck | **PASSING** (changed files, zero errors) |
| Ontology | **FROZEN** — do not modify `node_types.py` or `relationship_types.py` |
| api/main.py | **AT BUDGET** — 2600 lines; do not add inline logic; use router modules |

## Canonical principle now in force

**ONE INTELLIGENCE SPINE. MANY INTERFACES.** The Oracle is the capability;
Arkana is the persona; the Knowledge OS is the memory substrate. Oracle Chat,
ReasoMate, and NovaNet are windows onto the same runtime — they must NOT
become separate chatbots or separate memories. Do not create a second memory
system, a second Oracle endpoint, or a parallel social database.

## What CS1 Delivered

- `api/oracle_spine.py` — conversational spine: `resolve_thread_id`,
  `retrieve_arkana_context`, `build_memory_block`, `archive_oracle_turn`
  (now uses `ingest_conversation()` with thread linkage).
- `knowledge/vault.py` — `get_or_create_thread` / `get_thread_id`
  (session_id ↔ threads.id).
- `api/main.py` — `/api/commune/resonance` retrieves Knowledge OS context
  via `assemble_context()` (distinct from corpus RAG) and archives turns
  with thread linkage; response now includes a `memory` diagnostic object.
- `web/public_prism/src/lib/arkanaSession.ts` — shared, interface-independent
  session id resolver (uid → sovereign token → stable guest id).
- `ArkanaCommune.tsx`, `ReasoMatePage.tsx`, `NovaNetPage.tsx` — each now
  sends `session_id` in the resonance body (one-line additive change each;
  no UI redesign).
- Corrected stale active Render endpoint in `.replit` and `.env.production`.

## Recommended next checkpoint — CS2: Reusable conversational UI

The Oracle Chat UI is the reference interaction experience and must be
preserved, not rebuilt. The next checkpoint extracts/generalises its proven
capabilities (TTX, canvas/full-display, rich response presentation, response
controls) into a reusable conversational component boundary, informed by the
Arkana Pattern Intelligence Chat and ReasoMate messenger patterns — so all
surfaces inherit ONE canonical chat shell over the same spine. Do NOT flatten
to a generic chat box; do NOT rebuild the Oracle UI from scratch.

Out of scope for CS2 (later checkpoints): NovaNet localStorage→server message
persistence, ReasoMate standalone routing, Encyclopedia/Codex duplicate-
surface reconciliation, NovaNet sample-data removal. Do not start these
inside CS2.

## Your Startup Protocol (Maximum 5 minutes)

1. Read `MISSION.md`
2. Read `CURRENT_STATE.md`
3. Run `python3 -m pytest tests/architecture -q` — confirm **10/10**
4. Run `python3 -m pytest tests/test_oracle_spine.py -q` — confirm **4/4**
5. Implement next checkpoint
6. Update `CURRENT_STATE.md`, `NEXT_AGENT.md`, `docs/phase1/CONTINUATION_LEDGER.md`
7. Commit and push
8. Stop

## Do NOT Open at Startup

- ENGINEERING_PRINCIPLES.md, ROADMAP.md, ARCHITECTURE_MAP.md, PHASE_GATES.md, any ADR
- CONTINUATION_LEDGER.md (update at session end only)

## Hard Rules (permanent)

- Ontology frozen — no new node or relationship types without an approved checkpoint
- No new databases; no competing graph implementations; no second memory system
- api/main.py at 2600-line budget — any new startup logic must be compact
- No UI redesigns — extend only (the Oracle Chat UI is sacred product work)
- No ADR or ROADMAP edits
