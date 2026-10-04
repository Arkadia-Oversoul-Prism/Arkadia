# Node Transformation Probe

A tiny, deterministic probe for the recovered Prism lattice.

It tests one proposition:

> A node can transform state without becoming an authority.

The probe runs two sequential nodes, A01-L01 → A01-L02.

It checks that:

- evidence survives the transformation;
- UNKNOWN survives unless explicitly resolved;
- a provenance digest can be computed;
- no authority is created;
- no external side effect occurs.

Run:

```bash
python research/oversoul_prism_node_transform/probe.py
```

This is not an LLM runtime and not production execution.
