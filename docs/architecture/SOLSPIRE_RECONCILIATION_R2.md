# R2 — SolSpire Direct GitHub Mutation Closure

**Base:** `648fd025e5e70e2c1b389a393b2df36dd3119f83` (R1 validation workflow fix)
**Branch:** `recon/solspire-r0`

## Objective

Close the direct SolSpire GitHub repository mutation alternative identified by R0 while preserving legitimate read-only GitHub capabilities.

## Change

`solspire/tools_github.py` no longer performs GitHub Contents API writes.

The former `commit_file()` implementation has been replaced by a fail-closed compatibility shim. It returns `MUTATION_DISABLED` and points callers to the canonical Weaver K15 → K3 path. The symbol is retained temporarily only so legacy callers cannot accidentally gain a new mutation route through an import failure or an unhandled network write.

The module's exported surface is explicitly read-only:

- `list_repos`
- `get_tree`
- `read_file`
- `get_repo_info`

The legacy `/solspire/tools/github/commit` route therefore remains compatibility-visible for now, but its underlying mutation primitive is inert and cannot create or update GitHub commits.

## Preserved contract

- SolSpire does not authorize repository mutation.
- Direct GitHub Contents API writes are unavailable from SolSpire.
- K3 remains the sole repository mutation transaction path.
- Read-only GitHub discovery and inspection remain available.
- No frontend behavior is changed in R2.
- No K17 semantics, autonomous mutation, autonomous commit/push, or second K3 path are introduced.

## Proofs added

`tests/test_solspire_r2_github_mutation.py` proves:

1. `solspire.tools_github` contains no GitHub Contents API PUT implementation.
2. The legacy `commit_file()` compatibility symbol fails closed without performing a network write.
3. The exported GitHub tool surface is read-only.

## Validation

R1's first workflow attempt failed because the validation workflow invoked `pytest` without installing it. The workflow was corrected in commit `648fd025e5e70e2c1b389a393b2df36dd3119f83`; its replacement run is queued and must be green before R1 is formally marked green.

R2 is intentionally limited to the direct GitHub mutation closure. The broader SolSpire execution runtime and other mutation-capable surfaces remain untouched for the later R3 boundary decision.
