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
| K4 — Response Provenance | **COMPLETE** — PR #153 (`4a9281b`); 6 tests; record backfilled |
| Workstream K | **COMPLETE** — no K6 exists in the design doc |
| Architecture tests | **11/11 PASSING** (re-measured 2026-10-02) |
| Spine continuity tests | **7/7 PASSING** (`tests/test_oracle_spine.py`) |
| Production proof (Gate A) | **PASSING** — thread jump verified on arkadia-kw64.onrender.com |
| Frontend typecheck | **PASSING** (changed files, zero errors) |
| Ontology | **FROZEN** — do not modify `node_types.py` or `relationship_types.py` |
| api/main.py | **AT BUDGET** — 2600 lines; do not add inline logic; use router modules |
| Baseline full suite | **20F / 1240P / 17S / 1E** @ `64cbe74` — classified debt, see below |

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

## Workstream K is COMPLETE

K1, K2, K3, K4 and K5 are all shipped and all now carry a record under
`docs/checkpoints/`. The design doc `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` names no K6.

**K4 — Response Provenance** (the final checkpoint, shipped via PR #153 → `4a9281b`):
`knowledge/context_engine.assemble_context()` returns note UUIDs alongside the text chunks
it selects. K4 surfaces those identities as a `sources` array on the Oracle response and
renders "Based on: …" in the UI.

- Seam: `api/oracle_spine.py` holds the full context package; identities are derived there
  into the existing `meta` diagnostics dict. There is **no** second retrieval path.
- The response shape change is additive; `api/main.py` stayed at budget.
- UI renders conditionally in `web/public_prism/src/components/ArkanaCommune.tsx`.
- Record: `docs/checkpoints/K4_response_provenance.md`.

> **Divergence reconciled 2026-10-02.** This brief previously recommended K4 as "next",
> which was itself stale — K4 had already shipped. Both this file and `MISSION.md` now
> report Workstream K as complete. (An earlier 2026-09-30 note reconciled a *different*
> divergence, where this brief recommended CS2 while the K sequence was still live. That
> note is superseded: the K sequence has now finished.)

## Recommended next workstream — CS2: Reusable conversational UI

**Recommendation only. Beginning CS2 requires a sovereign decision** — it is a product
scope expansion beyond the completed Workstream K.

The Oracle Chat UI is the reference interaction experience and must be preserved, not
rebuilt. CS2 extracts and generalises its proven capabilities (TTX, canvas/full-display,
rich response presentation, response controls) into a reusable conversational component
boundary so all surfaces inherit ONE canonical chat shell over the same spine. Do NOT
flatten to a generic chat box; do NOT rebuild the Oracle UI from scratch.

Out of scope for CS2 (later checkpoints): NovaNet localStorage→server message
persistence, ReasoMate standalone routing, Encyclopedia/Codex duplicate-surface
reconciliation, NovaNet sample-data removal.

### Candidates requiring a sovereign ruling first (do not self-authorize)

1. **`weaver.autonomy` module/package shadowing** — deciding which object is canonical is
   an authority-model question, hence sovereign.
2. **Spiral Grove registry declaration-order vs topological-order contract** — which
   contract the registry means is a design ruling. `tests/test_spiral_grove_registry.py`
   currently pins neither clearly (see baseline debt).
3. **CP10 mutation-boundary allowlist completeness** — see `PARKING_LOT.md`; the invariant
   is that every path in `git ls-files` must be admitted by the policy module.
4. **Baseline test debt** — separately classified; must not be folded into an unrelated
   gate.

## Your Startup Protocol (Maximum 5 minutes)

1. Read `MISSION.md`
2. Read `.bootstrap/01_STATE.md`
3. Run `python3 -m pytest tests/architecture -q` — confirm **11/11**
4. Run `python3 -m pytest tests/test_oracle_spine.py tests/test_k4_response_provenance.py -q` — confirm green
5. Wait for a sovereign workstream selection, OR implement the selected bounded checkpoint
6. Update `.bootstrap/01_STATE.md`, `NEXT_AGENT.md`, `docs/phase1/CONTINUATION_LEDGER.md`
7. Commit and push
8. Stop

## Baseline debt — attribute by node name, not by count

Re-measured 2026-10-02 on `main` @ `64cbe74`:

- Full suite: **20 failed / 1240 passed / 17 skipped / 1 error** (21 failing/error nodes)
- Fingerprint `sha256("\n".join(sorted(FAILED/ERROR node ids)) + "\n")` =
  `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f`

Counts are environment-sensitive and at least one node
(`test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`) is
intermittent under the full suite. **Compare the sorted failing-node *set*, never the
count alone**, before attributing a regression.

## Do NOT Open at Startup

- ENGINEERING_PRINCIPLES.md, ROADMAP.md, ARCHITECTURE_MAP.md, PHASE_GATES.md, any ADR
- CONTINUATION_LEDGER.md (update at session end only)
