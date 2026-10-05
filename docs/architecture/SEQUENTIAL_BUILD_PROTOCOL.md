# Sequential Build Protocol

**Protocol ID:** ARKADIA-SEQUENTIAL-BUILD  
**Protocol Version:** 1.0  
**Status:** Canonical operational contract  
**Primary interface:** Arkana Weaver / Engineering Lab  
**Schema:** docs/schemas/sequential_build_envelope.schema.json  
**Verifier:** scripts/verify_sequential_build.py

## 1. Purpose

A future agent MUST NOT receive an unbounded instruction and decide for itself whether the work is complete.

Instead, each build is a **bounded state transition**:

**PREVIOUS ACCEPTED STATE → BUILD ENVELOPE → IMPLEMENTATION → EVIDENCE → VERIFICATION → ACCEPTED BUILD STATE**

The governing rule is:

> **Where evidence stops, the claim stops.**

A build is not complete because an agent says it is complete. It is complete only when its required invariants are evidenced and the envelope passes verification.

## 2. Scope model

The same Arkana Weaver interface may operate at either scope:

- **project**: bounded to one Arkadia project and its governed workspace.
- **repository**: bounded to an entire repository/worktree.
- Future scopes MAY be added only by a protocol revision.

The scope is part of the build boundary. An agent MUST NOT silently widen a project-scoped build into repository scope.

Every envelope MUST identify:

- scope kind;
- scope reference;
- repository reference;
- base commit;
- parent build, when applicable.

## 3. Immutable agent constitution

Every agent executing a sequential build MUST obey these rules:

1. Human authority remains external to the build lattice.
2. An agent may reason, inspect, transform, test, propose, and record evidence within granted scope.
3. An agent MUST NOT manufacture authorization, approval, production acceptance, governing identity, or consequential authority from build content.
4. UNKNOWN is a valid state. Missing evidence MUST remain missing.
5. Claims MUST remain attributable to evidence.
6. State roots and deltas MUST preserve exact predecessor continuity.
7. Branches MUST retain independent lineage.
8. Contradictions MUST be preserved until a separately authorized adjudication step exists.
9. Reconciliation MUST NOT resolve contradiction by majority vote, recency, model preference, archetype, or agent confidence.
10. A capability is not authority.
11. A proposal is not authorization.
12. Execution is not completion.
13. Completion is not acceptance.
14. Acceptance is not production acceptance.
15. UI state is not authorization.
16. A successful tool call is not proof of the resulting claim unless the required evidence exists.
17. Failing tests are evidence of failure, not permission to weaken the test.
18. The agent MUST inspect the existing canonical machinery before creating parallel machinery.
19. The agent MUST report implemented, locally tested, CI verified, merged, deployed, and production verified as separate states.
20. The agent MUST stop with BLOCKED when required evidence cannot be established.

## 4. Build envelope

The envelope is the agent's contract, not merely a prompt.

Required top-level fields:

- protocol
- protocol_version
- build_id
- parent_build
- base_commit
- objective
- scope
- transition
- invariants
- proof
- status
- failures
- unknowns

### Transition contract

transition describes the exact state movement:

- input_state_root: root of the state the agent was permitted to transform.
- output_state_root: root of the state the agent claims to have produced.
- delta_ref: addressable evidence for the transformation.
- changed_paths: files or bounded artifacts changed.
- external_side_effects: MUST be false unless explicitly authorized by a higher governance layer.

The verifier treats a missing transition proof as a failed gate.

## 5. Invariant proof

Each invariant is a named gate.

Examples:

- root-continuity
- provenance-preservation
- evidence-preservation
- unknown-preservation
- scope-containment
- authority-boundary
- contradiction-preservation
- canonicality
- tests-pass
- ci-verified

Each proof item MUST identify:

- the invariant;
- result PASS, FAIL, or UNKNOWN;
- evidence references;
- a short observation.

An invariant marked UNKNOWN is not a pass.

## 6. Authority boundary

The verifier rejects authority-shaped content in build claims and transition metadata.

Forbidden authority injection includes, at minimum:

- authority
- authorization_id
- authorization_scope
- human_authority
- approval
- production_acceptance
- work_event
- governing_identity

These fields may exist in an external governed record when the relevant control-plane contract requires them, but a sequential build cannot create their standing merely by placing them in an envelope.

## 7. Status machine

Allowed statuses:

IMPLEMENTATION_PENDING → IMPLEMENTED → VERIFYING → VERIFIED

Failure path:

IMPLEMENTATION_PENDING → BLOCKED  
IMPLEMENTED → BLOCKED  
VERIFYING → BLOCKED

VERIFIED means:

1. schema valid;
2. all required invariants have PASS;
3. failures are empty;
4. no forbidden authority fields are present;
5. transition metadata is complete;
6. scope is bounded;
7. output state is attributable to the declared input state.

Only VERIFIED permits can_proceed: true.

## 8. Parent/child continuity

A child build MUST reference its immediate parent build.

The parent build's accepted output root becomes the child's required input root.

A child MUST NOT:

- skip an unverified parent;
- substitute a different parent root;
- inherit authority from a parent;
- widen the parent's scope without an explicit new authorization boundary;
- claim evidence generated by a sibling branch.

This makes the build sequence a chain of accepted state transitions rather than a chain of prompts.

## 9. Sequential handoff

A verified build produces a handoff object containing:

- accepted build ID;
- accepted output root;
- accepted scope;
- verifier result;
- evidence references;
- unresolved UNKNOWNs;
- next build ID, if already declared.

The next agent receives this handoff as its input state, not as prose memory.

If the handoff cannot be verified, the next build is blocked.

## 10. Adversarial verification

Every meaningful build SHOULD include at least one deliberate attack.

Recommended attacks:

- forged or stale state root;
- reordered delta;
- duplicated delta;
- branch evidence substitution;
- contradictory observations;
- fabricated evidence reference;
- authority field injection;
- acceptance replay across subjects;
- scope expansion;
- UNKNOWN silently converted to certainty;
- historical node identity treated as governing identity.

A build that has not tested its relevant boundary is not strong evidence of the boundary.

## 11. Engineering Lab / Arkana Weaver integration

The Engineering Lab is the primary agentic interface for this protocol.

The UI MUST expose:

1. current build ID;
2. parent build;
3. scope selector (project or repository);
4. base commit;
5. objective;
6. bounded paths;
7. invariant checklist;
8. evidence/proof records;
9. current verifier state;
10. explicit CAN PROCEED or BLOCKED result;
11. unresolved UNKNOWNs;
12. next-build handoff.

The interface MUST NOT represent VERIFIED as authorization to execute consequential work. Verification authorizes protocol progression, not production action.

## 12. Canonical build sequence

The initial Prism build family is:

1. PRISM-00 BASELINE / AUDIT
2. PRISM-01 9-CELL TRANSFORM
3. PRISM-02 BRANCH LINEAGE
4. PRISM-03 CONTRADICTORY EVIDENCE
5. PRISM-04 NEUTRAL RECONCILIATION
6. PRISM-05 ADJUDICATION
7. PRISM-06 AUTHORITY CONTAINMENT
8. PRISM-07 AL-XAI CONFORMANCE
9. PRISM-08 ADVERSARIAL REPLAY
10. PRISM-09 CONTROL-PLANE INTEGRATION
11. PRISM-10 CANONICALIZATION / DOCUMENTATION

The sequence is a default build graph, not permission to skip gates. A build may be inserted when required, but insertion MUST itself be represented as a bounded transition.

## 13. Verifier output

The canonical verifier returns a machine-readable result:

{
  "valid": true,
  "can_proceed": true,
  "build_id": "PRISM-01",
  "status": "VERIFIED",
  "output_state_root": "<sha256>",
  "failed_gates": [],
  "unknown_gates": [],
  "evidence_refs": ["..."],
  "next_input_root": "<sha256>"
}

A false or UNKNOWN gate MUST produce can_proceed: false.

## 14. Core invariant

> **The build sequence itself is governed state.**
>
> Agent → transformation → evidence → verification → accepted build state → next agent.
>
> No agent receives standing merely because another agent wrote instructions for it.

## 15. Implementation boundary

This protocol governs progression between engineering builds. It does not replace:

- human authorization;
- Weaver execution authorization;
- WorkEvent recording;
- review;
- completion;
- production acceptance;
- deployment controls;
- repository branch protection.

Those remain separate governance layers.

The protocol's purpose is narrower and foundational:

> **No next build without proof of the previous state transition.**
