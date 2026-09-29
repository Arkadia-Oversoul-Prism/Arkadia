# R0 — SolSpire Ground-Truth Reconciliation

**Base:** `57fb207842e45150c4f81545f6168d8e72a64d5e`
**Status:** AUDIT / BASELINE ONLY
**Authority:** descriptive architecture record; not an authorization mechanism

## 1. Purpose

R0 establishes the implementation ground truth before any SolSpire consolidation work. It deliberately makes **no runtime behavior changes**.

The goal is to distinguish:

- intended surface ownership from actual implementation ownership;
- legitimate project/workspace capabilities from engineering execution capabilities;
- adapters from duplicated domain logic;
- read-only access from mutation paths;
- historical compatibility from canonical architecture.

## 2. Current architectural contract

The SCI registry is explicitly descriptive and states that:

- SCI owns global operator navigation, discovery, capability metadata, domain selection, and topology presentation;
- SolSpire owns project/workspace operating context;
- Knowledge owns knowledge surfaces;
- Weaver owns project-scoped engineering workflow;
- Governance owns PassSpec / PatchApproval visibility and the backend authorization chain;
- K15/K3 remain the governed engineering mutation path.

This contract is useful, but R0 finds that implementation ownership has not fully converged with it.

## 3. Ground-truth findings

### R0-01 — SolSpire contains Weaver governance logic

**Location:** `solspire/project_execution.py`

The module imports and directly uses Weaver's `PassSpec`, `PatchApproval`, `execute_patch`, `patch_content_hash`, `pass_spec_hash`, `current_head`, and `current_origin_main` primitives. It additionally implements its own:

- execution-state evaluation;
- PassSpec construction;
- PatchApproval construction;
- path allowlist / forbidden-path checking;
- HEAD drift checking;
- project patch execution orchestration.

**Classification:** `THIN / MOVE LOGIC`

**Target owner:** Weaver / governance lifecycle.

**Disposition:** Preserve lineage initially. Remove duplicated semantic ownership only after equivalent Weaver behavior is proven by tests.

---

### R0-02 — `solspire/weaver_bridge.py` is an orchestration façade, not only a bridge

**Location:** `solspire/weaver_bridge.py`

The module correctly exposes read-only Weaver analysis, capability discovery, and validation, but it also exposes project-level wrappers for:

- execution readiness;
- PassSpec binding;
- PatchApproval binding;
- governed execution.

These wrappers delegate to `solspire.project_execution`, which means the SolSpire layer currently remains part of the Weaver governance call chain rather than being a context adapter only.

**Classification:** `THIN`

**Target owner:** Weaver owns lifecycle semantics; SolSpire supplies project context and access checks.

**Disposition:** Keep a bridge, but converge it toward context translation + delegation. Do not create a second Weaver implementation.

---

### R0-03 — SolSpire exposes a direct filesystem mutation route

**Location:** `solspire/console_router.py`, `solspire/tools_fs.py`

`POST /solspire/tools/fs/write` calls `tools_fs.write_file()` directly. `tools_fs.py` performs real filesystem writes under `SOLSPIRE_WORKSPACE_ROOT`.

There is also a direct delete primitive in `tools_fs.py`.

**Classification:** `RECONCILE`

**Important distinction:** filesystem access is not automatically an engineering repository mutation. A project workspace may legitimately require file operations. The unresolved issue is whether these operations can mutate a repository/worktree outside the governed Weaver path.

**Target rule:** engineering repository mutation must not bypass the established Weaver → governance → K15 → K3 path.

**Disposition:** Preserve read/list capability. Audit write/delete call sites and establish an explicit workspace-vs-repository boundary before changing behavior.

---

### R0-04 — SolSpire exposes a direct GitHub commit route

**Location:** `solspire/console_router.py`, `solspire/tools_github.py`

`POST /solspire/tools/github/commit` calls `tools_github.commit_file()`. That function uses the GitHub Contents API to create or update a file and returns a commit SHA.

This is a genuine alternate repository mutation path.

**Classification:** `MOVE / DISABLE`

**Target owner:** governed Weaver/K3 repository mutation path.

**Disposition:** This route must not remain an independent engineering commit surface after reconciliation. Preserve read-only GitHub discovery/read operations where legitimate.

---

### R0-05 — SolSpire has a general execution runtime distinct from Weaver execution

**Location:** `solspire/execution_runtime.py`

SolSpire maintains its own in-process `ExecutionRuntime` with plan/execution state, pause/resume/cancel, retries, and tool dispatch. Its step executor can invoke `fs_write`, project creation, filesystem reads/lists, GitHub reads, and LLM calls.

This is not identical in semantics to Weaver's governed patch execution, but it is a second execution/orchestration substrate.

**Classification:** `RECONCILE`

**Decision required:** retain as a general project workflow runtime, or reduce it to a proposal/context layer and route engineering execution through Weaver. It must not silently acquire Weaver/K15/K3 semantics.

**Immediate invariant:** no SolSpire runtime step may be treated as authorization for repository mutation.

---

### R0-06 — Two top-level natural-language workflow routes duplicate orchestration

**Location:** `solspire/console_router.py`

Both:

- `POST /solspire/run`
- `POST /solspire/projects/{project_id}/run`

perform the same broad intent → plan → validate → execution-runtime flow, with the project route additionally logging an event.

**Classification:** `THIN / CONSOLIDATE`

**Disposition:** retain project context as the differentiator; converge shared orchestration instead of maintaining two independently evolving implementations.

---

### R0-07 — Project knowledge is composed inside SolSpire while Knowledge OS remains canonical

**Location:** `solspire/project_knowledge.py`, project knowledge routes in `solspire/console_router.py`

SolSpire exposes project knowledge, graph, embeddings, and keyword search surfaces. The implementation explicitly avoids introducing a second vector database or graph store, and document upload delegates ingestion to `knowledge.pipeline.ingest()`.

**Classification:** `KEEP / THIN`

**Target rule:** SolSpire owns project context and project-scoped presentation; Knowledge owns canonical knowledge representation, retrieval, graph, and embedding semantics.

**Disposition:** retain project-facing composition, but do not let SolSpire evolve into a second Knowledge OS.

---

### R0-08 — SCI route ownership is descriptive, not implementation ownership

**Location:** `web/public_prism/src/lib/sciCommandRegistry.ts`

SCI correctly classifies capabilities by owner and explicitly states that registry metadata does not grant authorization. Weaver capabilities currently route visually into the existing SolSpire ProjectDashboard / WeaverPanel.

**Classification:** `KEEP`

**Finding:** this is not itself a bleed-through. The remaining problem is that backend implementation ownership does not yet fully match the descriptive contract.

**Disposition:** do not add more SCI capabilities until the backend ownership map converges.

## 4. Canonical ownership after reconciliation

| Concern | Canonical owner | SolSpire role |
|---|---|---|
| Global operator discovery/navigation | SCI | none |
| Project/workspace state | SolSpire | canonical |
| Project conversations/files/tasks/memory/events | SolSpire | canonical |
| Knowledge representation/retrieval/graph/embeddings | Knowledge | project-scoped composition only |
| Repository reconnaissance/evidence/analysis/plan/patch/review | Weaver | host/context only |
| PassSpec / PatchApproval semantics | Weaver/Governance | adapter only |
| K15 readiness | Weaver/Governance | display/delegation only |
| K3 repository transaction | K3 | no parallel SolSpire path |
| Verification | Weaver/verification boundary | render result only |
| General project workflow execution | **UNRESOLVED IN R0** | existing runtime retained pending decision |
| Direct GitHub commit | **NOT A SOLSPIRE CANONICAL CAPABILITY** | reconcile/remove as engineering path |

## 5. Explicit non-goals for R0

R0 does **not**:

- introduce K17 semantics;
- create a new authorization authority;
- introduce autonomous mutation;
- introduce autonomous commit/push;
- create a second K3 path;
- rewrite SolSpire wholesale;
- delete historical modules merely because their ownership is being moved;
- change SCI's descriptive registry into a command authority.

## 6. Reconciliation order

The next passes should be deterministic and independently testable:

### R1 — Weaver semantic convergence

Collapse duplicated PassSpec / PatchApproval / execution-readiness semantics out of SolSpire and establish Weaver as the canonical lifecycle implementation.

### R2 — Mutation-path closure

Remove or disable the direct GitHub commit path and prove that engineering repository mutation has exactly one governed route.

Audit filesystem write/delete semantics at the same time, distinguishing workspace operations from repository mutation.

### R3 — Execution-runtime decision

Determine the canonical scope of `ExecutionRuntime`. If retained, explicitly constrain it to general project workflow execution and ensure engineering mutation cannot bypass Weaver governance.

### R4 — Route/orchestration convergence

Consolidate `/run` and project `/run` around one implementation with project context as an explicit parameter rather than duplicated logic.

### R5 — Knowledge boundary hardening

Keep SolSpire's project-facing composition while making Knowledge OS the only semantic owner of knowledge graph/retrieval/embedding behavior.

### R6 — Structural architecture tests

Turn the reconciled ownership rules into executable architecture tests so future feature work cannot recreate the same overlaps.

## 7. R0 exit condition

R0 is complete when this document exists against a verified repository baseline and every identified overlap has an explicit disposition. No runtime behavior is changed by R0.

**Current result:** baseline established. The architecture is not yet fully reconciled. The highest-risk unresolved bleed-throughs are `solspire/project_execution.py`, the direct GitHub commit route, and the mutation-capable SolSpire `ExecutionRuntime`.
