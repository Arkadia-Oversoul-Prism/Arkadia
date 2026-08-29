# WEAVER-W3 — Operator Workbench Scoping

**SCOPE ≠ AUTHORIZATION · DISPLAY ≠ APPROVAL · EXECUTION LOCKED**

## Capability

Operators supply optional `affected_paths` / `symbols` so analysis→plan→changeset→patch bind concrete files.

## API

```json
POST /api/analyze
{
  "objective": "...",
  "affected_paths": ["weaver/execution.py"],
  "symbols": ["execute_patch"],
  "pass_spec_display": { "allowed_paths": ["weaver/"], "forbidden_paths": ["api/"] }
}
```

`pass_spec_display` is informational scope context only. Execution remains LOCKED without K15 PatchApproval bindings.

## Launch

`python -m weaver.workbench_app web`
