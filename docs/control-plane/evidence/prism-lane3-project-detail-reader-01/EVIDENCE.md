# WS3 · Lane 3 — Knowledge OS single-project detail reader

Workstream: Prism UI reconciliation, Lane 3 (Agent 03 — Solariun & Knowledge OS).
Branch: `feat/prism-lane3-project-detail-reader-01`. PR: draft.
Base measured: `main` @ `49809f45274f2f81b24e01fefdfb3009e8717495` (Merge PR #490).

## Objective (bounded)

Wire the **verified** single-project detail contract into the console. The project
*collection* reader already exists (`KnowledgeProjectsPanel` → `GET /api/knowledge/projects`);
the *detail* read (`GET /api/knowledge/projects/{name_or_uuid}`) is served by the backend
but had no console consumer. This slice adds the reader and pins its refusal boundary.

## Capability matrix (contract evidence)

| Surface | Route | Handler | Verified by |
|---|---|---|---|
| Project collection | `GET /api/knowledge/projects` | `api/knowledge_routes.py::list_projects` → `knowledge.vault.list_projects` | `tests/test_knowledge_projects_boundary.py` |
| Project detail (new) | `GET /api/knowledge/projects/{name_or_uuid}` | `api/knowledge_routes.py::get_project` → `knowledge.vault.get_project` | `tests/test_knowledge_project_detail_boundary.py` |

The detail route is present in `api.main:app`'s served OpenAPI schema (asserted live, not
from memory). The row shape equals the collection row (no list wrapper).

## What changed

- `web/arkadia_console/src/components/knowledge/KnowledgeProjectDetail.tsx` (new) — the
  detail reader. Path composed from the canonical registry entry
  (`endpoints.knowledgeProjects` + `encodeURIComponent(identifier)`) — no page-local registry
  entry, no second API base.
- `web/arkadia_console/src/components/knowledge/KnowledgeProjectsPanel.tsx` — each project row
  is now a selectable button; the detail mounts **only when selected** (no N-request fan-out).
- `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` — added
  `isKnowledgeProject` (single-row structural guard, reuse of `isKnowledgeProjects`) and
  `projectRefusalNotice()` (the fail-closed refusal copy).
- `tests/test_knowledge_project_detail_boundary.py` (new) — 12 tests: backend contract,
  refusal boundary, honest-state source pins, and source detectors with negative controls.

## The load-bearing finding — a `404` is a boundary answer

`api.knowledge_routes.get_project` answers `404` **both** when a project does not exist *and*
when it is not readable by the caller (`knowledge.vault.get_project` applies the ownership
predicate `(user_id = ? OR user_id IS NULL)` authenticated / `user_id IS NULL` anonymous).
The handler does not distinguish them, so neither may the reader.

Measured live: a **non-owner** read and a **nonexistent id** read return the *same* `404`,
and an **anonymous** read of a private project likewise `404`s, while a public project is
`200` anonymously. Rendering that `404` as an ordinary transport fault would present a real
boundary answer as an outage; guessing which case it was would invent a fact the contract
withholds. The reader branches on `kind === "NOT_FOUND"` and renders `projectRefusalNotice()`,
which states the indistinguishability explicitly.

## Tests / proof

Measured (same environment, `python -m pytest`):

- `tests/test_knowledge_project_detail_boundary.py` + `test_knowledge_projects_boundary.py`
  + `test_console_endpoint_registry_contract.py` + `test_prism_console_ci_wiring.py`
  → **77 passed** (65 baseline + 12 new).
- `tests/architecture` → **11 passed**.
- Frontend: `corepack pnpm install --frozen-lockfile` then `corepack pnpm build`
  (`tsc --noEmit && vite build`) → **built clean**, 82 modules, no type errors.
- `scripts/console_contract_domain.py` → the new guard enters the derived gate domain
  (contains the `"arkadia_console"` needle); CP10 `--judge` admits all changed paths.

## Regression boundary

Additive only. No backend route, authorization, or shared Lane-1 file (`endpoints.ts`,
`App.tsx`, router) is edited — the detail path is derived from the existing registry entry,
which `test_console_endpoint_registry_contract.py` explicitly permits. Full-suite node-set
comparison is deferred to CI (`prism-console-contract.yml` derives and runs the whole console
domain, including this guard).

## Remaining uncertainty / not claimed

- No production deployment, merge, or acceptance is claimed. This is a repository-source and
  local-test claim only; production parity requires a deployment identity + runtime observation
  (ADR-016).
- The design touches only Lane-3-owned surfaces; if the shared shell lane later adds a
  route-parameterized Knowledge surface, a Lane-1 interface request is required then — not
  presupposed here.
