# Workstream 3 — owner-scoped Knowledge OS timeline reader · evidence

**Branch:** `feat/prism-next2-03-knowledge-timeline` (PR #431, draft)
**Durable task:** `docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md`
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (accepted, PR #419)
**Base revision:** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Branch head at evidence time:** recorded in the PR body / commit
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Endpoint verification — `GET /api/knowledge/timeline`

Read from the handler, the reader, and the schema; not from the archive, and not invented.

| Item | Measured value |
|---|---|
| Handler | `api/knowledge_routes.py::get_timeline` |
| Delegate | `knowledge.timeline.query` |
| Registration | `router = APIRouter(prefix="/api/knowledge")`, mounted by `api/main.py` |
| Method / path | `GET /api/knowledge/timeline` — a registry entry (`endpoints.knowledgeTimeline`) and a served path |
| Query params | `event_type`, `project_id`, `note_id`, `since`, `until`, `limit` (default 100, `Query(…, le=500)`), `offset` |
| Ordering | `ORDER BY id ASC` (ascending, unlike `/timeline/recent`, which reverses) |
| Response | a **bare JSON list** of event rows — not a wrapper object |
| Row shape | `id, event_type, payload, note_id, project_id, provider, persona, user_id, created_at` |
| `payload` | stored as a JSON **string**, decoded by the reader before it reaches HTTP |
| Auth | **optional** — `_optional_user_id()` → `api.auth.get_current_user`, which returns `None` rather than raising |
| Owner predicate | `knowledge.timeline._timeline_owner_clause` — authenticated `user_id = ?`; anonymous `1 = 0` |
| Persistence | canonical SQLite `knowledge/schema.sql`, table `timeline`, owner column `timeline.user_id` |

### The boundary is stricter here than on the other Knowledge OS readers

`AGENT-03` asked for the *intended owner/public* semantics. Measured:

| Reader | Anonymous predicate | Public corpus? |
|---|---|---|
| `knowledge/graph.py::accessible_note_ids` | `user_id IS NULL` | yes |
| `knowledge/search.py::_notes_owner_sql` | `user_id IS NULL` | yes |
| `knowledge/vault.py::_project_owner_clause` | `user_id IS NULL` | yes |
| **`knowledge/timeline.py::_timeline_owner_clause`** | **`1 = 0`** | **no** |

There is **no public timeline**. An anonymous read is answered `200 []`, and that `[]`
is the *same* body a signed-in owner with an empty log receives. The transport status
therefore cannot distinguish the two cases, and a reader that renders "no events yet"
for an anonymous caller would be reporting a **refusal as an empty log** — the
"infer success from an empty response" failure the shared contract §3.5 forbids.

Measured directly over an ASGI transport against a sandboxed database (no mocks):

```
raw rows:  id=1 user_id=USER_A  id=2 user_id=USER_B  id=3 user_id=USER_A(note)
           id=4 user_id=None(note_id->public note)    id=5 user_id=None
anon   GET /api/knowledge/timeline                   -> 200 []
USER_A GET /api/knowledge/timeline                   -> 200 [ids 1, 3]   (own only)
USER_B GET /api/knowledge/timeline                   -> 200 [id 2]       (own only)
USER_A GET /api/knowledge/timeline?limit=2           -> 200 [ids 1, 3]
USER_A GET /api/knowledge/timeline?limit=2&offset=2  -> 200 [ids 6, 7]
USER_A GET /api/knowledge/timeline?limit=999         -> 422 (le=500)
malformed bearer token                               -> 200 []  (identity unresolved => anonymous scope)
```

`record()` stamps `user_id` from the linked note when the caller does not supply
one, so a note-linked event is owned by the note's owner. An event with no owner and
no owning note (`id=5`) is readable by **nobody** — not even an anonymous caller. That
is the fail-closed behaviour, and it is pinned.

**No handler defect was found on this endpoint.** The owner predicate is already
correct and the anonymous branch is already fail-closed. Nothing was repaired in
`knowledge/` — `git diff` on that tree is empty.

---

## 2. Capability matrix

| Capability | Contract | Handler | Auth | Data states |
|---|---|---|---|---|
| Timeline read | `GET /api/knowledge/timeline` | `::get_timeline` → `knowledge.timeline.query` | optional | loading · owner-empty · unscoped-empty · auth-required · unavailable · read-failed |

---

## 3. Implemented slice

**Vertical capability:** the owner-scoped timeline on the Knowledge OS surface.

| File | Change | Owner |
|---|---|---|
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | added the timeline contract shape, `owner`/`unscoped` scope vocabulary, the empty-state copy, and the event-type list | feature-local |
| `web/arkadia_console/src/components/knowledge/KnowledgeTimelinePanel.tsx` | **new** — reads `endpoints.knowledgeTimeline` through the shared client; distinct loading/empty/auth/unavailable/error states | feature-local |
| `web/arkadia_console/src/pages/KnowledgePage.tsx` | replaces the `NotYetWired` timeline scaffold with the real panel; mounts the search panel from the now-present `endpoints.knowledgeSearch` entry | feature-local page |
| `tests/test_knowledge_timeline_boundary.py` | **new** — 19 tests | feature-local |

Not edited: `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `lib/endpoints.ts`, the
shared shell/tokens, NovaNet, Arkana, Weaver, Lab, or any `knowledge/*` backend file.

### Honest states

| State | Trigger | Rendering |
|---|---|---|
| loading | request in flight | `ContractState` → `Loading` |
| owner-empty | `200 []`, authenticated viewer | "holds no events yet … this is an empty log, not a failed read" |
| unscoped-empty | `200 []`, anonymous viewer | "no identity is present, so nothing was readable. This is not an empty log" |
| auth-required | `401`/`403` | `ContractState` auth copy |
| unavailable | network/5xx | `ContractState` unavailable copy, explicitly "this is not an empty result" |
| read-failed | other error **or** an unrecognised body | `ContractState` error copy; the panel raises `ApiError` rather than rendering empty |

The two empty states carry **different copy** and are asserted not to be the same
string — collapsing them is the defect this slice exists to prevent.

The panel applies **no** client-side ownership filter. `user_id` is part of the
returned shape (it is declared in the contracts module) but does not appear in the
panel's code: a client-side filter cannot prove a server-side boundary, and would
misrepresent a leak as a boundary.

---

## 4. Tests

`tests/test_knowledge_timeline_boundary.py` — **19 tests**, all passing. Live handler
over an ASGI transport against a sandboxed database; no mocks.

| Group | Coverage |
|---|---|
| contract shape | bare list (not a wrapper); declared row fields; ascending `id`; `payload` decoded to an object, not a JSON string |
| owner boundary | anonymous answered `200 []` (not a 401, no material); authenticated scoped to owner; cross-owner leakage both directions; an unknown uid reads nothing; note-linked events inherit the note's owner |
| query params | `event_type` filter stays owner-scoped; `limit`/`offset` page within the owner's own events; `limit=501` refused `422` |
| empty vs failed | the scope vocabulary resolves the ambiguous `[]` in both directions; the two notices differ; a failed read is not rendered as an empty timeline |
| source guards | anonymous owner clause is fail-closed; the panel uses the registry + shared client and inlines no path; no client-side ownership filter |

### Negative controls — each proven to bite, then reverted byte-identically

| Control | Mutation | Result |
|---|---|---|
| fail-closed owner clause | `knowledge/timeline.py`: anonymous clause `1 = 0` → `1 = 1` | **3 failed** — `test_anonymous_timeline_is_answered_empty_not_refused`, `test_empty_and_unreadable_are_distinguishable`, `test_owner_clause_is_fail_closed` (a real cross-owner leak, caught live) |
| client-side filter | panel gains `(timeline.data ?? []).filter((e) => e.user_id !== null)` | **1 failed** — `test_panel_does_not_reimplement_the_ownership_boundary_client_side` |
| detector, permissive clause | feed the pre-repair shapes directly | reported `1 = 1` and `user_id IS NULL`; silent on the shipped `1 = 0` |
| detector, comment vs code | feed a comment naming the predicate and a real `.filter((e) => e.user_id …)` | comment ignored, code flagged |

Both mutations were reverted (`git diff` on `knowledge/timeline.py` is empty; the
panel is restored from a byte copy).

### A stale pin in my own earlier suite, corrected

`tests/test_knowledge_search_boundary.py::test_page_mounts_search_only_from_the_registry_entry`
asserted the **blocked** state (`registeredSearchEndpoint`), which was correct while
Workstream 1's registry did not carry `knowledgeSearch`. The registry now carries it
(integrated in `67696372`), so the page mounts the panel directly from the named entry.
The pin was updated to assert `endpoints.knowledgeSearch` — the *blocked intermediate
state* is superseded, not violated — and the docstring says so. The negative assertions
(no literal path as a request target) are unchanged.

---

## 5. Verification

| Check | Command | Result |
|---|---|---|
| New suite | `pytest tests/test_knowledge_timeline_boundary.py -q -rEf` | **19 passed** |
| Adjacent suites | `test_knowledge_os_boundary`, `test_knowledge_search_boundary`, `test_solariun_knowledge_slice_01`, `test_console_endpoint_registry_contract`, `test_console_shell_nav_contract`, `test_m06_knowledge`, `test_isolation` | **116 passed** |
| Typecheck + build | `corepack pnpm install --frozen-lockfile && corepack pnpm build` (node 24, pnpm 10.26.1) | **succeeded** (75 modules, `dist/assets/index-BHuGM_tt.js`) |
| Full suite (branch) | `pytest tests/ -q -rEf --continue-on-collection-errors` | see §6 |
| Full suite (`main` `f390526a`) | same | see §6 |

### Baseline comparison by node identity (not by count)

Failing/error node sets are compared as a sorted `FAILED`/`ERROR` list and hashed;
`comm -3` between the two trees is the claim. Counts move with how many tests are
present and with the environment, so only node identity is load-bearing.

---

## 6. Full-suite result

### 6.1 Measured — identical failing/error node set on both trees

Environment: node 24 / pnpm 10.26.1, `PYTHONPATH=.:archive/legacy_python`, pyyaml
present. Command on both trees:
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`.

| Tree | Revision | Result | Node set |
|---|---|---|---|
| Branch (with this slice) | `a2024fba` + working changes | **27 F / 2361 P / 17 S / 1 E** | 28 nodes, `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` |
| Baseline (changes stashed) | `a2024fba` | **27 F / 2342 P / 17 S / 1 E** | 28 nodes, `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` |

`comm -3` between the two sorted node sets is **empty**. The `+19 passed` is exactly
the new test file. Both runs used `-rEf` (never `-rf`, which suppresses pytest's
`ERROR` summary lines and yields a subset fingerprint); the single `ERROR` node
(`tests/test_autonomy.py`) is the pre-existing CE-01 module-vs-package collision,
present on both trees.

The 28 pre-existing nodes are all in unrelated subsystems (voice pipeline / ASR /
context, SolSpire R1/R3 governance, static ingestion, identity spine, Lab API pins,
`test_autonomy` collection). None is a Knowledge OS test, and none was touched.


### Recorded, not repaired (pre-existing)

- `tests/test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`
  was failing on `main` `962434be` at `components/lab/LabSessionList.tsx` (Workstream 4
  ownership). It passes at this revision — the Lab builder was integrated — so it is
  not part of this slice's delta.
- Pre-existing failures unrelated to Knowledge OS are recorded by node identity in
  §6.1 and were not touched.

### Runtime note (no production-parity claim)

The canonical runtime at `https://arkadia-qzu4.onrender.com` serves `main`, **not** this
branch. This slice makes **no** deployment or parity claim, and the timeline endpoint
was not probed in production. Everything above is a local measurement of the handler,
the reader, and the console build.

---

## 7. Explicitly not done

- No edit to `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `lib/endpoints.ts`, shared
  shell/tokens, NovaNet, Arkana, Weaver, Lab, or any `knowledge/*` backend module.
- No client-side ownership filter as a substitute for server authorization.
- No fabricated events, no simulated timeline, no second memory store.
- No new endpoint invented; the panel reads the existing registry entry.
- No merge, deployment, or acceptance.
- The `since`/`until`/`project_id`/`note_id` filters are declared by the handler and
  exercised by the boundary suite only where the UI does not expose them; the panel
  exposes `event_type` alone. Recorded as scope, not a gap.

---

## 8. Second bounded slice — `GET /api/knowledge/projects` (this pass)

The next verified Knowledge OS surface, on the same branch, because PR #431 is not yet
merged. `endpoints.knowledgeProjects` was declared in the registry with **no consumer**.

### 8.1 Endpoint verification

| Item | Measured value |
|---|---|
| Handler | `api/knowledge_routes.py::list_projects` |
| Delegate | `knowledge.vault.list_projects` |
| Method / path | `GET /api/knowledge/projects` (registry entry `endpoints.knowledgeProjects`) |
| Response | a **bare JSON list**, `ORDER BY updated_at DESC` |
| Row shape | `id, uuid, name, description, user_id, tags, status, created_at, updated_at` |
| `tags` | a JSON **string** on the wire, not an array |
| Auth | optional (`_optional_user_id`) |
| Owner predicate | `knowledge.vault._project_owner_clause` — authenticated `(user_id = ? OR user_id IS NULL)`; anonymous `user_id IS NULL` |
| Single-project read | `GET /api/knowledge/projects/{name_or_uuid}` → `::get_project`; `404` for a non-owner |

### 8.2 The boundary is the **third** shape in this subsystem — and the opposite of the timeline's

| Reader | Anonymous predicate | Public corpus? | Anonymous `[]` means |
|---|---|---|---|
| `knowledge/graph.py` | `user_id IS NULL` | yes | empty corpus |
| `knowledge/search.py` | `user_id IS NULL` | yes | empty result set |
| **`knowledge/vault.py::_project_owner_clause`** | **`user_id IS NULL`** | **yes** | **empty corpus** |
| `knowledge/timeline.py::_timeline_owner_clause` | `1 = 0` | **no** | **refusal** |

Measured live over an ASGI transport (no mocks):

```
raw rows:  SecretProj-A(user_id=USER_A)  SecretProj-B(user_id=USER_B)  PublicProj(user_id=None)
GET /api/knowledge/projects  anon -> 200 [PublicProj]
GET /api/knowledge/projects  A    -> 200 [PublicProj, SecretProj-A]
GET /api/knowledge/projects  B    -> 200 [PublicProj, SecretProj-B]
GET /api/knowledge/projects/SecretProj-A  anon -> 404   A -> 200   B -> 404
```

The panel therefore states the *opposite* invariant to the timeline panel: a `[]` here is
always a genuine empty read (the public corpus is visible to everyone), and a **public-only
answer to a signed-in viewer** is the boundary working, not a partial result. Conflating
either with the timeline's ambiguity would be wrong.

**No handler defect found.** Nothing under `knowledge/` was changed.

### 8.3 Implemented

| File | Change |
|---|---|
| `pages/knowledge/knowledgeContracts.ts` | project row shape, `isKnowledgeProjects` guard, `public`/`scoped` vocabulary, `projectNotice`, `projectTags` (parses the JSON-string column) |
| `components/knowledge/KnowledgeProjectsPanel.tsx` | **new** — reads `endpoints.knowledgeProjects` through the shared client; distinct loading/empty/auth/unavailable/error states; labels ownership, never filters on it |
| `pages/KnowledgePage.tsx` | mounts the projects panel |
| `tests/test_knowledge_projects_boundary.py` | **new** — 17 tests |

### 8.4 Negative controls — proven to bite, then reverted byte-identically

| Control | Mutation | Result |
|---|---|---|
| anonymous project clause | `knowledge/vault.py`: `user_id IS NULL` → `1 = 1` | **4 failed** — anonymous reads a private project, non-owner single read stops 404-ing, and the clause detector reports `1=1` |
| wrong contract direction | detector fed the timeline's `1 = 0` shape | reported, not silently accepted — the two readers do not share a predicate |
| client-side filter | panel gains `.filter((project) => project.user_id !== null)` | **1 failed** |
| comment vs code | a comment naming `user_id` ignored; a real filter flagged | as intended |

`git diff` on `knowledge/vault.py` is empty after restore.

### 8.5 Verification

| Check | Result |
|---|---|
| Projects suite | **17 passed** |
| Adjacent suites (9 files) | **133 passed** |
| `corepack pnpm build` | **succeeded** (76 modules) |
| Full suite node set | see §6.1 / §8.6 |

### 8.6 Full-suite result for this slice

See the measured block in §8.6.1 below.

### 8.6.1 Measured

Both slices present (timeline + projects), `PYTHONPATH=.:archive/legacy_python`:

| Tree | Result | Node set |
|---|---|---|
| Branch (both slices) | **27 F / 2378 P / 17 S / 1 E** | 28 nodes, `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` |
| Baseline (both slices stashed) | **27 F / 2342 P / 17 S / 1 E** | 28 nodes, `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` |

`comm -3` empty. The `+36 passed` is exactly the two new test files (19 + 17).

### 8.7 Remaining declared-but-unconsumed Knowledge OS surfaces

- `GET /api/knowledge/projects/{name_or_uuid}` — verified and pinned at the boundary level
  (fail-closed 404 for a non-owner); not given its own panel. A project detail view is the
  next candidate, and it needs a registry **path builder** (the registry has none for
  knowledge sub-resources), which is Workstream 1's file — so it is a request, not an edit.
- `GET /api/knowledge/graph/{note_id}/traverse` — declared; not wired.
- `GET /api/knowledge/timeline/recent`, `/timeline/replay/{project_id}` — declared; the
  timeline panel reads the primary `query` contract only.
- `endpoints.codex` / `endpoints.field` — declared with no consumer; not Knowledge OS.

## 9. Next bounded task (non-overlapping)

The declared Knowledge OS read set (status, graph, search, timeline, projects) is now fully
consumed by the surface. The next non-overlapping candidates, in preference order:

1. **Project detail** — needs `endpoints` path-builder support (Workstream 1's file). Submit
   a precise request rather than editing the registry.
2. **Graph traversal** — `GET /api/knowledge/graph/{note_id}/traverse`; same handler-first
   verification, but it needs a note anchor the surface does not yet offer, so it is
   blocked on a note-selection surface rather than on a contract.
3. **`/timeline/recent` and `/timeline/replay/{project_id}`** — declared and owner-scoped;
   lower value than the above because the primary timeline reader already covers the use
   case, and `recent` merely reverses the same query.

None of these requires a shared-registry edit except (1), which is why (1) is a request.

