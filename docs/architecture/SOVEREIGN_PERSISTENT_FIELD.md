# SOVEREIGN PERSISTENT FIELD

**Status:** Implementation proposal instantiated on feature/sovereign-persistent-field  
**Scope:** SolSpire sovereign access identity, persistent field, Eden Buyer Recon  
**Authority boundary:** Sovereign access permits inspection and maintenance of the field. It does not authorize commercial execution.

## Purpose

The sovereign identity is now the durable entry boundary for a private operating field that persists across sessions.

The field is not a second identity system, hidden graph database, or autonomous operating authority. It is a persistent projection substrate attached to the canonical Firebase subject and canonical SolSpire workspace.

The field is resolved idempotently. A sovereign session does not create a new field. It resolves the existing field for the authenticated subject, creating it only when that subject has never had one.

## Architectural position

Firebase Identity → require_sovereign → Canonical SolSpire Workspace → Persistent Sovereign Field → Eden Buyer Recon → Requirement Captured → Commercial Confirmation → Existing Eden execution spine.

The Buyer Recon surface therefore extends the existing Eden architecture upstream. It does not replace EDEN-OPS or create a parallel transaction engine.

## Session semantics

Every authenticated sovereign session resolves the same field using the Firebase subject UID.

The persisted key is subject_ref → field_id → workspace_ref.

The client may expose the field through the authenticated identity surface, but client state is not the authority. The server enforces sovereign access.

## Hidden OS semantics

“Hidden” means intentionally absent from primary navigation, not secret security.

The field is available only through the existing sovereign access boundary. Its dashboard is a projection over durable state. It cannot authorize a transaction, create provenance, or execute consequential work.

## Buyer Recon

Buyer Recon is the first concrete operating surface in the persistent field.

Its lifecycle is:
UNCONTACTED → CONTACTED → CONVERSATION → REQUIREMENT_CAPTURED → PRICE_CONFIRMED → BUYER_COMMITMENT → SUPPLIER_CONFIRMED → ECONOMICS_CLOSED → READY_TO_EXECUTE → EXECUTED → SETTLED.

Every commercial attribute defaults to UNKNOWN. The system does not convert a contact, conversation, or AI inference into a commercial fact without evidence.

## Relationship to the existing architecture

Solariun remains the personal canvas.

SolSpire remains the enterprise workspace.

Eden remains the instantiated enterprise.

EDEN-OPS remains the execution substrate.

The Sovereign Persistent Field becomes the private control-plane projection that survives session boundaries and provides the upstream demand-acquisition surface needed to move Eden from intelligence into a real transaction.

No second universal object database is introduced.

No client-side sovereign flag is introduced.

No transaction execution authority is introduced.
