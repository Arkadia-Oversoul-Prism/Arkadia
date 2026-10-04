# Oversoul Prism Node Transformation Contract

**Status:** research prototype  
**Authority:** none  
**Production:** false

## Purpose

This document defines the smallest testable meaning of an Oversoul Prism node.

A node is **not an agent** and does not acquire authority by existing in the lattice.

A node performs a bounded transformation of an input state at a specified function/layer coordinate and emits a new state plus provenance.

## Transformation invariant

For a node `Axx-Lyy`:

`state_in → transform(Axx, Lyy, state_in) → state_out`

The transformation must preserve:

1. **Identity**: the originating context remains addressable.
2. **Provenance**: the source evidence remains attached.
3. **Authorization boundary**: the node cannot create authority.
4. **Uncertainty**: UNKNOWN remains UNKNOWN unless evidence resolves it.
5. **Determinism**: identical inputs and contract produce identical normalized output.
6. **Continuity**: the next layer consumes the prior normalized state, not an unrelated reconstruction.

## What changes across layers

The historical evidence supports changing **contextual granularity**, not changing authority.

Therefore a layer transition may:

- summarize;
- normalize;
- extract invariants;
- expose finer-grained structure;
- preserve unresolved fields;
- attach observations.

It may not silently:

- invent facts;
- promote inference to evidence;
- grant authorization;
- declare completion;
- create a consequential external side effect.

## Provenance envelope

Each transformation carries:

`source → node → input_digest → transformation → output_digest → next_node`

A prototype record contains:

- node_id
- function_id
- layer_id
- context_id
- input_state
- input_evidence
- transformation
- output_state
- output_evidence
- unknowns
- input_digest
- output_digest
- next_node
- execution_status

## Verification boundary

This prototype tests **state transformation only**.

It does not establish that the historical A01–A12 functions are semantically executable by themselves. It also does not establish the historical Bloom threshold or any symbolic score as a modern acceptance criterion.

> Where evidence stops, claim stops.
