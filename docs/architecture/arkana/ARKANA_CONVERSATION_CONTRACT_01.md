# Arkana Conversation Contract 01

**Status:** Proposed contract for implementation review. Existing endpoints and semantics are described separately. No API behavior is changed by this document.

## 1. Existing contracts (verified)

- `POST /api/commune/resonance` accepts `message`, `history`, `session_id`, optional `project_id`, and optional signal/audio fields. It returns JSON with `reply`, resonance/pattern fields, RAG references, Knowledge OS sources and memory diagnostics.
- The route optionally resolves the current user for personal context; it is not the authenticated first-class thread turn API.
- Successful response archival is launched on a daemon thread; durable completion is not awaited or reported.
- `GET/POST /api/commune/threads`, `GET/PATCH /api/commune/threads/{uuid}`, and `GET /api/commune/threads/{uuid}/messages` are implemented in `api/commune_threads.py`. They require verified user identity. Thread creation validates project ownership. Message reads are projected from canonical conversation notes.
- The existing thread API does not provide append-turn, delete, streaming, cancellation or retry/idempotency behavior.

The proposed path names and envelopes below require reconciliation against deployment/OpenAPI consumers before implementation. Prefer extending compatible existing routes or adding a versioned route deliberately rather than silently changing current response semantics.

## 2. Proposed conversation invariants

1. The server resolves the authenticated principal and owns the thread-to-user association.
2. A client-supplied thread UUID is only a lookup key; every operation verifies ownership.
3. The canonical transcript is server-side. Browser history is never authoritative prompt context.
4. Every submitted turn has an idempotency key and stable server turn ID to prevent duplicate persistence on retry/reconnect.
5. User and assistant turn ordering is durable and explicit.
6. A completion event may claim persistence only after the canonical store confirms the write.
7. Provenance identifies only retrieved material actually injected into the provider request.
8. Anonymous interaction has an explicit non-persistent policy or a separately authorized ephemeral session contract; it must not silently create an ownerless durable thread.
9. Project identifiers are validated against the same authenticated owner before retrieval, generation or persistence.

## 3. Proposed endpoints

| Method/path | Purpose | Auth |
|---|---|---|
| `GET /api/commune/threads` | List current user's threads | Required |
| `POST /api/commune/threads` | Create canonical thread | Required |
| `GET /api/commune/threads/{uuid}` | Read thread metadata | Required |
| `PATCH /api/commune/threads/{uuid}` | Rename metadata | Required |
| `GET /api/commune/threads/{uuid}/messages` | Read canonical transcript | Required |
| `POST /api/commune/threads/{uuid}/turns` (proposed) | Submit an idempotent turn and stream response | Required |
| `POST /api/commune/turns/{turn_id}/cancel` (proposed, only if transport cannot cancel) | Request cancellation | Required |

A single POST request using SSE is preferred initially if infrastructure supports streaming; the turn route is a proposal, not an existing implementation. Choose transport after verifying proxy/deployment behavior and cancellation support.

## 4. Proposed turn request

```json
{
  "message": "...",
  "idempotency_key": "client-generated-unique-value",
  "project_id": null,
  "mode": "auto",
  "attachments": []
}
```

For the first slice, `mode` may be omitted or restricted to the one supported behavior. Attachments remain empty until a server-side ingestion contract exists. The server derives user identity; request data cannot set user ownership or authoritative history.

## 5. Proposed ordered event protocol

Use `text/event-stream` with explicit event names and JSON data. Event payloads are suggestions; finalize schemas with implementation/tests.

```text
event: turn_started
data: {"turn_id":"...","thread_uuid":"..."}

event: context_status
data: {"status":"ready","sources":[],"retrieval":"completed"}

event: provider_selected
data: {"provider":"gemini","model":"reported-model-id"}

event: content_delta
data: {"sequence":1,"text":"..."}

event: turn_completed
data: {"turn_id":"...","persisted":true,"assistant_message_id":"..."}
```

Terminal variants: `turn_failed` with stable error code and retryability; `turn_cancelled` with partial-content and persistence status. Send a terminal event at most once. A transport interruption is not a successful completion. Reconnecting clients query canonical thread/turn state or retry with the same idempotency key; they do not blindly create a second turn.

## 6. Message/read model

```typescript
interface ConversationMessage {
  id: string;
  threadUuid: string;
  turnId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  status: "pending" | "streaming" | "complete" | "failed" | "cancelled";
  provider?: string;
  provenance?: {
    sources: SourceReference[];
    retrievalStatus: "completed" | "empty" | "unavailable";
  };
}
```

This is a transport/read model, not permission to add a parallel message database. Map it to canonical Knowledge OS persistence and preserve compatibility with the existing conversation-note projection or define a migration/reconciliation plan first.

## 7. Persistence and cancellation semantics

- Persist/associate the user turn and generation state before or as part of generation, with idempotency protection.
- Persist assistant output and terminal status through the canonical store.
- `persisted: true` means the completed assistant turn is durably readable through the owner-scoped thread read contract.
- If provider generation succeeds but persistence fails, report a persistence failure distinctly; do not claim completion or lose recoverable output.
- Cancellation requests provider cancellation where supported; otherwise mark cancellation as best-effort and disclose continued provider work if it cannot be stopped.
- Define behavior for partial output, client disconnect, server restart, retry, provider timeout and duplicate request before release.

## 8. Error envelope

Return structured, stable codes for authentication required, thread not found, invalid request, rate limit, provider unavailable, context unavailable (if blocking), stream interruption and persistence failure. Do not expose API keys, raw credentials or private provider diagnostics. Keep owner-mismatch response indistinguishable from absent thread where appropriate.

## 9. Compatibility and rollout gates

Before implementation, inspect OpenAPI and all existing clients of `/api/commune/resonance` and thread routes. Preserve the existing non-streaming route until a deliberate compatibility decision is tested. Version event schemas; test authorization, cross-owner rejection, idempotency, ordering, durable completion, cancellation, reconnect and provenance against the actual canonical store.