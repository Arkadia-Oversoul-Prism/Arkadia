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

## Purpose

This artifact defines the proposed canonical SolSpire Workspace boundary for the sovereign workspace sequence. It establishes vocabulary and structural constraints only. It does not create, provision, migrate, instantiate, authorize, or operate a SolSpire workspace.

SolSpire is treated as the canonical workspace surface through which governed work may later be organized and inspected. The workspace is not itself an authority source, identity system, provenance mechanism, execution engine, memory system, or mutation path.

## Constitutional Boundary

The workspace MUST preserve:

`HUMAN SOVEREIGNTY → IDENTITY → WORKSPACE → GOVERNED ACTION → K15 → K3`

Permanent distinctions remain intact:

- `IDENTITY ≠ AUTHORITY EVENT ≠ PROVENANCE ≠ AUTHORIZATION ≠ EXECUTION`
- `PROVISIONING EVENT ≠ RESULTING IDENTITY`
- `DOCUMENTATION ≠ OPERATION`
- `WORKSPACE ≠ AUTHORITY`
- `WORKSPACE STATE ≠ PROVENANCE`
- `WORKSPACE STATE ≠ AUTHORIZATION`

## Canonical Workspace Definition

A Canonical SolSpire Workspace is a bounded, inspectable workspace object associated with a canonical human subject and governed work context.

It has explicit workspace identity, subject binding, lifecycle, ownership and state boundaries, and inspectable references. It has no independent sovereign identity, no autonomous authority, and no direct mutation capability.

The workspace is a container and coordination surface, not a sovereign actor.

## Proposed Schema Boundary

A future workspace object MAY contain these conceptual fields:

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

## Workspace Lifecycle

`PROPOSED → AUTHORIZED_FOR_PROVISIONING → PROVISIONED → VERIFIED → ACTIVE → SUSPENDED / ARCHIVED / REVOKED`

The lifecycle is descriptive until implementation is separately authorized.

### Critical non-self-authorization rule

`AUTHORIZED_FOR_PROVISIONING` MUST NOT mean that the workspace object has proven or created its own authorization.

If implemented, the state MUST be derived from a distinct and inspectable authority/provisioning event. The resulting workspace object cannot serve as evidence of the legitimacy of the event that created it.

## Subject Binding

The workspace MUST bind to the existing canonical human subject substrate. It MUST NOT create a parallel sovereign identity.

Subject binding does not establish authority. Authentication does not establish workspace authorization. Workspace ownership labels do not establish human-origin provenance.

## Scope and Ownership

Workspace scope MUST be explicit and inspectable.

A workspace may organize references to work, projects, knowledge, conversations, tasks, files, or other governed surfaces, but those references do not grant authority over them.

`WORKSPACE OWNERSHIP ≠ AUTHORIZATION`

## State Model

Workspace state is descriptive operational context. It MUST NOT silently become provenance evidence, human authorization, execution permission, authority escalation, autonomous agency, or a substitute for the Architect Identity boundary.

`ACTIVE` means only that the workspace is represented as active under its governing lifecycle. It does not prove who authorized that state.

## Relationship to Architect Identity

CP-MOVE1 defines the vocabulary boundary for Architect Identity. CP-MOVE2 does not create or activate that identity.

The intended structural relationship is:

`CANONICAL HUMAN SUBJECT → ARCHITECT IDENTITY (if separately provisioned) → SOLSPIRE WORKSPACE (if separately provisioned)`

The arrow is structural, not an automatic authorization grant.

No workspace may manufacture an Architect Identity, upgrade a subject into an Architect, or infer sovereign authority from workspace ownership.

## Relationship to Provenance

Workspace records may reference provenance where a future implementation provides it, but workspace state is not provenance by default.

The chain remains:

`AUTHENTICATED SUBJECT → AUTHORITY EVENT → ORIGIN EVIDENCE → PROVENANCE STATE → AUTHORIZATION DETERMINATION → WORKSPACE OPERATION`

Historical workspace state cannot retrospectively manufacture human-origin evidence.

## Relationship to Execution and K15/K3

SolSpire Workspace is not an execution engine.

Any future governed mutation remains subject to:

`HUMAN INTENT → APPROVAL EVENT → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3 → MUTATION`

Workspace actions may describe, stage, inspect, or reference work. They do not create a second mutation route.

`K3 remains the sole mutation boundary.`

## Inspectability

A future implementation MUST make workspace identity, subject binding, lifecycle, scope, provenance references, and authority references inspectable without requiring inference from hidden state.

Inspectability does not convert a workspace record into proof of human authority.

## Failure and Ambiguity States

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

`UNKNOWN` MUST NOT silently become `VALID`, `AUTHORIZED`, or `ACTIVE`.

## Adversarial Self-Tests

- **W01 Workspace Sufficiency:** workspace existence cannot establish human authorization.
- **W02 Ownership Upgrade:** `owner_ref` cannot establish sovereign authority by itself.
- **W03 Lifecycle Upgrade:** `ACTIVE` or `AUTHORIZED_FOR_PROVISIONING` cannot prove that the underlying authority event occurred.
- **W04 Identity Creation:** workspace cannot create or upgrade an Architect Identity.
- **W05 Provenance Substitution:** workspace history cannot substitute for origin evidence.
- **W06 Execution Substitution:** workspace state cannot bypass K15 or K3.
- **W07 Parallel Authority:** SolSpire cannot become an independent authority system.
- **W08 Autonomous Operation:** workspace cannot initiate sovereign actions outside the applicable human-governed chain.
- **W09 Historical Laundering:** later workspace state cannot manufacture proof of an earlier authority event.
- **W10 Scope Expansion:** parent workspace cannot silently expand the authority or scope of a child workspace.

## Non-Claims

This artifact does NOT claim that a SolSpire Workspace exists, that an Architect Identity exists, that Move 0 or Move 1 has passed, that any workspace has been provisioned, that authority or credentials have been granted or created, that runtime has changed, that migration has occurred, that a memory system has been created, that workspace action is authorized, that a mechanism has been selected, or that implementation is authorized.

## Implementation Gate

Implementation remains separately gated.

At minimum:

`MOVE 0 = PASSED`

and

`MOVE 1 = AUTHORIZED / VERIFIED AS APPLICABLE`

and explicit human authorization for Move 2 must exist before provisioning or runtime work begins.

No schema artifact may be interpreted as permission to implement itself.

## Resolution State

`AUTHORED → ISOLATED → REVIEWED → VERDICT → HUMAN DECISION → MERGED → IMPLEMENTATION GATE → IMPLEMENTED → VERIFIED`

This artifact is presently:

`AUTHORED / ISOLATED / UNREVIEWED / UNMERGED / UNIMPLEMENTED`

## Constitutional Summary

The Canonical SolSpire Workspace is a bounded workspace concept, not a new sovereign entity.

It may organize governed work without becoming the source of governance. It may reference identity without becoming identity. It may reference provenance without becoming provenance. It may represent state without becoming authorization. It may stage work without becoming execution. It may coordinate surfaces without creating an alternate mutation route.

The governing separation remains:

`SPECIFICATION → REVIEW → DECISION → IMPLEMENTATION`

and, where implementation occurs:

`AUTHORITY EVENT → PROVENANCE → AUTHORIZATION → K15 → K3`

**The workspace may hold the work. It may not become the authority over the work.**
