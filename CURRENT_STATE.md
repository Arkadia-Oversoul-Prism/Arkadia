# Current State
> Moved to `.bootstrap/01_STATE.md`

## CS1 — Conversational Spine (Oracle/Arkana runtime) — COMPLETE

### Canonical principle established

**ONE INTELLIGENCE SPINE. MANY INTERFACES.** The Oracle is the capability;
Arkana is the conversational persona/interface; the Knowledge OS is the
contextual memory substrate. Oracle Chat, ReasoMate, and NovaNet
conversational surfaces are windows onto the same runtime — they are NOT
separate chatbots or separate memories. Memory and intelligence are now
interface-independent: a turn archived under a session_id in one surface is
retrievable in a subsequent turn under the same session_id regardless of
which surface initiated it.

### What was done

**Backend spine (new module `api/oracle_spine.py`):**
- `resolve_thread_id(session_id)` — maps the interface-independent session_id
  onto a Knowledge OS `threads.id` (read-only on retrieval).
- `retrieve_arkana_context(message, session_id)` — calls the canonical
  `knowledge.context_engine.assemble_context(query, thread_id=...)` +
  `format_context_for_provider()`; returns a distinct retrieved-memory block,
  empty when nothing is retrieved (never fabricates).
- `build_memory_block(message, session_id)` — wraps the above with the
  canonical `== RETRIEVED CONTEXTUAL MEMORY — KNOWLEDGE OS ==` header/footer.
- `archive_oracle_turn(user_input, response, session_id)` — switched from
  the generic `pipeline.ingest()` to the purpose-built
  `pipeline.ingest_conversation(prompt, response, provider, persona,
  thread_id=...)`, so each Oracle turn is linked to its conversation thread
  and stamped with provider/persona provenance on the timeline.

**`knowledge/vault.py`:**
- `get_or_create_thread(session_id)` — maps the external session_id onto a
  `threads` row (created at archive time so retrieval-only requests never
  mutate state).
- `get_thread_id(session_id)` — read-only lookup.

**`api/main.py` (within 2600-line budget — net +0 lines):**
- `/api/commune/resonance` now retrieves Knowledge OS context via
  `build_memory_block()` and injects it into the system prompt as a block
  distinct from the corpus context (corpus = canonical writings; retrieved
  memory = personal longitudinal conversation context).
- Archival now calls `api.oracle_spine.archive_oracle_turn` with thread
  linkage.
- Response payload now includes a `memory` diagnostic object
  (`session_id`, `thread_id`, `notes_retrieved`, `source`, `injected`) so
  continuity is observable and transparent.
- The old inline `_archive_oracle_turn` wrapper was removed; the spine lives
  in `api/oracle_spine.py` to respect the main.py budget.

**Frontend session propagation (minimal, additive — no UI redesign):**
- New shared helper `web/public_prism/src/lib/arkanaSession.ts` —
  `arkanaSessionId(uid?, sovereignToken?)` resolves a stable, interface-
  independent session id (authenticated uid → sovereign token → stable guest
  id). This is the thread key, NOT a second memory system.
- `ArkanaCommune.tsx` (Oracle Chat), `ReasoMatePage.tsx`, and
  `NovaNetPage.tsx` each now send `session_id` in the `/api/commune/resonance`
  body. Because authenticated users resolve to the same `uid` across all
  three surfaces, an Oracle conversation continues in ReasoMate/NovaNet.

**Production configuration:**
- Corrected stale active Render endpoint references:
  `.replit` (bot `ORACLE_URL`) and `web/public_prism/.env.production`
  (`VITE_API_URL`) now point to `https://arkadia-kw64.onrender.com`.
- `web/public_prism/src/lib/apiConfig.ts` already pinned the canonical
  endpoint as the production fallback and explicitly excludes the stale
  `VITE_API_URL` at runtime.

### Verification

- `pytest tests/architecture -q` → **10/10 PASSED**
- `pytest tests/test_oracle_spine.py -q` → **4/4 PASSED** (continuity,
  no-fabrication, transparency label, thread-boundary archive safety)
- `tsc --noEmit` → zero errors in changed files
- api/main.py at 2600-line budget (net +0)
- 3 pre-existing `test_steward_filter.py` failures confirmed present on
  clean `main` (HEAD `36fe2c6`) — not caused by this checkpoint

### Known gaps / NOT done this checkpoint (deliberate)

- The Oracle Chat UI was intentionally NOT redesigned — only a minimal
  `session_id` field was added to its request body. Extracting the proven
  Oracle Chat interaction model into a reusable conversational component
  architecture (Oracle Chat × Arkana Pattern Intelligence × ReasoMate) is
  the next checkpoint.
- NovaNet/ReasoMate still persist conversation history to browser
  `localStorage`; the spine makes retrieval interface-independent server-
  side, but client-side message lists are still per-surface. Cross-device
  client continuity is a later checkpoint.
- `assemble_context()` retrieval requires stored embeddings
  (`all_chunk_embeddings()` joins `chunks` to `embeddings`). In production a
  Gemini key must be configured so `embed_text` persists vectors; without it,
  archived chunks are stored but not retrievable via the semantic path. This
  is an operational configuration dependency, not a code defect.
- ReasoMate standalone page routing and Encyclopedia/Codex duplicate-
  surface reconciliation (recon P0/P1) remain for a later checkpoint.
- Historical/ADR/recon documents retain old `arkadia-n26k` references by
  design (they document the migration); only active operational config was
  corrected.

---

## K3-C — Knowledge Graph Enrichment — COMPLETE

### What was done

**Backend:**
- `knowledge/edge_migration.py` — legacy edge migration utility; 40-entry mapping table; `--report | --dry-run | --apply` CLI; never auto-deletes
- `knowledge/enrichment.py` — semantic enrichment engine; 5 evidence scorers (tag, project, thread, type affinity, source provider); confidence threshold gate (0.25 min); idempotent
- `knowledge/embedding_queue.py` — embedding completion queue; detects pending/partial notes; background pass at startup
- `knowledge/pipeline.py` — auto-link step now calls `enrichment.schedule_enrichment()` with tag-heuristic fallback
- `api/main.py` — startup now schedules embedding pass + orphan enrichment (background threads)
- `api/knowledge_routes.py` — 10 new endpoints: `/node/{id}`, `/neighbors/{id}`, `/path`, `/enrich/{id}`, `/enrich/orphans`, `/migrate/edges/report`, `/migrate/edges/apply`, `/embeddings/status`, `/embeddings/process`; extended `/status` growth metrics
- `web/public_prism/src/lib/knowledgeApi.ts` — 8 new types + 8 new API call functions

**Frontend:**
- `web/public_prism/src/pages/knowledge/NodeInspector.tsx` — node detail panel: stable UUID, degree stats, scrollable edge browser (in/out), type badges, drill-down button
- `KnowledgeGraphView.tsx` — selected-node card replaced with `NodeInspector`

### Verification

- `pytest tests/architecture -q` → **10/10 PASSED**
- `npm run build` → **✓ zero errors**
- Canonical ontology untouched
- api/main.py within 2600-line budget

### Next session: K4 — Relational Intelligence / Trust Telemetry

Do NOT begin trust metrics, moderation, recommendation systems, or social scoring until a new checkpoint authorises it.
