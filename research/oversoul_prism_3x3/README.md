# Oversoul Prism 3×3 Research Prototype

This is the first bounded experimental slice of the recovered 12×12 architecture.

**A01–A03 × L01–L03 = 9 nodes.**

It exists to test topology and invariants before any larger implementation.

## What it tests

1. Stable Axx-Lyy addressing.
2. Sequential recursion within each function branch.
3. Context-granularity ordering L01 → L02 → L03.
4. Absence of invented cross-function edges.
5. Explicit non-authority and non-production boundaries.

## What it does not do

- no LLM calls;
- no external APIs;
- no consequential execution;
- no authorization grants;
- no WorkEvents;
- no production routing;
- no claim that historical resonance thresholds are valid.

Run the validator:

```bash
python research/oversoul_prism_3x3/validate.py
```

The experiment is a topology probe, not a new runtime.
