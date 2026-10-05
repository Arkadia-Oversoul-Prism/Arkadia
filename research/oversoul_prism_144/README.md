# Oversoul Prism 144 Substrate

Status: research prototype, non-governing.

This package turns the recovered A01-A12 x L01-L12 address space into a deterministic, inspectable transformation substrate.

It:
- validates all 144 historical addresses against the recovered registry;
- represents node application as immutable transformation state;
- computes deterministic SHA-256 state roots;
- emits explicit state deltas;
- preserves evidence references and UNKNOWN fields;
- records node provenance;
- rejects historical nodes that carry authority or executable status.

It does not:
- authorize actions;
- create identities;
- create WorkEvents;
- claim verification or completion;
- call models or external tools;
- perform external side effects;
- infer meanings for L01-L12;
- turn historical archetypes into personas.

The bounded 3x3 slice is A01-A03 x L01-L03 = 9 nodes.

The governing chain remains:
Human authority -> Identity -> Context -> Authorization -> Execution -> WorkEvent -> Evidence -> Verification -> Projection

The lattice is a transformation substrate inside that architecture, not a replacement for it.

## 9-cell transformation/conformance harness

The bounded conformance slice is A01-A03 x L01-L03.

Each branch starts from one immutable genesis state and recursively traverses its
three layer addresses. The harness checks:

- every delta consumes exactly the previous state root;
- the branch result root equals the final delta result root;
- evidence references and UNKNOWN fields survive recursion;
- branch identity and node provenance survive neutral convergence;
- agreeing branch claims converge without creating verification;
- deliberately contradictory branch claims remain explicit conflicts;
- authority-shaped fields are rejected at the transformation boundary;
- convergence cannot mint authorization, approval, production acceptance, or WorkEvent authority.

The contradiction test is intentional. A branch is made to claim one value while another
claims a different value for the same probe fact. Neutral convergence removes the disputed
claim from the canonical claim set, records the conflict key, preserves both branches'
provenance, and leaves verification UNKNOWN.

This harness is a research/conformance test. It does not assign meanings to L01-L12,
does not execute external tools, and does not authorize any action.
