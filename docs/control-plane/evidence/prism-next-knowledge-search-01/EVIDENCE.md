# Workstream 3 — verified Knowledge OS search (next wave) · evidence

**Branch:** `feat/prism-next-03-knowledge-search` (PR #427, draft)
**Durable task:** `docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md`
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (accepted, PR #419)
**Starting `main`:** `962434bed1bccb11fbf5edfcb0299317b12a8915`
**Branch head at evidence time:** `7b5b71c508652369bc6f22adc353568356b9f062`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Endpoint verification — `POST /api/knowledge/search`

Read from the handler and the served schema; not from the archive, and not invented.

| Item | Measured value |
|---|---|
| Handler | `api/knowledge_routes.py::search` |
| Delegate | `knowledge.search.unified_search` |
| Registration | `router = APIRouter(prefix="/api/knowledge")` mounted at `api/main.py:346` |
| Method / path | `POST /api/knowledge/search` — present in the served `GET /openapi.json` at `962434be` |
| Request body | `{query: str, modes?: [str], top_k: int = 20}` (`knowledge_routes.SearchRequest`) |
| Response | mapping of *mode name* → list of retrieved records; only the requested modes are emitted |
| Default modes | `semantic, fulltext, tag, timeline, project, people, reference` (`graph` needs a note anchor) |
| Auth | **optional** — `_optional_user_id()` → `api.auth.get_current_user`, which returns `None` rather than raising |
| Owner predicate | `knowledge.search._notes_owner_sql`: authenticated `(user_id = ? OR user_id IS NULL)`, anonymous `user_id IS NULL` |
| Rate limit | declared in `api/rate_limit.py` (`/api/knowledge/search`: 60/60) |
| Persistence | canonical SQLite `knowledge/schema.sql`; owner column `notes.user_id` / `projects.user_id` / `timeline.user_id` |

### Auth boundary — measured

An anonymous caller is a **real** caller and receives the public corpus. It is not
a `401`, and it is not "all rows". Verified live (anonymous
`POST /api/knowledge/search` → `200`) and in-suite.

---

## 2. Three defects measured on this endpoint

All three were confirmed by direct execution before any repair.

### D1 — `references` table declared with an unquoted SQL reserved word (live 500)

`knowledge/schema.sql` declared `CREATE TABLE IF NOT EXISTS references (…)`.
SQLite rejects it (`near "references": syntax error`); `knowledge/db.py::_apply_schema`
swallows `OperationalError`, so the table was **never created** and
`knowledge.search.reference_search` (which correctly quotes the name) failed.

Observed **live** at `https://arkadia-qzu4.onrender.com`:

```
POST /api/knowledge/search {"query":"Arkadia","modes":["reference"]}          -> 500 {"detail":"no such table: references"}
POST /api/knowledge/search {"query":"Arkadia","top_k":3}   # default modes     -> 500 {"detail":"no such table: references"}
POST /api/knowledge/search {"query":"Arkadia","modes":["fulltext"],"top_k":3} -> 200
```

The **default** mode set includes `reference`, so the endpoint's normal,
unspecified-mode call was broken.

### D2 — `project` and `timeline` modes were not owner-scoped (cross-owner leak)

`unified_search` dispatched `project_search(query, limit=10)` and
`timeline_search(keyword=query, …)` **without** `user_id`. Both functions ignore
ownership without it, so an anonymous caller received every owner's private
projects and timeline events. Measured before the repair:

```
anon  project: ['PublicProj Alpha', 'SecretProj Alpha']  timeline: [('decision','probe-user-a')]
A     project: ['PublicProj Alpha', 'SecretProj Alpha']  timeline: [('decision','probe-user-a')]
B     project: ['PublicProj Alpha', 'SecretProj Alpha']  timeline: [('decision','probe-user-a')]
```

This is the exact boundary the shared contract obliges this workstream to
preserve, on the exact endpoint it was asked to integrate.

### D3 — `graph_search` was already owner-aware but not given the identity

`graph_search(note_id, …, user_id=None)` forwards to `knowledge.graph.traverse`,
which applies an ownership predicate. `unified_search` called it without
`user_id`, so the anchor traversal read unscoped. Threaded in the same change
(the mode still requires `note_id_for_graph`, which the HTTP route never sets —
recorded as a gap, not a defect of this slice).

---

## 3. Repairs

| File | Change |
|---|---|
| `knowledge/schema.sql` | quote the reserved table name: `CREATE TABLE IF NOT EXISTS "references"` (+ comment naming the failure mode) |
| `knowledge/search.py` | `project_search(…, user_id)` and `timeline_search(…, user_id)` accept and apply the ownership predicate; `unified_search` forwards `user_id` to `timeline_search`, `project_search` **and** `graph_search` |
| `web/.../pages/knowledge/knowledgeContracts.ts` | added the search contract shape guard, mode vocabulary, and record helpers |
| `web/.../components/knowledge/KnowledgeSearchPanel.tsx` | re-pointed at the verified handler contract; rejects an unrecognised payload; distinct loading/empty/error states |
| `web/.../pages/KnowledgePage.tsx` | mounts the panel **only when the shared registry carries the path**, else renders the blocked state |

**No migration is required for D1**: `_apply_schema` runs the DDL on every
connection, so the existing production database (where the table is absent)
creates it on the next boot.

`project_search` reuses `knowledge.vault._project_owner_clause` and
`timeline_search` reuses `knowledge.timeline._timeline_owner_clause` rather than
re-deriving the predicate, so ownership stays defined in one place per reader.

---

## 4. Shared-registry status — integration request raised, not bypassed

`web/arkadia_console/src/lib/endpoints.ts` is owned by **Workstream 1** and does
**not** carry `/api/knowledge/search` (measured at `962434be` and on Workstream
1's branch head `e82f7465`). Per the shared contract §3.1 a feature page must not
add a second registry entry or inline the path.

`KnowledgePage.tsx` therefore reads the registry *shape*
(`endpoints["knowledgeSearch"]`) and mounts `KnowledgeSearchPanel` when it is a
root-absolute path; until then it renders a `NotYetWired` blocked state naming the
verified contract. A precise integration request was posted to Workstream 1 (PR
#425). The panel is complete and mounts with no further edit once the entry
exists.

---

## 5. Tests

`tests/test_knowledge_search_boundary.py` — **21 tests**, all passing. Live
handler over an ASGI transport against a sandboxed database; no mocks.

| Group | Coverage |
|---|---|
| schema | request/response shape; only requested modes returned; default modes served (**D1 pin**); `references` table materialised; quoted-table read |
| private/public (notes) | anonymous excludes private; owner sees own + public; no cross-owner leak |
| private/public (projects, timeline) | anonymous/non-owner cannot read another owner's private project or timeline event; owner positive control (**D2 pin**) |
| no-fabrication | an unmatched query is an empty list, not an invented record |
| source guards | no unquoted reserved-word DDL; every owner-scoped dispatch forwards `user_id`; panel keeps the boundary server-side, rejects unrecognised payloads, and shows distinct loading/empty/error states |

### Negative controls — each proven to bite, then reverted

| Control | Mutation | Result |
|---|---|---|
| D1 root cause | revert `schema.sql` to the unquoted `references` DDL | **4 failed** (`test_search_default_modes_are_served_not_a_500`, `test_references_table_is_materialised_by_the_schema`, `test_reference_search_reads_the_quoted_table`, `test_no_unquoted_reserved_word_table_is_declared`) |
| D2 root cause | drop `user_id` from the `project`/`timeline` dispatch | **3 failed** (`test_project_mode_does_not_leak_private_projects`, `test_timeline_mode_does_not_leak_private_events`, `test_unified_search_forwards_user_id_to_every_scoped_mode`) |
| Detector (DDL) | feed the pre-repair DDL shape directly | reported `['references']`; silent on the quoted form |
| Detector (dispatch) | feed the pre-repair dispatch shape directly | reported `['project_search']`; silent on the scoped form |

Both mutations were reverted byte-identically (`git diff` shows only the intended
changes).

The dispatch detector originally used a naive `[^)]*` argument match, which
stopped at the first `)` and **falsely reported** the correctly-scoped
`timeline_search` call (whose argument is `limit=min(top_k, 50)`). Fixed to a
balanced-parenthesis scan; recorded because a detector that cannot read its own
subject is not a detector.

---

## 6. Verification

| Check | Command | Result |
|---|---|---|
| New suite | `pytest tests/test_knowledge_search_boundary.py -q -rEf` | **21 passed** |
| Adjacent suites | `test_knowledge_os_boundary`, `test_solariun_knowledge_slice_01`, `test_console_endpoint_registry_contract`, `test_oracle_spine`, `test_m06_knowledge`, `test_isolation`, `test_evidence_verification_boundary` | **84 passed, 1 failed** |
| Typecheck + build | `corepack pnpm build` (node 24.21.0, pnpm 10.26.1) | **succeeded** (68 modules, `dist/assets/index-C1nkyEaN.js`) |
| Full suite (branch) | `pytest tests/ -q -rEf --continue-on-collection-errors` | **19 F / 2241 P / 17 S / 1 E** |
| Full suite (`main` `962434be`) | same, new test file removed | **19 F / 2220 P / 17 S / 1 E** |

### Baseline comparison by node identity (not by count)

Sorted `FAILED`/`ERROR` node sets for both trees hash to the **same**
fingerprint `dc06db02cd24067e8a61728a139fdc2e64ecc03834fd6ec69f3bdf20e123091c`
(20 nodes). `comm -3` is **empty**. The `+21 passed` is exactly the new file.

### Recorded, not repaired (pre-existing on `main`)

- `tests/test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`
  fails on `main` `962434be` at `components/lab/LabSessionList.tsx` — Lab is
  **Workstream 4's** ownership. Verified by measuring the same file on `main`.
- The 19 failing / 1 error nodes in the baseline are pre-existing and unchanged.

### Runtime note (no production-parity claim)

The canonical runtime at `https://arkadia-qzu4.onrender.com` reports
`source_revision = 962434be` (`RENDER_GIT_COMMIT`, `revision_conflict: false`) —
i.e. the deployed revision is `main`, **not** this branch. The D1 500 above is a
production observation of the pre-repair revision. This slice makes **no**
deployment or parity claim; a post-merge deploy is required before the repaired
endpoint is observable in production.

---

## 7. Explicitly not done

- No edit to `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `lib/endpoints.ts`,
  shared shell/tokens, NovaNet, Arkana, Weaver or Lab files.
- No client-side ownership filter as a substitute for server authorization.
- No fabricated/search-simulated results; no fake persistence.
- No merge, deployment, or acceptance.
- The `modes=["graph"]` HTTP path (needs a note anchor the route never supplies)
  and the broader `NotYetWired` timeline surface remain open, non-overlapping
  follow-ons.

## 8. Next move

Commit and push this slice; post the Workstream 1 integration request for the
`knowledgeSearch` registry entry; then continue the next non-overlapping
Knowledge OS task (the timeline read surface) from fresh `main` after this PR
merges.
