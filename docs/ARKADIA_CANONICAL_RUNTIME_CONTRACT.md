# Arkadia Canonical Runtime Contract

**Status:** FROZEN — Phase 4B Contract Freeze
**Proven at:** production commit `0242b79` (CS1 `1e7840f` + CS1.1 `28bd02b`)
**Proof method:** live thread-jump test on `arkadia-kw64.onrender.com`, Tests 1–3 passed
**Authority:** this contract documents ONLY what has been implemented and verified in production. It is not a wish-list. Anything not yet implemented is explicitly marked `NOT YET IMPLEMENTED` so future work cannot accidentally create a divergent implicit contract.

The invariant this contract freezes:

```
ONE INTELLIGENCE SPINE  →  MANY INTERFACES  →  ONE KNOWLEDGE SUBSTRATE
```

Memory and intelligence are interface-independent. The UI is a window; the
contextual state lives beneath it.

---

## 1. Identity

The conversational spine keys longitudinal continuity on identifiers. Only one
of these is fully implemented today; the rest are named here so the gaps are
visible, not hidden.

### Proven

| Identifier | Status | Ownership | Creation | Propagation |
|---|---|---|---|---|
| `session_id` | ✅ PROVEN | Human-owned (issued client-side, stored in browser `localStorage` via `web/public_prism/src/lib/arkanaSession.ts`) | First Oracle/ReasoMate/NovaNet turn for a device | Sent in the `session_id` field of every `POST /api/commune/resonance` body, identical across all three surfaces |
| `thread_id` | ✅ PROVEN | System-owned (`threads.id` in the Knowledge OS SQLite vault) | Lazily by `get_or_create_thread(session_id)` at archive time only — never at retrieval time | Derived server-side from `session_id`; returned in the `memory` diagnostic |

**Critical relationship:** `session_id → thread_id` is a stable, one-way mapping.
`session_id` is the human-facing handle; `thread_id` is the Knowledge OS internal
key. A retrieval-only request NEVER creates a thread (so reading memory is
non-mutating). Threads are created exclusively at archival.

### NOT YET IMPLEMENTED (named for visibility, do not assume they exist)

| Identifier | Status | Intended role |
|---|---|---|
| `user_id` | ❌ NOT YET IMPLEMENTED | Cross-device identity. Today `session_id` is per-device (localStorage); there is no authenticated user concept tying multiple devices/sessions to one human. A user is only loosely identified via `node_key`/`uid` in the personal-node block, which is separate from the spine. Introducing `user_id` would let the same human's thread be retrievable across devices — this is a future capability, not current behaviour. |
| `message_id` | ❌ NOT YET IMPLEMENTED | Stable per-turn id. Today each archived turn is a Knowledge OS note (with a note `id`/`uuid`), but there is no explicit `message_id` surfaced in the runtime contract. Turn identity is implicit via note id + thread linkage. |

**Implication for downstream work:** anything that depends on cross-device
continuity or per-message addressing must first implement `user_id`/`message_id`
explicitly. Do not build on the assumption they exist.

---

## 2. Context

The context delivered to a provider is a single structured package assembled by
`knowledge.context_engine.assemble_context()`. This is the canonical shape:

```python
{
  "query": <str>,                    # the incoming user message
  "relevant_notes": [                # ranked, thread-scoped when thread_id set
    {
      "id": <int>, "uuid": <str>, "title": <str>,
      "note_type": <str>,            # e.g. "conversation"
      "tags": <str>, "created_at": <iso>,
      "relevant_chunks": [<str>, ...]  # up to max_chunks_per_note
    }, ...
  ],
  "graph_expansions": [              # 1-hop graph neighbours of retrieved notes
    {"note": {...}, "via": <note_id>}, ...
  ],
  "project_context": <dict|None>,    # populated only when project_id provided
  "recent_timeline": [               # recent activity, thread-scoped when set
    {"event_type": <str>, "created_at": <iso>}, ...
  ],
  "token_budget_total": <int>,
  "token_budget_used": <int>,
}
```

### What is proven vs proposed

| Context field | Status |
|---|---|
| `current` (the live query) | ✅ PROVEN — `query` field |
| `retrieved` (relevant notes/chunks) | ✅ PROVEN — `relevant_notes` + `relevant_chunks` |
| `historical` (timeline) | ✅ PROVEN — `recent_timeline` (event_type + created_at) |
| `provenance` | ✅ PARTIAL — provenance is stamped at archive time (`provider=gemini`, `persona=arkana` on the timeline), but NOT surfaced per-note inside the returned context package |
| `confidence` | ❌ NOT YET IMPLEMENTED — retrieval returns a `score` (cosine or BM25) per chunk, but no normalized confidence is surfaced to the runtime or response |
| `temporal_status` | ❌ NOT YET IMPLEMENTED — timestamps exist; there is no explicit "current vs stale" classification |

**Rule:** the runtime must inject the rendered context package via
`format_context_for_provider()` and never fabricate fields that are absent. An
empty `relevant_notes` list means "nothing retrieved" — the response must not
invent memory.

---

## 3. Runtime

The frozen runtime path. Every conversational surface reduces to this:

```
SURFACE  (Oracle Chat | ReasoMate | NovaNet | future)
   │
   │  POST /api/commune/resonance
   │  body: { message, session_id, context, history }
   ▼
CANONICAL RUNTIME  (api/main.py :: commune_resonance)
   │
   │  1. resolve provider key
   │  2. corpus RAG (scrolls)            ← Arkadia corpus, separate from memory
   │  3. build_memory_block(session_id)  ← THE SPINE
   ▼
api/oracle_spine.build_memory_block(message, session_id)
   │
   │  resolve_thread_id(session_id)      ← read-only, never mutates
   │  assemble_context(query, thread_id) ← Knowledge OS context engine
   │  format_context_for_provider(pkg)
   ▼
KNOWLEDGE OS  (knowledge.context_engine / knowledge.embeddings / knowledge.vault)
   │
   │  retrieval hierarchy (see §5)
   ▼
RESPONSE  (Gemini provider call, system prompt + memory_block + corpus_block + personal_block)
   │
   │  archive_oracle_turn(message, reply, session_id)  ← fire-and-forget daemon thread
   │     get_or_create_thread(session_id) → thread_id
   │     ingest_conversation(prompt, response, provider, persona, thread_id)
   ▼
return { reply, resonance, patterns, rag_refs, rag_hits, memory }
```

**Non-negotiable properties of this path:**
- Retrieval is **non-mutating**. Threads are created only at archive time.
- Archival is **fire-and-forget**. A failure to archive never blocks the response.
- The provider receives the rendered memory block as a string, never raw vault rows.
- An empty memory block is the correct response to "nothing retrieved"; the runtime must not fabricate.

---

## 4. Response

The canonical response object returned by `/api/commune/resonance`:

```json
{
  "reply":      "<generated response text>",
  "resonance":  <float>,
  "patterns":   [],
  "rag_refs":   [<corpus references>],
  "rag_hits":   <int>,
  "memory": {
    "session_id":      "<string|null>",
    "thread_id":       "<int|null>",
    "notes_retrieved": <int>,
    "source":          "knowledge_os",
    "injected":        <bool>
  }
}
```

| Field | Meaning |
|---|---|
| `reply` | Generated language from the provider |
| `resonance` | Cosmetic resonance score |
| `patterns` | Reserved (currently empty) |
| `rag_refs` / `rag_hits` | Corpus (scrolls) retrieval — distinct from Knowledge OS memory |
| `memory.session_id` | The session_id this turn was scoped to (echoed back for client continuity) |
| `memory.thread_id` | The Knowledge OS thread id resolved for retrieval (null on first turn, before any archive) |
| `memory.notes_retrieved` | Count of Knowledge OS notes retrieved into the context package |
| `memory.source` | `knowledge_os` on success, `knowledge_os_error` if retrieval threw |
| `memory.injected` | Whether a memory block was actually injected into the prompt |

**Transparency contract:** `memory.injected: false` or `notes_retrieved: 0`
must mean Arkana did NOT receive retrieved context for this turn. The persona
must not claim continuity it was not given. (This is the basis of Test 3 —
invisibility/no-fabrication.)

---

## 5. Retrieval Hierarchy

```
embed_text(query)
      │
      ├── query vector available (Gemini configured)
      │         │
      │         ▼
      │   all_chunk_embeddings()  (chunks INNER JOIN embeddings)
      │         │
      │         ▼
      │   cosine similarity ranking   ← semantic retrieval
      │
      └── query vector unavailable (Gemini offline/unconfigured)
                │
                ▼
          all_chunks()  (chunks, NO embeddings JOIN)
                │
                ▼
          BM25 keyword scoring   ← local-first fallback (LAW II)
                │
                ▼
          context returned
```

**Thread scoping:** when a `thread_id` is resolved, retrieval is filtered to
notes belonging to that thread. When no `thread_id` exists (first turn),
retrieval is global — which is correct: there is no thread yet to scope to.

### Operational fact (proven)

> **BM25 is the guaranteed retrieval floor. Embeddings improve semantic
> retrieval but are not the continuity dependency.**

Proof: production `arkadia-kw64.onrender.com` currently has `embeddings: 0,
pending: 30` (Gemini unconfigured). The thread-jump test passes via the BM25
path alone. Continuity does not depend on the embedding provider.

This is why CS1.1 exists: the documented BM25 "local-first" fallback was
previously **dead code** (both retrieval paths called `all_chunk_embeddings()`,
an INNER JOIN that returns `[]` when 0 embeddings exist, making the BM25 branch
unreachable). CS1.1 (`28bd02b`) added `all_chunks()` and gated each retrieval
path on the query-vector's availability, making the local-first law actually
true. See `docs/checkpoints/CS1_conversational_spine.md` § CS1.1.

---

## 6. What this contract forbids

- A second conversational runtime. All surfaces go through `/api/commune/resonance`.
- A second memory system. All archival goes through `archive_oracle_turn` → `ingest_conversation`.
- A second context assembler. All retrieval goes through `assemble_context`.
- Fabricating memory from an empty retrieval. Empty block = no continuity claim.
- Mutating state on retrieval. Threads are created at archive time only.
- Treating `user_id` / `message_id` / `confidence` / `temporal_status` as if
  they exist. They are named here as future work, not current capability.

---

## 7. Proven test surface

| Suite | Result | Location |
|---|---|---|
| Architecture gate | 10/10 | `tests/architecture` |
| Spine continuity | 5/5 | `tests/test_oracle_spine.py` |
| Production thread jump (Test 1) | PASS | live, `arkadia-kw64.onrender.com` |
| assemble_context contract (Test 2) | PASS | live, identical `memory` across surfaces |
| Invisibility / no-fabrication (Test 3) | PASS | live, no source-surface leak |

The contract above is what these tests protect. Any change to the runtime,
retrieval, or response shape must keep these green — or explicitly renegotiate
this contract with an updated freeze.
