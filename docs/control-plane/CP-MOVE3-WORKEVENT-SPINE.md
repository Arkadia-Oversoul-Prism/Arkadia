# CP-MOVE3 — WorkEvent Spine

**Status:** SCHEMA_ONLY / READ_ONLY / NORMATIVE DESIGN  
**Technology:** Technology-neutral  
**Implementation:** NOT AUTHORIZED  
**Provisioning:** NOT PERFORMED  
**Runtime Mutation:** NONE  
**Authority Grant:** NONE  
**Memory System:** NONE CREATED  
**Move 0:** BLOCKED  
**Move 1:** BLOCKED  
**Move 2:** DESIGN MERGED / IMPLEMENTATION NOT AUTHORIZED  
**K15/K3:** UNCHANGED

---

## 1. Purpose

This artifact defines the proposed **WorkEvent Spine** as the central continuity vocabulary for governed work in Arkadia.

It establishes a schema-level boundary for representing discrete, inspectable events in the life of governed work without creating a new memory system, execution engine, authority system, provenance mechanism, or mutation path.

The WorkEvent Spine exists conceptually to answer a narrow question:

> **What happened to the governed work, in what context, and how can that occurrence be referenced without confusing the record of an event with authority over the event?**

The WorkEvent Spine is therefore a continuity record, not a sovereign actor.

It may preserve a thread of work across time. It may not become the authority over that work.

---

## 2. Constitutional Boundary

The WorkEvent Spine MUST preserve the governing chain:

`HUMAN SOVEREIGNTY → IDENTITY → WORKSPACE → WORKEVENT → GOVERNED ACTION → K15 → K3`

The addition of WorkEvent does not insert a new authority layer into that chain.

The protected execution chain remains:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION`

The WorkEvent Spine may record references to stages in this chain where such references legitimately exist. It cannot manufacture any stage merely by recording a reference to it.

---

## 3. Permanent Distinctions

CP-MOVE3 MUST preserve all prior permanent distinctions and extend them with continuity-specific separations.

### Existing distinctions

- `IDENTITY ≠ AUTHORITY EVENT ≠ PROVENANCE ≠ AUTHORIZATION ≠ EXECUTION`
- `PROVISIONING EVENT ≠ RESULTING IDENTITY`
- `DOCUMENTATION ≠ OPERATION`
- `FILESYSTEM REMOVAL ≠ HISTORY REMOVAL`
- `ATTESTATION ≠ ORIGINATION`
- `PRECEDENCE ≠ CAUSATION`
- `IDENTITY-DEPENDENCE ≠ EVIDENCE OF CAUSAL ORIGINATION`
- `WORKSPACE ≠ AUTHORITY`
- `WORKSPACE STATE ≠ PROVENANCE`
- `WORKSPACE STATE ≠ AUTHORIZATION`

### WorkEvent-specific distinctions

- `WORKEVENT ≠ AUTHORITY EVENT`
- `WORKEVENT ≠ PROVENANCE`
- `WORKEVENT ≠ AUTHORIZATION`
- `WORKEVENT ≠ EXECUTION`
- `WORKEVENT RECORD ≠ EVENT ORIGINATION PROOF`
- `EVENT REFERENCE ≠ EVENT OCCURRENCE`
- `EVENT OCCURRENCE ≠ HUMAN DELIBERATE ORIGIN`
- `CONTINUITY ≠ MEMORY SYSTEM`
- `HISTORY ≠ AUTHORITY`
- `SEQUENCE ≠ CAUSATION`
- `TEMPORAL ORDER ≠ HUMAN INTENT`
- `EVENT CHAIN ≠ SOVEREIGN CHAIN`

These distinctions are load-bearing. No future implementation may collapse them for convenience.

---

## 4. Definition

A **WorkEvent** is a bounded, inspectable representation of an occurrence relevant to a governed work context.

A WorkEvent may describe, for example:

- creation of a governed work item;
- transition of a work item between declared states;
- attachment of a document or artifact;
- review or inspection occurrence;
- human decision record;
- approval record;
- implementation-stage observation;
- verification observation;
- handoff between governed work contexts;
- closure or suspension of a work thread.

The examples are vocabulary only. They do not authorize any operation.

A WorkEvent is a **record about an occurrence**. It is not the occurrence itself, and it is not automatically evidence that the claimed occurrence was caused by a particular human subject.

---

## 5. The Core Continuity Problem

Without a bounded continuity record, a governed workspace can become temporally fragmented:

`WORKSPACE STATE₁ → WORKSPACE STATE₂ → WORKSPACE STATE₃`

A later observer may see states without a precise vocabulary for the transitions between them.

The WorkEvent Spine introduces a conceptual continuity relation:

`WORK CONTEXT → EVENT₁ → EVENT₂ → EVENT₃ → CURRENT STATE`

This relation is descriptive, not authoritative.

Temporal ordering does not establish causation.

Event adjacency does not establish human intent.

A later WorkEvent cannot retroactively prove the provenance of an earlier event.

The spine therefore preserves continuity without laundering continuity into authority.

---

## 6. Proposed WorkEvent Schema Boundary

A future WorkEvent object MAY contain the following conceptual fields:

- `work_event_id`
- `event_type`
- `event_version`
- `occurred_at`
- `recorded_at`
- `effective_from`
- `effective_until`
- `subject_ref`
- `workspace_ref`
- `work_ref`
- `parent_event_ref`
- `causal_parent_ref`
- `sequence_ref`
- `scope_ref`
- `actor_ref`
- `authority_event_ref`
- `provenance_ref`
- `authorization_ref`
- `pass_spec_ref`
- `mutation_ref`
- `artifact_refs`
- `state_before_ref`
- `state_after_ref`
- `decision_ref`
- `witness_ref`
- `status`
- `integrity_ref`
- `supersedes_ref`
- `reversal_of_ref`
- `created_by_event`
- `schema_version`

These are **vocabulary-level fields**, not an implementation mandate.

The presence of a field does not imply that its referenced object exists, is valid, is authoritative, or is proven.

No secret, private key, provider credential, access token, password, or equivalent credential belongs in a WorkEvent object.

---

## 7. Event Identity

`work_event_id` identifies the WorkEvent record within the future governed model.

Event identity MUST remain distinct from:

- the identity of the human subject;
- the identity of an Architect role;
- the identity of a workspace;
- the identity of an authority event;
- the identity of a provenance claim;
- the identity of a mutation;
- the identity of any external provider object.

A WorkEvent identifier does not prove who caused the event.

A WorkEvent identifier does not create an authority relationship.

A WorkEvent identifier does not establish provenance.

---

## 8. Occurrence Time vs Recording Time

The WorkEvent vocabulary deliberately separates:

`occurred_at ≠ recorded_at`

An event may be recorded after the occurrence it describes.

This distinction prevents the time at which a record is created from being silently treated as the time at which the underlying occurrence happened.

Likewise:

`recorded_at ≠ authority event time`

unless a separate authority-event record legitimately establishes that relationship.

Temporal metadata is evidence about chronology. It is not, by itself, evidence of human origination.

---

## 9. Sequence and Causation

A WorkEvent Spine may establish an inspectable sequence:

`E₁ → E₂ → E₃ → E₄`

but sequence MUST NOT be interpreted as causal proof.

The following implication is prohibited:

`E₁ precedes E₂ → E₁ caused E₂`

Likewise:

`Human subject appears on E₂ → human subject caused E₂`

is invalid unless separate provenance/origin evidence establishes that claim.

This preserves the CP-10 distinction:

`PRECEDENCE ≠ CAUSATION`

and extends it to continuity records.

---

## 10. Actor vs Origin

A future WorkEvent MAY reference an `actor_ref` or `subject_ref`.

That reference MUST NOT automatically establish:

- deliberate human action;
- authority exercise;
- causal origination;
- provenance;
- authorization;
- execution permission.

The semantic chain remains:

`SUBJECT REFERENCE → EVENT CLAIM → ORIGIN EVIDENCE → PROVENANCE STATE → AUTHORIZATION`

A WorkEvent can point to evidence. It cannot become the evidence merely by pointing to itself.

---

## 11. Authority Event Relationship

An **Authority Event** is distinct from a WorkEvent.

An authority event concerns the exercise of defined authority by an authorized subject over a bounded scope.

A WorkEvent may record that an authority event was referenced, observed, approved, or associated with governed work.

It MUST NOT infer:

`WORKEVENT EXISTS → AUTHORITY EVENT OCCURRED`

Nor may it infer:

`WORKEVENT EXISTS → HUMAN AUTHORIZED THE WORK`

If a future WorkEvent contains `authority_event_ref`, the reference remains a reference until the underlying authority-event semantics and provenance state are independently established.

---

## 12. Provenance Relationship

The WorkEvent Spine does not replace CP-10 provenance.

The provenance chain remains:

`AUTHENTICATED SUBJECT → AUTHORITY EVENT → ORIGIN EVIDENCE → PROVENANCE STATE → AUTHORIZATION DETERMINATION`

A WorkEvent may carry `provenance_ref` where a valid provenance object exists.

It MUST NOT create provenance merely because:

- the event exists;
- the event is signed or hashed;
- the event is associated with an authenticated session;
- the event is present in a workspace;
- the event appears in chronological order;
- a later reviewer accepts the event record;
- a downstream system relies upon the event.

`WORKEVENT ≠ PROVENANCE`

---

## 13. Authorization Relationship

Authorization remains a separate determination.

A WorkEvent may describe an authorization decision or reference one:

`authorization_ref`

but it cannot derive authorization from its own existence.

The following are prohibited semantic upgrades:

- `WORKEVENT → AUTHORIZED`
- `EVENT_CHAIN → AUTHORIZED`
- `WORKSPACE + WORKEVENT → AUTHORIZED`
- `AUTHENTICATED SUBJECT + WORKEVENT → AUTHORIZED`
- `SIGNED WORKEVENT → AUTHORIZED`
- `HASHED WORKEVENT → AUTHORIZED`

Authorization must remain independently determined within the governing chain.

---

## 14. Execution and K15/K3 Boundary

The WorkEvent Spine is not an execution engine.

It MUST NOT:

- execute commands;
- mutate repositories;
- grant authority;
- authorize itself;
- invoke K3 directly;
- create an alternate mutation path;
- bypass K15;
- turn an event record into permission to execute.

If a future implementation records a mutation-related WorkEvent, the event is a record of the mutation lifecycle, not the mutation authority.

The sole mutation boundary remains:

`K15 → K3`

and the full protected sequence remains:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION → COMMIT → PUSH → VERIFICATION → PUBLICATION`

A WorkEvent may describe these stages. It may not collapse them.

---

## 15. Continuity Without a New Memory System

The WorkEvent Spine is explicitly **not a new memory system**.

It defines a continuity record vocabulary for governed work. It does not define:

- a memory database;
- a vector store;
- an autonomous memory agent;
- a retrieval authority;
- a hidden state layer;
- an independent knowledge graph;
- a parallel archive of sovereign identity;
- a new persistence subsystem.

Continuity means that governed work can be represented as a traceable sequence of declared events.

It does not mean that the event spine becomes the authoritative source of all knowledge, identity, intent, or history.

`CONTINUITY ≠ MEMORY SYSTEM`

---

## 16. Event Immutability and Historical Integrity

A future implementation SHOULD preserve the historical identity of a WorkEvent once it has entered a governed event sequence.

Where correction is necessary, the preferred vocabulary is a new event that explicitly supersedes, reverses, corrects, or annotates the earlier record rather than silently rewriting the historical meaning of the earlier event.

This is a schema-level integrity principle, not an implementation mandate.

The conceptual relation is:

`E₁ → E₂(corrects E₁)`

rather than:

`E₁ silently becomes E₁'`

Historical integrity does not establish historical authority.

A preserved event record is still not proof of human origination unless the relevant provenance requirements are independently satisfied.

---

## 17. Event Status

A future WorkEvent MAY use a bounded status vocabulary such as:

`PROPOSED / OBSERVED / RECORDED / VERIFIED / SUPERSEDED / REVERSED / DISPUTED / UNKNOWN`

These statuses are descriptive.

In particular:

- `OBSERVED` does not mean authorized;
- `RECORDED` does not mean true;
- `VERIFIED` does not mean sovereignly authorized;
- `SUPERSEDED` does not erase historical existence;
- `REVERSED` does not mean the original event never occurred;
- `DISPUTED` must remain visible;
- `UNKNOWN` must not silently become `VALID`, `AUTHORIZED`, or `VERIFIED`.

A future implementation must define the evidence and authority required for any transition between these states before treating them as operational states.

---

## 18. Event Types

The following event classes are proposed as vocabulary only:

### 18.1 Formation Events

Events describing the formation or declaration of a governed work context.

Examples:

- `WORK_OPENED`
- `WORK_ATTACHED`
- `WORK_SCOPE_DECLARED`

### 18.2 Human Decision Events

Events describing a human decision or decision record.

Examples:

- `DECISION_RECORDED`
- `APPROVAL_RECORDED`
- `REJECTION_RECORDED`
- `HOLD_DECLARED`

These event labels do not themselves prove human origin or authority. CP-10 provenance requirements remain separate.

### 18.3 Review Events

Events describing inspection, review, validation, or gate evaluation.

Examples:

- `REVIEW_STARTED`
- `REVIEW_COMPLETED`
- `GATE_EVALUATED`
- `VERDICT_RECORDED`

### 18.4 Implementation Lifecycle Events

Events describing an implementation stage where implementation has separately been authorized.

Examples:

- `IMPLEMENTATION_AUTHORIZED`
- `IMPLEMENTATION_STARTED`
- `IMPLEMENTATION_COMPLETED`
- `VERIFICATION_RECORDED`

The existence of an event label does not authorize the corresponding operation.

### 18.5 Continuity Events

Events describing transfer or continuation of governed work.

Examples:

- `HANDOFF_RECORDED`
- `THREAD_RESUMED`
- `THREAD_SUSPENDED`
- `THREAD_CLOSED`

These are continuity records, not authority transfers.

---

## 19. WorkEvent and Workspace

The structural relationship is:

`CANONICAL HUMAN SUBJECT → ARCHITECT IDENTITY (if separately provisioned) → SOLSPIRE WORKSPACE (if separately provisioned) → WORKEVENT SPINE (if separately implemented)`

This is structural only.

The WorkEvent Spine does not inherit authority merely because it is associated with a workspace.

Likewise:

`WORKSPACE OWNERSHIP + WORKEVENT → AUTHORITY`

is invalid.

The governing Move 2 sentence remains active:

> **The workspace may hold the work. It may not become the authority over the work.**

Move 3 extends that boundary:

> **The WorkEvent may preserve the thread of the work. It may not become the authority over the thread.**

---

## 20. WorkEvent and Architect Identity

CP-MOVE1 defines the Architect Identity vocabulary.

CP-MOVE3 does not create, provision, activate, or modify an Architect Identity.

A WorkEvent may reference an Architect Identity if a future legitimate implementation provides such a reference.

It MUST NOT:

- create an Architect Identity;
- upgrade a human subject into an Architect;
- infer Architect authority from `actor_ref`;
- infer Architect authority from `subject_ref`;
- infer Architect authority from workspace membership;
- infer Architect authority from event history.

`EVENT HISTORY ≠ ARCHITECT AUTHORITY`

---

## 21. WorkEvent and Delegation

Delegation must remain explicit and bounded.

A WorkEvent may record a delegation-related occurrence or reference a delegation lineage.

It MUST NOT expand delegation merely by being associated with a delegated subject.

The following is prohibited:

`DELEGATED EVENT → UNBOUNDED AUTHORITY`

A future implementation MUST preserve:

- delegator identity;
- delegated subject;
- delegated scope;
- effective time;
- expiry;
- revocation;
- lineage;
- applicable authority class.

No WorkEvent may manufacture delegation lineage after the fact.

---

## 22. Event Chain Integrity

A future WorkEvent Spine SHOULD make the following relationships inspectable:

`EVENT → PARENT EVENT`

`EVENT → WORK CONTEXT`

`EVENT → SUBJECT REFERENCE`

`EVENT → WORKSPACE REFERENCE`

`EVENT → AUTHORITY EVENT REFERENCE`

`EVENT → PROVENANCE REFERENCE`

`EVENT → AUTHORIZATION REFERENCE`

`EVENT → ARTIFACT REFERENCE`

`EVENT → STATE TRANSITION`

References MUST remain distinguishable from the objects they reference.

A missing or unresolved reference MUST remain visible as missing or unresolved.

The system must not manufacture a valid object merely because a reference field exists.

---

## 23. Failure and Ambiguity States

A future implementation MUST fail closed for at least:

- missing WorkEvent identity;
- duplicate WorkEvent identity;
- contradictory event timestamps;
- impossible temporal ordering where ordering is semantically required;
- unknown subject binding;
- ambiguous workspace binding;
- unresolved work context;
- missing event type;
- invalid event transition;
- authority event referenced but not established;
- provenance referenced but not established;
- authorization referenced but not established;
- mutation referenced without the applicable K15/K3 chain;
- disputed event silently treated as settled;
- superseded event silently treated as current;
- reversed event silently treated as active;
- unknown state silently upgraded;
- event chain used as an alternate authority system;
- event chain used as an alternate mutation path;
- event history used to create an Architect Identity;
- event history used to manufacture human-origin provenance;
- event sequence used as causal proof;
- continuity record used as a substitute for memory governance.

`UNKNOWN MUST REMAIN UNKNOWN UNTIL ITS GOVERNING CONDITION IS SATISFIED.`

---

## 24. Adversarial Self-Tests

### E01 — WorkEvent Sufficiency

**Attack:** `WORKEVENT EXISTS → HUMAN AUTHORIZATION`

**Required result:** REJECT.

### E02 — Sequence Causation

**Attack:** `E₁ PRECEDES E₂ → E₁ CAUSED E₂`

**Required result:** REJECT.

### E03 — Actor Upgrade

**Attack:** `actor_ref = human → HUMAN ORIGIN PROVEN`

**Required result:** REJECT.

### E04 — Authentication Upgrade

**Attack:** `authenticated subject + WorkEvent → authority event proven`

**Required result:** REJECT.

### E05 — Workspace Upgrade

**Attack:** `workspace + WorkEvent → workspace authority`

**Required result:** REJECT.

### E06 — Provenance Substitution

**Attack:** `WorkEvent history → provenance`

**Required result:** REJECT.

### E07 — Authorization Substitution

**Attack:** `WorkEvent status = VERIFIED → authorization`

**Required result:** REJECT.

### E08 — Execution Substitution

**Attack:** `WorkEvent → direct mutation`

**Required result:** REJECT.

### E09 — K15/K3 Bypass

**Attack:** `WorkEvent → K3 without the governing authorization chain`

**Required result:** REJECT.

### E10 — Identity Creation

**Attack:** `event history → Architect Identity`

**Required result:** REJECT.

### E11 — Delegation Expansion

**Attack:** `delegated WorkEvent → broader delegated authority`

**Required result:** REJECT.

### E12 — Historical Laundering

**Attack:** later event rewrites an earlier unproven event into proven origin.

**Required result:** REJECT.

### E13 — Unknown Conversion

**Attack:** `UNKNOWN → VERIFIED` without a governing condition.

**Required result:** REJECT.

### E14 — Memory-System Drift

**Attack:** WorkEvent Spine becomes an autonomous retrieval/memory authority.

**Required result:** REJECT.

### E15 — Parallel Mutation

**Attack:** WorkEvent subsystem introduces a mutation route outside K15 → K3.

**Required result:** REJECT.

---

## 25. Semantic Laundering Tests

The following forms of laundering remain prohibited:

- **L01 Rename:** calling an authority event a WorkEvent and treating it as equivalent;
- **L02 Wrapper:** wrapping an authorization object in a WorkEvent and claiming the WorkEvent itself is authoritative;
- **L03 Duplication:** copying provenance into event history and treating the copy as independent proof;
- **L04 Shadow State:** storing hidden authority state behind event records;
- **L05 Accumulation:** treating many individually insufficient events as automatically sufficient authority;
- **L06 Retrospective Laundering:** using later verified records to manufacture earlier human-origin proof;
- **L07 Sequence Laundering:** converting chronological order into causal evidence;
- **L08 Workspace Laundering:** converting workspace ownership into WorkEvent authority;
- **L09 Status Laundering:** converting `VERIFIED`, `RECORDED`, or `ACTIVE` labels into authorization;
- **L10 Memory Laundering:** converting continuity records into an independent sovereign memory or decision authority.

A future mechanism fails if it relies on any of these substitutions.

---

## 26. No Parallel Authority System

The WorkEvent Spine MUST NOT become:

- a second identity system;
- a second authority system;
- a second provenance system;
- a second authorization system;
- a second mutation system;
- a hidden memory authority;
- an autonomous decision authority.

Its role is continuity representation.

Its semantic power must remain bounded to that role.

---

## 27. Inspectability

A future implementation MUST make the continuity chain inspectable enough to answer, without hidden inference:

1. What event is being represented?
2. When did the claimed occurrence happen?
3. When was it recorded?
4. What work context does it belong to?
5. What workspace, if any, was involved?
6. What subject or actor is referenced?
7. What authority event is referenced, if any?
8. What provenance state is referenced, if any?
9. What authorization decision is referenced, if any?
10. What state transition is being represented?
11. What prior event does it relate to?
12. Is the event disputed, superseded, reversed, or unknown?
13. Does the record make any claim that exceeds the evidence available?

Inspectability must expose uncertainty rather than conceal it.

---

## 28. Non-Claims

This artifact does NOT claim:

- that a WorkEvent exists;
- that a WorkEvent Spine has been implemented;
- that a memory system has been created;
- that any event has occurred;
- that any human authority event has occurred;
- that any provenance has been proven;
- that any authorization has been granted;
- that any Architect Identity exists;
- that any SolSpire Workspace exists;
- that Move 0 has passed;
- that Move 1 is authorized or verified;
- that Move 2 implementation is authorized;
- that any credentials have been created or rotated;
- that any runtime has changed;
- that K15 or K3 has changed;
- that any mutation path exists outside K15 → K3;
- that any mechanism has been selected;
- that any implementation is authorized;
- that any Barnabas data has been ingested;
- that continuity itself creates authority.

---

## 29. Implementation Gate

The WorkEvent Spine remains separately gated from this design artifact.

At minimum:

`MOVE 0 = PASSED`

and

`MOVE 1 = AUTHORIZED / VERIFIED AS APPLICABLE`

and

`MOVE 2 = EXPLICITLY AUTHORIZED FOR IMPLEMENTATION`

and explicit human authorization for Move 3 must exist before any WorkEvent provisioning, persistence, runtime integration, migration, or operational implementation begins.

No schema artifact may be interpreted as permission to implement itself.

The existence of a WorkEvent design does not create a WorkEvent.

---

## 30. Resolution State

The Move sequence remains:

`AUTHOR → ISOLATE → REVIEW → VERDICT → HUMAN DECISION → MERGE → IMPLEMENTATION GATE`

The intended artifact state is:

`AUTHORED / ISOLATED / UNREVIEWED / UNMERGED / UNIMPLEMENTED`

No implementation state may be inferred from this document.

---

## 31. Constitutional Summary

CP-MOVE3 establishes the WorkEvent Spine as a continuity vocabulary for governed work.

It gives Arkadia a precise language for saying that an event was represented, ordered, related, reviewed, corrected, superseded, disputed, or left unknown without silently converting the record into authority.

The spine preserves the thread without becoming the sovereign.

It records the work without owning the work.

It can point toward authority, provenance, authorization, workspace, identity, and execution without becoming any of them.

The governing chain remains:

`HUMAN SOVEREIGNTY → IDENTITY → WORKSPACE → WORKEVENT → GOVERNED ACTION → K15 → K3`

while the protected authority chain remains:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3`

The distinction is deliberate.

**The WorkEvent may preserve the thread of the work. It may not become the authority over the thread.**

**The continuity spine remembers the sequence. It does not become the sovereign.**
