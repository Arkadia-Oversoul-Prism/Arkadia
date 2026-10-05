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
