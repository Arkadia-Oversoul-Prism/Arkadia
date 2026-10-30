# Arkana Product Constitution 01

**Status:** Proposed product constitution; A0 read-only reconciliation completed against repository source. This document is not evidence that proposed capabilities are implemented or production-verified.

## 1. Product identity

**Arkana** is Arkadia's general-purpose conversational intelligence interface: a coherent place to ask, explore, analyze and create, with a path toward governed agentic work. It is a product surface over the shared Arkadia substrate—not a second intelligence authority, memory system, identity system or execution authority.

## 2. Mission

Make advanced intelligence useful through a clear, capable and trustworthy interaction experience. Users should be able to focus on the work rather than provider or infrastructure details, while retaining visibility and control over context, model use and consequential actions.

## 3. Product principles

1. **Conversation first; workspace when useful.** Keep the default surface quiet. Reveal artifacts, evidence and activity when a task benefits from them.
2. **Capability must be real.** A visible control is not a delivered capability. Each capability needs a functioning contract, observable lifecycle, failure behavior and acceptance evidence.
3. **One substrate.** Reuse Arkadia identity, Knowledge OS, persistence, governance, execution and evidence contracts. Do not create parallel sources of truth.
4. **Providers are replaceable, claims are not.** Declare actual provider capability and disclose what handled a request. Do not imply multi-model routing where only one model ran.
5. **Context is bounded and inspectable.** Distinguish current conversation, retrieved memory, project context, attached material and external sources. Let users inspect and control persistent memory.
6. **Human sovereignty.** A model proposal is not authorization. Authentication is not authorization; execution is not completion; completion is not verification or acceptance.
7. **Truthful lifecycle.** Show pending, streaming, completed, failed, cancelled and persisted states distinctly. Never report persistence or verification before it is confirmed.
8. **Privacy by default.** Owner-scope private data and make anonymous persistence policy explicit. Do not expose private context in public interfaces or logs.
9. **Premium, restrained design.** Prioritize legibility, responsive behavior, purposeful motion, accessibility and focus over decorative complexity.
10. **Failure is a product state.** Provider, network, context and persistence failures remain visible and recoverable; no fabricated fallback answer.

## 4. Authority and safety boundaries

- Arkana can propose actions; only the applicable human-governed authorization boundary can authorize them.
- Provider output and client-provided identifiers/history are untrusted inputs.
- The frontend never grants permissions or establishes ownership.
- External tool execution must pass through existing Arkadia governance and execution infrastructure.
- Sources shown as evidence must correspond to material actually retrieved and supplied to the model.
- Memory must be inspectable, owner-scoped and subject to user controls.

## 5. Product boundary

Arkana is the general-purpose intelligence interface. Engineering Lab remains a specialized engineering environment. Arkana may hand off to specialized Arkadia products through explicit, governed contracts; it does not absorb their authority or duplicate their execution systems.

## 6. Existing foundation (verified in source; not equivalent to production verification)

- `web/arkadia_console/src/pages/ArkanaPage.tsx` provides a basic prompt/reply UI, error display, read-aloud and provenance panel.
- `api/main.py` serves `POST /api/commune/resonance`, calls Gemini, and obtains keys through the shared key pool when no user key applies.
- `api/oracle_spine.py` assembles Knowledge OS context and derives source provenance from retrieved context; successful turns are archived on a daemon thread.
- `api/commune_threads.py` provides authenticated owner-scoped thread list/create/get/rename and message-read routes over Knowledge OS threads.
- `ArkanaThreadHistory` is a read-only history surface. It does not create, resume, append to or rename threads.
- `AuthContext` uses Firebase identity and the API client sends the bearer token. Arkana itself remains reachable anonymously; thread history requires identity.

## 7. Explicitly not claimed as delivered

Streaming, server-controlled turn ordering, confirmed durable completion, resumable chat against first-class threads, cancellation, multi-provider routing, web research, general file analysis, voice conversation, image generation, agent execution and advanced artifacts are not established by the inspected Arkana implementation. They require separate implementation and evidence.

## 8. Decision rule

When product polish conflicts with accuracy, authorization, privacy or provenance, preserve the latter and redesign the interaction. Specification, implementation, deployment, verification and acceptance are separate states.