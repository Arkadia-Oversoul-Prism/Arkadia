# CP-MOVE1 — Architect Identity Design Contract

**Status:** SCHEMA_ONLY / READ_ONLY / NORMATIVE DESIGN
**Move:** 1 — Architect Identity
**Mechanism:** NOT SELECTED
**Implementation:** NOT AUTHORIZED
**Provisioning:** NOT PERFORMED
**Credential Mutation:** NONE
**Runtime Mutation:** NONE
**Authority Grant:** NONE
**Move 0 Gate:** BLOCKED
**Move 1 Gate:** BLOCKED

---

## 0. Purpose

This artifact defines the design boundary for Move 1 of the Sovereign Workspace sequence: establishment of an explicit **Architect Identity** capable of being referenced by later governed operations.

It is a preparation artifact only.

It does **not** provision an identity, create credentials, alter Firebase, modify authentication, grant authority, create a WorkEvent, authorize mutation, or unblock Move 1.

The purpose is to make the future operation deterministic before the operation becomes executable.

The governing sequence remains:

```text
MOVE 0 CLEARANCE
        ↓
ARCHITECT IDENTITY DESIGN
        ↓
HUMAN AUTHORIZATION
        ↓
IDENTITY PROVISIONING
        ↓
IDENTITY VERIFICATION
        ↓
MOVE 1 CLOSURE
```

Move 1 cannot begin operationally while Move 0 remains blocked.

---

## 1. Design Objective

The Architect Identity is a repository-recognizable subject representing the human authority designated as Architect for the Sovereign Workspace.

The identity must be:

- explicit rather than implicit;
- uniquely referenceable;
- bound to the governed human subject;
- distinguishable from ordinary authenticated users;
- distinguishable from AI nodes and service accounts;
- bounded by an explicit authority class;
- inspectable without exposing secret credentials;
- revocable and replaceable through an explicit governance process;
- unable to create authority merely by existing.

The core distinction is:

```text
IDENTITY
    ≠
AUTHORITY EVENT
    ≠
PROVENANCE
    ≠
AUTHORIZATION
    ≠
EXECUTION
```

An Architect Identity identifies the subject. It does not, by itself, prove that a particular authority event occurred or authorize a particular mutation.

---

## 2. Constitutional Position

The Architect Identity exists beneath constitutional authority and above ordinary system execution only as a **recognized subject of authority**.

It does not become a second constitution, parallel sovereign, autonomous principal, or substitute for human sovereignty.

The intended hierarchy is:

```text
HUMAN SOVEREIGNTY
        ↓
CONSTITUTIONAL BOUNDS
        ↓
ARCHITECT AUTHORITY CLASS
        ↓
ARCHITECT IDENTITY
        ↓
AUTHORITY EVENT
        ↓
PROVENANCE EVALUATION
        ↓
AUTHORIZATION
        ↓
K15
        ↓
K3
        ↓
MUTATION
```

No lower layer may manufacture a higher layer.

In particular:

```text
IDENTITY → AUTHORITY
```

is not a valid inference by itself.

---

## 3. Identity Object Schema

The future Architect Identity record should contain, at minimum, the following semantic fields.

| Field | Required meaning | Boundary |
|---|---|---|
| `identity_id` | Stable unique identifier for the Architect subject | Identifier only |
| `subject_ref` | Reference to the governed human subject | Must not expose unnecessary PII |
| `authority_class` | Explicit authority class | Must equal Architect, not Constitutional |
| `role` | Canonical Architect role designation | Descriptive, not self-authorizing |
| `status` | Lifecycle state | Must support inactive/revoked states |
| `issued_at` | Time identity was provisioned/recognized | Lifecycle evidence only |
| `effective_from` | Start of validity | Temporal boundary |
| `expires_at` | Optional explicit end of validity | Temporal boundary |
| `delegation_ref` | Delegation lineage when applicable | Must not invent delegation |
| `issuer_ref` | Authorized issuer/governance reference | Does not replace provenance |
| `binding_state` | State of subject binding | Must be inspectable |
| `verification_state` | State of identity verification | Must not be treated as authorization |
| `revocation_state` | Revocation status | Must fail closed when revoked |
| `created_by_event` | Reference to the governed provisioning event | Event reference, not event proof by itself |
| `schema_version` | Version of this identity contract | Compatibility only |

Secret credentials, private keys, provider secrets, recovery material, or authentication tokens are **not** part of this documentation schema.

No secret value is to be authored into this artifact.

---

## 4. Required Identity States

The lifecycle should distinguish at least:

```text
PROPOSED
    ↓
AUTHORIZED_FOR_PROVISIONING
    ↓
PROVISIONED
    ↓
VERIFIED
    ↓
ACTIVE
    ↓
SUSPENDED / REVOKED / EXPIRED
```

These states are not interchangeable.

In particular:

```text
PROVISIONED ≠ VERIFIED
VERIFIED ≠ ACTIVE
ACTIVE ≠ AUTHORIZED FOR A SPECIFIC MUTATION
```

A state transition must be attributable to an explicit governed event.

No state may be inferred merely because an adjacent state exists.

---

## 5. Subject Binding

Architect Identity must be bound to the intended human subject without creating a parallel identity system.

The design therefore requires:

1. one canonical subject reference;
2. an explicit authority class;
3. a bounded identity lifecycle;
4. a verifiable binding state;
5. an explicit revocation path;
6. no duplicate sovereign identity namespace;
7. no AI-generated self-assertion of Architect status.

The identity record must not claim that a person is Architect merely because a system process, model, node, or document says so.

The future implementation must establish the binding through the repository's selected identity mechanism and the applicable human-governance process.

That mechanism is intentionally **not selected here**.

---

## 6. Identity vs Provenance

Move 1 must preserve the provenance boundary established by CP-10.

An authenticated Architect Identity may establish that a subject is recognized as Architect.

It does not, by itself, establish that the subject deliberately performed a particular authority event.

Therefore:

```text
AUTHENTICATED ARCHITECT IDENTITY
        ≠
PROOF OF A PARTICULAR AUTHORITY EVENT
```

The future implementation must remain compatible with the provenance chain:

```text
AUTHENTICATED SUBJECT
        ↓
AUTHORITY EVENT
        ↓
ORIGIN EVIDENCE
        ↓
PROVENANCE STATE
        ↓
AUTHORIZATION DETERMINATION
        ↓
PASSSPEC
        ↓
K15
        ↓
K3
```

Move 1 must not silently collapse the first five stages into identity authentication.

---

## 7. Identity vs Authority

Architect Identity recognizes an authority class. It does not grant arbitrary authority.

The following substitutions are prohibited:

```text
ARCHITECT IDENTITY EXISTS
    → therefore ALL ACTIONS ARE AUTHORIZED
```

```text
AUTHENTICATED USER
    → therefore ARCHITECT
```

```text
ARCHITECT ROLE LABEL
    → therefore HUMAN PROVENANCE
```

```text
IDENTITY TOKEN
    → therefore AUTHORITY EVENT
```

```text
ACTIVE IDENTITY
    → therefore MUTATION AUTHORIZATION
```

A later authorization decision must evaluate the identity, authority class, scope, provenance, temporal validity, delegation lineage, and applicable governance constraints independently.

---

## 8. Scope of Architect Authority

The Architect Identity must carry an explicit authority class rather than an unbounded administrative capability.

At design level:

```text
AUTHORITY_CLASS = ARCHITECT
```

The class means the subject may be recognized as the designated architect within the constitutional and governance boundaries of Arkadia.

It does **not** mean:

- unrestricted repository access;
- unrestricted credential access;
- autonomous execution;
- authority to alter constitutional constraints;
- authority to create new sovereigns;
- authority to bypass K15;
- authority to bypass K3;
- authority to convert evidence into provenance;
- authority to convert identity into authorization.

Specific actions remain subject to their own governed authorization boundary.

---

## 9. Delegation

If Architect authority is ever delegated, the identity design must preserve delegation lineage.

A delegated subject must not become indistinguishable from the original Architect.

The minimum conceptual chain is:

```text
ARCHITECT
    ↓
DELEGATION EVENT
    ↓
DELEGATED SUBJECT
    ↓
BOUNDED SCOPE
    ↓
TEMPORAL VALIDITY
    ↓
REVOCATION / EXPIRY
```

Delegation must never silently expand authority.

The existence of `delegation_ref` does not itself prove that a valid delegation event occurred. That event remains subject to provenance and governance evaluation.

---

## 10. Revocation and Expiry

Architect Identity must be designed for loss of validity as deliberately as establishment of validity.

At minimum, the future implementation must be able to represent:

```text
ACTIVE
EXPIRED
SUSPENDED
REVOKED
```

A revoked or expired identity must not remain operationally equivalent to an active identity.

Historical records may retain the identity reference for audit continuity, but historical existence must not imply current validity.

```text
HISTORICAL IDENTITY RECORD
        ≠
CURRENT ACTIVE AUTHORITY
```

---

## 11. Identity Verification

Move 1 closure requires independent verification of the identity state after provisioning.

Verification must establish, at minimum:

- the intended subject is bound;
- the identity is the expected identity;
- the authority class is correct;
- the lifecycle state is correct;
- revocation/expiry state is correct;
- no duplicate or parallel Architect identity was created;
- no secret material was exposed by the identity record;
- no mutation capability was silently granted beyond the intended boundary.

Verification is a state assertion about the identity implementation.

It is not proof that every future authority event will be legitimate.

---

## 12. Failure States

The following conditions must fail closed for Move 1:

```text
UNKNOWN SUBJECT BINDING
CONTRADICTORY IDENTITY STATE
UNVERIFIED IDENTITY
EXPIRED IDENTITY
REVOKED IDENTITY
AMBIGUOUS AUTHORITY CLASS
DUPLICATE SOVEREIGN IDENTITY
UNBOUNDED DELEGATION
MISSING PROVISIONING EVENT
MISSING GOVERNANCE ISSUER
```

No UNKNOWN state may silently become VERIFIED or ACTIVE.

No system component may upgrade an identity state merely because downstream execution requires it.

---

## 13. Adversarial Self-Tests

The design is not considered implementation-ready until it survives these tests.

### A01 — Identity Sufficiency

**Question:** If all authority-event provenance evidence is removed, does Architect Identity alone still authorize a protected mutation?

**Required answer:** NO.

### A02 — Role-Label Substitution

**Question:** Can a string such as `role=Architect` establish human authority by itself?

**Required answer:** NO.

### A03 — Authentication Substitution

**Question:** Can successful authentication alone establish that a specific protected authority event occurred?

**Required answer:** NO.

### A04 — Delegation Expansion

**Question:** Can a delegated Architect identity acquire broader authority than the delegation event permits?

**Required answer:** NO.

### A05 — Revocation Bypass

**Question:** Can a revoked or expired identity continue to satisfy a current authorization requirement?

**Required answer:** NO.

### A06 — Downstream Upgrade

**Question:** Can K15, K3, or another execution component manufacture missing Architect provenance after the fact?

**Required answer:** NO.

### A07 — Parallel Identity

**Question:** Can a second identity namespace become an alternative route to sovereign authority?

**Required answer:** NO.

### A08 — Autonomous Creation

**Question:** Can an AI node, system process, or document create or self-declare Architect Identity?

**Required answer:** NO.

---

## 14. Relationship to Existing Arkadia Identity

Move 1 must not create a parallel user identity architecture.

The design assumes the existing authenticated subject boundary remains the underlying identity substrate unless a later, explicitly authorized architecture decision changes that boundary.

The Architect Identity is therefore a governed role/authority designation bound to an existing canonical subject, not a second personhood model and not a new authentication universe.

Conceptually:

```text
CANONICAL HUMAN SUBJECT
        ↓
ARCHITECT DESIGNATION
        ↓
ARCHITECT IDENTITY
```

The implementation must preserve existing authentication ownership and must not duplicate identity records merely to make the Architect concept visible.

---

## 15. No Credential Design in Move 1

Move 1 design does not select:

- passwords;
- API keys;
- service-account credentials;
- cryptographic keys;
- biometric factors;
- tokens;
- session mechanisms;
- provider credentials;
- secret-storage mechanisms.

Those are implementation decisions belonging to a later authorized mechanism-selection stage.

This artifact defines **what the identity must mean**, not **which credential technology must instantiate it**.

---

## 16. Provisioning Contract

When Move 0 is cleared and Move 1 is explicitly authorized, the future provisioning operation must produce an identity satisfying this contract:

```text
AUTHORIZED HUMAN DECISION
        ↓
IDENTITY PROVISIONING EVENT
        ↓
CANONICAL SUBJECT BINDING
        ↓
ARCHITECT AUTHORITY CLASS
        ↓
IDENTITY VERIFICATION
        ↓
ACTIVE IDENTITY
```

The provisioning event must be recorded separately from the resulting identity object.

The identity object must not be used as retrospective proof that its own provisioning was authorized.

This preserves the provenance distinction:

```text
IDENTITY RECORD
        ≠
PROOF OF IDENTITY ORIGIN
```

---

## 17. Move 1 Closure Conditions

Move 1 may only advance after all applicable conditions are independently established:

1. Move 0 has explicitly passed through its own re-audit gate;
2. the Architect designation has been explicitly authorized by the human sovereign;
3. the canonical human subject has been identified without ambiguity;
4. exactly one intended Architect identity is provisioned within the selected identity substrate;
5. the identity is bound to the intended subject;
6. the authority class is exactly `ARCHITECT`;
7. lifecycle state is independently verified;
8. expiry and revocation semantics are operationally represented;
9. any delegation lineage is explicit and bounded;
10. no second identity or parallel authority system has been created;
11. no credential secret is embedded in the repository artifact;
12. identity authentication remains distinct from authority-event provenance;
13. identity remains distinct from authorization;
14. K15 remains the protected preflight boundary;
15. K3 remains the sole mutation boundary;
16. no autonomous authority has been introduced;
17. the resulting identity state is inspectable;
18. Move 1 is explicitly marked passed only after independent verification.

Until these conditions are satisfied:

```text
MOVE 1 = BLOCKED
```

---

## 18. Explicit Non-Claims

This artifact does **not** claim:

- that an Architect Identity currently exists;
- that an Architect has been provisioned;
- that Move 0 has passed;
- that Move 1 is authorized;
- that any authentication mechanism has been selected;
- that any credential has been created or rotated;
- that any authority event has occurred;
- that human-origin provenance has been established;
- that any protected mutation is authorized;
- that K15 or K3 has been changed;
- that a WorkEvent exists;
- that Barnabas data has been ingested;
- that any runtime has changed.

The design is preparatory, not operational.

---

## 19. Authority and Change Boundary

This document is documentation-only.

Its existence does not provision an identity.

Its existence does not create credentials.

Its existence does not grant Architect authority.

Its existence does not authorize Move 1.

Its existence does not authorize mutation.

Its existence does not establish provenance.

Its existence does not alter runtime behavior.

The governing distinction is:

```text
SCHEMA
    ≠
PROVISIONING
    ≠
VERIFICATION
    ≠
AUTHORIZATION
    ≠
EXECUTION
```

---

## 20. Readiness State

This artifact is intended to be **ready for execution after Move 0 clears**, subject to a final implementation-specific review.

Current state:

```text
MOVE 0                = BLOCKED
MOVE 1 DESIGN         = AUTHORED
MECHANISM             = NOT SELECTED
IDENTITY              = NOT PROVISIONED
CREDENTIALS           = UNTOUCHED
AUTHORITY             = NOT GRANTED
PROVENANCE             = NOT ESTABLISHED
RUNTIME               = UNCHANGED
K15                   = UNCHANGED
K3                    = UNCHANGED
```

The design may therefore move through review now without advancing the operational gate.

---

## 21. Execution Gate

The future operational command must not be inferred from the existence of this document.

The required gate is:

```text
MOVE 0 = PASSED
        AND
ARCHITECT EXPLICITLY AUTHORIZES MOVE 1
        ↓
IMPLEMENTATION MAY BEGIN
```

Absent both conditions:

```text
NO PROVISIONING
NO CREDENTIAL CREATION
NO AUTHORITY GRANT
NO RUNTIME CHANGE
```

---

## Final Invariant

> **Architect Identity identifies the governed human subject and their authority class. It does not, by itself, prove a particular authority event, establish provenance, authorize a protected mutation, or execute anything.**

The design prepares the boundary.

It does not cross it.

**Move 0 remains BLOCKED. Move 1 remains BLOCKED until Move 0 passes and the Architect explicitly authorizes execution.**
