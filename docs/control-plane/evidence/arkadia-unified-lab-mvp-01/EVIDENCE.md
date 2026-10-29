# ARKADIA Unified Engineering Lab MVP — mission workspace vertical slice

**Status:** IMPLEMENTED · TESTED · REPORTED — **not merged, not deployed, not accepted.**
**Branch:** `feat/arkadia-unified-lab-mvp-01`
**Base revision:** `36f53be2` (`main`)
**Observed:** 2026-10-27

> **Corrected 2026-10-27.** The header previously named
> `gate-hygiene/lane-guard-fixed-scope-01` and base `389e3b39`. Both were stale: the slice
> was re-cut from `main` so its PR could be reviewed against its own scope, and `389e3b39`
> is not this branch's base. The measurements below were taken on the re-cut branch; the
> figures that moved are re-measured in §6.1.

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
| `tests/test_lab_mission_workspace_contract.py` | new — 14 contract tests (9 lifecycle + 5 resume) |

Second slice (2026-10-27, §6.2) — resume across a reload:

| Path | Change |
|---|---|
| `components/lab/missionContract.ts` | +`rememberMissionSession` / `forgetMissionSession` / `recallMissionSession`, uid-scoped |
| `components/lab/MissionWorkspace.tsx` | mount-confirmed resume offer; gates read `session.authorization_ref` |

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

### 6.1 Re-measured 2026-10-27 (supersedes the absolute figures in §6)

The figures in §6 were taken before this sandbox lost its Python dependencies mid-session
(`fastapi`, `pydantic`, `httpx`, `requests` disappeared, producing 111 collection errors).
They were re-measured after reinstallation, in the same environment for both arms:

```
main content  : 15 failed / 3447 passed / 30 skipped / 1 error   16 nodes  8ecf24ab…
WS3 branch    : 15 failed / 3446 passed / 30 skipped / 1 error   16 nodes  8ecf24ab…
NEW on branch: NONE     GONE on branch: NONE
```

The failing/error **node set is identical** (`8ecf24ab…`, 16 nodes), so the conclusion in
§6 is unchanged: zero regression attributable to this slice. The absolute counts differ
from §6 (`8 failed / 3509 -> 3518 passed`, 9 nodes, `0c1f3ada…`) because the dependency set
differs, not because the tree does. Compare node **identity**, never totals.

Two nodes named in §6 no longer exist under those names in the current environment
(`test_engineering_lab_api.py::test_public_authority_endpoints_are_dispositioned` and
`test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` appear in one
measurement and not the other); the node-set hash above is the authoritative comparison.

## 6.2 Resume across a reload — second slice (2026-10-27)

The first slice held its entire state in `useState`, so a page reload presented a
blank form while the substrate still held a live mission. Three facts were
measured against the running backend before any code was written, because each
one constrains what a resume is allowed to do:

| Claim | Measurement |
|---|---|
| a retained session survives a new client | same uid, **new token** → `200`, `READY_FOR_REVIEW`, 1 run, 13 events |
| a different operator is refused | different uid → **`404 session not found`** |
| a resumed session at the boundary cannot run again | re-execute → **`400 session must be AUTHORIZED or QUEUED to execute (currently READY_FOR_REVIEW); SESSION != AUTHORIZATION`**, runs still 1 |
| an authorization cannot be read back | `GET …/{id}/authorize` → **`405`**; `GET /authorizations` → **`404`**; session view has no `authorization` key; only `authorization_ref` survives |

The third and fourth rows are the load-bearing ones. Resume therefore restores
the session, its state and the substrate's own events **from the server**, and
deliberately does **not** restore an authorization: the original `originated_by`,
`operations_allowed` and duration are unknowable, so reconstructing the object
would assert `originated_by: "human"` on evidence the surface does not have —
inventing the exact claim the substrate exists to keep.

### 6.2.1 A defect in this slice's own first cut

`canAttempt` / `canAuthorize` were keyed off the local `authorization` object. A
resumed session carries `authorization_ref` while that object is empty, so
**step 3 would have executed successfully** and the surface would have reported
`BOUNDARY NOT ENFORCED` — a false alarm about a gate that held. That is worse
than a missed check: it destroys the operator's trust in the one signal that
matters. The gates now read `session?.authorization_ref`, i.e. the substrate's
own statement. Recorded rather than quietly fixed.

### 6.2.2 Verification

```
tests/test_lab_mission_workspace_contract.py     9 -> 14 passed
console-contract domain (52 files, derived)      820 passed
```

Negative controls, planted into the **real** file and reverted byte-identically:

| Planted defect | Result |
|---|---|
| reconstruct an authorization in `onResume` | `2 failed` (the contract test **and** its own control) |
| revert `canAttempt` to the local `authorization` object | `1 failed` |
| restored | `14 passed` |

Regression, same branch, same environment, before and after:

```
pre-resume : 15 failed / 3446 passed   16 nodes  8ecf24ab…
post-resume: 15 failed / 3451 passed   16 nodes  8ecf24ab…
NEW: NONE      GONE: NONE      collect: 3490 -> 3495 = +5 == the new tests
```

## 7. Not claimed

- **Not merged, not deployed, not accepted.** The base branch is unchanged.
- The Gap 1 approval-perimeter work remains **uncommitted** in this tree and was not
  disturbed.
- The temporary verification harness and the `data/engineering_lab/` runtime artifact it
  produced were deleted; `git status` shows only the four intended changes plus the two
  new files.
- No production, Render, or Vercel action was taken.


## 8. DEA-01 mission-state execution guard — 2026-10-29

**Move ID:** `DEA-01-MISSION-STATE-01`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Baseline latest observed commit:** `d9a16f1269b2ab8ce74b527b3f2f0f00ad2793c2` before branch creation.  
**Branch:** `feat/dea-01-mission-state-guard-01`  
**PR:** [#591 — fix(lab): make mission next action follow substrate state](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Code commit:** `9b5b55f567b4fd18e6b6c2b866c6589fca2b8d73`  
**Contract-test commit:** `a913dd2df0abad2317d7915b47dd4d7d7882a76f`  
**PR head at creation:** `a913dd2df0abad2317d7915b47dd4d7d7882a76f`

### Problem

The prior UI enabled Execute when a session had an authorization reference and no local run object, without checking the session's current state. Existing §6.2 evidence records that a resumed session at `READY_FOR_REVIEW` is rejected by the backend if executed again. The UI therefore offered an action the substrate would refuse.

### Bounded change

- Execution now requires the canonical state `AUTHORIZED` or `QUEUED`, the existing authorization signal, and no local run.
- A visible **Next decision** line is derived from the actual agent/session/run state.
- `READY_FOR_REVIEW` directs the operator to inspect recorded events and evidence and explicitly says that this session cannot execute again.
- Added a regression assertion in `tests/test_lab_mission_workspace_contract.py`.
- No backend, API, identity, authorization, provenance, WorkEvent, persistence, production, or deployment code changed.

### Verification and limitations

- Source mutation and regression-test addition were accepted by GitHub's file API.
- Local test/build commands and authenticated browser/device checks were not available in this connector-backed run; no local pass is claimed.
- PR CI must be read from the current PR head. Preview and production verification remain unclaimed.
- Human review, merge, and production authority remain final.


## 8.1 CI verification snapshot — 2026-10-29 21:23–21:26 UTC

**Observed PR head:** `158b3f48277de994442074df224e6c5e6d3420d3`  
**PR:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)

### Completed checks

| Workflow / command | Run or job | Observed result |
|---|---|---|
| `python -m pytest -q $(python scripts/console_contract_domain.py)` | Prism Console Contract run `40957276646`, job `123740508728` | **945 passed in 25.18s** |
| `python -m pytest tests/test_prism_console_ci_wiring.py -q` | Same job | **30 passed in 3.33s** |
| Build Arkadia Console | `SG-02-FE.2-V` run `40957276506`, job `123740507581`, step 6 | **Completed / success** |
| CP10-A Lab tests | Same SG-02 job, step 19 | **Completed / success** |
| SolSpire isolated runtime and integration contract tests | Same SG-02 job, step 20 | **Completed / success** |
| `security-secret-scan` | Run `40957276491` | **Success** |
| `Boot Syntax Boundary` | Run `40957276859` | **Success** |
| `Operator Console Posture Currency` | Run `40957276303` | **Success** |
| `Canonical Render Runtime Probe` | Run `40957276298` | **Success** |
| `N-ATLAS provider forensics` | Run `40957276445` | **Success** |
| `N-ATLAS external beta validation` | Run `40957276595` | **Success** |
| `N-ATLAS Developer Lab` | Run `40957276921` | **Success** |
| `economic-seam-engine` | Run `40957276873` | **Success** |

The derived console-contract domain includes `tests/test_lab_mission_workspace_contract.py` because the domain derives tracked test modules from the active-console path needles. The new review-boundary regression assertion was therefore included in the 945-test run.

### Still unverified at this snapshot

- `SG-02-FE.2-V` run `40957276506` remained **in progress**; its CP10-B broader backend regression step was running. CP10 API verification and authenticated browser route verification had not started at the last step inspection.
- A successful canonical runtime probe does not prove this PR is deployed or that production reflects its code.
- No manual desktop/mobile interaction or preview acceptance is claimed.

This snapshot records results observed on the stated head. Any subsequent evidence-only commit causes CI to evaluate the new PR head again; the results above are not represented as checks on that future head.


## 8.2 Mission scope preview and intent lock — 2026-10-29 21:32 UTC

**Move ID:** `DEA-01-SCOPE-INTENT-01`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Existing PR updated:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Baseline PR head:** `5b6ca321b31f967fe9fb11bd65fb47b954932e43`  
**Implementation commit:** `1f769909f989d11d578269b038407710ff3109c7`  
**Contract-test commit:** `ef825a22ee213074041a569a7d150fa86a785cb7`

### Problem and bounded change

The mission form allowed the objective and read targets to change after the server had created a session. The execute request uses current form values, while the persisted session records the objective supplied at creation; changing inputs afterward could make the visible intent drift from the session's original intent.

- Added a responsive, source-derived scope preview for intent, selected role, read targets, operation ceiling, and human gate.
- The preview explicitly says it is a local draft, not a backend-generated plan or evidence; after session creation it shows the server-confirmed session ID.
- Intent and target inputs lock after session creation to prevent post-creation scope drift.
- Mission creation requires a non-empty objective and at least one read target.
- Added a source-level regression contract test for the preview, draft truthfulness, input lock, and read-only request ceiling.
- No backend, canonical API, identity, authorization subsystem, provenance, WorkEvent, workspace, persistence schema, production configuration, merge, or deployment changes.

### Verification snapshot before this change

At baseline head `5b6ca321b31f967fe9fb11bd65fb47b954932e43`, PR workflow runs returned completed/success for: Canonical Render Runtime Probe `40957961284`, N-ATLAS provider forensics `40957961324`, economic-seam-engine `40957961278`, N-ATLAS external beta validation `40957961537`, Operator Console Posture Currency `40957961611`, Boot Syntax Boundary `40957961405`, security-secret-scan `40957961253`, Prism Console Contract `40957961519`, N-ATLAS Developer Lab `40957961558`, and SG-02-FE.2-V `40957961733`.

Those results apply to the baseline head only. This implementation commit and the following contract-test commit require fresh CI on the final PR head. No local build, local pytest, authenticated browser, responsive device, preview, or production verification is claimed from this connector-backed run.

### Remaining acceptance gaps

- Await fresh CI on the final PR head.
- Authenticated browser verification of the new scope preview at desktop and mobile widths remains UNKNOWN.
- Preview and production verification remain unclaimed.
- Human review/merge and production authority remain final.


## 8.3 Resume scope continuity — 2026-10-29 21:43 UTC

**Move ID:** `DEA-01-RESUME-SCOPE-02`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Existing PR updated:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Baseline head:** `406f8c4eea066a5fb4b182a41a99fa54d03d8456`  
**Implementation commits:** `59b3c70028273342812f24fe2d6a4e48e931365c` (resume hint), `c4a3b7175c7620cb058eaa640c4e7858bad3e1aa` (resume UI)  
**Contract-test commit:** `62540aedcf490801c7e8153a8b5b21aac14ac9c4`

### Problem and bounded change

The existing resume hint stored only a session ID. The server session view returns the persisted objective but does not return the original read-target list. After reload, the UI could therefore show the default objective/README target and offer an execution scope that did not match the original mission.

- Extended the existing uid-scoped localStorage resume hint to include the objective and read-target list; no new store or tracker was added.
- Resume re-reads the session and uses the server-returned objective as authoritative.
- Read targets are restored only from the existing local hint and explicitly labeled as local, not server-confirmed.
- Legacy raw session-ID hints remain readable.
- If no saved target hint exists, the target list is blank and authorization/execution affordances remain disabled; the UI does not silently substitute `README.md`.
- Added a source-level regression contract test for server-first intent, local target hints, legacy compatibility, and fail-closed behavior.

### Verification

- Implementation and contract-test changes are committed on the existing PR branch; fresh CI is required on the resulting head.
- No local build/pytest or authenticated browser/device run is claimed from this connector-backed execution.
- No backend, canonical API, identity, authorization subsystem, provenance, WorkEvent, workspace, database, merge, or production deployment changes.
- Desktop/mobile behavior and preview/production verification remain UNKNOWN / unclaimed.


## 8.4 CI finding and source-contract correction — 2026-10-29 21:49 UTC

**Affected PR head:** `953bd71444eda4580de4e7fdcf14b99ca0ac7d10`  
**Workflow:** [Prism Console Contract run 40960749813](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40960749813)  
**Job:** `123752552174`  
**Observed result:** `3 failed, 944 passed in 32.63s`.

The three failures were stale source-contract assertions after the intended scope-safety change:
- expected `canExecute` without the new non-empty-target guard;
- expected `setResumable(view.session.session_id)` rather than the server-confirmed object carrying the local scope hint;
- expected `canAttempt` / `canAuthorize` without the non-empty-target guard.

The code paths were changed intentionally to prevent execution or authorization with an unknown/empty target scope. The assertions have now been updated to pin those stricter conditions and the object-shaped, server-confirmed resume offer.

**Correction commit:** `d6d66553634737c8117830e03aa0c8440018065b`  
**Verification:** fresh CI required on the new head; no pass is claimed from the failed run. The independent runtime probe and other completed workflow checks at the affected head were successful, but they do not replace the contract suite.

No production, backend, identity, authorization subsystem, canonical API, merge, or deployment action occurred.

## 8.5 Resume Mission Control context — 2026-10-29 22:02 UTC

**Move ID:** `DEA-01-RESUME-AGENT-CONTEXT-01`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Existing PR updated:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Baseline head:** `6984d2b9a1d1c299e68295d083ef9350f432b3c9`  
**Implementation commit:** `ffcad3d06b986834e34e05cf32e8c23ae7e4c8dc`  
**Regression-test commit:** `0475e195dd893ded648ecbfb00bb97bfb46d21dc`

### Defect and bounded repair

On resume, `MissionWorkspace` re-read the session from the canonical session-view endpoint and restored the session, objective, target hint, events and last run, but did not restore the session's server-returned `agent_id` into the local view state. The state-derived Next decision checks `!agentId` before `!session`, so a valid resumed mission could incorrectly tell the operator to deploy an agent instead of describing the active mission's next decision.

- Resume now sets the local agent context from `view.session.agent_id`.
- This is session context only. It does not restore or manufacture an authorization object, change the backend, or grant capabilities.
- Added `test_resume_restores_server_confirmed_agent_context` to the existing mission workspace contract suite.
- Updated this existing PR; no competing branch or PR was created.

### Verification and limitations

- GitHub Contents API accepted both source and test updates on `feat/dea-01-mission-state-guard-01`.
- The existing evidence record was updated through the same PR branch.
- Fresh CI must be checked against the final PR head after these commits. No local pytest/build or authenticated browser run is claimed.
- Desktop/mobile interaction, preview acceptance and production verification remain UNKNOWN / unclaimed.
- No merge, deployment, backend change, protected-boundary change, or production configuration change occurred.

## 8.6 Mission-first Engineering Lab composition — 2026-10-29 22:08 UTC

**Move ID:** `DEA-01-LAB-MISSION-FIRST-01`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Existing PR updated:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Baseline code/test head:** `d9325478a2d4a65ebd3051c56d536580703d4127`  
**Page composition commit:** `ad83909e19afee74bef588035c9c0cf8cf6f08c4`  
**Mission label commit:** `e1f49a7e291fa05e8bd6e8ebdc263ef9c0507e53`  
**Regression-test commit:** `ad0bf651b8b48927d5ff56f426d7a45aae1cd34b`

### Problem and bounded integration

The served Engineering Lab page mounted overview, operational surfaces, the loop, provider state and authority readings before the MissionWorkspace, then rendered the remaining technical surfaces as one uninterrupted sequence. The primary governed mission path was therefore below several technical panels.

- Moved MissionWorkspace to the first content position beneath the Engineering Lab page heading.
- Renamed its visible section heading to **Mission Control**.
- Grouped the existing overview, provider, authority, session, artifact, agent, model, automation and not-yet-wired surfaces in a native, keyboard-accessible `<details>` disclosure titled **Engineering evidence & diagnostics**.
- Kept all existing components, routes, API contracts, and truthful state handling. No backend, persistence, authorization, identity, or production changes.
- Added `test_engineering_lab_leads_with_mission_control_and_discloses_diagnostics` to assert the primary ordering and continued reachability of the existing surfaces.

### Verification snapshots and freshness

On the immediately preceding code/test head `d9325478a2d4a65ebd3051c56d536580703d4127` (before this layout move):
- Prism Console Contract run [40962930190](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40962930190): `python -m pytest -q $(python scripts/console_contract_domain.py)` — **948 passed in 35.14s**.
- Same run/job: `python -m pytest tests/test_prism_console_ci_wiring.py -q` — **30 passed in 4.45s**.
- SG-02-FE.2-V run [40962930365](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40962930365): **Build Arkadia Console** and **CP10-A Lab tests** steps reported success; **CP10-B broader backend regression** was still running at last observation.
- Canonical Render Runtime Probe run [40962930145](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40962930145), security-secret-scan run `40962930066`, and Boot Syntax Boundary run `40962930117` reported success on that head.

These are explicitly prior-head results and do **not** verify the layout change. Fresh CI is required on the final head created by this evidence update. No authenticated browser, responsive-device, preview, or production verification is claimed.

### Remaining acceptance gaps

- Fresh final-head console contract, build, and broader regression checks.
- Authenticated browser verification of mission-first composition and disclosure behavior at desktop/mobile widths.
- Preview verification and live revision confirmation.
- Human review/merge and production authority remain final.

## 8.7 Final-head CI and runtime boundary snapshot — 2026-10-29 22:12 UTC

**Code/test/evidence head checked:** `3c45818375346860cfd334ea72d0567d2b0d2743`  
**PR:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)

### Checks observed on head `3c458183`

- Prism Console Contract run [40963717103](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40963717103), job `123762752659`:
  - `python -m pytest -q $(python scripts/console_contract_domain.py)` — **949 passed in 37.54s**.
  - `python -m pytest tests/test_prism_console_ci_wiring.py -q` — **30 passed in 5.53s**.
- SG-02-FE.2-V run [40963716864](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40963716864): **Build Arkadia Console** and **CP10-A Lab tests** steps succeeded. **CP10-B broader backend regression** was still in progress at this snapshot; CP10 API and browser route verification had not yet started.
- These workflows reported success on the same head: Canonical Render Runtime Probe `40963716740`, security-secret-scan `40963716795`, Boot Syntax Boundary `40963716704`, N-ATLAS provider forensics `40963717031`, N-ATLAS external beta validation `40963716718`, economic-seam-engine `40963716904`, Operator Console Posture Currency `40963716950`, and N-ATLAS Developer Lab `40963716863`.

### Production / preview boundary

Read-only Render inventory observed service `srv-db49jbh42hec73aj84qg` (Arkadia, branch `main`, automatic deploy on commit, preview generation off, pull-request previews disabled). Latest listed live deployment was `dep-dbhr75bvnpks73f00n6g`, commit `d9a16f1269b2ab8ce74b527b3f2f0f00ad2793c2`, finished `2026-10-29T21:00:00.778943Z`. The PR head is not deployed; no production deploy was triggered.

This evidence append creates a new PR head. The test/build results above are tied to `3c458183`; fresh checks on the evidence-only successor head are required before treating that successor as fully checked. No authenticated browser, desktop/mobile, preview, or production acceptance is claimed.

## 8.8 Session evidence and artifact projection — 2026-10-29 22:18 UTC

**Move ID:** `DEA-01-SESSION-EVIDENCE-01`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Existing PR updated:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Baseline head:** `09d880eb4c3979ea55ac38cd96eaead4f7b2bc5a`  
**Implementation commit:** `2702b1c34d37f3a7b22de460b1845a2626089891`  
**Regression-test commit:** `85f43a3b023348e86cfc4993160720bc1a2d5d21`

### Problem and bounded repair

The canonical `GET session view` contract returns server-filtered `evidence` and `artifacts` linked to the session's runs. Before this move, MissionWorkspace consumed the session, events and last run, but did not project the returned evidence records or artifacts into the primary mission surface. A run could show evidence references without making the linked server records and provenance inspectable in Mission Control.

- Added state for server-returned evidence and artifacts; refresh and resume both apply the same canonical session-view response.
- Added a compact **Recorded evidence & artifacts** panel showing actual IDs, state, summary, run reference, timestamp, provenance/detail, artifact metadata and returned content.
- Added distinct `IDLE`, `LOADING`, `LIVE`, `EMPTY`, `UNAVAILABLE` and `FAILED` states. Missing fields are labeled unavailable rather than replaced with synthetic values.
- Added a refresh action that re-reads the existing session-view endpoint.
- Added `test_mission_control_reads_server_evidence_and_artifacts_with_truthful_states`.
- No new endpoint, backend route, persistence, database, authority, or protected-boundary change.

### Verification freshness

The prior head `09d880eb4c3979ea55ac38cd96eaead4f7b2bc5a` passed the console contract domain (**949 passed in 42.91s**), CI-wiring guard (**30 passed in 4.45s**), console build and CP10-A Lab test step. Those results predate this evidence-panel change and are not claimed as its verification. Fresh CI is required on the successor head after this evidence append.

### Remaining acceptance gaps

- Fresh console contract/build and broader backend regression for the evidence-panel code.
- CP10 API and authenticated browser route verification; desktop/mobile responsive behavior remains unverified.
- Preview unavailable because Render pull-request previews are disabled; production remains on main revision `d9a16f1269b2ab8ce74b527b3f2f0f00ad2793c2`.
- Human review/merge and production authority remain final.

## 8.9 Evidence panel contract hardening — 2026-10-29 22:21 UTC

**Move ID:** `DEA-01-SESSION-EVIDENCE-01` (continuation)  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Existing PR updated:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)  
**Baseline head:** `5d8a53ec68d2326332a80db08b7fc0b236d7d5b5`  
**Panel wrapper correction:** `0e4df9e41c9d07516b0c281879d091fa8c6e22bf`  
**Missing-vs-empty state correction:** `81e793722089b30142b962443a25e573273dcc8e`  
**Regression-test update:** `a92a8a9ce12a0a015ffd836fae962f5e71446263`

### Corrections after diff inspection

- The shared `Panel` component accepts only `children` and `className`; the evidence test ID is therefore placed on a native wrapper rather than passed as an unsupported prop.
- Because the session-view contract types `evidence` and `artifacts` as optional, missing collections are now `UNAVAILABLE`, not falsely presented as `EMPTY`. If one collection is returned with records while the other is missing, the available records remain visible with an explicit partial-response warning.
- Extended the source-contract test to pin both conditions.

### Verification

- GitHub Contents API accepted the source and test updates on the existing PR branch.
- Fresh CI is required on the successor head after this evidence append. No build/test pass is claimed for the evidence panel or its state corrections yet.
- No backend/API, persistence, identity, authorization, provenance schema, WorkEvent, production configuration, merge, or deployment change.

## 8.10 Resume contract assertion updated after evidence projection — 2026-10-29 22:24 UTC

**Move ID:** `DEA-01-SESSION-EVIDENCE-01` (regression-test correction)  
**Failed-test head:** `45b0e0cf6985000d1bdad3b8e40dda8addc88f99`  
**Test correction commit:** `0ec1dbc96490550b0fa02e641192301cf146ecbd`

The first fresh Prism Console Contract run on `45b0e0cf` reported **1 failed, 949 passed in 37.67s**. The failure was `test_resume_never_reconstructs_an_authorization`: its source assertion required `setSession` to appear directly in the resume handler. The implementation now delegates session application to `applySessionView(view)`, which still calls `setSession(view.session)` and applies the canonical server-returned evidence/artifacts without reconstructing authorization.

Updated the assertion to require both `applySessionView(view)` and `getSessionView`, preserving the actual invariant: resume must re-read and apply server state and must not reconstruct authorization. This was a stale test assertion caused by the refactor, not evidence of an authorization regression.

Fresh CI is required on the successor head after this evidence append. No merge or deployment occurred.



## 9. DEA-01 mission scope capture closure — 2026-10-29

**Move ID:** `DEA-01-MISSION-SCOPE-CLOSURE-01`  
**Canonical directive:** [Issue #590](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/590)  
**Baseline head:** `086b283cb9e748e1fddf393dc8be37dd0c032ca6` on `feat/dea-01-mission-state-guard-01` (PR #591).  
**Observed:** 2026-10-29 22:36 UTC.

### Problem

Fresh inspection found that `onCreateSession` used `targetList` and `refreshView` but its `useCallback` dependencies were only `[agentId, objective, note, uid]`. If the operator changed targets after the agent was created, the retained callback could persist an earlier target list into the uid-scoped resume hint. The served session view does not return original targets, so this hint is the only scope continuity available to the UI; stale scope would make refresh/re-entry misleading.

### Bounded change

- Memoize parsed targets from the editable `targets` input with `useMemo`.
- Include `targetList` and `refreshView` in the session-creation callback dependencies.
- Add a source-contract regression test that pins both the target-input dependency and persisted current scope.
- No backend/API, identity, authorization, provenance, WorkEvent, workspace, persistence contract, production configuration, or deployment changes.

### Verification

- Before this change, commit `086b283cb9e748e1fddf393dc8be37dd0c032ca6` had 16 successful GitHub check runs, including **Prism Console Contract** (run `40965521458`, completed `2026-10-29T22:25:18Z`) and **SG-02-FE.2-V** (run `40965521534`, completed `2026-10-29T22:28:26Z`). These are baseline results only and do not verify this change.
- New branch-head CI is required after this commit. No local test/build or authenticated browser/device run is claimed from this connector-backed execution.
- Not merged, not deployed, not accepted.


### Pre-CI correction — same move

Post-write inspection found two separate over-escaping defects in the first draft. Commit `e6262e05587c6b183524a5fcc94962166777d4f8` corrected the TypeScript target separator, but its source-contract regex still failed. The failure was observed in Prism Console Contract run `40967600085` (1 failed, 950 passed in 37.26s). Commit `1cdc797a2916938d685971d1e93c37489372f6b4` replaced that regex with scoped string assertions; only the current-head checks below are evidence for the corrected test.

### CI result and guard correction — 2026-10-29

On commit `e6262e05587c6b183524a5fcc94962166777d4f8`, Prism Console Contract run `40967600085` reported **1 failed, 950 passed in 37.26s**. The failing assertion was the new scope-closure regression test's over-escaped regular expression; it did not indicate a runtime or backend failure. Replaced that expression with scoped source assertions for the memoized target block, persisted target list, and callback dependencies. The next branch-head CI run is the verification authority for this correction.
### Current-head verification snapshot — 2026-10-29

**Code/test head:** `1cdc797a2916938d685971d1e93c37489372f6b4`  
**PR:** [#591](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/591)

- Prism Console Contract run [`40968707631`](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40968707631): **951 passed in 32.62s**; the same job's CI-wiring guard passed **30 in 4.29s**.
- SG-02-FE.2-V run [`40968707623`](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40968707623): **Build Arkadia Console**, **CP10-A Lab tests**, and **SolSpire isolated runtime/integration contract tests** passed.
- At this snapshot, **15 of 16** checks had succeeded and SG-02-FE.2-V remained in progress at **CP10-B broader backend regression**. CP10 API verification and CP10 browser-route verification had not started.
- Other completed checks on this head included frontend/backend jobs, canonical container-image build, self-host image build, boot-syntax, full-history secret scan, provider forensics, and the read-only production probe. Their success is CI evidence only, not production deployment or browser acceptance.
- The evidence-only follow-up commit will trigger a fresh check set. No merge, production deployment, or protected-boundary change occurred.
