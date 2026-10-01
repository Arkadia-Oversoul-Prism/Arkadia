# Relational Lineage 01

Status: AUTHORIZED
Scope: canonical relational graph projection

The graph remains note-to-note and remains the single Knowledge OS graph implementation.

This bounded change exposes GATE-01 provenance alongside graph nodes and establishes existing
conversation sequence edges using the already-canonical `replies_to` relationship.

It does NOT:
- create a second graph;
- create external-node types;
- infer authorship;
- turn provenance into WorkEvent;
- change authorization or execution;
- alter the canonical runtime.

For a graph consumer, lineage is therefore:

canonical note
  ├─ provenance → capture source / raw checksum / authorship state
  └─ relationships → existing note-to-note graph edges

External sources remain represented by GATE-01 capture records rather than fabricated graph nodes.
