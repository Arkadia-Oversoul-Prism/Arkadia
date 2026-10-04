# Oversoul Prism Verification Boundary

## Status

Research prototype. Non-governing. No production execution.

## Question

Can a resolved claim be independently verified without allowing the verification mechanism to become the resolver or to create authority?

## State transition

`CONFLICT → RESOLVED_PENDING_VERIFICATION → VERIFIED | VERIFICATION_FAILED | UNKNOWN`

Verification is a separate operation from resolution.

The verifier may inspect the resolution evidence and the resolved claim. It may confirm or reject the claim according to an explicit verification predicate. It may not:

- choose the claim to resolve a conflict;
- alter the resolution record;
- grant authorization;
- manufacture evidence;
- declare production acceptance.

## Independence invariant

A verification operation must receive a resolved state as input and emit a verification result as a separate record.

`resolution_record ≠ verification_record`

The verification record carries the input resolution digest so the relationship is inspectable without allowing the verifier to rewrite history.

## Outcomes

- `VERIFIED`: the explicit verification predicate passes.
- `VERIFICATION_FAILED`: the predicate is evaluated and fails.
- `UNKNOWN`: the predicate cannot be evaluated from available evidence.

None of these outcomes grants authority.

## Acceptance boundary

Production acceptance is intentionally separate from verification.

`verification ≠ acceptance`

A verified claim can therefore remain pending human or governance acceptance where the canonical architecture requires it.

## Architectural consequence

The Prism now separates four distinct transitions:

`CONFLICT → RESOLUTION → VERIFICATION → ACCEPTANCE`

Each transition has its own state, provenance, and authority boundary.