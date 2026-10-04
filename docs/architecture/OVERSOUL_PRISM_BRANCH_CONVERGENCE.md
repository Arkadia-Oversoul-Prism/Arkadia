# Oversoul Prism Branch Convergence

## Status
Research prototype. Non-governing. No production execution.

## Question
Can multiple functional transformation branches converge on one evidence-bearing state without losing provenance, uncertainty, or authority boundaries?

## Model
A shared input state is transformed independently through bounded deterministic branches:

- A01-L01 → A01-L02 → A01-L03
- A02-L01 → A02-L02 → A02-L03
- A03-L01 → A03-L02 → A03-L03

The branches preserve the same canonical evidence and UNKNOWN fields while attaching branch-specific provenance.

A neutral convergence operation then combines the branch outputs.

Convergence is **not consensus**. It must not choose a winner between contradictory claims. Contradictions remain explicit as unresolved conflicts.

## Invariants
A valid convergence must preserve:

1. Source evidence.
2. UNKNOWN fields unless explicitly resolved by evidence.
3. Distinguishable branch provenance.
4. Deterministic canonical facts.
5. Explicit conflicts where branches disagree.
6. No newly created authority.
7. No external side effects.
8. No LLM calls.
9. No claim of verification merely because convergence succeeded.

## Expected result
For agreement, the convergence state contains one canonical fact plus all branch provenance.

For disagreement, the convergence state contains the competing claims under `conflicts` and leaves the relevant verification state `UNKNOWN`.

The lattice therefore behaves as a **coherence topology**, not a consensus authority.

## Boundary
This prototype does not establish that the historical 144-node lattice should become a production runtime. It only tests one property that a future runtime would need.
