# 07 — AI Infrastructure Blueprint

## Gemini Call Sites
| File:Line | Purpose | Model | Temp | Max tokens |
|---|---|---|---|---|
| `weaver/llm.py:30` | Autonomy agent reasoning | `gemini-1.5-flash` (default, `weaver/llm.py:15`) | not captured | not captured |
| `api/main.py:2055` | `/api/ceo/chat` (ARKANA CEO advisor) | `gemini-2.0-flash-exp` (`api/main.py:2054`) | 0.75 | 2048 |
| `kernel/planner.py:126` | Phase 7 LLM planner (`_gemini_plan`) | fallback list incl. `gemini-2.5-flash`, `gemini-flash-latest` (`kernel/planner.py:55`) | 0.2 | 1024 |
| `solspire/llm.py:60,85` | Intent parsing + fallback (SolSpire console) | `gemini-1.5-flash` default (`solspire/llm.py:20`) | not captured | not captured |
| `api/pulse.py:232` | AIC diagnostic Oracle summary | not captured | 0.88 | 400 |

No streaming responses anywhere — all calls are blocking `requests.post`/`httpx.post`/SDK calls returning full JSON.

## Retry / Fallback Logic
- `weaver/llm.py`: `MAX_RETRIES = 3`, exponential backoff via `time.sleep`.
- `kernel/planner.py`: iterates a tuple of model names (`PLANNER_MODELS`) on failure; if all fail, falls back to `_fallback_plan` (line 347) → deterministic regex classification in `kernel/execution.py:classify_input` (line 59).

## ORACLE_IDENTITY (Constitutional Prompt)
Defined inline in `api/main.py` (lines ~2024–2042) for the CEO chat. Structure:
1. Identity statement (ARKANA, Node OR'HA-EL'UN, CEO advisor/OS role)
2. Injected tool registry catalog (from `kernel/tools.py:list_tools()`)
3. Mandated `<tool_call>` JSON protocol for tool invocation
4. Sovereignty gate — sensitive actions require `requires_approval: true`
5. Tone directives (sovereign, direct, non-generic)

Backed by doctrine documents in the corpus: `docs/ARKADIA_SPEC_v3.md` (core doctrines — non-sentience, human sovereignty) and `docs/DOC3_PRINCIPLES_REGISTRY.md` (228 Sovereign Laws + 7 Immutable Laws).

## Document Retrieval / "Embeddings"
- **No external embedding provider** (no OpenAI/Pinecone/etc.) anywhere in the codebase.
- `corpus/` scoring: priority-tier based (1–3), assigned by directory mapping in `github.py`, not true TF-IDF cosine similarity despite replit.md's "TF-IDF semantic relevance" description — this is a **documentation-vs-implementation discrepancy** worth flagging to the user (not corrected here per read-only mandate).
- `weaver/echofield/vector_stack.py` + `retrieval.py`: a **custom, deterministic 6-axis symbolic vector** (identity/function/resonance/structure/mythic/directive) with cosine similarity — used only for governance/autonomy reasoning, not chat document retrieval.

## Conversation Assembly
`api/main.py` (~lines 2044–2050): last 12 turns, mapped to "Human"/"Arkana" role prefixes, concatenated into the prompt alongside retrieved corpus context.

## Phase 7 Planner Flow
1. `kernel/execution.py:classify_input` attempts regex classification first.
2. If no match, intent is tagged `__plan__` and routed to `kernel/execution.py:_execute_planner_intent` (line 239).
3. `kernel/planner.py:generate_plan` (line 389) calls Gemini to produce a JSON multi-step plan.
4. `validate_plan` (line 207) enforces tool existence and a max step count of 5.
5. `execute_plan` (line 260) runs steps sequentially, resolving `$step_n.field` references (`_resolve_ref`, line 234) between steps.
6. On any LLM failure, `_fallback_plan` (line 347) reverts to the deterministic Phase 4 regex classifier.

## Arkadia Symbolic Engine (deterministic, no LLM)
`api/arkadia_engine.py`:
- `generate_verse()` (line 146) — assembles from `INVOCATIONS`/`symbolic_movement`/`FRACTURES`/`SEALS` line pools, applies a 10-syllable cap (`shape_line`, via `pronouncing` lib or vowel-cluster fallback) and 40%-probability rhyme tagging.
- `compress()`/`expand()` (lines 163/173) — small fixed lexicon substitution (`flame↔F3`, `spiral↔S9`, `codex↔C4`, `field↔FD6`, `archive↔A7`).

## Bot Integrations
- **Discord** (`bot/discord-bot.mjs:52`): posts to `/api/commune/resonance`; has a **direct Gemini SDK fallback** (`source: 'fallback'`, line 79) if the backend is unreachable — meaning Discord can bypass the entire Oracle/corpus/kernel pipeline and talk to Gemini raw during backend outages.
- **Telegram** (`bot/telegram-bot.mjs:128`): posts to `/api/commune/resonance`; supports async jobs via `/api/job/create` when `TELEGRAM_ASYNC_JOBS=true` (line 73); also has a **direct Gemini fallback** (line 149) for chat and document parsing.

## Extensibility Hook
Per replit.md, `kernel/tools.py:select_tool()` is the designated seam for a future LLM-based tool router (Phase 7 already partially delivers this via `kernel/planner.py`, which the tool registry integrates with).
