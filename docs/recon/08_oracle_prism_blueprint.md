# 08 — Oracle / Prism Audit

## Responsibilities
"ARKANA" (the Oracle) is the conversational intelligence layer exposed via `/api/commune/resonance` (general chat) and `/api/ceo/chat` (CEO-advisor mode with tool-calling). "Prism" refers to the frontend product surface (`web/public_prism/`) through which users interact with the Oracle.

## Modules Involved in a Single Oracle Turn
1. **Frontend** — `ArkanaCommune.tsx` collects user input, sends to `/api/commune/resonance`, renders markdown response via `MarkdownViewer.tsx`.
2. **Backend entry** — `api/main.py` handler for `/api/commune/resonance`.
3. **Symbolic Engine short-circuit** — if the message starts with `⟐ generate`, `⟐ compress <text>`, or `⟐ expand <text>`, it's routed directly to `api/arkadia_engine.py` functions and returned in the standard Oracle response shape, **bypassing Gemini entirely**.
4. **Corpus retrieval** — `corpus/manager.py` supplies relevant document context (priority-scored, not true semantic embedding search — see AI Infrastructure Blueprint).
5. **History assembly** — last 12 turns injected as "Human"/"Arkana" pairs.
6. **Identity injection** — ORACLE_IDENTITY constitutional prompt prepended.
7. **Gemini call** — `gemini-2.0-flash-exp` (CEO chat) or model used by `/api/commune/resonance` (not separately confirmed this pass — likely same family; flagged as uncertain).
8. **Kernel short-circuit alternative path** — per replit.md, `/api/commune/resonance` first attempts kernel classification (`classify_input`) and only falls through to Gemini if no deterministic intent matches. This "classify-first" behavior was documented in replit.md but not independently re-verified against current `api/main.py` line numbers this session — **flagged as needing direct confirmation**, since the explore pass for AI infra found the Gemini call at `api/main.py:2055` without confirming the kernel-classify branch precedes it in the same handler.
9. **Response rendering + persistence** — response returned to frontend; conversation persisted to Firestore (`conversationService.ts`) for authenticated users or `localStorage` for anonymous sessions.

## Semantic Search / Graph Traversal
- No graph database or true semantic embedding search exists. "Semantic relevance" in the Oracle context is priority-tier document selection (`corpus/`), not vector similarity over the corpus text itself.
- Governance/autonomy reasoning (a separate, non-chat-facing pipeline) does use real cosine-similarity vector search (`weaver/echofield/`), but this does not feed the user-facing Oracle chat.

## Context Injection
Two independent context sources are combined per Oracle turn: (a) corpus document context (`corpus/manager.py`), (b) kernel memory snapshot (`kernel/memory.py`, keyword-matched) — the latter is documented as feeding the **kernel planner**, not confirmed as also feeding the Gemini chat prompt directly. **Flagged as uncertain** — needs direct code confirmation of whether `kernel/memory.py` context reaches the `/api/commune/resonance` prompt or is scoped only to `/api/job/create` planning.

## Performance / Limitations (evidence-based, not measured)
- All Gemini calls are synchronous/blocking with no streaming — response latency is bound by full-generation time (subjectively affects perceived responsiveness but not measured this session).
- No embedding cache or vector index — corpus retrieval scans the in-memory 6-hour cache directly.
- 12-turn history window is a hard cap — long conversations lose earlier context (no summarization is actually active, contra replit.md's Cycle 15 description — see Memory Blueprint).

## Integration Points
- Discord bot, Telegram bot: both call `/api/commune/resonance` and both carry independent Gemini fallback paths that bypass the Oracle/corpus/kernel stack entirely during backend outages — meaning **prompt/identity/tool consistency is not guaranteed across all client surfaces**.
