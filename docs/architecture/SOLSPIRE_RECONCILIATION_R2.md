# R2 — SolSpire Ground-Truth Reconciliation

**Base:** `2f2caf00c5ac68c78e7bbdd8c2139e89908d1061` (R1)
**Scope:** close direct SolSpire repository mutation paths
**Status:** IMPLEMENTED / VALIDATION PENDING

## Objective

Close the two concrete mutation bypasses identified by R0 without redesigning SolSpire or creating a new authority:

1. direct GitHub Contents API repository mutation;
2. direct filesystem mutation when the SolSpire workspace is a Git worktree.

## R2 changes

### 1. Direct GitHub commit path disabled

`solspire.tools_github.commit_file()` remains as a compatibility seam, but it no longer performs any HTTP write. It returns a truthful `NOT_AVAILABLE` result and explicitly points engineering mutation to the governed `Weaver → K15 → K3` path.

The read/discovery operations remain available:

- `list_repos`
- `get_tree`
- `read_file`
- `get_repo_info`

This preserves lineage and avoids a breaking import failure while removing the mutation capability itself.

### 2. Filesystem repository boundary closed

`solspire.tools_fs` still permits ordinary workspace file operations, but `write_file()` and `delete_file()` now refuse mutation when the target lies inside a Git worktree detected under the SolSpire workspace root.

This is deliberately a boundary check, not an authorization system. It prevents a generic SolSpire filesystem tool from becoming a second engineering repository mutation path.

Read/list operations remain available.

### 3. Tests

Added `tests/test_solspire_r2_mutation_boundaries.py` proving:

- direct GitHub commit is fail-closed and performs no HTTP write;
- ordinary non-repository workspace writes remain possible;
- Git-worktree writes are blocked;
- Git-worktree deletes are blocked;
- GitHub read/discovery tools remain exported.

## Canonical mutation invariant

```text
Engineering repository mutation
        │
        ▼
     Weaver
        │
   Governance
        │
       K15
        │
       K3
```

SolSpire's direct GitHub and Git-worktree filesystem tools are no longer alternate mutation paths.

## Explicit non-goals

R2 does not:

- redesign `ExecutionRuntime`;
- remove the SolSpire `/tools/github/commit` compatibility route;
- introduce K17 semantics;
- introduce a new authorization authority;
- introduce autonomous mutation;
- introduce autonomous commit/push;
- modify the frontend;
- change K15/K3 semantics.

The `/tools/github/commit` route remains present for compatibility, but its underlying operation is deliberately disabled. A later cleanup may remove the dead route once callers and frontend dependencies are proven absent.

## Validation status

The deterministic R2 tests have been added. Runtime test execution is not claimed because the available repository workflow is configured for `main`, not this reconciliation branch. Merge remains gated on CI/test execution.

## Exit condition

R2 is complete when the direct GitHub mutation operation and Git-worktree filesystem mutation operation are both fail-closed, read/discovery surfaces remain intact, and architecture tests preserve those boundaries.
