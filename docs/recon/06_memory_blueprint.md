# 06 — Memory Architecture Blueprint

Distinguishes "memory" (in the AI/agent sense — context carried across turns/sessions) from the general database layer (05).

## Types of Memory Present

### 1. Kernel Memory (Phase 8) — `kernel/memory.py`
- `retrieve_context(user_input)` — **keyword-match retrieval** (not embeddings) over `data/oracle_store.json`, returning balance/open-loop/event snapshots relevant to the planner.
- Lifecycle: read-only, computed fresh per planning call; no separate cache.
- **Note on replit.md claim**: replit.md's Phase 8 description implies richer memory-aware planning; the actual retrieval mechanism confirmed in code is simple keyword matching, not semantic/embedding search. This is a documentation-vs-code gap worth flagging, not a contradiction to "fix" — just noted for accuracy.

### 2. Conversation History (Oracle Chat)
- `api/main.py` assembles the last 12 turns of conversation history inline for each Gemini call (`/api/commune/resonance` and `/api/ceo/chat`), mapping to "Human"/"Arkana" role labels.
- Persisted client-side via Firestore (`conversationService.ts`) per authenticated user, and/or `localStorage` (`arkadia-commune-messages`) for anonymous/offline chat continuity in `ArkanaCommune.tsx`.
- Summarization: replit.md's Cycle 15 claims "conversation summarization, pattern extraction" — the only summarization code actually found is in `archive/legacy_python/build_corpus_summaries.py` (explicitly archived/legacy). **Active `api/main.py` does sliding-window history injection, not summarization.** This is a doc-vs-code discrepancy to flag for the user, not to silently "fix."

### 3. Symbolic Vector Memory — `weaver/echofield/`
- `vector_stack.py`: 6-axis (`identity, function, resonance, structure, mythic, directive`) deterministic vector representation for governance/autonomy "nodes."
- `retrieval.py`: cosine similarity over these axes — used by the autonomy loop (`weaver/run_autonomy.py`), not by the Oracle chat.
- This is a genuinely distinct memory system from `corpus/` (which retrieves markdown documents by TF-IDF/priority) — both exist and serve different consumers.

### 4. Browser-Side Memory (`localStorage`)
| Key | Used by | Purpose |
|---|---|---|
| `LS_STATES` / `LS_REFLECTIONS` | `EncyclopediaGalactica.tsx` | Cached chamber research state |
| `arkadia-commune-messages` | `ArkanaCommune.tsx` | Local chat history fallback |
| `arkadia-token` | Auth flow | Session token |
| `arkadia-voice-resume` | `OracleVoicePlayer.tsx` | Playback resume position |
| `arkadia_chambers_v2` | Encyclopedia Galactica (per prior-session memory) | 12-chamber navigation state |

### 5. Cross-Restart Durability
`api/firebase_store.py` mirrors `job_store.json` and `goal_store.json` to Firestore purely so in-flight kernel jobs/goals survive an ephemeral filesystem restart — this is infrastructure durability, not "AI memory" in the retrieval sense.

## Ownership Summary
| Memory type | Owner code | Retention |
|---|---|---|
| Kernel state memory | `kernel/oracle_store.py` + `kernel/memory.py` | Indefinite (JSON file) |
| Conversation history | `api/main.py` (server-side, per-call) + Firestore/`localStorage` (client-side) | 12-turn window server-side; unlimited client-side until manually cleared |
| Symbolic vector memory | `weaver/echofield/` | Indefinite (governance JSON) |
| Browser UI state | `localStorage` keys above | Until browser storage cleared |

## Redundancy Note
No true redundant memory systems were found — `corpus/` (documents), `kernel/memory.py` (kernel state), and `weaver/echofield` (governance vectors) serve three distinct, non-overlapping purposes despite superficially similar "retrieval" framing.
