# R3 — SolSpire Ground-Truth Reconciliation

**Base:** `ecb4e7fad1e43d2afafe1fb539f8440bb8f4d772` (R2)
**Head:** `3c7686885530fff8cd5e432dfc7903bb60e27026`
**Scope:** reconcile SolSpire `ExecutionRuntime` without inventing a second engineering execution engine
**Status:** IMPLEMENTED / VALIDATION PENDING

## Finding

`solspire/execution_runtime.py` is not semantically equivalent to Weaver's governed engineering execution. It owns a separate generic in-process workflow lifecycle: execute, pause, resume, cancel, execution state, and retry accounting.

That lifecycle is retained for now because no canonical Weaver equivalent was found in the inspected surface. R3 therefore does **not** pretend the two runtimes are interchangeable.

The important boundary is instead made explicit: `ExecutionRuntime` is a generic SolSpire workflow coordinator, not an engineering repository mutation engine.

## Surgical change

The previous dispatcher used a catch-all match arm:

`case "llm" | _:`

That meant an unknown tool name silently became an LLM invocation. This was an accidental authority expansion and could turn an unrecognized engineering operation into model execution.

R3 changes dispatch to:

- explicitly recognize `llm`;
- explicitly recognize the existing read/workspace/project operations;
- fail closed with `NOT_AVAILABLE` for unknown tools;
- report `mutation_path: NONE` for unknown operations.

No direct Weaver transaction is added to this runtime. No second K3 path is introduced.

## Ownership after R3

```text
SolSpire ExecutionRuntime
  ├── workflow lifecycle: execute / pause / resume / cancel
  ├── read/workspace/project tool dispatch
  └── explicit LLM invocation

Engineering repository execution
  └── Weaver → Governance → K15 → K3
```

## Tests

`tests/test_solspire_r3_runtime_boundaries.py` proves:

- unknown tool names fail closed instead of falling through to LLM;
- explicit LLM invocation remains functional;
- the runtime does not import or invoke Weaver's transaction/execution mutation primitives directly.

## Explicitly deferred

R3 does not remove `ExecutionRuntime`, redesign its lifecycle, or migrate generic SolSpire workflow state into Weaver without a proven canonical owner and caller inventory.

Frontend integration remains deferred.

## Exit condition

The accidental catch-all execution path is removed and the runtime's ownership is explicit. Future consolidation can address lifecycle duplication only after identifying a real canonical owner rather than deleting a functioning compatibility surface by assumption.
