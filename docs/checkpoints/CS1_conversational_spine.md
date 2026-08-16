# CS1 — Conversational Spine (Oracle / Arkana runtime)

**Checkpoint:** CS1 — Conversational Spine
**Branch:** main
**Base HEAD:** `36fe2c6`
**Architecture gate:** 10/10 PASSING

## Objective

Make the conversational spine real and testable. Establish ONE intelligence
spine with MANY interfaces — memory and intelligence must be interface-
independent. Do NOT touch the Oracle UI beyond the minimal change required to
propagate session identity.

## Canonical principle

```
                    HUMAN
                      │
             ┌────────▼────────┐
             │ Conversation UI │  (Oracle Chat / ReasoMate / NovaNet)
             └────────┬────────┘
                      ▼
             CANONICAL ARKANA / ORACLE RUNTIME
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Context Retrieval         Response Generation
   (Knowledge OS)            (Gemini)
          │                       │
          └───────────┬───────────┘
                      ▼
              Knowledge OS  (longitudinal memory)
```

The UI is NEVER the source of truth for memory. The contextual state belongs
beneath the surfaces, keyed on an interface-independent session_id.

## Changes

### Backend spine — new module `api/oracle_spine.py`

- `resolve_thread_id(session_id)` — read-only map from the external
  session_id to a Knowledge OS `threads.id`. Does not create a thread on
  retrieval (retrieval must never mutate state).
- `retrieve_arkana_context(message, session_id, token_budget=2000)` —
  delegates to the canonical
  `knowledge.context_engine.assemble_context(query, thread_id=...)` +
  `format_context_for_provider()`. Returns `(block_text, meta)`; empty block
  when nothing is retrieved. Never fabricates.
- `build_memory_block(message, session_id)` — wraps the retrieved context
  with the canonical `== RETRIEVED CONTEXTUAL MEMORY — KNOWLEDGE OS ==`
  header/footer and returns `(block, meta)`.
- `archive_oracle_turn(user_input, response, session_id)` — fire-and-forget;
  resolves/creates the thread via `get_or_create_thread`, then calls the
  purpose-built `knowledge.pipeline.ingest_conversation(prompt, response,
  provider="gemini", persona="arkana", thread_id=...)` (replaces the
  previous generic `pipeline.ingest()` call that did not preserve thread
  linkage). All failures are swallowed+logged so archival never blocks the
  Oracle response.

### `knowledge/vault.py`

- `get_or_create_thread(session_id, title=None)` — inserts a `threads` row
  keyed on `session_id` if absent, returns its id; None for empty session.
- `get_thread_id(session_id)` — read-only lookup.

### `api/main.py` (net +0 lines, within 2600-line budget)

- `/api/commune/resonance` now:
  1. retrieves Knowledge OS context via `build_memory_block(message,
     session_id)` and injects it into the system prompt as a block DISTINCT
     from the corpus RAG block (corpus = canonical writings; retrieved
     memory = personal longitudinal conversation context);
  2. archives the turn via `api.oracle_spine.archive_oracle_turn` with
     thread linkage;
  3. returns a `memory` diagnostic object in the response
     (`session_id`, `thread_id`, `notes_retrieved`, `source`, `injected`)
     so continuity is observable and transparent.
- Removed the inline `_archive_oracle_turn` wrapper (its body now lives in
  the spine module) to keep main.py at budget.

### Frontend session propagation (minimal, additive — no UI redesign)

- New `web/public_prism/src/lib/arkanaSession.ts`:
  `arkanaSessionId(uid?, sovereignToken?)` resolves a stable, interface-
  independent session id — authenticated uid → sovereign token → stable
  guest id (localStorage-backed, shared across surfaces). This is the thread
  key, NOT a second memory system.
- `ArkanaCommune.tsx` (Oracle Chat) — imports `useAuth` + `arkanaSessionId`,
  adds `session_id` to the resonance request body. No other Oracle UI change.
- `ReasoMatePage.tsx` — adds `session_id: arkanaSessionId(profile?.uid)`.
- `NovaNetPage.tsx` — adds `session_id: arkanaSessionId(profile?.uid)`.
- Because authenticated users resolve to the same `uid` across all three
  surfaces, a conversation begun in the Oracle continues in ReasoMate/NovaNet.

### Production configuration

- `.replit` — bot `ORACLE_URL` corrected from `arkadia-n26k` → `arkadia-kw64`.
- `web/public_prism/.env.production` — `VITE_API_URL` corrected likewise.
- `web/public_prism/src/lib/apiConfig.ts` already pinned the canonical
  endpoint as the production fallback and excludes the stale `VITE_API_URL`
  at runtime — verified, no change needed.
- Historical/ADR/recon documents retain old `arkadia-n26k` references by
  design (they document the migration); only active operational config was
  corrected.

## Verification

| Check | Result |
|---|---|
| `pytest tests/architecture -q` | **10/10 PASSING** |
| `pytest tests/test_oracle_spine.py -q` | **4/4 PASSING** |
| `tsc --noEmit` (changed files) | zero errors |
| api/main.py line budget | 2600 (at budget, net +0) |
| main.py imports + all routers mount | OK |
| CORS allows canonical `arkadia-kw64.onrender.com` | verified |
| Stale active `arkadia-n26k` references | 0 (only historical docs remain) |
| Pre-existing `test_steward_filter.py` failures | confirmed present on clean `main` — not caused by CS1 |

### Spine tests (`tests/test_oracle_spine.py`)

1. `test_conversational_spine_archives_and_retrieves_across_interfaces` — a
   unique fact archived under session S in one surface is retrieved when a
   related query arrives under the SAME session S later (continuity).
2. `test_spine_does_not_retrieve_empty_when_nothing_archived` — when the
   Knowledge OS holds no notes, retrieval returns an empty block, never a
   hallucinated one (no fabrication).
3. `test_session_continuity_and_transparency_label` — same-session retrieval
   finds the archived turn AND the block is explicitly labelled "retrieved
   historical context, NOT the current conversation" (transparency).
4. `test_archive_survives_thread_boundary` — the spine helper is safe to
   call from a daemon Thread (as the production archive path does) and still
   persists.

The Gemini embedding API is unavailable offline, so `embed_text` /
`store_chunk_embedding` are stubbed with deterministic local vectors. This is
strictly necessary to exercise the REAL retrieval plumbing (chunk storage,
thread_id filtering, cosine/BM25 scoring, format_context_for_provider)
without a network model; every other code path runs unmodified.

## Known gaps (deliberate, for later checkpoints)

- Oracle Chat UI was NOT redesigned — only a minimal `session_id` field was
  added. Extracting its proven interaction model into a reusable
  conversational component architecture is CS2.
- NovaNet/ReasoMate still persist client message lists to `localStorage`;
  server-side retrieval is now interface-independent, but client-side
  message lists remain per-surface.
- `assemble_context()` retrieval requires stored embeddings
  (`all_chunk_embeddings()` joins `chunks` to `embeddings`); a Gemini key
  must be configured in production for archived chunks to be retrievable via
  the semantic path. Operational config dependency, not a code defect.
- ReasoMate standalone routing and Encyclopedia/Codex duplicate-surface
  reconciliation remain.

## Files changed

- `api/oracle_spine.py` (new)
- `knowledge/vault.py`
- `api/main.py`
- `web/public_prism/src/lib/arkanaSession.ts` (new)
- `web/public_prism/src/components/ArkanaCommune.tsx`
- `web/public_prism/src/pages/ReasoMatePage.tsx`
- `web/public_prism/src/pages/NovaNetPage.tsx`
- `web/public_prism/.env.production`
- `.replit`
- `tests/test_oracle_spine.py` (new)
- `CURRENT_STATE.md`, `NEXT_AGENT.md`, `docs/phase1/CONTINUATION_LEDGER.md`

(Plus the prior architecture-gate repair in this session: `kernel/tools.py`,
`kernel/execution.py`, `kernel/intent_types.py`, `kernel/planner.py`,
`tests/architecture/LAYER_MAP.py`.)

## Next recommended checkpoint

CS2 — Reusable conversational UI: extract/generalise the Oracle Chat
interaction model into a canonical conversational component boundary, informed
by Arkana Pattern Intelligence Chat and ReasoMate. Preserve the Oracle UI;
do not rebuild it.
