# Gate-hygiene · SolSpire `commit_file` refusal-contract convergence

**Status:** IMPLEMENTED — code change + evidence (merge requires human authority)
**Date:** 2026-10-04
**Measured at:** `357fbd83001924e909979fbaebdedbd991a2aadb` (main, BASE_MAIN)
**Branch:** `test-hygiene/commit-file-refusal-contract-01`
**Gate:** Phase 1 runtime stabilization · Gate-10 governance surface (SolSpire mutation closure)

## 1. Objective

Repair the bounded, repository-owned contract drift on the SolSpire
direct-GitHub-mutation refusal path so that the *implemented* refusal agrees with
the *documented* one. This is the smallest valid next task: one field, one
function, one pre-existing failing node, with no authority-path change.

## 2. Evidence-backed defect

`docs/architecture/SOLSPIRE_RECONCILIATION_R2.md` states that the fail-closed
compatibility shim "returns `MUTATION_DISABLED`". The implementation
(`solspire/tools_github.py::commit_file`) returned `status == "BLOCKED"` but no
`code` key, so the documented machine-readable refusal code was absent.

Measured failure (before repair):

```
tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write
E   KeyError: 'code'
```

The boundary itself held (no network write, `ok is False`, K15/K3 in the error);
only the structured refusal contract had drifted. Classified `REAL_DEFECT`
(contract-code drift, boundary intact) in
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/`
and `docs/control-plane/evidence/gate-hygiene-sh02-queue-disposition-01/`.

## 3. Change (exact)

`solspire/tools_github.py::commit_file` — add the stable refusal code to the
fail-closed return dict:

```python
return {
    "ok": False,
    "status": "BLOCKED",
    # Stable machine-readable refusal code, per SOLSPIRE_RECONCILIATION_R2.
    "code": "MUTATION_DISABLED",
    "error": "Direct GitHub mutation is disabled; use the governed Weaver K15 → K3 path.",
    ...
}
```

No new mutation path, no new authorization path, no signature change, no change
to the read-only exported surface (`__all__` unchanged).

## 4. Scope

- **Allowed paths:** `solspire/tools_github.py`,
  `docs/control-plane/evidence/gate-hygiene-commit-file-refusal-contract-01/**`.
- **Non-goals (explicitly not done):** the sibling R1
  (`pass_id` delegation) and R3 (`ExecutionRuntime`) nodes are **not** touched —
  see §6. No CP10 allowlist change. No `api/main.py` change.
- **Dependencies:** none.

## 5. Verification

| command | expected | measured |
|---|---|---|
| `pytest tests/test_solspire_r2_github_mutation.py -q` | 3 passed | 3 passed |
| `pytest tests/test_convergence_mutation_boundary.py -q` (regression boundary: pins `status == "BLOCKED"` + K15/K3) | 6 passed | 6 passed |
| `pytest tests/architecture -q` | 11 passed | 11 passed |
| full suite node set vs. recorded baseline | delta = exactly the repaired node | recorded below |

Full suite, `PYTHONPATH=archive/legacy_python pytest tests/ -q --continue-on-collection-errors`:

| revision | result | failing/error nodes | outcomes fingerprint |
|---|---|---|---|
| `357fbd8` (baseline) | 28 failed / 1362 passed / 20 skipped / 1 error | 29 | `5745314330ce11df9ee8c06986c506ac71a5883e4c2ff1f0a4902400e971bef6` |
| this branch | 27 failed / 1363 passed / 20 skipped / 1 error | 28 | `0556b8e0f530df682e70ddcec94a9e9193a97f064077ee311d1960e912dd26b9` |

Sorted-node delta: **1 fixed, 0 new** —
`FAILED tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write`.
No other node's identity changed, so the fingerprint shift is fully attributed.

## 6. Remaining uncertainty / adjacent nodes not repaired

- `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
  demands `results[0]["code"] == "MUTATION_DISABLED"` from `ExecutionRuntime.execute`,
  but the runtime raises `PermissionError` synchronously — and
  `tests/test_convergence_mutation_boundary.py` **pins that raise** and currently
  passes. Converging R3 therefore requires a product decision on the refusal
  *shape* (raise vs. blocked-result), i.e. it is a **contradiction between two
  live tests**, not a mechanical repair. Not in scope here; recorded as a separate
  proposed workstream (`test-hygiene/execution-runtime-refusal-shape-01`).
- `test_solspire_r1_governance_convergence.py` (2 nodes) needs the Weaver
  `pass_id`/`execute_patch` semantics — product judgement, separate workstream.
- Frontend literal pins (`test_identity_spine_w1`, `test_m02_reasomate_truth`,
  `test_ais_w2_living_gate_grove_handoff`) are owned by open PRs #249/#251/#253
  and the Living-Gate proxy-invalidation is a governance call — not duplicated here.
- `test_agents_md_encoding_adjudication.py` is under the AGENTS.md insertion-only
  constraint (sovereign-reserved) and is not repairable in a shallow clone.

## 7. Authority boundary

Bounded code repair + tests + evidence. No merge. No push to `main`. Human
authority is required to merge this PR.
