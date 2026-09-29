# CP-MOVE7 — Proposal Feedback Loop

**SCHEMA_ONLY / READ_ONLY / NORMATIVE / TECHNOLOGY_NEUTRAL**

No implementation, provisioning, runtime mutation, authority grant, or new memory system. K15 → K3 remains the sole mutation boundary.

## Purpose

A bounded lifecycle for presenting a proposal, receiving feedback, revising it, returning it for human decision, and preserving proposal history.

> **Feedback can change a proposal. It cannot become the authority to execute the proposal.**

`PROPOSAL → FEEDBACK → REVISION → HUMAN DECISION → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3`

This is descriptive flow, not automatic authorization.

## Distinctions

`PROPOSAL ≠ AUTHORITY`
`FEEDBACK ≠ AUTHORIZATION`
`REVIEW ≠ APPROVAL`
`REVISION ≠ EXECUTION`
`ACCEPTANCE SIGNAL ≠ HUMAN AUTHORITY EVENT`
`CONSENSUS ≠ SOVEREIGN AUTHORIZATION`
`RECOMMENDATION ≠ DECISION`
`DECISION ≠ EXECUTION`
`PROPOSAL STATUS ≠ AUTHORIZATION`
`FEEDBACK HISTORY ≠ PROVENANCE`
`ITERATION ≠ CAUSATION`
`LOOP ≠ AUTONOMOUS AGENT`
`LOOP ≠ MEMORY SYSTEM`

## Conceptual schema

```text
proposal_id
proposal_version
workload_ref
workspace_ref
subject_ref
objective
scope
assumptions
alternatives
requested_decision
proposal_status
feedback_refs
revision_refs
decision_ref
provenance_ref
authorization_ref
evidence_refs
work_event_refs
supersedes_ref
effective_from
effective_until
closure_ref
integrity_ref
created_by_event
schema_version
```

Feedback may reference its own id, proposal, reviewer, submission time, type, observation, question, objection, recommendation, evidence, response, status, and creation event. These are vocabulary fields only.

## States

`DRAFT / PRESENTED / UNDER_REVIEW / REVISION_REQUESTED / REVISED / DECISION_PENDING / ACCEPTED / DECLINED / WITHDRAWN / SUPERSEDED / DISPUTED / UNKNOWN`

`ACCEPTED ≠ AUTHORIZED`
`DECISION_PENDING ≠ DECISION MADE`
`AUTHORIZED ≠ EXECUTED`
`EXECUTED ≠ VERIFIED`

If `ACCEPTED` is ever implemented, its meaning must remain explicit. It cannot silently mean `AUTHORIZED`.

## Feedback and human decision

Feedback may challenge assumptions, request evidence, propose alternatives, identify risks, flag scope conflicts, request clarification, or recommend revision.

`FEEDBACK → HUMAN DELIBERATION`
`FEEDBACK ≠ HUMAN AUTHORITY EVENT`
`FEEDBACK ≠ AUTHORIZATION`

Positive feedback, unanimous review, reviewer identity, authenticated session, proposal signature/hash, repeated acceptance, workload ownership, or workspace membership cannot substitute for independent event-origin evidence.

Decisive test: if unanimous positive feedback existed without independent provenance evidence for the required authority event, would feedback itself establish human-origin authority? **NO.**

## Scope boundary

`FEEDBACK → SCOPE CHANGE REQUEST`
`SCOPE CHANGE REQUEST ≠ AUTHORIZED SCOPE`
`PROPOSAL REVISION ≠ AUTHORIZATION`
`WORKLOAD UPDATE ≠ AUTHORIZATION`

Iteration must not smuggle authority expansion into the workload.

## Execution boundary

The loop cannot execute a proposal, dispatch autonomous tasks, place commercial orders, authorize procurement/trading, modify a repository, publish protected changes, invoke K3, bypass K15, or create an alternate mutation path.

Protected chain:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION → COMMIT → PUSH → VERIFICATION → PUBLICATION`

## WorkEvent and synthesis boundaries

`PROPOSAL EXISTS → WORK EVENT OCCURRED = NO`
`FEEDBACK EXISTS → WORK EVENT OCCURRED = NO`
`REVISION EXISTS → HUMAN AUTHORITY EVENT = NO`
`PROPOSAL HISTORY → CAUSAL ORIGIN = NO`

Weekly Synthesis may surface proposals. The feedback loop may return revised state to later synthesis. Neither becomes automatic authorization.

## History and memory

`PROPOSAL₁ → REVISION → PROPOSAL₂ → REVISION → PROPOSAL₃`

`REVISION ≠ ERASURE`
`SUPERSESSION ≠ AUTHORIZATION`
`CURRENT PROPOSAL ≠ HISTORICAL PROPOSAL`

The loop is not a new memory system. No hidden conversational memory, autonomous proposal agent, sovereign knowledge graph, parallel identity archive, or independent retrieval authority may be introduced.

## Fail-closed tests

Fail closed for ambiguous proposal identity, broken version lineage, missing workload/subject binding, contradictory feedback, unresolved evidence, disputed decision, unclear decision owner, ambiguous acceptance semantics, provenance claims without origin evidence, authorization claims without authorization determination, automatic scope expansion, autonomous execution, hidden persistence, alternate authority, or K15/K3 bypass.

P01 feedback sufficiency: NO.  
P02 consensus upgrade: NO.  
P03 acceptance upgrade: NO.  
P04 reviewer upgrade: NO.  
P05 session upgrade: NO.  
P06 proposal provenance: NO.  
P07 scope laundering: NO.  
P08 WorkEvent substitution: NO.  
P09 execution/K3 substitution: NO.  
P10 memory drift: NO.  
P11 historical laundering: NO.  
P12 unknown conversion: NO.  
P13 decision substitution: NO.  
P14 decision-execution collapse: NO.

## Inspectability and gate

Future implementation must expose proposal lineage, feedback sources, evidence, unresolved objections, scope changes, pending decision, independent human decision event, provenance, authorization, execution status, supersession, and closure.

Implementation requires Move 0 passed, Move 1 explicitly authorized/verified as applicable, Moves 2–6 explicitly authorized, and explicit human authorization for Move 7. No proposal or feedback state may create identity, provenance, authorization, execution, memory authority, or an alternate mutation path. K15 remains immediately before K3.

## Non-claims

No Proposal Feedback Loop exists. No proposal is accepted or authorized by this document. No feedback or Barnabas data is ingested. No workload, workspace, Architect Identity, memory system, or runtime process is instantiated. Move 0 remains blocked. No credentials or K15/K3 boundary changes occur. Implementation is not authorized.

`AUTHORED → ISOLATED → REVIEWED → VERDICT → HUMAN DECISION → MERGED → IMPLEMENTATION GATE → IMPLEMENTED → VERIFIED`
