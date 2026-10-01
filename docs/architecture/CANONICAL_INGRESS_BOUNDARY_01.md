# Canonical Ingress Boundary 01

Status: AUTHORIZED
Mode: ARCHITECTURE CONTRACT / BOUNDED IMPLEMENTATION PREPARATION
Authority: HUMAN
Source of truth: CURRENT REPOSITORY + CURRENT RUNTIME

## Objective

Promote the existing GATE-01 canonical SOURCE/CAPTURE/AUTHORSHIP capability into the shared ingress boundary for Arkadia without creating a second provenance system, second Knowledge OS write path, second graph, second runtime, or second authorization/execution spine.

The intended invariant is:

SOURCE -> CAPTURE -> CANONICAL OBJECT -> RELATIONAL GRAPH -> INTERPRETATION -> CONTEXT -> AUTHORIZATION -> ACTION -> WORK/EVIDENCE

The first four stages establish what entered Arkadia and where it came from. Later stages may interpret or act on that object, but must not retroactively redefine its origin.

## Existing canonical primitives

The repository already provides:

- `knowledge.capture.register_source()`
- `knowledge.capture.capture()`
- `knowledge.capture.bind_capture_to_note()`
- `knowledge.capture.provenance_for_capture()`
- `knowledge.capture.provenance_for_note()`
- `knowledge.capture.capture_and_ingest()`
- existing `knowledge.pipeline.ingest()`
- Knowledge OS SQLite as the canonical durable knowledge substrate
- the canonical relational graph vocabulary
- the canonical Oracle runtime and context assembly
- SolSpire WorkEvent as the operational evidence spine

These are to be extended, not replaced.

## Boundary rule

Every system ingress that creates, archives, interprets, routes, or derives a durable Arkadia object must have a traceable origin/capture boundary before downstream interpretation or object creation.

The implementation must prefer the smallest common interception point.

Do not introduce a universal middleware abstraction merely for conceptual symmetry if the repository has a more direct existing seam.

## Authorship rule

Authorship is declared, never inferred.

If the author is unavailable or cannot be established from the ingress contract, store UNKNOWN.

Captured-by and authored-by remain distinct.

A system actor that receives or records an artifact is not thereby its author.

## Graph rule

The relational graph must remain the canonical relationship substrate.

Do not create a second provenance graph.

Where the existing graph vocabulary can represent origin/authorship relationships, use that vocabulary rather than inventing parallel relationship names.

Provenance metadata and graph relationships may coexist, but their semantics must remain distinct and inspectable.

## Operational separation

Do not move authorization, execution, or WorkEvent semantics into capture.

Capture establishes origin and immutable raw evidence.

Authorization establishes legitimate permission.

Execution establishes consequential action.

WorkEvent establishes operational continuity/evidence.

No upstream capture success authorizes downstream execution.

## Required ingress audit

Before implementation, trace at minimum:

Oracle/conversation ingress;
Knowledge API ingress;
document/file ingestion;
corpus ingestion;
GitHub or external synchronization;
SolSpire conversation/action ingress;
proposal/orchestration ingress;
agent/system-generated ingress;
WorkEvent creation;
any direct calls to `knowledge.pipeline.ingest()`;
any direct Knowledge OS writes that bypass `pipeline.ingest()`.

For each path record:

entry point;
first durable write;
current capture/authorship behavior;
canonical object produced;
graph relationship behavior;
authorization boundary, if applicable;
WorkEvent/evidence boundary, if applicable;
bypass status;
smallest viable interception seam.

## Implementation constraints

No new database.

No new memory system.

No new graph.

No second context assembler.

No second conversational runtime.

No inference of authorship.

No mutation during retrieval.

No authorization or execution changes in this workstream.

No merge or production acceptance may be inferred from tests alone.

Existing GATE-01 behavior must remain behavior-compatible.

## Verification requirements

The implementation must prove at least:

A raw ingress produces a registered source and capture record before downstream canonicalization.

The capture record retains the exact raw checksum.

Known authorship is preserved.

Unknown authorship remains UNKNOWN.

Captured-by and authored-by remain distinct.

Duplicate source registration remains idempotent.

Existing Knowledge OS ingestion remains the single canonical durable write path.

Existing Oracle continuity remains intact.

Existing WorkEvent authorization/execution boundaries remain unchanged.

A direct legacy bypass is either removed, redirected through the boundary, or explicitly classified as a non-runtime migration/test path.

Negative controls demonstrate that bypassing the boundary is detectable.

Architecture tests and the relevant existing suites retain their baseline fingerprint, with any change explicitly attributed.

## Stop conditions

Stop without implementation if the proposed interception would:

create a second durable write path;
collapse provenance into WorkEvent;
collapse authorization into capture;
require changing the canonical relational vocabulary without a separate architectural decision;
change the canonical runtime;
require guessing authorship;
or require changing protected governance/constitutional boundaries.

The next implementation should therefore be a bounded ingress-boundary change, not an architecture rewrite.
