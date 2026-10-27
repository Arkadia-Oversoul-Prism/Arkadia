# ARKADIA Unified Engineering Lab MVP — mission workspace vertical slice

**Status:** IMPLEMENTED · TESTED · REPORTED — **not merged, not deployed, not accepted.**
**Branch:** `gate-hygiene/lane-guard-fixed-scope-01`
**Base revision:** `389e3b39870c8483c32c6d4bac6e08a845d9ca4e`
**Observed:** 2026-10-27

## 1. What was built

One complete, deterministic mission lifecycle on the Engineering Lab surface: create a
session, record a human authorization, execute a bounded read-only run, and render the
evidence the substrate returned. It is a **wired vertical slice**, not a scaffold: every
step calls the real backend and renders the real response.

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/lab/missionContract.ts` | new — the served request/response shapes |
| `web/arkadia_console/src/components/lab/MissionWorkspace.tsx` | new — the surface |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | mounts `<MissionWorkspace />`, restores the `NotYetWired` panel |
| `tests/test_lab_mission_workspace_contract.py` | new — 9 contract tests |

The lifecycle is exposed as five explicit steps, not one "run" button, because
authorization is a human decision rather than a side effect of creating work:

```
1 Deploy agent → 2 Create mission → 3 Attempt before approval → 4 Record human approval → 5 Execute bounded run
```

## 2. Verification

### 2.1 Backend vertical slice (real HTTP against the running dev backend)

Reproduced against `uvicorn api.main:app` on `:12000` with a dev-mode bearer token.
Verbatim output:

```
agent: 200 AGT-ebbbd7625d19
session: 200 SES-9b4408c648e9 PROPOSED
execute-before-approval: 400 session must be AUTHORIZED or QUEUED to execute
                             (currently PROPOSED); SESSION != AUTHORIZATION
authorize: 200 AUTH-724b1f7181a6 originated_by= human
execute-after-approval: 200 RUN-0aa70587ad7c IMPLEMENTED
terminal state: READY_FOR_REVIEW | evidence: 1 | runs: 1
```

| Step | Endpoint | Result |
|---|---|---|
| register agent | `POST /api/lab/engineering/agents` | `200` · `AGT-ebbbd7625d19` |
| create session | `POST /api/lab/engineering/sessions` | `200` · `SES-9b4408c648e9` · `PROPOSED` |
| execute before approval | `POST …/{id}/execute` | **`400`** · `session must be AUTHORIZED or QUEUED to execute (currently PROPOSED); SESSION != AUTHORIZATION` |
| record approval | `POST …/{id}/authorize` | `200` · `AUTH-724b1f7181a6` · `originated_by human` |
| execute after approval | `POST …/{id}/execute` | `200` · `RUN-0aa70587ad7c` · `IMPLEMENTED` · evidence `EVD-95e18f2a2eeb` |
| read session view | `GET …/{id}` | `200` · `READY_FOR_REVIEW` · 1 evidence · 1 run · 13 events |

The refusal at step 3 is the point of the slice: the authority boundary is a backend
decision the surface can demonstrate, not a UI convention it asserts.

### 2.2 Frontend build

`corepack pnpm build` (`tsc --noEmit && vite build`) — **clean**:

```
✓ 106 modules transformed.
dist/index.html                            1.25 kB │ gzip:  0.62 kB
dist/assets/index-CDwf0d25.css            17.58 kB │ gzip:  4.53 kB
dist/assets/vendor-react-nf7bT_Uh.js     140.87 kB │ gzip: 45.26 kB
dist/assets/vendor-firebase-DNJjg0gV.js  167.59 kB │ gzip: 34.09 kB
dist/assets/index-Dx_rTO0L.js            181.28 kB │ gzip: 46.29 kB
✓ built in 1.79s
```

`dist/` is untracked and was removed after the measurement.

### 2.3 Browser-level end-to-end (real UI, real backend)

Driven through a temporary Vite harness that mounts the **real** `MissionWorkspace`
against the **real** backend over a same-origin `/api` proxy. The harness was deleted
after the run; `AuthContext` and every gate were left untouched.

Observed in the live DOM, post-refactor run `SES-a9ed0bd8beed` / `AGT-16cdc773460a`:

- agent deployed → `AGT-16cdc773460a`
- mission created → `SES-a9ed0bd8beed`, state `PROPOSED`
- execute before approval → **`400 BAD_REQUEST: session must be AUTHORIZED or QUEUED to
  execute (currently PROPOSED); SESSION != AUTHORIZATION`** rendered in the operator log
- approval recorded → `AUTH-92f443b5b68e · originated_by human · merge false · production false`
- bounded run → the timeline rendered **13** numbered substrate events, and the final
  click surfaced the real `README.md` content in the rendered view

Backend request log for the same run confirms each hop, including the refusal:

```
POST /api/lab/engineering/agents                       200
POST /api/lab/engineering/sessions                     200
GET  /api/lab/engineering/sessions/SES-a9ed0bd8beed    200
POST /api/lab/engineering/sessions/SES-a9ed0bd8beed/execute   400
POST /api/lab/engineering/sessions/SES-a9ed0bd8beed/authorize 200
POST /api/lab/engineering/sessions/SES-a9ed0bd8beed/execute   200
```

The 13-event sequence and the terminal state were read back from the backend (§2.1); the
browser read confirmed the count rendered and the content arrived. The event names below
are the **backend's** own, captured from `GET /sessions/{id}` — not a client narration:

```
#1  SESSION_CREATED         #8  SESSION_TRANSITION   QUEUED
#2  SESSION_TRANSITION      #9  SESSION_TRANSITION   RUNNING
    AUTHORIZED              #10 SESSION_TRANSITION   CHECKPOINTED
#3  PLAN_PRODUCED           #11 SESSION_TRANSITION   VERIFYING
#4  SANDBOX_OPERATION       #12 SESSION_TRANSITION   READY_FOR_REVIEW
#5  EVIDENCE_RECORDED       #13 RUN_FINISHED
#6  PROPOSAL_PREPARED
#7  AUTHORIZATION_REQUIRED  "human review required; the substrate does not merge or deploy"
```

## 3. Two contract defects found and repaired

The first cut violated two guards in this repository. Both were genuine defects in my
code, both were caught by existing guards, and both are repaired rather than waived.

### 3.1 Endpoint literals (registry contract)

`tests/test_console_endpoint_registry_contract.py::test_no_page_passes_a_literal_path_to_api_request`
reported five inline paths passed to `apiRequest`:

```
components/lab/missionContract.ts: apiRequest path literal '"/api/lab/engineering/agents"'
components/lab/missionContract.ts: apiRequest path literal '"/api/lab/engineering/sessions"'
components/lab/missionContract.ts: apiRequest path literal '`/api/lab/engineering/sessions/${…}/authorize`'
components/lab/missionContract.ts: apiRequest path literal '`/api/lab/engineering/sessions/${…}/execute`'
components/lab/missionContract.ts: apiRequest path literal '`/api/lab/engineering/sessions/${…}`);'
```

A literal is a second, unreviewed endpoint contract. Repaired by deriving every path
from the console's one registry (`endpoints.labAgents`, `endpoints.labSessions`, the
declared `labSession()` builder, and a local `sessionAction()` helper composed from
`endpoints.labSessions`). 18/18 pass.

### 3.2 The "not wired" panel (read-only ceiling)

`tests/test_prism_w4_lab_read_model.py::test_lab_page_keeps_the_mutating_acts_as_an_explicit_blocked_state`
requires the page to keep naming the mutating acts it cannot perform. Mounting the
workspace **removed** the `NotYetWired` panel that carried that statement.

Restored — but reworded, because a note claiming authorize/execute are "not wired" would
now be false: the workspace wires exactly those two acts, bounded to read-only. The
panel now names what genuinely remains unwired (`transition`, `run-agent`, merge,
production deploy) and restates that an approval is not an execution and a run at the
review boundary is not acceptance. 48/48 pass across both suites.

## 4. Read-only ceiling

The surface cannot request a write: `requires_write: false` is fixed in the request body
and operations are constructed only as `{ kind: "read", target }`. The authorization is
recorded with `merge: false`, `production: false`. The terminal state is rendered as
**awaiting human review**, and the panel states the substrate cannot merge, deploy, or
self-authorize. There is no merge, deploy, or acceptance claim anywhere in the slice.

## 5. Negative controls

Each detector was proven to bite on the defect it claims to detect, not merely to pass.

- **bare-session read** — planted the mutation that actually reintroduces the bug
  (`getSessionView` retyped `Promise<LabSession>`) into the real `missionContract.ts`:
  **`2 failed, 7 passed`**. Restored byte-identically: **`9 passed`**. The control now
  pins all four shapes (bare accessor, mistyped view accessor, legitimate collection
  create, repaired view accessor).
- **registry literals** — the raw-literal scan asserts none remain, and the upstream
  detector's own control (`test_request_detector_is_not_trivially_true`) covers both the
  literal and template-literal shapes.
- **advertised contract** — the restored `NotYetWired` string is a served path
  (`/api/lab/engineering/sessions/{session_id}/transition`), so it adds no new drift.

### 5.1 A negative control that did not bite

The first cut of the bare-session detector matched on the **name** `getSession`:

```python
re.search(r"function\s+getSession\s*\([^)]*\)\s*:\s*Promise<\s*LabSession\s*>", source)
```

Measured: planting `Promise<LabSession>` on `getSessionView` left the suite at
**`9 passed`** — the guard stayed green on the exact mutation it exists to catch, because
it was looking for a name the repaired file no longer contains. It passed the live file
for the wrong reason. The detector is now **shape**-based (any function reading the view
endpoint while declaring a bare-session return), with the legitimate `createSession`
collection create explicitly excluded. This defect is recorded rather than quietly fixed
because it is the reason the control is now proven against the real mutation.

## 6. Regression comparison

Command (both trees, same environment, same session):

```
PYTHONPATH=archive/legacy_python python3 -m pytest tests/ -q -rEf --continue-on-collection-errors
```

`-rEf` is required: `-rf` alone drops pytest's `ERROR` lines and yields a **subset**
fingerprint.

Baseline — slice stashed (`git stash push -u`), clean tree, same session:

```
8 failed, 3509 passed, 17 skipped, 3 warnings, 1 error in 234.68s
```

With the slice restored:

```
8 failed, 3518 passed, 17 skipped, 3 warnings, 1 error in 232.86s
```

The failing/error **node set** is **identical** on both trees — 9 nodes, `diff` empty,
sha256 `0c1f3ada9df0918b0295494c45765d7d9e90e37bdfe7df1307f75a03904c93a3`:

```
ERROR   tests/test_autonomy.py
FAILED  tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED  tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED  tests/test_engineering_lab_api.py::test_public_authority_endpoints_are_dispositioned
FAILED  tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED  tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED  tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED  tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED  tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

The `+9 passed` is exactly the new nodes (`--collect-only tests/test_lab_mission_workspace_contract.py`
→ `9 tests collected`). Attribution is by node identity, never by count.

Two intermediate runs of this slice were **red** (10 then 11 nodes) while I was iterating:
the extra nodes were the two contract defects in §3, both since repaired. Those runs are
superseded by the measurement above and are recorded here rather than dropped.

## 7. Not claimed

- **Not merged, not deployed, not accepted.** The base branch is unchanged.
- The Gap 1 approval-perimeter work remains **uncommitted** in this tree and was not
  disturbed.
- The temporary verification harness and the `data/engineering_lab/` runtime artifact it
  produced were deleted; `git status` shows only the four intended changes plus the two
  new files.
- No production, Render, or Vercel action was taken.
