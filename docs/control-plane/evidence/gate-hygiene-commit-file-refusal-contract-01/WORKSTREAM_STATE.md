# WORKSTREAM STATE · gate-hygiene-commit-file-refusal-contract-01

**Workstream:** test-hygiene / SolSpire mutation-closure contract convergence
**Owner of execution:** OpenHands (Weaver pass) · **Authority:** human sovereign
**PR:** #254 · **Branch:** `test-hygiene/commit-file-refusal-contract-01`
**BASE_MAIN:** `357fbd83001924e909979fbaebdedbd991a2aadb`
**Head at record time:** `6107ab4cc4f9092835fd4ffef88ae87902b309b6`

## Status

IMPLEMENTED — code + evidence committed, PR open, awaiting human merge.

## What changed

`solspire/tools_github.py::commit_file` refusal dict now carries
`"code": "MUTATION_DISABLED"` (documented in `SOLSPIRE_RECONCILIATION_R2.md`).
One node repaired; zero new failures.

## Next bounded task (NOT authorized yet — proposed)

`test-hygiene/execution-runtime-refusal-shape-01` — resolve the **contradiction**
between:
- `tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
  (expects `results[0]["code"] == "MUTATION_DISABLED"`, i.e. a blocked result), and
- `tests/test_convergence_mutation_boundary.py::test_generic_execution_runtime_rejects_engineering_mutation`
  (expects a synchronous `PermissionError`, currently passing).

This needs a **product decision** on the refusal shape (raise vs. blocked-result)
before any code changes. Human authority required to select the shape.

## Explicit non-goals for this PR

R1 `pass_id` delegation; R3 shape; frontend literal pins (#249/#251/#253);
Living-Gate proxy-invalidation (F-01, sovereign); `AGENTS.md` encoding
(insertion-only, sovereign); CP10 allowlist.

## Baseline fingerprint (measured, not inherited)

`PYTHONPATH=archive/legacy_python pytest tests/ -q --continue-on-collection-errors`

| revision | result | nodes | outcomes fingerprint |
|---|---|---|---|
| `357fbd8` | 28F / 1362P / 20S / 1E | 29 | `5745314330ce11df9ee8c06986c506ac71a5883e4c2ff1f0a4902400e971bef6` |
| branch | 27F / 1363P / 20S / 1E | 28 | `0556b8e0f530df682e70ddcec94a9e9193a97f064077ee311d1960e912dd26b9` |

## Authority boundary

No merge, no push to `main`. Human merge only.
