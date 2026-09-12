# CP-MOVE2 — Canonical SolSpire Workspace

**Status:** SCHEMA_ONLY / READ_ONLY / NORMATIVE DESIGN  
**Technology:** Technology-neutral  
**Implementation:** NOT AUTHORIZED  
**Provisioning:** NOT PERFORMED  
**Runtime Mutation:** NONE  
**Authority Grant:** NONE  
**Move 0:** BLOCKED  
**Move 1:** BLOCKED  
**K15/K3:** UNCHANGED

## 1. Purpose

This artifact defines the proposed canonical SolSpire Workspace boundary for the sovereign workspace sequence. It establishes vocabulary and structural constraints only. It does not create, provision, migrate, instantiate, authorize, or operate a SolSpire workspace.

SolSpire is treated as the canonical workspace surface through which governed work may later be organized and inspected. The workspace is not itself an authority source, identity system, provenance mechanism, execution engine, memory system, or mutation path.

The design answers: **what is the canonical SolSpire Workspace?** It does not answer by itself: **who may create it, who may operate it, or what actions may occur inside it?**

## 2. Constitutional Boundary

The workspace MUST preserve:

`HUMAN SOVEREIGNTY → IDENTITY → WORKSPACE → GOVERNED ACTION → K15 → K3`

The workspace does not replace or bypass any upstream authority condition or downstream mutation control.

Permanent distinctions remain intact:

- `IDENTITY ≠ AUTHORITY EVENT ≠ PROVENANCE ≠ AUTHORIZATION ≠ EXECUTION`
- `PROVISIONING EVENT ≠ RESULTING IDENTITY`
- `DOCUMENTATION ≠ OPERATION`
- `WORKSPACE ≠ AUTHORITY`
- `WORKSPACE STATE ≠ PROVENANCE`
- `WORKSPACE STATE ≠ AUTHORIZATION`

## 3. Canonical Workspace Definition

A Canonical SolSpire Workspace is a bounded, inspectable workspace object associated with a canonical human subject and governed work context.

It has:

1. an explicit workspace identity;
2. an explicit subject binding;
3. an explicit lifecycle;
4. explicit ownership and state boundaries;
5. inspectable membership/reference semantics;
6. explicit separation between descriptive workspace state and authority;
7. no independent sovereign identity;
8. no autonomous authority;
9. no direct mutation capability;
10. no requirement for a new memory system.

The workspace is a container and coordination surface, not a sovereign actor.

## 4. Proposed Schema Boundary

A future workspace object MAY contain the following conceptual fields:

- `workspace_id`
- `workspace_type`
- `canonical_subject_ref`
- `display_name`
- `status`
- `created_at`
- `effective_from`
- `expires_at`
- `owner_ref`
- `parent_workspace_ref`
- `scope_ref`
- `membership_refs`
- `surface_refs`
- `state_ref`
- `created_by_event`
- `provenance_ref`
- `schema_version`

These are vocabulary-level fields, not an implementation mandate. No secret, credential, private key, access token, or provider credential belongs in the workspace object.

## 5. Workspace Lifecycle

The proposed lifecycle is:

`PROPOSED → AUTHORIZED_FOR_PROVISIONING → PROVISIONED → VERIFIED → ACTIVE → SUSPENDED / ARCHIVED / REVOKED`

The lifecycle is descriptive until an implementation is separately authorized.

### Critical non-self-authorization rule

`AUTHORIZED_FOR_PROVISIONING` MUST NOT mean that the workspace object has proven or created its own authorization.

The state MUST, if implemented, be derived from a distinct and inspectable authority/provisioning event. The resulting workspace object cannot serve as evidence of the legitimacy of the event that created it.

## 6. Subject Binding

The workspace MUST bind to the existing canonical human subject substrate. It MUST NOT create a parallel sovereign identity.

Subject binding does not establish authority.

Authentication does not establish workspace authorization.

Workspace ownership labels do not establish human-origin provenance.

## 7. Scope and Ownership

Workspace scope MUST be explicit and inspectable.

A workspace may organize references to work, projects, knowledge, conversations, tasks, files, or other governed surfaces, but those references do not grant authority over them.

Ownership is descriptive unless separately backed by the applicable authority and authorization chain.

`WORKSPACE OWNERSHIP ≠ AUTHORIZATION`

## 8. State Model

Workspace state is descriptive operational context. It MUST NOT silently become:

- provenance evidence;
- human authorization;
- execution permission;
- authority escalation;
- autonomous agency;
- a substitute for the Architect Identity boundary.

A state value such as `ACTIVE` means only that the workspace is represented as active under its governing lifecycle. It does not prove who authorized that state.

## 9. Relationship to Architect Identity

CP-MOVE1 defines the vocabulary boundary for Architect Identity. CP-MOVE2 does not create or activate that identity.

The intended relationship is:

`CANONICAL HUMAN SUBJECT → ARCHITECT IDENTITY (if separately provisioned) → SOLSPIRЕ WORKSPACE (if separately provisioned)`

The arrow is structural, not an automatic authorization grant.

No workspace may manufacture an Architect Identity, upgrade a subject into an Architect, or infer sovereign authority from workspace ownership.

## 10. Relationship to Provenance

Workspace records may reference provenance where a future implementation provides it, but workspace state is not provenance by default.

The chain remains:

`AUTHENTICATED SUBJECT → AUTHORITY EVENT → ORIGIN EVIDENCE → PROVENANCE STATE → AUTHORIZATION DETERMINATION → WORKSPACE OPERATION`

The workspace does not collapse any of these stages.

Historical workspace state cannot retrospectively manufacture human-origin evidence.

## 11. Relationship to Execution and K15/K3

SolSpire Workspace is not an execution engine.

Any future governed mutation remains subject to the existing protected path:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION`

Workspace actions may describe, stage, inspect, or reference work. They do not create a second mutation route.

`K3 remains the sole mutation boundary.`

## 12. Inspectability

A future implementation MUST make workspace identity, subject binding, lifecycle, scope, provenance references, and authority references inspectable without requiring inference from hidden state.

Inspectability means a reviewer can determine what the workspace claims to be, what it references, what lifecycle state it carries, and which external events or records it relies upon.

Inspectability does not convert a workspace record into proof of human authority.

## 13. Failure and Ambiguity States

A future implementation MUST fail closed for at least:

- unknown subject binding;
- contradictory workspace identity;
- ambiguous scope;
- duplicate canonical workspace claim;
- invalid lifecycle transition;
- expired workspace;
- revoked workspace;
- missing provisioning event;
- missing governance issuer where required;
- unbounded parent/child workspace relationship;
- attempted authority escalation through workspace state;
- attempted alternate mutation path;
- workspace-derived Architect Identity creation;
- provenance asserted solely by workspace existence.

UNKNOWN MUST NOT silently become VALID, AUTHORIZED, or ACTIVE.

## 14. Adversarial Self-Tests

### W01 — Workspace Sufficiency
Can the existence of a workspace establish human authorization by itself?

Required result: **NO**.

### W02 — Ownership Upgrade
Can `owner_ref` establish sovereign authority by itself?

Required result: **NO**.

### W03 — Lifecycle Upgrade
Can `ACTIVE` or `AUTHORIZED_FOR_PROVISIONING` prove that the underlying authority event occurred?

Required result: **NO**.

### W04 — Identity Creation
Can the workspace create or upgrade an Architect Identity?

Required result: **NO**.

### W05 — Provenance Substitution
Can workspace history substitute for origin evidence?

Required result: **NO**.

### W06 — Execution Substitution
Can workspace state bypass K15 or K3?

Required result: **NO**.

### W07 — Parallel Authority
Can SolSpire become an independent authority system?

Required result: **NO**.

### W08 — Autonomous Operation
Can the workspace initiate sovereign actions without the applicable human-governed chain?

Required result: **NO**.

### W09 — Historical Laundering
Can later workspace state manufacture proof of an earlier authority event?

Required result: **NO**.

### W10 — Scope Expansion
Can a parent workspace silently expand the authority or scope of a child workspace?

Required result: **NO**.

## 15. Non-Claims

This artifact does NOT claim:

- that a SolSpire Workspace currently exists;
- that an Architect Identity currently exists;
- that Move 0 has passed;
- that Move 1 has passed;
- that any workspace has been provisioned;
- that any authority has been granted;
- that any credentials have been created;
- that any runtime has changed;
- that any migration has occurred;
- that any memory system has been created;
- that any workspace action is authorized;
- that a mechanism has been selected;
- that implementation is authorized.

## 16. Implementation Gate

Implementation remains separately gated.

At minimum:

`MOVE 0 = PASSED`

and

`MOVE 1 = AUTHORIZED / VERIFIED AS APPLICABLE`

and explicit human authorization for Move 2 must exist before provisioning or runtime work begins.

No schema artifact may be interpreted as permission to implement itself.

## 17. Resolution State

`AUTHORED → ISOLATED → REVIEWED → VERDICT → HUMAN DECISION → MERGED → IMPLEMENTATION GATE → IMPLEMENTED → VERIFIED`

This artifact is presently:

`AUTHORED / ISOLATED / UNREVIEWED / UNMERGED / UNIMPLEMENTED`

## 18. Constitutional Summary

The Canonical SolSpire Workspace is a bounded workspace concept, not a new sovereign entity.

It may organize governed work without becoming the source of governance.

It may reference identity without becoming identity.

It may reference provenance without becoming provenance.

It may represent state without becoming authorization.

It may stage work without becoming execution.

It may coordinate surfaces without creating an alternate mutation route.

The governing separation remains:

`SPECIFICATION → REVIEW → DECISION → IMPLEMENTATION`

and, where implementation occurs:

`AUTHORITY EVENT → PROVENANCE → AUTHORIZATION → K15 → K3`

**The workspace may hold the work. It may not become the authority over the work.**
