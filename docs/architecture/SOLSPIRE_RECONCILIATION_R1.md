# R1 — Weaver Governance Convergence

**Base checkpoint:** `57fb207842e45150c4f81545f6168d8e72a64d5e`
**Branch:** `recon/solspire-r0`
**Scope:** `solspire/project_execution.py` only, plus canonical Weaver governance extraction and tests.

## Objective

Reconcile SolSpire's governed project execution adapter against the canonical Weaver execution/governance implementation without changing frontend behavior, introducing authority, or creating another mutation path.

## Change

The duplicated governance semantics formerly implemented inside `solspire/project_execution.py` now live in `weaver/governance.py`:

- K15 readiness evaluation;
- PassSpec construction;
- PatchApproval binding.

The existing canonical hashing and K15/K3 execution primitives remain in `weaver.execution`.

`solspire/project_execution.py` remains as a compatibility/project-context adapter. It now:

- derives project-specific defaults;
- enriches canonical PassSpec/approval representations with project-facing metadata;
- delegates readiness to Weaver;
- delegates execution to `weaver.execution.execute_patch`.

## Preserved contract

- PROJECT ACCESS ≠ PASSSPEC ≠ PATCHAPPROVAL ≠ EXECUTION.
- SolSpire does not authorize itself.
- SolSpire does not implement K3.
- K3 remains the sole mutation transaction path.
- `run_k3=False` remains a non-mutating precheck mode.
- Existing SolSpire function names and response shapes are preserved for compatibility.

## Proofs added

`tests/test_solspire_r1_governance_convergence.py` proves:

1. SolSpire readiness output delegates to canonical Weaver readiness.
2. SolSpire PassSpec/approval builders match canonical Weaver objects for semantic fields.
3. SolSpire no longer defines local `PassSpec(...)` or `PatchApproval(...)` constructors.
4. SolSpire no longer defines local hash functions or path-authorization logic.
5. Weaver exposes the canonical governance primitives.
6. The SolSpire project execution adapter still reaches the K15 seam without invoking K3 in precheck mode.

## Explicit non-goals

R1 does not:

- remove `solspire/project_execution.py`;
- remove `solspire/weaver_bridge.py`;
- change direct filesystem/GitHub mutation paths;
- modify the frontend;
- introduce K17 semantics;
- introduce autonomous mutation;
- introduce autonomous commit/push;
- create a second K3 path;
- create a new authorization authority.

## Validation status

The R1 test suite has been added and a branch-scoped validation workflow has been added. The available GitHub workflow-run interface did not report a run for the branch commit, so CI execution is **not claimed as passed** here. Code-level proof is captured in the test suite; runtime CI must be confirmed before treating R1 as green.

## Next gate

Do not proceed to frontend reconciliation. The next pass after a green R1 should be R2: close the direct repository mutation alternatives, starting with the SolSpire GitHub commit route, while preserving legitimate read-only/project workspace capabilities.
