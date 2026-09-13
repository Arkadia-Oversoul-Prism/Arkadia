# CP-MOVE4 — Canonical Workload

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
**Move 3:** DESIGN MERGED / IMPLEMENTATION NOT AUTHORIZED  
**K15/K3:** UNCHANGED

---

## 1. Purpose

This artifact defines the proposed **Canonical Workload** as the bounded vocabulary for representing a governed unit of work in Arkadia.

The concrete reference context is the existing human-directed Barnabas / Eden Food Systems market-intelligence engagement. The reference is architectural context only. This artifact does not instantiate that workload, ingest live data, create a runtime object, create a project database, or authorize commercial activity.

> **The workload can define what is being worked on. It cannot define who is authorized to work on it.**

A Canonical Workload is the governed object of work, not an identity, authority source, provenance mechanism, authorization decision, execution engine, memory system, workspace, or event record.

---

## 2. Constitutional Boundary

CP-MOVE4 extends the established structural chain:

`HUMAN SOVEREIGNTY → IDENTITY → WORKSPACE → CANONICAL WORKLOAD → WORKEVENT → GOVERNED ACTION → K15 → K3`

The protected authority/execution chain remains separate:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION`

A Workload may reference stages in that chain where independently established objects exist. It may not manufacture any stage merely by containing a reference to it.

The workload therefore sits inside the governed-work model, not inside the authority model.

---

## 3. Load-Bearing Distinctions

CP-MOVE4 preserves the prior distinctions:

- `IDENTITY ≠ AUTHORITY EVENT ≠ PROVENANCE ≠ AUTHORIZATION ≠ EXECUTION`
- `PROVISIONING EVENT ≠ RESULTING IDENTITY`
- `DOCUMENTATION ≠ OPERATION`
- `FILESYSTEM REMOVAL ≠ HISTORY REMOVAL`
- `CURRENT TREE ≠ ACTIVE RUNTIME ≠ HISTORICAL SURFACE`
- `ATTESTATION ≠ ORIGINATION`
- `PRECEDENCE ≠ CAUSATION`
- `IDENTITY-DEPENDENCE ≠ EVIDENCE OF CAUSAL ORIGINATION`
- `WORKSPACE ≠ AUTHORITY`
- `WORKSPACE STATE ≠ PROVENANCE`
- `WORKSPACE STATE ≠ AUTHORIZATION`
- `WORKEVENT ≠ AUTHORITY EVENT`
- `WORKEVENT ≠ PROVENANCE`
- `WORKEVENT ≠ AUTHORIZATION`
- `WORKEVENT ≠ EXECUTION`
- `CONTINUITY ≠ MEMORY SYSTEM`
- `HISTORY ≠ AUTHORITY`
- `SEQUENCE ≠ CAUSATION`

New workload distinctions:

- `WORKLOAD ≠ AUTHORITY`
- `WORKLOAD ≠ IDENTITY`
- `WORKLOAD ≠ PROVENANCE`
- `WORKLOAD ≠ AUTHORIZATION`
- `WORKLOAD ≠ EXECUTION`
- `WORKLOAD ≠ MEMORY SYSTEM`
- `WORKSPACE ≠ WORKLOAD`
- `WORKEVENT ≠ WORKLOAD`
- `WORKLOAD ≠ WORK EVENT`

These are semantic boundaries, not naming conventions. Renaming, wrapping, duplication, or embedding authority-bearing data inside a workload object does not satisfy them.

---

## 4. Definition

A **Canonical Workload** is a bounded, inspectable representation of a governed unit of work with a declared subject, workspace relationship, scope, objective, lifecycle, references, and closure conditions.

A workload may describe what the work concerns, why it exists, its declared scope, associated subject, workspace relationship, phase, descriptive status, intended deliverables, evidence and artifact references, WorkEvent references, decision references, provenance and authorization references, temporal validity, supersession, and closure conditions.

These are vocabulary-level concepts. They do not authorize the corresponding activity.

---

## 5. Barnabas as Reference Workload

For architectural testing, the reference workload is:

**Barnabas / Eden Food Systems — Plateau Food Market Intelligence**

This reference represents the shape of an existing human-directed project context. It is a semantic test case, not a live workload instance.

CP-MOVE4 does not:

- create a runtime workload record;
- ingest project communications or personal data;
- create a WorkEvent for the engagement;
- create a market-intelligence database;
- create a new memory system;
- authorize procurement, trading, investment, sales, or other commercial activity;
- assign an Architect Identity;
- provision a SolSpire Workspace;
- create autonomous tasks;
- execute the market-intelligence work;
- establish a parallel project database.

No project data is created, copied, persisted, transformed, or ingested by this artifact.

---

## 6. Proposed Schema Boundary

A future Canonical Workload object MAY contain the following conceptual fields:

- `workload_id`
- `workload_type`
- `canonical_subject_ref`
- `workspace_ref`
- `display_name`
- `title`
- `objective`
- `scope_ref`
- `market_intelligence_scope_ref`
- `principal_ref`
- `owner_ref`
- `participant_refs`
- `phase`
- `status`
- `deliverable_refs`
- `artifact_refs`
- `evidence_refs`
- `work_event_refs`
- `decision_refs`
- `provenance_refs`
- `authorization_refs`
- `approval_refs`
- `created_by_event`
- `effective_from`
- `effective_until`
- `supersedes_ref`
- `closure_ref`
- `schema_version`

These are vocabulary-level fields, not an implementation mandate. The presence of a reference does not establish the existence, validity, authority, provenance, or authorization of the referenced object.

No workload object may contain secrets, private keys, provider credentials, access tokens, passwords, or equivalent credential material.

---

## 7. Subject, Principal, and Ownership

A workload may identify the human subject or principal associated with the work. This relationship MUST remain distinct from authorization.

Prohibited upgrades include:

`WORKLOAD OWNER → AUTHORIZED OPERATOR`

`WORKLOAD PRINCIPAL → AUTHORITY`

`WORKLOAD PARTICIPANT → UNBOUNDED AUTHORITY`

`WORKLOAD OWNER → ARCHITECT AUTHORITY`

`owner_ref`, `principal_ref`, and `participant_refs` describe relationships to the workload. They do not create a new identity system and do not upgrade a subject's authority.

---

## 8. Workspace Relationship

The structural relationship remains:

`CANONICAL HUMAN SUBJECT → ARCHITECT IDENTITY (if separately provisioned) → SOLSPIRE WORKSPACE (if separately provisioned) → CANONICAL WORKLOAD (if separately implemented)`

This relationship is structural only.

A workload does not inherit authority from workspace ownership or membership.

> **The workspace may hold the work. It may not become the authority over the work.**

Move 4 adds:

> **The workload can define what is being worked on. It cannot define who is authorized to work on it.**

---

## 9. Workload and WorkEvent

A WorkEvent describes an occurrence relevant to governed work. A Workload describes the governed unit of work to which such occurrences may relate.

Therefore:

`WORKLOAD ≠ WORKEVENT`

A workload may contain `work_event_refs` in a future implementation, but those references remain references.

Prohibited implications:

- `WORKLOAD EXISTS → WORKEVENT OCCURRED`
- `WORKLOAD + WORK EVENT → AUTHORIZED`
- `WORK EVENT EXISTS → WORKLOAD AUTHORITY`
- `WORKLOAD STATUS + EVENT HISTORY → HUMAN ORIGINATION`

The WorkEvent Spine remains independently bounded by CP-MOVE3. A workload may provide continuity context. It cannot become the event record itself.

---

## 10. Objective and Scope

The workload may declare an objective and bounded scope. For the reference context, a future workload could describe market reconnaissance, evidence collection, commodity and corridor intelligence, synthesis, and defined deliverables.

These examples are descriptive only.

A declared objective does not authorize execution. A scope declaration does not grant access to data. A market-intelligence scope does not authorize procurement or trading. A deliverable reference does not require autonomous production.

`WORKLOAD SCOPE → OPERATIONAL AUTHORITY` is prohibited.

---

## 11. Phase and Status

A future workload may use a bounded descriptive lifecycle such as:

`PROPOSED / OPEN / ACTIVE / ON_HOLD / COMPLETED / CLOSED / SUPERSEDED / DISPUTED / UNKNOWN`

These states are descriptive unless separately backed by governing evidence and authority.

- `ACTIVE` does not mean authorized.
- `COMPLETED` does not prove successful execution.
- `CLOSED` does not erase historical events.
- `SUPERSEDED` does not erase historical existence.
- `DISPUTED` remains visible.
- `UNKNOWN` must not silently become `VALID`, `AUTHORIZED`, or `ACTIVE`.

A workload lifecycle must not become a hidden authorization state machine.

If a future implementation introduces `AUTHORIZED_FOR_PROVISIONING` or equivalent language, that state MUST derive from a distinct, inspectable authority/provisioning event and MUST never self-prove authorization.

---

## 12. Deliverables and Evidence

A workload may reference intended deliverables and evidence, including reconnaissance reports, market observations, interview records, corridor findings, commodity findings, decision records, and handover artifacts.

These are reference categories only.

`deliverable_refs` do not prove that a deliverable was produced.

`evidence_refs` do not prove the provenance of evidence.

A document attached to a workload does not become authoritative merely because the workload references it.

Evidence remains subject to the CP-10 provenance chain.

---

## 13. Provenance Relationship

The provenance chain remains:

`AUTHENTICATED SUBJECT → AUTHORITY EVENT → ORIGIN EVIDENCE → PROVENANCE STATE → AUTHORIZATION DETERMINATION`

A workload may reference provenance objects through `provenance_refs`.

It MUST NOT manufacture provenance merely because:

- the workload exists;
- the workload is owned by a human subject;
- the workload is inside a workspace;
- the workload has a participant list;
- the workload contains a signed artifact;
- the workload has a chronological event sequence;
- the workload has been reviewed;
- downstream systems rely upon the workload.

`WORKLOAD ≠ PROVENANCE`

Decisive test:

> If the workload existed without provenance evidence, would the workload itself be sufficient to establish human-origin authority?

Required answer: **NO**.

---

## 14. Authorization Relationship

Authorization remains independently determined.

A workload may reference an authorization decision through `authorization_refs` or `approval_refs` where such objects legitimately exist.

It MUST NOT derive authorization from ownership, principal association, participant membership, workspace membership, workload status, workload scope, deliverable assignment, event history, evidence presence, or artifact presence.

Prohibited semantic upgrades include:

`WORKLOAD → AUTHORIZED`

`WORKLOAD OWNER → AUTHORIZED`

`WORKLOAD + WORKSPACE → AUTHORIZED`

`WORKLOAD + WORKEVENT → AUTHORIZED`

`WORKLOAD + SIGNATURE/HASH → AUTHORIZED`

The workload may represent the object being governed. It may not become the governing authority.

---

## 15. Execution and K15/K3 Boundary

The Canonical Workload is not an execution engine.

It MUST NOT execute commands, create autonomous tasks that execute themselves, mutate repositories, invoke external commercial actions, authorize procurement or trading, bypass K15, invoke K3 directly, create an alternate mutation path, or convert workload state into execution permission.

The protected sequence remains:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION → COMMIT → PUSH → VERIFICATION → PUBLICATION`

`WORKLOAD ≠ EXECUTION`.

---

## 16. Continuity Without Memory-System Drift

A workload may reference WorkEvents and artifacts necessary to understand its governed context. It must not become an autonomous memory system, hidden state store, vector database, retrieval authority, parallel knowledge graph, sovereign identity archive, new persistence subsystem, or autonomous project-memory agent.

`WORKLOAD ≠ MEMORY SYSTEM`

Structured references do not authorize creation of a new persistence layer.

---

## 17. Temporal Validity and Supersession

A workload may define `effective_from`, `effective_until`, `supersedes_ref`, and `closure_ref`.

Temporal validity describes when the workload definition applies. It does not establish human intent, provenance, or authorization.

Supersession must not silently rewrite historical workload identity.

`WORKLOAD₁ → WORKLOAD₂ (supersedes WORKLOAD₁)`

`SUPERSESSION ≠ AUTHORIZATION`

`TEMPORAL VALIDITY ≠ HUMAN ORIGINATION`

---

## 18. Closure Conditions

A future workload implementation should define explicit closure conditions before treating a workload as closed. These may include objective addressed or formally terminated, deliverables accounted for, unresolved decisions identified, evidence references preserved, outstanding actions explicitly represented under authorized mechanisms, final status recorded, supersession established where applicable, and a separate closure event where WorkEvent is implemented.

Closure is a workload state, not an authority event.

`CLOSED ≠ AUTHORIZED`

---

## 19. Delegation and Participation

A workload may reference participants or delegated subjects. Participation does not automatically create authority.

Delegation remains explicit and bounded by delegator identity, delegated subject, delegated scope, effective time, expiry, revocation state, and required provenance and authorization references.

Prohibited:

`PARTICIPANT → UNBOUNDED AUTHORITY`

`DELEGATED PARTICIPANT → WORKLOAD OWNER`

`WORKLOAD PARTICIPATION → ARCHITECT AUTHORITY`

A workload cannot widen delegation merely by listing a subject as a participant.

---

## 20. Failure and Fail-Closed Conditions

A future workload implementation MUST fail closed where any of the following is unresolved or contradictory:

- canonical subject binding;
- workspace binding;
- workload identity;
- workload scope;
- lifecycle transition;
- principal or owner relationship;
- delegated scope;
- temporal validity;
- provenance reference;
- authorization reference;
- contradictory status;
- disputed or superseded workload misuse;
- workload-derived identity creation;
- workload-derived authority creation;
- workload-derived provenance creation;
- workload-derived execution;
- memory-system drift;
- alternate mutation path;
- K15 bypass;
- K3 bypass;
- autonomous task execution;
- hidden persistence;
- parallel project database.

`UNKNOWN` MUST remain explicit. `UNKNOWN → AUTHORIZED` is prohibited. `UNKNOWN → ACTIVE` is prohibited where `ACTIVE` carries operational meaning.

---

## 21. Adversarial Semantic Tests

### W01 — Workload Sufficiency
Can the workload itself establish human authorization? **Required: NO.**

### W02 — Ownership Upgrade
Does `owner_ref` become authority merely by ownership? **Required: NO.**

### W03 — Status Upgrade
Can `ACTIVE`, `COMPLETED`, or `CLOSED` become authorization? **Required: NO.**

### W04 — Identity Creation
Can workload membership or ownership create an Architect Identity? **Required: NO.**

### W05 — Provenance Substitution
Can workload existence, signature, hash, or artifact association substitute for CP-10 provenance? **Required: NO.**

### W06 — Execution Substitution
Can the workload execute commands or commercial actions because its scope declares them? **Required: NO.**

### W07 — Workspace Laundering
Can workspace ownership or membership become workload authority? **Required: NO.**

### W08 — WorkEvent Substitution
Can workload state create, imply, or become a WorkEvent or authority event? **Required: NO.**

### W09 — Memory-System Drift
Can the workload become a hidden memory store, retrieval authority, or parallel project database? **Required: NO.**

### W10 — Scope Expansion
Can declared workload scope expand delegated authority, execution rights, or mutation rights? **Required: NO.**

### W11 — Historical Laundering
Can supersession or closure silently erase prior workload state? **Required: NO.**

### W12 — Unknown Conversion
Can unresolved workload state silently become `ACTIVE`, `AUTHORIZED`, `VERIFIED`, or equivalent? **Required: NO.**

---

## 22. Semantic Laundering Tests

The workload boundary must survive:

- **L01 Rename:** authority metadata does not become harmless because it is called workload metadata.
- **L02 Wrapper:** placing an authorization object inside workload state does not make workload ownership authoritative.
- **L03 Duplication:** copied authority state does not create a valid second authority source.
- **L04 Shadow State:** hidden workload state cannot become a parallel authorization system.
- **L05 Accumulation:** many references do not collectively become provenance or authority merely by quantity.
- **L06 Retrospective Laundering:** later workload acceptance cannot manufacture historical human-origin proof.
- **L07 Status Laundering:** a status label cannot become an authorization state through naming.
- **L08 Workspace Laundering:** workspace association cannot become workload authority.
- **L09 Event Laundering:** WorkEvent references cannot become authority by appearing in workload state.
- **L10 Memory Laundering:** persistence or retrieval convenience cannot silently become a new memory authority.

---

## 23. Inspectability Requirements

A future implementation must allow an inspector to answer, without semantic inference:

1. What workload is this?
2. What subject is it associated with?
3. What workspace is it associated with?
4. What is its declared objective?
5. What is its declared scope?
6. What phase and status does it claim?
7. Which artifacts and evidence does it reference?
8. Which WorkEvents does it reference?
9. Which decisions does it reference?
10. Which provenance and authorization objects does it reference?
11. What is its temporal validity?
12. What supersedes or closes it?
13. Which claims remain UNKNOWN or DISPUTED?
14. Can any field be misread as authority?
15. Is operational capability being inferred solely from workload state?

If an inspector cannot distinguish **what the work is** from **who is authorized to act on the work**, the implementation is not boundary-safe.

---

## 24. Relationship to the Five Control Plane Domains

| Domain | Boundary preserved by Move 4 |
|---|---|
| Provenance | Workload may reference provenance; it cannot manufacture it |
| Credentials | No credential material belongs in workload state |
| Identity | Workload cannot create or upgrade identity |
| Workspace | Workload is held within a workspace relationship; workspace is not authority |
| Continuity | Workload may reference WorkEvents; continuity remains distinct from workload and memory |

The workload is a governed object layer, not a sixth authority domain.

---

## 25. Implementation Gate

CP-MOVE4 MUST NOT be implemented merely because this document exists or is merged.

A future implementation gate requires, at minimum:

1. `MOVE 0 = PASSED`;
2. `MOVE 1 = AUTHORIZED / VERIFIED AS APPLICABLE`;
3. `MOVE 2 = EXPLICITLY AUTHORIZED FOR IMPLEMENTATION`;
4. `MOVE 3 = EXPLICITLY AUTHORIZED FOR IMPLEMENTATION`;
5. explicit human authorization for Move 4 implementation;
6. canonical subject and workspace bindings established through their own governing paths;
7. provenance and authorization remain separate determinations;
8. no new identity, authority, memory, credential, or alternate mutation system;
9. K15 remains the gate immediately before K3;
10. implementation remains inspectable and fail closed.

The existence of this design does not satisfy any of these conditions.

---

## 26. Non-Claims

This artifact does not claim that a Barnabas workload currently exists as a runtime object, that project data has been ingested, that communications have been copied into Arkadia, that a WorkEvent Spine has been instantiated, that a WorkEvent has been created, that a SolSpire Workspace has been provisioned, that an Architect Identity has been provisioned, that Move 0 has passed, that Move 1 has passed, that Move 2 or Move 3 implementation is authorized, that any workload operation is authorized, that commercial activity is authorized, that any credential has been created or rotated by this artifact, that any memory system has been created, that any autonomous task has been created or executed, that any repository mutation has occurred because of this workload design, or that any mechanism or implementation has been selected or authorized.

The repository remains the source of truth for actual state.

---

## 27. Resolution State

Current Move 4 state:

`AUTHORED → ISOLATED → UNREVIEWED → UNMERGED → UNIMPLEMENTED`

No operation follows automatically from authoring this artifact.

The intended review sequence remains:

`AUTHOR → ISOLATE → REVIEW → VERDICT → HUMAN DECISION → MERGE → IMPLEMENTATION GATE`

This artifact is not self-approving.

---

## 28. Closing Boundary

The Barnabas workload is the first concrete governed object in this sequence, but concreteness must not become authority.

The workload can define the work. It can name the objective. It can bound the scope. It can point toward evidence, artifacts, decisions, provenance, authorization, and continuity.

It cannot create the human authority behind those references. It cannot turn ownership into permission. It cannot turn scope into execution. It cannot turn continuity into memory authority. It cannot turn a project into a sovereign actor.

> **The workload can define what is being worked on. It cannot define who is authorized to work on it.**

`HUMAN SOVEREIGNTY → IDENTITY → WORKSPACE → CANONICAL WORKLOAD → WORKEVENT → GOVERNED ACTION → K15 → K3`

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION`

**The workload holds the object of work. It does not become the authority over the work.**
