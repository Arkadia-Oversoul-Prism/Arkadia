# Oversoul Prism Acceptance and WorkEvent Boundary

## Status

Research prototype. Non-governing. No production execution.

## Question

What constitutes acceptance, who owns that boundary, and how can an accepted result become a consequential WorkEvent without collapsing verification, authorization, and execution into one operation?

## Acceptance

Acceptance is an explicit decision that a verified result is eligible to enter an operational context.

Acceptance is not:

- evidence;
- resolution;
- verification;
- authorization to perform every possible action;
- execution;
- completion.

A minimal accepted-result record contains:

- the verified claim or result;
- the verification record digest;
- the accepting authority;
- the authorization scope that permits acceptance;
- the accepted context/project;
- the acceptance timestamp or sequence identifier;
- an explicit status.

## Ownership

The research prototype does not assign production ownership to an AI node, verifier, resolver, model, or lattice layer.

Production acceptance belongs to the **human-authority / governance boundary** appropriate to the context.

The key invariant is:

`verification may recommend eligibility; only the authorized acceptance boundary may accept.`

An automated system may execute a previously accepted instruction only within the authorization already granted. It may not infer acceptance from verification.

## WorkEvent boundary

A WorkEvent is an observable record of a consequential state transition. It is not the authorization itself and not proof that the action was correct.

The safe sequence is:

`Verified result → Acceptance → Execution authorization → Execution → WorkEvent → Verification/Review`

Where an acceptance already contains explicit execution authorization for a bounded action, the authorization may be carried forward by reference. It must not be recreated from the WorkEvent.

## Non-collapse invariants

1. Acceptance cannot happen without a verified result.
2. Acceptance records who accepted and under what scope.
3. Acceptance does not itself execute an action unless execution authority is explicitly included.
4. Execution cannot infer authorization from verification.
5. A WorkEvent records an observed consequential transition; it does not create permission.
6. WorkEvent creation cannot retroactively authorize the action.
7. Completion remains distinct from execution.
8. Verification of the WorkEvent remains a separate operation.

## Research experiment

The probe models two paths:

### Accepted but not executable

`Verified → Accepted → no execution authorization → execution rejected`

### Accepted and explicitly executable

`Verified → Accepted(scope/action) → Authorized execution → WorkEvent`

The WorkEvent references the acceptance and execution authorization but does not replace either.

## Architectural consequence

The resulting chain is:

`Evidence → Claim → Conflict → Resolution → Verification → Acceptance → Authorization → Execution → WorkEvent → Review`

This preserves the Arkadia boundary rule:

**execution ≠ completion ≠ approval ≠ merge ≠ deployment ≠ production acceptance.**

Acceptance is therefore a governance transition, while WorkEvent is an observability transition.