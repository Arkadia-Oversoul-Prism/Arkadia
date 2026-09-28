# ARK-WEAVER-01 — Canonical Enterprise Orchestration Spine

Status: IMPLEMENTATION BASELINE
Specification authorized 2026-09-28.

This implementation introduces ten durable enterprise-operational primitives:
Canonical Record, Human Authority Event, Interpretation Record, Knowledge
Mutation, Operational Event, Proposal, Authorization, Execution Attempt,
Evidence Record, and Verification Record.

It deliberately does not modify WorkEvent semantics, K15/K3, Eden
instantiation, or create a repository mutation path. Operational records are
append-only and correlated. Claims can be reverse-walked to their canonical
source or human authority event where such ancestry exists.

The initial acceptance exercise is a deterministic simulated Eden supplier
path. It proves the transition gates without asserting that simulated evidence
is real-world evidence.
