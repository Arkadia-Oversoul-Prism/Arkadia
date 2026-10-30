# Arkana V1 Vertical Slice 01

**Status:** Proposed first production-oriented slice. No implementation or production acceptance is claimed by this specification.

## 1. V1 outcome

An authenticated Arkadia user can create a conversation, send a message, receive a progressively rendered response from the existing Gemini-first path, refresh or return later, reopen the canonical transcript, and inspect truthful retrieval/provider status. The UI is responsive and polished, and failures do not silently lose or duplicate turns.

## 2. Scope

### Required

- Refined desktop and mobile Arkana shell within `web/arkadia_console`.
- Existing Firebase identity and verified backend owner scoping.
- First-class thread creation, listing, selection and resume against the canonical Knowledge OS thread contract.
- Server-owned transcript/context; browser history and session identifiers are not authoritative.
- Progressive response delivery if provider and deployment transport support it; otherwise revise the release contract rather than simulate streaming.
- Confirmed persistence and stable turn ordering before reporting durable completion.
- Gemini-first provider adapter seam using existing key-pool/key-resolution paths.
- Bounded Knowledge OS retrieval, exact source provenance and explicit retrieval status.
- Markdown/code display, retry/idempotency, interruption recovery and stop/cancel semantics where supported.
- Visible, recoverable identity, network, retrieval, provider and persistence errors.
- Keyboard accessibility, reduced motion and responsive/mobile behavior.

### Out of scope for V1

Multi-provider auto-routing/comparison, web search, broad document ingestion/analysis, image generation, voice conversation, video understanding, branching, custom assistants, generalized tool integrations, autonomous agent execution and advanced artifact workspaces. Existing read-aloud may remain separate; it is not equivalent to live voice conversation.

## 3. End-to-end journey

1. Open Arkana; resolve identity state without issuing owner-scoped requests prematurely.
2. Start a new canonical thread or select an existing owned thread.
3. Load its canonical messages and present a usable empty state when no turns exist.
4. Compose and submit once with a stable idempotency key; preserve draft on failure.
5. Server verifies principal, thread ownership, project ownership, input bounds and capability support.
6. Server loads canonical history and authorized context through the Oracle spine.
7. Gemini adapter returns ordered output/events; client renders without reordering or duplication.
8. Server persists turn and terminal status using canonical Knowledge OS persistence.
9. UI reports completion only after durable confirmation, with actual provider and provenance metadata.
10. Refresh/reopen verifies the same transcript and permits continuation in the same thread.

## 4. Existing-vs-required matrix

| Capability | Repository evidence | V1 disposition |
|---|---|---|
| Basic Arkana page | Exists | Elevate visual/interaction quality |
| Firebase identity | Exists in console/auth | Reuse; verify protected turn semantics |
| Gemini call/key pool | Exists | Reuse behind adapter seam |
| Knowledge OS retrieval | Exists in Oracle spine/context engine | Reuse; verify owner/project filters and report errors |
| Source provenance | Exists for injected Knowledge OS notes and RAG refs | Preserve and expose retrieval status |
| Thread CRUD/read | Exists, owner-scoped | Integrate into active conversation lifecycle |
| Thread append turn | Not established | Implement against canonical store |
| Streaming | Not established for Arkana route | Verify and implement; no fake streaming |
| Durable completion acknowledgment | Not established; archive is background | Required before V1 acceptance |
| Client history authority removal | Not satisfied; browser supplies recent history | Required |
| Thread resume/continue | Not satisfied; history UI read-only | Required |
| Stop/cancellation | Not established | Implement where provider supports; otherwise honest limited semantics |
| Anonymous persistence policy | Not established as coherent contract | Decide before launch; default is no durable ownerless archive |
| Mobile/accessibility acceptance | Existing shared foundations; Arkana-specific acceptance absent | Verify as part of slice |

## 5. Acceptance gates

1. Identity required for persistent threads; anonymous policy is explicit and enforced.
2. Cross-user thread read, rename and turn append are rejected without information leak.
3. Cross-user project context is rejected and not retrieved.
4. New thread and both message roles are durable and reopenable after refresh.
5. Concurrent/duplicate submission preserves ordering and idempotency.
6. Stream deltas are ordered; reconnect does not duplicate a turn; terminal event occurs once.
7. Completion reports durable persistence only after a canonical read confirms it.
8. Provider, retrieval and persistence failures are distinguishable and recoverable; no fabricated answer.
9. Displayed sources are exactly the materials retrieved and injected; empty retrieval differs from retrieval failure.
10. Stop/cancel behavior is verified against the provider and leaves an accurate partial/persisted state.
11. Keyboard, focus, screen-reader announcement, contrast, reduced motion and mobile layout meet defined checks.
12. Existing shared Oracle spine and other consumers remain functional; no parallel memory/database or authority path is introduced.

These are acceptance criteria, not a claim that tests currently exist or pass. Implementation should add focused tests for the newly introduced contracts and run the relevant existing regression checks.

## 6. Delivery increments

- **A0 — Reconciliation (this document set):** map source truth and define contracts; no implementation.
- **A1 — Experience foundation:** tokens, shell, responsive empty/active states and accessibility structure.
- **A2 — Canonical conversation lifecycle:** integrate thread create/select/read/append with owner and project checks.
- **A3 — Provider runtime and streaming:** Gemini adapter, event protocol, cancellation/recovery and idempotency, conditional on verified transport support.
- **A4 — Persistence/provenance hardening:** durable completion, source status and failure semantics.
- **A5 — Acceptance:** focused authorization/isolation/persistence/stream/UI checks and shared-consumer regression verification.

Do not advance a later increment by treating a design mock, static UI or successful provider call as proof of end-to-end acceptance.

## 7. Release blockers and unresolved decisions

- Confirm the canonical deployed API's actual OpenAPI and intermediary streaming behavior.
- Choose whether persistent Arkana conversations require sign-in and define anonymous ephemeral behavior.
- Reconcile existing Oracle archive note formats with first-class turn writes without duplicating or losing historical turns.
- Define idempotency storage/transaction boundary using canonical persistence rather than a parallel store.
- Confirm Gemini library streaming and cancellation behavior currently installed/configured.
- Establish supported message/file limits, retention/deletion policy, and rate/cost controls.
- Verify project-context ownership through retrieval and archive, not only thread creation.

## 8. Stop conditions

Stop implementation and return for architecture review if meeting V1 requires a parallel memory database, a new identity/authorization authority, an unverified production deployment assumption, provider credential exposure, or falsely reporting completion without durable evidence.