# Arkadia Human Attention Bus · Google Workspace

## Bounded capability

The Weaver Attention Bus converts an already-produced Arkadia/Weaver state change into a bounded human-facing delivery plan.

Contract:

INSPECT → PRODUCE EVENT → CLASSIFY → DELIVER → RECORD → STOP

This is downstream of the existing Weaver governance chain. It does not choose engineering moves, authorize execution, merge, deploy, or promote evidence.

## Surfaces

| Surface | Meaning | Role |
|---|---|---|
| Google Tasks | ACT | Human action queue |
| Google Keep | KNOW | Human-readable response feed |
| Push | NOTICE | Interruptive attention |
| Workspace Studio | ROUTE | Google workflow trigger |

Arkadia remains canonical.

## Google Workspace path

Preferred architecture:

Weaver → AttentionEvent → Workspace Studio custom starter → configured Workspace flow

Workspace Studio exposes a custom starter mechanism for external services and a REST trigger endpoint. Arkadia can fire one event at a time with requestId=event_id for replay-safe delivery.

A Workspace flow can then fan the event into Google-native steps. This keeps Google as the presentation/automation layer rather than allowing Google surfaces to become an Arkadia state store.

## Google Tasks

A narrow REST adapter is included for direct task creation when a governed OAuth access token is supplied.

Required scope:

https://www.googleapis.com/auth/tasks

The adapter does not obtain or persist credentials.

## Google Keep

The capability does not hard-code a direct Keep credential path into the Weaver worker.

Google's current Keep API is oriented toward enterprise administration and requires Keep OAuth authorization. The safer bounded route is therefore:

AttentionEvent → Workspace Studio → configured Keep-capable flow

A future direct Keep adapter may be added as a separate bounded move if the target Workspace account and authorization model are confirmed.

## Idempotency

event_id is the canonical delivery key.

A local JSONL outbox records pending channel deliveries. The outbox never changes the canonical event and never treats external delivery as proof of state.

## Human authority

Task completion means only:

human acknowledged / acted on task

It never means:

authorized

executed

verified

or

accepted.

## Current execution boundary

The existing Weaver scheduler remains one-move-per-cycle and human-review gated.

This capability is an adapter layer only. It does not replace the scheduler, trajectory router, execution adapter, or review boundary.

## Configuration

Google Tasks direct delivery requires a caller-supplied OAuth access token.

Workspace Studio delivery requires:
- OAuth access token with https://www.googleapis.com/auth/workspace.studio.trigger
- configured custom starter trigger_id
- an active Workspace Studio flow

No secrets belong in the repository.

## Current implementation boundary

Implemented in this bounded move:
- AttentionEvent V1 and deterministic channel classification.
- Durable local JSONL outbox with event/channel idempotency.
- Worker review-boundary event recording.
- Direct Google Tasks REST adapter behind caller-supplied OAuth.
- Workspace Studio custom-starter trigger adapter behind caller-supplied OAuth.
- No external delivery is enabled by default.

The next bounded move is external Workspace authorization/configuration, not another scheduler.

## Future bounded moves

1. Configure Workspace Studio custom starter and a Keep feed flow.
2. Add typed delivery acknowledgements to the evidence ledger.
3. Add governed push adapter.
4. Add standing Arkana attention policies.
