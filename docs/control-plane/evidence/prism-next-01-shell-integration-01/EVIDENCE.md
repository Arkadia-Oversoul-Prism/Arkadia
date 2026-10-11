# Evidence — Workstream 1, next-wave shell/integration slice 1

**Bounded objective:** on `feat/prism-next-01-shell-integration` (draft PR #425),
(a) refresh the active branch map in `SHARED-CONTRACTS.md` §1 to the four
next-wave branches, (b) resolve Workstream 4's `labSession(id)` shared-registry
request after re-verifying the served handler and URL encoding, (c) resolve the
cross-workstream contract seam that request exposes, and (d) answer Workstream
2's Opportunity Radar integration request with a measurement.

**Baseline `main` observed this pass:** `962434bed1bccb11fbf5edfcb0299317b12a8915`
(PR #424 merge). **Branch head observed at pass start:** `e82f7465`.
**Authority:** inspect, implement on the owned branch, test, commit, update the
PR. No merge, deployment, or acceptance. Canonical production is Render
`https://arkadia-qzu4.onrender.com` (ADR-016); no Vercel deployment was created,
promoted, or used as evidence.

---

## 1. Revision binding and live PR state

| Fact | Value | How measured |
|---|---|---|
| `main` | `962434bed1bccb11fbf5edfcb0299317b12a8915` | `git rev-parse origin/main` |
| This branch head at pass start | `e82f7465f846197c39b1e16f773123ad60146124` | `git rev-parse HEAD` |
| PR #425 (this branch) | open, **draft**, base `main` | `GET /repos/.../pulls/425` |
| Sibling #426 | open, draft, head `d3ef3729` | `GET /repos/.../pulls/426` |
| Sibling #427 | open, draft, head `7b5b71c5` | `GET /repos/.../pulls/427` |
| Sibling #428 | open, draft, head `91cac4bf` | `GET /repos/.../pulls/428` |
| First wave | merged: #423 `972c3423`, #420 `55b27d10`, #421 `22941cc5`, #422 `e924aec1` | `GET /pulls?...&state=all` |

All four next-wave branches descend from `962434be` and, at this pass, each
carried only its own bootstrap commit (the durable-task doc for its workstream),
so they were **textually disjoint** — no branch chose a conflicting seam.

### 1.1 Verified served contracts (OpenAPI, from `api.main:app` in this environment)

```
/api/lab/engineering/sessions                      ['get', 'post']
/api/lab/engineering/sessions/{session_id}         ['get']
/api/lab/engineering/sessions/{session_id}/authorize|execute|run-agent|transition  ['post']
/solspire/buyer-recon                              ['get']
/solspire/buyer-recon/projects/{project_id}        ['get']
/api/commune/threads                               ['get', 'post']
/api/knowledge/search                              ['post']
```

`GET /api/lab/engineering/sessions/{session_id}` is the real handler
(`api/lab_routes.py:168`, `require_auth`, owner-scoped); `POST` on the same
collection is the mutating open-session route. The view path is a
sub-resource of the collection, not a collection entry.

---

## 2. Deliverable 1 — branch map refreshed

`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §1 now lists the four
**next-wave** branches and their PR numbers/heads, with the first wave recorded
as closed history. The header's baseline moved to `962434be`. Paths, ownership
boundaries, and §7.1 scope assignments were **not** changed — only the stale
branch/PR/revision map that still named the merged first-wave branches.

---

## 3. Deliverable 2 — `labSession(id)` builder, verified

**Request** (Workstream 4, `docs/control-plane/evidence/prism-w4-lab-read-model-01/EVIDENCE.md` §5):
add `labSession: (id) => /api/lab/engineering/sessions/${id}` to
`src/lib/endpoints.ts` so the Lab view path stops being composed feature-locally.

**Re-verification, not acceptance of the request text.** The requested value was
`/api/lab/engineering/sessions/${id}` — a template with **no encoding**. That
does not satisfy the repository's own convention (every other sub-resource path
in the console encodes its parameter, e.g.
`opportunityRadarContract.ts` uses `encodeURIComponent`). Implemented instead as
a **typed builder derived from the declared collection**:

```ts
export function labSession(sessionId: string): string {
  return `${endpoints.labSessions}/${encodeURIComponent(sessionId)}`;
}
```

Two properties this buys, both asserted:
- the base cannot drift from the registry (`endpoints.labSessions` is the single
  source), rather than a second copy of the collection literal;
- an id containing `/`, `?` or `#` cannot address a different route.

Guard: `test_registry_path_builders_derive_from_a_collection_and_encode` and
`test_lab_session_builder_matches_the_served_route` bind the builder to the
served route (`collection in served`, `collection/{session_id} in served`).

---

## 4. Deliverable 3 — the cross-workstream contract seam (the load-bearing finding)

**The endpoint-registry guard was already RED on `main`, and the new builder did
not cause it.** Measured node attribution, same command, three revisions:

| Revision | `test_every_page_read_uses_the_registry_not_an_inline_path` |
|---|---|
| `972c3423` (PR #423, introduced the guard) | **passed** (8 passed) |
| `55b27d10` (PR #420) | passed (8 passed) |
| `22941cc5` (PR #421) | passed (8 passed) |
| **`e924aec1` (PR #422, Lab read model)** | **FAILED** (1 failed, 7 passed) |
| `962434be` (`main`) | FAILED |

So W4's `LabSessionList.tsx` — which derives its view path from
`endpoints.labSessions` in a local helper, exactly the pattern W1 is now
formalising — was reported by W1's own guard as
`useHydration path argument 'path'`: a **page-local path**. It is not. The
detector only recognised a literal `endpoints.` prefix at the call site and
could not follow a local binding or a helper, so it flagged the canonical
registry-derived form as the defect it exists to catch.

This is a cross-workstream contract seam: W1 owns the guard, W4 owns the file the
guard misreads. It is resolved **in W1's file** (the guard), so no feature-local
file was touched.

### 4.1 The repair

`_inline_path_arguments` now resolves each `useHydration` path argument through
the file's own definitions (`_local_definitions` + transitive
`_registry_derived_names`, over `const`/`let`/`var`/`function`, and identifiers
imported from an `endpoints` module) before deciding it is an inline path. Only a
path that resolves to a raw literal is still a defect. Extraction is
brace-balanced, because a template literal's `${…}` contains a `}` that a
`[^}]*` scan truncates at — the first cut of this patch did exactly that and
silently produced an empty body.

### 4.2 Negative controls (all run against the real tree, restored byte-identically)

| Control | Where | Result |
|---|---|---|
| Raw literal passed to `useHydration` | `LabSessionList.tsx` in place | **guard reddens** (`test_every_page_read_…`); restored identical |
| Remove `encodeURIComponent` from `labSession` | `endpoints.ts` in place | **guard reddens** (`test_registry_path_builders_…`); restored identical |
| Replace the builder base with a raw literal `/api/lab/invented/…` | `endpoints.ts` in place | **guard reddens** (2 nodes); restored identical |
| Registry-derived helper (should **not** flag) | in-file control | passes |
| Imported builder `labSession(id)` (should **not** flag) | in-file control | passes |
| Raw literal inside a helper (should flag) | in-file control | reported |

The acceptance is specifically registry-derived: the same shape with a raw
literal is still reported.

---

## 5. Deliverable 4 — Workstream 2 Opportunity Radar request (measured, not executed)

W2's request (`CAPABILITY-MATRIX-02.md` §4, `prism-parallel-02-…EVIDENCE.md` §5)
asks W1 to pass `projectBoardPath(project.id)` as `readPath` to the landed
`ProjectOpportunityRadar`. W2 **itself conditions** that on repairing defects 1
and 2 in `solspire/buyer_recon.py`:

- **Defect 1** — `create_entry` supplies 34 values to a 33-column table.
- **Defect 2** — `buyer_recon_boards.subject_ref` is `UNIQUE`, so a subject who
  has opened the workspace board cannot open a project board; the project read
  path 500s.

`/solspire/buyer-recon/projects/{project_id}` is confirmed **served**
(`GET`, in the OpenAPI check above), so the route exists — the blocker is the
handler's board uniqueness, not the path.

**Disposition:** the endpoint contract needs **no shared-registry change**. The
radar's path is project-parameterised (`/solspire/buyer-recon/projects/{id}`),
like the Lab session view; W2's own contract module already supplies the base.
When W2 repairs the two defects and asks for the mount, W1's contribution is a
parameterised builder alongside `labSession` (its natural shape:
`projectOpportunityBoard(projectId)`). **Do not mount before the repair lands** —
the read path 500s for any subject with an open workspace board, and a surface
that 500s on open is worse than a visibly not-wired one. Recorded as a
dependency, not implemented here.

---

## 6. Verification (measured in this environment)

| Check | Command | Result |
|---|---|---|
| Endpoint-registry guard | `pytest tests/test_console_endpoint_registry_contract.py -q -rEf` | **11 passed** (was 1F/7P on `main`) |
| Registry + shell + route + W4/W2 guards | registry + `test_console_shell_nav_contract` + `test_prism_w4_lab_read_model` + `test_prism_opportunity_radar_module` + `test_canonical_frontend_routing` + `test_aeas05_canonical_frontend_acceptance` + `test_documented_route_contract` + `test_frontend_arkadia_console_rebuild_01` | **101 passed** |
| Architecture + route composition | `pytest tests/architecture tests/test_solspire_route_composition.py tests/test_solspire_route_composition_ci_wiring.py tests/test_router_schema_vocabulary_closure.py tests/test_router_clean_stop_contract.py tests/test_production_health_route.py -q -rEf` | **69 passed** (architecture 11/11) |
| Typecheck + build | `corepack pnpm build` (`tsc --noEmit && vite build`) | **exit 0** — 67 modules, `dist/assets/index-wPwgnV9d.js` 41.73 kB |
| CP10 mutation boundary | `scripts/cp10_mutation_boundary_policy.py --judge` on the new/changed paths | **PASS (exit 0)** |

### 6.1 Baseline comparison — node identity, not counts

Both trees measured in **this environment**, same command, same dependency set:
`python -m pytest tests/ -q -rEf --continue-on-collection-errors` (with
`PYTHONPATH=<repo>/archive/legacy_python`). `-rEf`, not `-rf`, so a collection
`ERROR` line is not dropped.

| Run | `main` @ `962434be` | branch |
|---|---|---|
| 1 | 21 nodes (20F/1E) | 28 nodes (27F/1E) |
| 2 | **20 nodes (19F/1E)** | **19 nodes (18F/1E)** |

The suites are **non-deterministic** (the known `test_voice_*` /
`knowledge.db` cross-test contamination; `main` itself moved 21 → 20 between two
runs). The counts are therefore not the claim. The claim is the node **set**:

```
comm -3 <main run2 nodes> <branch run2 nodes>
→ FAILED tests/test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path
```

That single line is **the repaired node**: it fails on `main` and passes on the
branch. `comm` is otherwise **empty** — zero new failures, zero unexplained
errors. The `+4 passed` (2220 → 2224) is the four net new passing nodes in the
guard file (11 − 7). The `test_voice_*` / `test_static_ingestion_sources` nodes
that appear in run 1 and not run 2 are order-dependent contamination and were
verified passing in isolation on **both** trees (`43 passed`, 1 pre-existing
`test_static_ingestion_sources` failure present on `main` independently).

---

## 7. Files changed (this pass)

| Path | Change | Owner |
|---|---|---|
| `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` | §1 branch map refreshed; baseline SHA updated | Workstream 1 |
| `web/arkadia_console/src/lib/endpoints.ts` | `labSession(id)` derived, encoding path builder | Workstream 1 |
| `tests/test_console_endpoint_registry_contract.py` | detector follows registry-derived bindings; 3 positive tests + controls | Workstream 1 |
| `docs/control-plane/evidence/prism-next-01-shell-integration-01/EVIDENCE.md` | this file | Workstream 1 |

No feature-local file, shared token, route registry, `App.tsx`, `router.ts`,
`surfaces.ts`, `types.ts`, or backend/authority file was touched.

## 8. Boundaries preserved / non-claims

- No merge, no production deployment, no acceptance. Render is canonical
  (ADR-016); no Vercel artifact was created or treated as evidence.
- The Opportunity Radar was **not** mounted: its backend repair is W2's, and
  mounting before it lands would surface a 500 as a product state.
- The `recorded advertised drift` finding was left as-is; it is display copy in
  pages owned by W2–W4.

**Next bounded move:** next archived shell/navigation gap in W1's ownership
(shared shell primitives under `src/components/`, non-overlapping with the
feature pages), continuing to hold the route/registry seam for the other three
workstreams.

---

## 9. Pass N+1 — `knowledgeSearch` registry entry (WS3 integration request)

**Objective (bounded).** W3 requested the verified `POST /api/knowledge/search`
contract be added to the shared endpoint registry so its feature-local
`KnowledgeSearchPanel` binds a canonical path instead of an inline literal.
`endpoints.ts` is Workstream 1's file-level integration surface
(`SHARED-CONTRACTS.md` `endpoints.ts` row); W3 provides the verified name/path
and evidence. Adding it is exactly the recorded W1 integration duty.

**Handler verification (this tree).** `app.openapi()["paths"]` on the
composition root (`api.main:app`) lists `/api/knowledge/search`;
`knowledgeSearch: "/api/knowledge/search"` declared in the registry resolves to
`served == True`.

| Field | Value |
|---|---|
| Registry key | `knowledgeSearch` |
| Path | `/api/knowledge/search` |
| Method | `POST` (registry stores the path only; method is the caller's contract) |
| Served by canonical app | **yes** — present in `app.openapi()["paths"]`, `served == True` |
| Owner | Workstream 1 (`endpoints.ts`); request originated W3 |

**Change.** One insertion in `web/arkadia_console/src/lib/endpoints.ts`
(no deletions, no other key or type altered). `KnowledgePage.tsx` was **not**
touched — it is W3's feature page; W3 mounts its panel.

**Guard / negative control.** `tests/test_console_endpoint_registry_contract.py`
passes 11 on the branch. Negative control: mutating the value to an invented
path (`/api/knowledge/ghost-search`) reddens
`test_every_declared_endpoint_is_served_by_the_canonical_app`; restoring the
verified path returns the file to `git diff --stat` = 1 insertion, guard green.
The detector bites on the defect and is silent on the correct entry.

**Proof run this pass.**

| Check | Result |
|---|---|
| `pytest tests/test_console_endpoint_registry_contract.py` | 11 passed |
| `pytest` registry + shell-nav + W4-lab + canonical-frontend-routing | 50 passed |
| `pytest tests/architecture -q` | 11 passed (contract budget 10/10; 11/11 measured) |
| `tsc --noEmit` (console) | exit 0 |
| `pnpm build` (console) | exit 0 — `dist/assets/index-DJoUhqIx.js` 41.77 kB |
| Full suite `-rEf --continue-on-collection-errors` | 18 failed / 2221 passed / 20 skipped / 1 error |

**Regression boundary (node set, same environment).** Failing/error node set on
branch == on `main` `962434b`, byte-identical: 19 nodes,
`sha256 a24c695f24998816ee4537096cad075718f21ef47840c6380431fb639cb3ab36`
(`git stash` -> measure main -> `git stash pop`). Zero new failures, zero
unexplained errors. The change relative to §6 is the closure of the prior
`test_every_page_read_uses_the_registry_not_an_inline_path` repair; the
residual 18F/1E are pre-existing `main` debt (`test_autonomy.py` collection
error = CE-01 module-vs-package collision, sovereign-reserved).

**Boundaries / non-claims.** No merge, no deployment, no acceptance (ADR-016:
Render `https://arkadia-qzu4.onrender.com` is canonical; no Vercel artifact was
created or treated as evidence). No backend, authority, `App.tsx`, `router.ts`,
`surfaces.ts`, `types.ts`, or shared token touched. Method semantics are not
asserted here — W3's panel owns the call.

**Next bounded move (W1).** Hold the route/registry seam for W2-W4; next
archived shell/navigation gap inside W1's ownership (shared shell primitives
under `src/components/`), non-overlapping with feature pages.

