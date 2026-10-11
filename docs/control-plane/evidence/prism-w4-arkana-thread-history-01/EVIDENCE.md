# Workstream 4 -- Arkana thread history · Slice 01 evidence

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
omitted** -- ownership is enforced server-side and never round-trips to the client.

`GET .../messages` returns `{role, content, created_at}` per message. Roles are
**`user` and `arkana`** -- *not* `assistant`. A UI that reuses the resonance
endpoint's vocabulary (`assistant`) would render every reply with the wrong label,
so this is pinned by both a source test and a backend test.

The handler parses each `conversation` note's stored content for the literals
`## Prompt\n\n` and `\n\n## Response\n\n`. A note missing either marker, a note with
a prompt but no response, and non-`conversation` notes are **skipped** -- the API
never fabricates an assistant answer. Verified by a dedicated test.

### Failure states (measured)

| Condition | Result |
|---|---|
| No identity | `401` on every route (`Authentication required`) |
| Unknown uuid, or another owner's uuid | `404 {"detail":"Thread not found"}` |
| Another identity's list | `200 {"threads": []}` -- never a leak, never a 404 |
| Empty thread messages | `200 {"messages": []}` |
| Non-integer `project_id` | `422` on **list** (FastAPI query typing); `400` on **create** (manual body validation) |
| Non-existent project on create | `404 Project not found` |
| Empty title on rename | `400` |
| **Body-less `POST`** | **`500`** -- see §4 |

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
  the mutating thread verbs at all -- opening, renaming, and appending a turn are
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
`useHydration<LabSessionView>(path, …)` -- the path is legitimately built from
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
* **Next bounded move:** the Weaver run/event/evidence read surfaces -- **landed in slice 02** (§6).
* No mutating Lab control is wired. No deployment, merge, or acceptance is claimed.

---

## 6. Slice 02 -- Weaver run / work-event / evidence ledger

The Weaver page read `/api/approvals` and advertised an unbuilt execute view
(`NotYetWired ... "The run view is not yet built"`). The Lab substrate already
exposes the records the page promised, so the page now surfaces them.

### Contract (measured against the real runtime + store)

`GET /api/lab/engineering/sessions/{id}` -> `EngineeringLabRuntime.session_view`
returns `{session, agent, runs, events, evidence, artifacts, loop,
reached_review_boundary, human_decision_required}`. Verified by driving the real
runtime over an isolated SQLite DB (`tests/test_weaver_run_evidence_contract.py`):

| Reading | Measured |
|---|---|
| A newly opened session | `state=PROPOSED`, `runs=[]`, `evidence=[]`, one `SESSION_CREATED` event |
| Recording an authorization | `state→AUTHORIZED`, still `runs=[]`, `evidence=[]` -- a decision is not an execution |
| Event shape | `{event_id, session_id, run_id, event_type, sequence, timestamp_utc, payload}` |
| Owner scoping | another subject -> `KeyError` (handler -> `404`) |
| `reached_review_boundary` | `false` for PROPOSED/AUTHORIZED; true only at the review states |

### Slice (read-only; reuses the existing read model, no duplicate)

* `components/lab/LabSessionList.tsx` -- extended with three distinct record
  sections (`lab-runs` / `lab-events` / `lab-evidence`), each with its own
  non-error empty state. Evidence renders "not a verdict"; an empty run set reads
  "an authorized session is not an executed run".
* `pages/WeaverPage.tsx` -- mounts the ledger (`<LabSessionList />`) and replaces
  the false "not yet built" note with a blocked-state note naming the mutating
  acts (`/authorize`, `/execute`, `/transition`, `/run-agent`).
* No duplicate Weaver component was authored -- the existing read model was
  reused and extended, per the contract's "do not create duplicate abstractions".

### Repaired pre-existing defect (in an owned file)

`components/lab/LabSessionList.tsx` passed a helper-computed `path` to
`useHydration`, which `test_console_endpoint_registry_contract.py` flags: the
first argument must be a registry member. The path is now built inline at the
call site (`endpoints.labSessions + "/" + …`). This node was **failing on `main`
and now passes** -- see §7. The `test_prism_w4_lab_read_model.py` assertion that
pinned the old template-literal form was updated accordingly.

### Tests

```
python -m pytest tests/test_weaver_run_evidence_contract.py tests/test_prism_w4_lab_read_model.py \
  tests/test_console_endpoint_registry_contract.py tests/test_prism_w4_arkana_thread_history.py \
  tests/test_arkana_thread_history_contract.py -q -rEf
  -> 63 passed

corepack pnpm build   (web/arkadia_console)
  -> tsc --noEmit clean; vite build succeeded
```

### Baseline comparison (full suite)

| Tree | Summary | Failing/error nodes |
|---|---|---|
| `main` `962434be` | 19F / 2220P / 17S / 1E | 20 |
| branch (slice 01) | 19F / 2249P / 17S / 1E | 20 |
| branch (slice 02) | 18F / 2263P / 17S / 1E | 19 |
| branch (slice 03) | 18F / 2279P / 17S / 1E | 19 |
| branch (slice 04) | 18F / 2293P / 17S / 1E | 19 |

Node-set delta between slice 02 and slice 03 (`comm -3` on the sorted ids):
**empty** -- no new failures. `+16 passed` = 10 canvas oracle + 6 canvas guard
tests.

Node-set delta between slice 03 and slice 04: **empty**. `+14 passed` = 8
agent-registry oracle + 6 agent-registry guard tests.

Node-set delta vs `main`: the **only** difference is
`tests/test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`,
failing on `main` and **passing** here (the repaired owned-file defect).

### Known gaps / next bounded move (after slice 02)

* **Not wired:** artifacts canvas (`/api/lab/engineering/artifacts` is a real
  `GET`; not surfaced yet), automations, and the mutating Lab state acts.
* **Not attempted:** live run progress, streaming events, PR projection
  (`/api/lab/engineering/pr/{number}` is a real `GET`). The ledger is a snapshot,
  not a live feed; the UI does not imply liveness.
* **Next bounded move:** mount the read-only artifact canvas
  (`GET /api/lab/engineering/artifacts` + `GET /api/lab/engineering/canvas/{id}`)
  on the Engineering Lab page's currently-`NotYetWired` artifacts panel, from the
  same handler-verified contract, with the same loading/empty/unavailable states.
  -- **landed in slice 03** (§7).

---

## 7. Slice 03 -- Engineering Lab artifact canvas

The Engineering Lab page carried a `NotYetWired contract="/api/lab/engineering/artifacts"`
placeholder for a contract that **is** served. This slice mounts the real
read surface.

### Contract (measured against the real store and `canvas_view`)

| Endpoint | Response |
|---|---|
| `GET /api/lab/engineering/artifacts[?session_id=]` | `{"artifacts": [...], "count": n}`; each record `{artifact_id, session_id, run_id, kind, title, content, created_at}` |
| `GET /api/lab/engineering/canvas/{artifact_id}` | `canvas_view(artifact)` → `{artifact, renderer, available, kind, actions, unavailable_reason}`; missing/foreign id → 404 |

Measured (`tests/test_lab_artifact_canvas_contract.py`, isolated DB):

| Reading | Measured |
|---|---|
| List, owner-scoped | own records only; another subject → `[]` |
| `session_id` filter | matches only that session |
| Content present | `available=true`, `renderer=MarkdownViewer` |
| Content absent (`None`) | `available=false`, `unavailable_reason` non-empty |
| Declared `actions` | `INSPECT, COMPARE, ANNOTATE, EXPORT, ATTACH, ARCHIVE` -- no `EXECUTE`/`AUTHORIZE`/`APPROVE`/`MERGE`/`DEPLOY` |
| Cross-subject `get_artifact` | `None` (handler → 404) |

### Slice (read-only)

* `components/lab/LabArtifactCanvas.tsx` -- lists artifacts, expands one into its
  canvas descriptor. Renders captured text as source only when it is genuinely a
  present string; otherwise shows the backend's `unavailable_reason` or "captured
  as structured data -- no text renderer wired". Declared actions render as a
  **non-interactive label**, never buttons that would do nothing.
* `pages/EngineeringLabPage.tsx` -- mounts the canvas and drops the placeholder
  panel; the remaining `NotYetWired` names only the mutating acts.

### Tests

```
pytest tests/test_lab_artifact_canvas_contract.py tests/test_prism_w4_lab_read_model.py \
       tests/test_console_endpoint_registry_contract.py tests/test_weaver_run_evidence_contract.py \
       tests/test_prism_w4_arkana_thread_history.py tests/test_arkana_thread_history_contract.py -q -rEf
  -> 79 passed
corepack pnpm build   -> tsc clean; vite build OK
```

### Known gaps / next bounded move (after slice 03)

* **Not wired:** the declared canvas actions (`INSPECT`…`ARCHIVE`) -- no click
  behavior, rendered as labels. Rendering an artifact is not verification, and
  the UI does not imply it.
* **Not attempted:** non-text renderers (diff/code/svg/image) -- the descriptor
  names a canonical renderer but the console has no `DiffSurface`/`ImageSurface`
  yet; structured content is reported honestly rather than faked. Live run
  progress and PR projection (`GET /api/lab/engineering/pr/{number}`) remain
  unsurfaced.
* **Next bounded move:** surface the owner-scoped agent registry
  (`GET /api/lab/engineering/agents`) on the Engineering Lab page next to the
  N-ATLAS panel -- it is a real `GET`, already registry-declared as
  `endpoints.labAgents` -- then continue to automations only if a read contract
  exists. -- **landed in slice 04** (§8).

---

## 8. Slice 04 -- Engineering Lab deployed-agent registry

### Contract (measured against the real runtime)

`GET /api/lab/engineering/agents` -> `{"agents": [...]}`. Each record
`{agent_id, role, display_name, capabilities, tool_access, model_ref,
policy_ref, created_at}` with `tool_access = {tools, write_allowed,
network_allowed, allowed_paths, forbidden_paths}`.

| Reading | Measured |
|---|---|
| Owner scoping | own agents only; another subject -> `[]` |
| Unknown role | `register_agent(role="engineer")` -> `ValueError` |
| Capability ceiling | `REVIEWER` + `EDIT` -> `BoundaryViolation` (exceeds the role ceiling) |
| Ceiling is real, not blanket | `BUILDER` + `EDIT` accepted (negative control) |
| Read-only role | `SENTINEL` -> `write_allowed=false`; no `EXECUTE`/`MERGE`/`DEPLOY`/`AUTHORIZE` capability |

### Slice (read-only)

* `components/lab/LabAgentRegistry.tsx` -- lists deployed agents with role,
  model, tool envelope, and declared capabilities. The copy states the contract:
  a capability is a **declared ceiling**, a tool envelope is what the substrate
  would enforce, and neither grants the surface power to act. Deploying an agent
  (`POST /engineering/agents`) is a mutating act and stays unwired.
* `pages/EngineeringLabPage.tsx` -- mounts the registry alongside the canvas.

### Tests

```
pytest tests/test_lab_agent_registry_contract.py tests/test_lab_artifact_canvas_contract.py \
       tests/test_prism_w4_lab_read_model.py tests/test_console_endpoint_registry_contract.py \
       tests/test_weaver_run_evidence_contract.py tests/test_prism_w4_arkana_thread_history.py \
       tests/test_arkana_thread_history_contract.py -q -rEf
  -> 93 passed
corepack pnpm build   -> tsc clean; vite build OK
```

### Known gaps / next bounded move (after slice 04)

* **Not wired:** deploying an agent, and the declared canvas actions. Both are
  mutating or unimplemented; neither is presented as available.
* **Not attempted:** automations (EL-03) -- the directive names it, but it must
  not be surface-mounted until a read contract for it exists and is verified
  against a handler, per the same rule used here.
* **Next bounded move:** the Arkana thread-history slice is already landed
  (slice 01); the remaining Workstream 4 surfaces are the Weaver
  evidence/event read views, which slices 02-04 now cover through the session
  view, the canvas, and the agent registry. Next: reconcile this PR against the
  shared contract before requesting anything from Workstream 1, and re-run the
  full suite on the composed tree if `main` has moved.


---

## 9. Slice 05 -- BLOCKED: automations read surface needs a Workstream 1 registry entry

`GET /api/lab/engineering/automations` **is** a served, real read contract:

```
{"automations": [...], "grammar": {grammar: [TRIGGER, AGENT, TOOLS, SANDBOX,
 OUTPUT, EVIDENCE, NOTIFICATION, HUMAN_GATE], states, trigger_kinds,
 may_prepare_consequential_action: true,
 may_authorize_consequential_action: false, final_transition: "HUMAN_GATE"}}
```

Each record carries `{automation_id, name, state, trigger{kind,detail,schedule,
event}, agent_role, objective, tools, sandbox_write_allowed,
human_gate_required, may_authorize, notification_target, created_at, updated_at}`;
`TRIGGER_KINDS = scheduled | repository_event | pr_event | runtime_health |
manual | external_event`; `AUTOMATION_STATES = DRAFT | ENABLED | RUNNING |
OBSERVED | COMPLETED | FAILED | AWAITING_HUMAN_ACTION`.

**Blocker.** The surface cannot be mounted without an endpoint-registry entry,
and `web/arkadia_console/src/lib/endpoints.ts` is owned by **Workstream 1**
(SHARED-CONTRACTS section 1) and is not editable from this branch. SHARED-CONTRACTS
section 3.3 forbids inventing an endpoint, and section 4 says to "pause that
dependent slice and record the blocker" when a shared contract change is needed.
No component was committed for this slice.

**Workstream 1 request (adds to the earlier `labCanvas(id)`/`labSession(id)` ask):**
add `labAutomations: "/api/lab/engineering/automations"` to `endpoints.ts`. The
path is verified served (`api/lab_routes.py:335`); the response shape above is
measured against `make_automation` + `grammar_view`.

**Not wired, deliberately:** `POST /engineering/automations` (create) and
`POST /engineering/automations/{id}/state` (transition) are mutating acts; the
read surface would render the served grammar's `HUMAN_GATE` framing and keep
both unwired.

**Next bounded move (once the registry entry exists):** mount
`components/lab/LabAutomations.tsx` with an oracle test over `make_automation` +
`grammar_view` (owner scoping, trigger-kind and state vocabularies, the
`may_authorize_consequential_action === false` gate, and a negative control).
Until then, the non-overlapping move is to re-verify the Arkana thread-history
slice against the current handler (done this pass; 29 passed) and keep the PR
reconciled with `main`.



