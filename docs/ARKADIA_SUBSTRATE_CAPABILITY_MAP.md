# Arkadia Substrate Capability Map

**Status:** Canonical architecture artifact  
**Scope:** Arkadia source monorepo (Arkadia-Oversoul-Prism/Arkadia)  
**Reference:** main at af3a3541d9fedf8c2d38bb7a0aac56856a879523  
**Purpose:** Define what the canonical Arkadia substrate can natively represent, enforce, trace, and prove without importing an external methodology.

## 1. Capability boundary

Arkadia's substrate is an **evidence-bearing governed-action substrate**.

Its native concern is the controlled relationship between:

IDENTITY → AUTHORITY → AUTHORIZATION → PROPOSAL → APPROVAL → EXECUTION → WORK EVENT → EVIDENCE → VERIFICATION → REVIEW

The repository already describes this as the effective governance order. The substrate must preserve the distinction between each stage rather than infer one stage from another.

> **No stage inherits standing merely because a neighbouring stage is valid.**

- Identity does not imply authority.
- Authority does not imply authorization.
- Authorization does not imply approval.
- Approval does not itself execute.
- Execution does not imply a WorkEvent.
- A WorkEvent does not manufacture evidence.
- Evidence does not imply verification.
- Verification does not automatically produce review.
- Review may alter an earlier governance state.

## 2. Native capabilities

| Capability | Native substrate role | Current evidence | Status |
|---|---|---|---|
| Identity | Authenticate and attribute a subject | require_auth and identity-spine evidence | Implemented / tested; deployment must be witnessed |
| Authority | Determine who may render governed decisions | Govern permission / sovereign-tier enforcement | Implemented / tested |
| Authorization | Gate access to consequential operations | authenticated route boundaries, tool registry | Implemented / tested |
| Proposal | Represent intended action separately from execution | approval/proposal routes and subject attribution | Implemented / tested |
| Approval | Record a distinct governed decision | approval routes; self-approval prevention; single-use decisions | Implemented / tested |
| Execution | Perform an authorized action through a distinct act | tool execution boundary | Implemented / tested |
| Work Event | Preserve operational continuity records | SolSpire WorkEvent spine | Implemented / tested; distinct from kernel Job |
| Evidence | Preserve execution/effect evidence without auto-verification | enterprise evidence store | Implemented / tested as a separate act |
| Verification | Explicitly verify evidence rather than infer verification | enterprise verification store | Implemented / tested as a separate act |
| Review | Expose records for governed human review | scoped approval/review surfaces | Implemented / tested |
| Causal lineage | Traverse relationships forward/reverse where explicitly modeled | enterprise orchestration + console grammar | Implemented in bounded surfaces |
| Scope containment | Keep identity, approval, evidence and execution within subject/scope boundaries | same-subject approval consumption; scoped listings | Implemented in bounded surfaces |
| Unresolved state | Preserve uncertainty without manufacturing completion | existing posture vocabulary and boundary grammar | Architecturally required; canonical primitive still to formalize |

## 3. Evidence classes

Every capability claim must distinguish:

- **IMPLEMENTED:** code exists.
- **TESTED:** a test exercises the mechanism and passes.
- **DEPLOYED:** the code is running on a live environment.
- **PRODUCTION-VERIFIED:** the running environment was directly probed and the boundary was observed to hold.

These statuses are not interchangeable. A passing test is not a production observation. A deployed route is not automatically a verified boundary. A documented architecture is not evidence that the runtime behaves accordingly.

## 4. Proven non-collapse boundaries

The current repository contains explicit tests for several boundaries:

### AUTHORITY ≠ AUTHORIZATION
A principal may be authenticated/authorized to reach an operation without possessing the authority required to decide it.

### APPROVAL ≠ EXECUTION
Approval records a decision. It does not execute the tool.

### EXECUTION ≠ WORK EVENT
A gated tool execution does not automatically create a kernel job or WorkEvent.

### WORK EVENT ≠ EVIDENCE
A WorkEvent does not automatically produce evidence or verification.

### EVIDENCE ≠ VERIFICATION
Evidence may exist without verification. Verification is a separate explicit act and references evidence rather than being manufactured by evidence creation.

These distinctions are enforced by dedicated boundary tests, not merely by prose.

## 5. What the substrate can prove

When the relevant runtime witness exists, Arkadia can establish bounded claims such as:

1. Who acted.
2. Which authority relationship applied.
3. Whether the operation was authorized.
4. What was proposed.
5. Whether a distinct authority approved it.
6. Whether execution occurred under that decision.
7. What operational record was created.
8. What evidence was recorded.
9. Whether that evidence was separately verified.
10. What a reviewer was permitted to inspect.
11. Which causal relationships are explicitly represented.
12. Which relationships remain absent, contradicted, or unresolved.

The substrate must never upgrade an unproven relationship merely because adjacent records exist.

## 6. Canonical non-claims

Arkadia must not claim that:

- an authenticated actor is automatically authoritative;
- an approval proves execution;
- an execution proves intended effect;
- a WorkEvent proves evidence;
- evidence proves verification;
- a verified event proves consequence;
- a complete workflow proves correctness;
- an AI-generated explanation proves that the described action occurred;
- a neighbouring record supplies missing evidence;
- a deployment claim proves production behavior without a runtime witness.

These are architectural prohibitions, not documentation preferences.

## 7. Product projections

The substrate is canonical. Product surfaces are projections over it.

### Engineering Lab
inspect → propose → approve → execute → observe → evidence → verify

### Weaver
operational intent → governed proposal → authorization → execution → work event → evidence → verification

### SolSpire
enterprise decision → authority → proposal → approval → authorization → execution → evidence → review

### Solariun
The same substrate can preserve governed human actions and continuity without making Solariun itself the authority layer.

### Arkana / Oracle
Arkana can synthesize, retrieve, propose and explain. It must not become a second authority or mutation perimeter.

**Different surfaces. Same substrate.**

## 8. Canonical architectural rule

External methodologies, assessment frameworks, client-specific procedures and future vertical protocols must be represented as **bounded configurations or projections over Arkadia's substrate**.

They must not create:

- a second identity system;
- a second authority system;
- a second authorization perimeter;
- a second execution path;
- a second evidence store;
- a second verification mechanism;
- an implicit mutation channel.

The substrate remains methodology-neutral.

## 9. Immediate engineering gaps

### P0 — Formalize UNRESOLVED
Make unresolved state a first-class canonical primitive with explicit semantics and tests.

UNRESOLVED ≠ FALSE  
UNRESOLVED ≠ TRUE  
UNRESOLVED ≠ PERMITTED  
UNRESOLVED ≠ VERIFIED  
UNRESOLVED ≠ COMPLETE

### P1 — Canonicalize evidence lineage
Ensure every consequential evidence object has explicit subject, scope, source/event reference, temporal provenance and verification relationship.

### P1 — Canonicalize causal edges
Where a transition is important, model the transition itself rather than deriving it from endpoint records.

### P1 — Strengthen production witness coverage
For every claimed production capability: implemented → tested → deployed → directly probed → production-verified. No skipped arrows.

### P2 — Unify projection contracts
Engineering Lab, Weaver, SolSpire and Arkana should consume canonical substrate contracts rather than recreating governance semantics locally.

### P2 — Capability registry
Expose a machine-readable capability manifest stating, per capability: mechanism, implementation, test evidence, deployment evidence, production witness, scope, and known gaps.

## 10. Acceptance principle

A capability enters the **canonical proven set** only when the evidence chain supports the exact claim being made.

CLAIM → MECHANISM → TEST → DEPLOYMENT → RUNTIME WITNESS → ACCEPTED CAPABILITY

If the chain stops:

> **the claim stops there.**

That is the substrate's governing discipline.

## 11. Product thesis

Arkadia's durable product primitive is not an AI agent.

> **A governed action whose identity, authority, authorization, execution, evidence and verification can be independently traced.**

Models can change. Agents can change. Interfaces can change.

The substrate preserves the relationship between **who may act, what was authorized, what actually happened, and what can be evidenced about it**.

That is the continuity layer.

---

**Canonical direction:** strengthen the substrate first; compose products second; add intelligence only where the substrate can preserve the evidence boundary.