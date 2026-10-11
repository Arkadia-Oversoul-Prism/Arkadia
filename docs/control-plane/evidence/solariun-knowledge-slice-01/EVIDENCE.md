# Workstream 3 — Solariun & Knowledge OS · Slice 01 evidence

**Branch:** `feat/prism-parallel-03-solariun-knowledge` (PR #421, draft)
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (accepted in `main`, PR #419)
**Instruction:** `docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Discovery — exact current and archived paths

Paths were read from the live tree, not inferred from product names.

### Current (canonical) frontend — `web/arkadia_console/`

| Path | Role |
|---|---|
| `src/pages/SolariunPage.tsx` | Solariun surface (lenses: projects/knowledge/memory/weaver) |
| `src/pages/KnowledgePage.tsx` | Knowledge OS surface |
| `src/lib/surfaces.ts` | canonical surface registry — **workstream 1 owns** |
| `src/lib/router.ts` | path resolution — **workstream 1 owns** |
| `src/lib/endpoints.ts` | shared endpoint registry — **workstream 1 owns file-level integration** |
| `src/lib/apiClient.ts`, `src/lib/apiConfig.ts` | canonical client + base URL |
| `src/lib/useHydration.ts` | loading / auth-required / unavailable / error states |
| `src/components/ui.tsx` | shared primitives (`Page`, `Panel`, `Facts`, `ContractState`, `NotYetWired`) |

### Archived (evidence, not code to restore) — `archive/frontend/arkadia-prism/web/public_prism/`

| Path | Role |
|---|---|
| `src/pages/SolariunConsole.tsx` | legacy Solariun entry -> `SolSpireExperience` |
| `src/pages/knowledge/KnowledgeOSPage.tsx` | legacy Knowledge OS (graph/health/timeline/search/projects tabs) |
| `src/pages/knowledge/KnowledgeGraphView.tsx` | legacy graph view |
| `src/lib/knowledgeApi.ts` | legacy `/api/knowledge/*` client |
| `src/lib/solariunApi.ts` | legacy Solariun read/write boundary |

The legacy Knowledge OS page confirms the capability set is real (graph, timeline,
search, projects, health); the current console renders only vault status, so graph
and timeline are genuine reconciliation gaps.

---

## 2. Capability matrix (verified against the live handler, not the archive)

| Capability | Declared contract | Handler | Auth | Persistence |
|---|---|---|---|---|
| Knowledge vault status | `GET /api/knowledge/status` | `api/knowledge_routes.py::knowledge_os_status` | none (rate-limit **exempt**) | `notes`/`graph_edges`/`timeline` counts |
| **Readable graph** | `GET /api/knowledge/graph` | `::full_graph` -> `knowledge.graph.full_graph_export` | **optional** (`_optional_user_id`) | `notes` + `graph_edges` |
| Graph traversal | `GET /api/knowledge/graph/{note_id}/traverse` | `::traverse_graph` -> `knowledge.graph.traverse` | optional | same |
| Timeline | `GET /api/knowledge/timeline`, `/timeline/recent` | `::get_timeline`, `::recent_timeline` -> `knowledge.timeline` | optional | `timeline` |
| Knowledge projects | `GET/POST /api/knowledge/projects` | `::list_projects`, `::create_project` -> `knowledge.vault` | optional | `projects` |
| Private note mutation | `PATCH/DELETE /api/knowledge/notes/{uuid}` | `::patch_note`, `::remove_note` -> `knowledge.vault` | **required** (explicit `401`) | `notes` |
| Solariun projects | `GET /solspire/projects` | `solspire/console_router.py::list_projects` | **required** (`Depends(require_auth)` on the router) | `solspire_projects.db` |
| Personal ingest | `POST /api/personal/ingest-file`, `/ingest-note` | `api/main.py` | authenticated node | private Knowledge OS vault |

### Auth boundary — measured

`api/knowledge_routes.py` resolves identity with `_optional_user_id()` ->
`api.auth.get_current_user`, which is an **optional** dependency that returns
`None` rather than raising. So an anonymous caller is a *real* caller and receives
the public corpus (`user_id IS NULL`) — it is not a `401`. Only the note
mutation routes and the whole `/solspire` router raise on missing identity.

### Persistence — measured

One SQLite schema, `knowledge/schema.sql`. Ownership is the `notes.user_id`
column: `NULL` = public/legacy corpus, a Firebase uid = private. The ownership
predicate lives in four places, each scoped to its reader:

- `knowledge/vault.py::_note_owner_clause` — `(user_id = ? OR user_id IS NULL)` / `user_id IS NULL`
- `knowledge/graph.py::accessible_note_ids` — same shape, used by the graph endpoints
- `knowledge/search.py::_notes_owner_sql` — same shape, used by search
- `knowledge/timeline.py::_timeline_owner_clause` — **stricter**: authenticated `user_id = ?`, anonymous `1 = 0`

---

## 3. Implemented slice

**Vertical capability:** the readable knowledge graph on the Knowledge OS surface.

| File | Change | Owner |
|---|---|---|
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | **new** — declared contract shape + `empty`/`public`/`scoped` scope vocabulary | feature-local |
| `web/arkadia_console/src/pages/knowledge/KnowledgeGraphPanel.tsx` | **new** — reads `endpoints.knowledgeGraph` via the shared client; reports the viewer's scope | feature-local |
| `web/arkadia_console/src/pages/KnowledgePage.tsx` | mounts the panel; adds a `NotYetWired` scaffold for `/api/knowledge/timeline` | feature-local page |

Not edited: `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `lib/endpoints.ts`,
shared shell/tokens, NovaNet, or any other workstream's files. The slice reuses the
existing declared `endpoints.knowledgeGraph` constant, so no shared-registry change
was needed and no workstream-1 integration request was raised.

The panel deliberately does **not** filter by `user_id` client-side. The ownership
predicate is enforced server-side; a client-side filter would only *look* like a
boundary while the response still carried the data.

---

## 4. Tests

| File | Tests | Purpose |
|---|---|---|
| `tests/test_knowledge_os_boundary.py` | 11 | live handler over ASGI: private/public separation, auth denial, owner positive controls |
| `tests/test_solariun_knowledge_slice_01.py` | 13 | source contract: slice wiring, no shared-seam edit, no hardcoded host, payload shape guard |

### Negative controls (each proven to bite, then reverted)

| Control | Mutation | Result |
|---|---|---|
| Anonymous graph leak | `graph.accessible_note_ids` anonymous branch -> `SELECT id FROM notes` | **2 failed** (`test_anonymous_graph_excludes_private_material`, `test_scope_vocabulary_tracks_the_live_boundary`) |
| Ownership check disabled | `vault._user_owns_note` -> `return True` | **2 failed** (`test_private_note_mutation_denies_non_owner`, `test_public_note_is_not_mutable_through_the_private_path`) |
| Hardcoded host | inject `https://arkadia-qzu4.onrender.com` into the panel | **2 failed** (`test_panel_declares_no_hardcoded_host_or_second_api_base`, `test_detector_is_silent_on_the_shipped_panel`) |
| Weakened shape guard | `isKnowledgeGraphData` checking only `nodes` | detector control rejects it (`test_shape_guard_detector_flags_a_weakened_guard`) |

All three source mutations were reverted byte-identically (`git diff --stat` empty).

The first negative-control attempt targeted `vault._note_owner_clause` and **did not
bite** — the graph endpoint reads through `graph.accessible_note_ids`, not the vault
clause. The control was re-pointed at the real boundary. This is recorded because a
control that cannot bite is not a control.

### Boundary assertions

- anonymous graph contains the public corpus and neither user's private material;
- owner sees own + public; **other node's private material never appears**;
- the two users' graphs do not intersect;
- anonymous `PATCH`/`DELETE` on a note -> `401`;
- non-owner `PATCH`/`DELETE` -> `404` (fail-closed, not a distinguishable "forbidden");
- owner `PATCH` -> `200` (positive control);
- public note is not mutable through the private path;
- anonymous timeline -> `[]`; authenticated timeline -> `200` (answered, not refused).

---

## 5. Verification commands and results

```
python -m pytest tests/test_knowledge_os_boundary.py -q      -> 11 passed
python -m pytest tests/test_solariun_knowledge_slice_01.py -q -> 13 passed
python -m pytest <both> --collect-only -q                    -> 24 tests collected
python -m py_compile api/main.py                              -> OK (untouched)
printf '<paths>\n' | python scripts/cp10_mutation_boundary_policy.py --judge
                                                              -> Mutation boundary PASS
cd web/arkadia_console && corepack pnpm install --frozen-lockfile -> INSTALL_EXIT=0
cd web/arkadia_console && corepack pnpm build                 -> see §6a (pre-existing failure)
```

`api/main.py` and `api/knowledge_routes.py` were **not** modified — the slice is
frontend-local plus tests.

### 5a. Composed tree (rebased onto a concurrent slice)

While this slice was in progress another slice landed on the same branch
(`e47789f1` / `2c3bf45c`, `web/arkadia_console/src/components/knowledge/KnowledgeSearchPanel.tsx`).
This commit was rebased onto `2c3bf45c` with **no conflict** (zero overlapping
files) and the composed tree was re-measured:

| Check | Result |
|---|---|
| `pytest` (my two files) on the composed tree | 24 passed |
| full suite, composed tree | 18 failed, 2161 passed, 17 skipped, 1 error |
| failing/error node set vs branch baseline | **identical** (`204d0a4e...`, 19 nodes) |
| CP10 mutation boundary | PASS |
| `pnpm build` | **fails on the other slice's file** (see §6a) |

`+24 passed` over the baseline is exactly the collection count of the two new
test files, so no other node changed outcome.

### 6a. Pre-existing build failure — NOT this slice

`web/arkadia_console/src/components/knowledge/KnowledgeSearchPanel.tsx(133,27)`:

```
error TS2322: Type 'unknown' is not assignable to type 'ReactNode'.
```

This was **pre-existing on the branch tip** `2c3bf45c`, proven by building a
detached worktree of that commit alone (same error, no slice applied). It was
initially recorded as "not repaired here" on the assumption it belonged to another
slice — see §8: `components/knowledge/KnowledgeSearchPanel.tsx` is a Knowledge OS
feature-local component and therefore **is** Workstream 3's ownership, so it was
repaired on this branch.

---

## 6. Baseline comparison

Measured in this environment with
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`.

| Tree | Result | Failing/error node-set sha256 |
|---|---|---|
| branch baseline `b48ae1c7` | 18 failed, 2137 passed, 17 skipped, 1 error | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` (19 nodes) |
| with slice | 18 failed, 2161 passed, 17 skipped, 1 error | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` (19 nodes) |
| with slice, composed on `2c3bf45c` | 18 failed, 2161 passed, 17 skipped, 1 error | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` (19 nodes) |

**Zero node-set delta** in every comparison (`diff` empty; identical sha256). The
`+24 passed` is exactly the two new test files (11 + 13). The 18 failures and 1
error are pre-existing on the branch and are unchanged by this slice.

Failures are compared by **node identity**, never by count (the suite is known to
be unstable on `main`). The 19 pre-existing nodes include the two
`tests/test_engineering_lab_api.py` pins and the Landing-copy pin recorded in
`AGENTS.md` as unowned drift, plus a `sqlite3.ProgrammingError: Cannot operate on a
closed database` error surfaced from the voice/plan suites — all present on the
branch baseline before this slice.

---

## 7. Unknowns / BLOCKED (recorded, not filled by assumption)

- **`/api/knowledge/graph/{note_id}/traverse`** — declared and present; not wired in
  this slice. Scope unverified beyond the shared `accessible_note_ids` predicate.
- **`/api/knowledge/timeline`** — declared; rendered as an explicit `NotYetWired`
  scaffold. Response shape read from `knowledge.timeline.query` (JSON `payload`
  decoded) but not exercised over HTTP in this slice.
- **`/api/knowledge/search`** — declared (`POST`); mode list from
  `knowledge.search.unified_search`. Not wired; not verified over HTTP.
- **Solariun lens routing** — `SolariunPage` accepts a `section` prop but the page
  owns no lens routing; the lens strip is presentational. Routing into a lens is a
  `lib/router.ts` concern (**workstream 1**), so this slice did not touch it.
- **`/api/personal/*`** — private ingest boundary exists in `api/main.py`; the
  personal vault is server-side and was **not** modified or read by this slice.
- **`endpoints.codex` / `endpoints.field`** — declared in the registry with **no
  consumer** in the console. Not this slice's capability; recorded as discovery.
- No deployment identity or production observation is claimed. Render remains
  canonical (ADR-016); nothing was deployed.

---

## 8. Bounded repair — Workstream 3 build blocker (2026-10-11)

**Defect.** `web/arkadia_console/src/components/knowledge/KnowledgeSearchPanel.tsx(133,27)`:

```
error TS2322: Type 'unknown' is not assignable to type 'ReactNode'.
```

The panel types each record as `Record<string, unknown>`, so `record.note_type` is
`unknown`. `unknown && <jsx>` yields `unknown`, which is not assignable to
`ReactNode` when used as a JSX child. This is the root cause of **both** red PR #421
jobs — `validate` and `Build canonical Render image` (`gh run view 38126349544
--log-failed`, `web/arkadia_console` step, exit code 2). The `docker build` is not
independently broken; it compiles the same console and hits the same `tsc` error.

**Ownership.** `components/knowledge/` is a Knowledge OS feature-local path
(`SHARED-CONTRACTS.md` §1, Workstream 3: "Solariun/Knowledge OS page modules and
feature-local components/tests/evidence"). It is not a shell/router/surfaces/shared
file, so this is in-workstream, not a drive-by edit. The prior §6a note deferred it
to the coordinator; that deferral is superseded (see the corrected §6a).

**Fix (minimal).** Derive `noteType` through the existing `asText` helper and gate
on the string, matching how `title` and `detail` are already computed one line
above:

```tsx
const noteType = asText(record.note_type);
...
{noteType && <p ...>{noteType}</p>}
```

**Verification.**

```
cd web/arkadia_console && corepack pnpm build
  -> tsc clean; vite build OK (64 modules; index-CP2-Ifkb.js 32.95 kB)
python -m pytest tests/test_solariun_knowledge_slice_01.py tests/test_knowledge_os_boundary.py -q
  -> 24 passed
python -m pytest tests/test_frontend_arkadia_console_rebuild_01.py \
  tests/test_canonical_frontend_routing.py \
  tests/test_aeas05_canonical_frontend_acceptance.py \
  tests/test_documented_route_contract.py -q
  -> 38 passed
python -m pytest tests/architecture -q   -> 11 passed
python -m py_compile api/main.py         -> OK (api/main.py untouched)
```

No behavior change beyond restoring compilation; no endpoint, route, token, or
authority surface touched. Human retains merge and acceptance.

