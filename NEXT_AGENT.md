# Arkadia Implementation Steward — Next Session Brief

## Status

| Item | State |
|---|---|
| CS1 — Conversational Spine (Oracle/Arkana) | **COMPLETE** |
| CS1.1 — Production-proof BM25 retrieval repair | **COMPLETE** (Phase 4 Gate A PASSED) |
| K3-A — Canonical Ontology | **COMPLETE** |
| K3-B — Operational Graph | **COMPLETE** |
| K3-C — Semantic Enrichment | **COMPLETE** |
| K1 — Corpus Document Ingestion | **COMPLETE** |
| K5 — Static Ingestion | **COMPLETE** — `knowledge/static_ingestion.py`, lifespan-wired, 12 tests |
| K4 — Response Provenance | **NEXT** (workstream K) |
| Architecture tests | **11/11 PASSING** (reconciled 2026-09-28) |
| Spine continuity tests | **7/7 PASSING** (`tests/test_oracle_spine.py`) |
| Production proof (Gate A) | **PASSING** — thread jump verified on arkadia-kw64.onrender.com |
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

## Recommended next checkpoint — K4: Response Provenance

> **Divergence reconciled 2026-09-30.** This brief previously recommended CS2, while
> `.bootstrap/01_STATE.md` and `MISSION.md` tracked the live Workstream K sequence. Both
> could not be "next". The repository's active workstream is **K**, and its next
> checkpoint is **K4**; CS2 is recorded below as deferred, not discarded.

Workstream K is the active sequence. K1, K2, K3, and K5 are complete; **K4** is next.

**K4 — Response Provenance.** `knowledge/context_engine.assemble_context()` returns note
UUIDs alongside the text chunks it selects, but the Oracle response discards them — the
reader gets a confident answer with no way to tell which archived knowledge produced it.
Surface those identities as a `sources` array and render "Based on: ..." in the UI.

- Seam: `api/oracle_spine.py` already holds the full context package; extract identities
  into the existing `meta` diagnostics dict there. Do **not** add a second retrieval path.
- Response shape change is **additive** (`api/main.py` is at budget — keep it compact).
- UI renders conditionally: `web/public_prism/src/components/ArkanaCommune.tsx`.
- Verified starting state: no Oracle response path currently returns a `sources` array.

## Deferred — CS2: Reusable conversational UI

Preserved from the previous brief; not scheduled in this pass. The Oracle Chat UI is the
reference interaction experience and must be preserved, not rebuilt. CS2 extracts and
generalises its proven capabilities (TTX, canvas/full-display, rich response presentation,
response controls) into a reusable conversational component boundary so all surfaces
inherit ONE canonical chat shell over the same spine. Do NOT flatten to a generic chat
box; do NOT rebuild the Oracle UI from scratch.

Out of scope for CS2 (later checkpoints): NovaNet localStorage→server message
persistence, ReasoMate standalone routing, Encyclopedia/Codex duplicate-surface
reconciliation, NovaNet sample-data removal.

## Your Startup Protocol (Maximum 5 minutes)

1. Read `MISSION.md`
2. Read `CURRENT_STATE.md`
3. Run `python3 -m pytest tests/architecture -q` — confirm **11/11**
4. Run `python3 -m pytest tests/test_oracle_spine.py -q` — confirm **7/7**
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
