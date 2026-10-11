# Workstream 4 — Arkana thread history · Slice 01 evidence

**Branch:** `feat/prism-next-04-arkana-threads` (PR #428, draft)
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (accepted in `main`, PR #419)
**Instruction:** `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md` (next-wave section)
**Starting `main`:** `962434bed1bccb11fbf5edfcb0299317b12a8915` (next-wave authorisation merge)
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Route + auth verification (measured against the handler, not inferred)

`api/commune_threads.py` mounts `APIRouter(prefix="/api/commune/threads")`, composed
into the app at `api/main.py:338`. Measured with a composed `FastAPI()` over the real
router and a real identity seam (`tests/test_arkana_thread_history_contract.py`):

| Method | Path | Auth (no identity) | Success |
|---|---|---|---|
| `GET` | `/api/commune/threads` | `401 {"detail":"Authentication required"}` | `{"threads": [ArkanaThread]}` |
| `POST` | `/api/commune/threads` | `401` | thread projection |
| `GET` | `/api/commune/threads/{thread_uuid}` | `401` | `{"thread": ArkanaThread}` |
| `PATCH` | `/api/commune/threads/{thread_uuid}` | `401` | thread projection |
| `GET` | `/api/commune/threads/{thread_uuid}/messages` | `401` | `{"messages": [ArkanaThreadMessage]}` |

* `GET /api/commune/threads` also accepts an optional `project_id: int` query filter.
* `GET /api/commune/threads/{uuid}/messages` accepts no parameters.

### Response shape (exact keys)

`_public_thread(row)` returns exactly
`{id, uuid, title, project_id, created_at, updated_at}`. **`user_id` is deliberately
omitted** — ownership is enforced server-side and never round-trips to the client.

`GET .../messages` returns `{role, content, created_at}` per message. Roles are
**`user` and `arkana`** — *not* `assistant`. A UI that reuses the resonance
endpoint's vocabulary (`assistant`) would render every reply with the wrong label,
so this is pinned by both a source test and a backend test.

The handler parses each `conversation` note's stored content for the literals
`## Prompt\n\n` and `\n\n## Response\n\n`. A note missing either marker, a note with
a prompt but no response, and non-`conversation` notes are **skipped** — the API
never fabricates an assistant answer. Verified by a dedicated test.

### Failure states (measured)

| Condition | Result |
|---|---|
| No identity | `401` on every route (`Authentication required`) |
| Unknown uuid, or another owner's uuid | `404 {"detail":"Thread not found"}` |
| Another identity's list | `200 {"threads": []}` — never a leak, never a 404 |
| Empty thread messages | `200 {"messages": []}` |
| Non-integer `project_id` | `422` on **list** (FastAPI query typing); `400` on **create** (manual body validation) |
| Non-existent project on create | `404 Project not found` |
| Empty title on rename | `400` |
| **Body-less `POST`** | **`500`** — see §4 |

The load-bearing distinction: **an empty collection is a `200`.** The UI therefore
cannot infer "no data" from a failure, or a failure from "no data".

---

## 2. Implemented slice (feature-local, read-only)

| Path | Role |
|---|---|
| `web/arkadia_console/src/components/arkana/ArkanaThreadHistory.tsx` | the read-only thread-history surface |
| `web/arkadia_console/src/components/arkana/arkanaThreadsContract.ts` | handler-derived response types |
| `web/arkadia_console/src/pages/ArkanaPage.tsx` | mounts `<ArkanaThreadHistory />` |
| `tests/test_arkana_thread_history_contract.py` | backend oracle (14 tests) |
| `tests/test_prism_w4_arkana_thread_history.py` | frontend source contract (15 tests) |

* **Read-only by construction.** The slice issues only `GET`. It does not reference
  the mutating thread verbs at all — opening, renaming, and appending a turn are
  human acts, deliberately unwired. Pinned by `test_slice_issues_no_mutating_request`
  and `test_slice_does_not_reference_the_mutating_thread_verbs`.
* **Honest states.** Loading / auth-required / unavailable / read-failed come from the
  shared `useHydration` + `ContractState`; the empty list and the empty thread render
  distinct, non-error copy. No mock data, no inferred success.
* **One declared base.** The parameterised `.../messages` sub-resource is built from
  `endpoints.arkanaThreads`, so the shared registry (`lib/endpoints.ts`, workstream 1)
  remains the single source of the declared collection.

### Shared-file boundary

No shared-registry file was edited. `lib/endpoints.ts`, `App.tsx`, `lib/router.ts`,
and `lib/surfaces.ts` are untouched. The existing `endpoints.arkanaThreads` entry was
already present and `GET /api/commune/threads` is served by `api.main:app`, so
`test_console_endpoint_registry_contract.py::test_every_declared_endpoint_is_served_by_the_canonical_app`
passes.

### Request to Workstream 1 (do not edit the registry)

1. Add a first-class parameterised helper for the messages sub-resource, e.g.
   `arkanaThreadMessages(uuid: string): string`, so the path literal lives in the
   registry rather than as an expression in the feature module.
2. Optionally promote the `ArkanaThread` / `ArkanaThreadMessage` response types from
   `components/arkana/arkanaThreadsContract.ts` into `lib/types.ts` once a second
   workstream consumes the same contract.

Until §1 lands, the slice keeps a registry-anchored expression and the source guard
requires every `useHydration` path argument to start with `endpoints.`.

---

## 3. Tests and verification

Commands run in this worktree on the branch (node 24, pnpm 10.26, `corepack pnpm`):

```
python -m pytest tests/test_arkana_thread_history_contract.py tests/test_prism_w4_arkana_thread_history.py -q -rEf
  -> 29 passed

corepack pnpm install --frozen-lockfile && corepack pnpm build   (web/arkadia_console)
  -> tsc --noEmit clean; vite build succeeded (68 modules, dist/assets/index-DFS_H8Qr.js 44.28 kB)
```

### Baseline comparison (full suite, same environment)

| Tree | Summary | Failing/error nodes |
|---|---|---|
| `main` `962434be` | 19 failed, 2220 passed, 17 skipped, 1 error | 20 |
| branch (this slice) | 19 failed, 2249 passed, 17 skipped, 1 error | 20 |

`diff` of the sorted `FAILED`/`ERROR` node sets is **empty**. The `+29 passed` is
exactly the two new test files (14 + 15). No node was fixed or broken.

The 20 pre-existing nodes include one that touches the console:
`tests/test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`,
failing on `components/lab/LabSessionList.tsx` (workstream 4's *previous* slice, on
`main`). It is a **pre-existing** defect, not introduced here: the detector's regex
`useHydration<[^>]*>\(\s*([^,\n]+)` mis-parses the nested generics in
`useHydration<LabSessionView>(path, …)` — the path is legitimately built from
`endpoints.labSessions` two lines above. It is recorded here and left for a bounded
follow-up; this slice's own hydration arguments are registry-anchored and pass.

---

## 4. Recorded backend defect (not repaired here)

`create_arkana_thread` calls `await request.json()` **without guarding a body-less
request**, so `POST /api/commune/threads` with no body raises and returns `500`
(`tests/test_arkana_thread_history_contract.py::test_recorded_defect_bodyless_create_is_a_server_error`).
A `400 "A JSON body is required"` is the expected repair. Recorded, not repaired:
`api/commune_threads.py` is not owned by workstream 4 and the read-only slice never
issues a create. When it is repaired, this pin must be re-pointed.

---

## 5. Known gaps / next bounded move

* **Not wired (intentionally):** thread creation, rename, and turn append. These
  mutate the Knowledge OS threads table; the slice stays read-only.
* **Not attempted:** live message streaming, citations/RAG refs, per-message voice.
  The thread messages contract carries none of those, so the UI must not imply them.
* **Next bounded move:** the Weaver run/event/evidence read surfaces. `WeaverPage`
  currently reads `/api/approvals` and advertises an unwired execute contract. The
  verified read path is the Lab session view already consumed by
  `LabSessionList` (`GET /api/lab/engineering/sessions/{id}`) whose `runs` / `events`
  / `evidence` arrays are real; surfacing those on the Weaver page from the same
  handler-verified contract is the next non-overlapping slice. Proposal ≠ approval ≠
  execution ≠ work event ≠ evidence ≠ verification ≠ acceptance must stay distinct.
* No mutating Lab control is wired. No deployment, merge, or acceptance is claimed.
