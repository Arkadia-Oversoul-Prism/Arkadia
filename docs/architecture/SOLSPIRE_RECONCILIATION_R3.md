# R3 — SolSpire ExecutionRuntime Boundary

**Branch:** `recon/solspire-r0`
**R3 scope:** ExecutionRuntime decision and constraint
**Status:** IMPLEMENTED
**Authority:** descriptive architecture record; not an authorization mechanism

## Decision

Retain `solspire/execution_runtime.py` as a **general project-workflow lifecycle substrate**.

It owns:

- in-process execution lifecycle;
- plan execution state;
- pause / resume / cancel;
- bounded retries;
- tool dispatch for non-governed project workflow;
- caller ownership propagation for project creation.

It does **not** own:

- PassSpec semantics;
- PatchApproval semantics;
- K15 readiness;
- K3 transaction semantics;
- repository authorization;
- governed patch execution;
- GitHub repository commits;
- autonomous engineering mutation.

## R3-01 — Mutation boundary

ExecutionRuntime now fails closed for mutation-class tools including:

- `fs_write`
- `fs_delete`
- `github_commit`
- `git_commit`
- `repository_mutation`
- `execute_patch`

A blocked step returns `MUTATION_DISABLED` and explicitly directs engineering mutation to the canonical Weaver K15 → K3 path.

This is a runtime constraint, not a new authorization authority.

## R3-02 — Planner convergence

The SolSpire planner no longer advertises `fs_write` as an available runtime tool. Coding templates therefore produce a code proposal rather than writing into a workspace.

LLM planning is explicitly instructed not to emit repository mutation tools.

## R3-03 — Ownership propagation

When the general runtime creates a project, it passes the authenticated execution owner's UID through to the project manager. The runtime therefore does not create an unowned project as a side effect of an authenticated workflow.

## Preserved capabilities

Read-only workflow operations remain available:

- `fs_read`
- `fs_list`
- `github_repos`
- `github_tree`
- `github_read`
- `llm`

`project_create` remains a legitimate SolSpire project-state operation and now preserves caller ownership.

## Explicit non-goals

R3 does not:

- introduce K17 semantics;
- create a new authorization authority;
- introduce autonomous mutation;
- create a second K3 path;
- remove the general execution lifecycle;
- redesign the frontend;
- collapse the duplicated `/run` routes;
- redefine Knowledge ownership.

## R3 invariant

> **ExecutionRuntime may orchestrate general project workflow, but execution through it is never authorization for engineering repository mutation.**

Engineering repository mutation remains exclusively governed by the Weaver → Governance → K15 → K3 path.

## Verification target

`tests/test_solspire_r3_execution_runtime.py` proves:

1. mutation-class runtime steps fail closed;
2. read-only workflow steps remain executable;
3. authenticated owner context propagates through project creation.
