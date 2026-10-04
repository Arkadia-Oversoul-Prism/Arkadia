# Oversoul Prism Resolution Authority and Evidence Sufficiency

## Status

Research prototype. Non-governing. No production execution.

## Question

When a conflict reaches an explicit resolution boundary, what minimum conditions permit a resolution transition without allowing the lattice to manufacture authority or certainty?

## Boundary

Resolution requires two independent inputs:

1. **Evidence sufficiency**: the proposed resolution must identify evidence that supports the selected claim.
2. **Resolution authority**: an explicit resolver must be authorized for the relevant context.

Neither condition is implied by branch count, node depth, model confidence, convergence, or prior transformation.

## Decision matrix

| Evidence | Resolver authority | Result |
|---|---|---|
| missing | missing | REJECTED |
| sufficient | missing | REJECTED |
| missing | present | REJECTED |
| sufficient | present | RESOLVED_PENDING_VERIFICATION |

The prototype deliberately does not define a production authority registry. It represents authorization as an explicit input and rejects UNKNOWN authority.

## Evidence rule

Evidence sufficiency is intentionally narrow in this experiment:

- evidence must be present;
- evidence must identify a source;
- evidence must explicitly support the proposed claim;
- evidence does not automatically mean verification.

## Authority rule

The resolver must carry an explicit authorization record:

`resolver → authorization_id → scope → permitted_action`

An absent, unknown, or mismatched authorization cannot resolve a conflict.

## Architectural consequence

The Prism now has a three-step epistemic boundary:

`Conflict → Resolution eligibility → Resolved pending verification`

Resolution is therefore neither consensus nor verification. It is an explicitly authorized state transition backed by identified evidence.

Production authority semantics remain UNKNOWN until established by the canonical governance architecture.