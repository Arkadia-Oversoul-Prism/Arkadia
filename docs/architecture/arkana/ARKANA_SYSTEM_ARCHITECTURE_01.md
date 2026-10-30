# Arkana System Architecture 01

**Status:** Proposed logical architecture grounded in read-only repository inspection. Existing behavior is identified separately from target behavior. No runtime changes are included.

## 1. Architecture constraints

- Evolve `web/arkadia_console` and the existing FastAPI application; do not create a new deployment or independent service for the initial slice.
- Reuse the Oracle spine and Knowledge OS as the canonical contextual-memory substrate.
- Reuse Firebase identity and verified backend user identity. Client-provided identity, session IDs and conversation history are not authority.
- Keep provider adapters replaceable, while routing initial requests through the existing Gemini/key-pool path.
- Reuse existing Arkadia authorization and execution infrastructure for future tools; Arkana is not an execution authority.

## 2. Current verified component map

| Concern | Current source | Observed behavior and gap |
|---|---|---|
| Product UI | `web/arkadia_console/src/pages/ArkanaPage.tsx` | Basic non-streaming prompt/reply surface, transient in-component turns, error panel, read-aloud, provenance. No active-thread lifecycle. |
| API transport | `web/arkadia_console/src/lib/arkana.ts`, `lib/apiClient.ts` | JSON request to `/api/commune/resonance`; recent history and browser `localStorage` session ID are sent. API client attaches Firebase token when present. |
| Identity | `web/arkadia_console/src/contexts/AuthContext.tsx`, `api/auth.py` | Firebase client sign-in; backend token verification. Thread endpoints require authenticated identity. Chat route calls optional current-user lookup. |
| Conversation endpoint | `api/main.py::commune_resonance` | Non-streaming Gemini request. Reads client-supplied `history`, `session_id` and `project_id`; archives asynchronously after generation. |
| Provider access | `api/main.py`, `api/key_pool.py` | Gemini is the effective conversational provider; key pool distributes configured keys/cools failures. No Arkana-level provider-neutral routing contract is verified. |
| Context/retrieval | `api/oracle_spine.py`, `knowledge/context_engine.py` | Bounded context assembly with optional thread/project/user filtering; source list is derived from retrieved context. Retrieval catches and reports failures in metadata rather than stopping chat. |
| Canonical thread records | `api/commune_threads.py`, `knowledge/vault.py` | Threads reside in Knowledge OS tables. List/create/get/rename/message-read routes are owner-scoped. Message projection parses existing conversation-note formats. |
| Turn archive | `api/oracle_spine.py::archive_oracle_turn` | Fire-and-forget thread creation and Knowledge OS ingest. Endpoint response does not await durable confirmation. |
| History UI | `components/arkana/ArkanaThreadHistory.tsx` | Auth-gated, read-only list and message view; does not resume a conversation or send into selected thread. |
| Presentation | `src/index.css`, shared UI components | Dark theme, focus ring, reduced-motion handling and shared console shell exist. Current Arkana page uses shared `Page`/`Panel`; premium dedicated chat layout is not present. |

## 3. Target logical architecture (not a mandate to create services)

```text
Arkana Experience (React)
  ├─ conversation surface and composer
  ├─ thread navigation and responsive workspace
  ├─ source/provenance and activity views
  └─ explicit user controls
        │ authenticated API contract
        ▼
Arkana Conversation Runtime (FastAPI modules/routes)
  ├─ identity + owner validation
  ├─ server-owned thread/turn lifecycle
  ├─ bounded context assembly through Oracle spine
  ├─ capability-aware provider request
  ├─ streaming event lifecycle + cancellation
  └─ durable turn confirmation before completion event
        │
        ├─ Intelligence gateway → provider adapters (Gemini first)
        ├─ Capability modules → later, per contract and authorization
        └─ Arkadia substrate
             ├─ Firebase-verified identity
             ├─ Knowledge OS threads, notes and retrieval
             ├─ existing governance and execution
             └─ evidence/provenance contracts
```

These are logical seams. Keep the first implementation in the existing application composition and persistence architecture; do not split into independently deployed services without a separate architecture decision.

## 4. Request lifecycle target

1. Authenticate the request where the selected conversation contract requires identity.
2. Resolve the requested thread on the server and verify ownership; do not trust a browser session ID as a thread authority.
3. Validate message size, attachment references and supported capabilities.
4. Assemble bounded context from authorized conversation/project/memory sources; preserve retrieval status and exact injected-source provenance.
5. Select a declared provider/capability, defaulting to the existing Gemini integration until additional adapters are implemented and verified.
6. Generate and stream ordered events with stable turn ID and explicit error/cancel states.
7. Persist user and assistant turn through the canonical Knowledge OS/thread mapping; only emit persisted completion after durable success.
8. Return provider and provenance metadata based on actual execution, not inference.

Streaming must not weaken authentication, ordering, persistence or cancellation semantics. If the current storage contract cannot atomically store a turn, the contract must describe partial failure and recovery explicitly.

## 5. Provider and capability boundaries

A provider adapter should declare models, modality and tool capabilities, context limits, streaming/cancellation support and error mapping. Routing may account for task, user preference, availability, latency and cost, but only after measurable policies exist. V1 remains Gemini-first; no simulated fallback or multi-model claim.

Research, files, vision, audio/voice, generation, data analysis, tools and agents are capability modules, not implied features of a chat endpoint. Each requires its own authorization, limits, lifecycle and failure behavior.

## 6. Security and data boundaries

- Resolve principal from verified backend credentials; never accept `user_id` from request JSON as authority.
- Scope thread reads and writes to authenticated owner; return a consistent not-found behavior for foreign threads.
- Define anonymous-chat persistence before attaching anonymous turns to a durable archive. Existing anonymous access is not evidence of a safe persistence policy.
- Treat client history as display input only until the canonical thread transcript is loaded and validated server-side.
- Validate `project_id` ownership wherever project context is used; existing thread creation checks project ownership, but the chat route's client-provided project value requires reconciliation before reuse.
- Do not leak provider credentials, private context or raw internal diagnostics to the browser.
- Ensure cancellation reaches provider work where supported and leaves a truthful persisted/cancelled state.

## 7. Failure and observability model

Represent identity, ownership, validation, retrieval, provider, stream transport and persistence outcomes separately. The UI should distinguish retrieval unavailable from no sources found; provider failure from empty answer; transport interruption from completed answer; and generation complete from durably persisted. Activity events should be inspectable but must not expose secrets or private payloads.

## 8. Architecture risks to resolve before implementation

1. Chat calls are not bound to the first-class thread CRUD API.
2. Client history and `session_id` currently influence prompts and memory lookup.
3. Archive happens on a daemon thread and its success is not reflected in the response.
4. Thread message reads project notes, while UI turn history is ephemeral and cannot resume.
5. Authenticated and anonymous chat have different persistence/continuity expectations that are not yet one explicit contract.
6. Project ownership and thread ownership checks must be consistent across retrieval, prompt context and archival.
7. Existing broad shared `api/main.py` is close to a documented line budget; future work should follow repository router-composition conventions rather than growing it indiscriminately.