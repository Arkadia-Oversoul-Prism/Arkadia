# Arkadia One — live console walkthrough (read-only)

**Date:** 2026-10-28
**Scope:** read-only observation of the canonical deployment. No mutation, no merge, no deploy.
**Authorization:** sovereign ("You are authorised to proceed"), covering inspection and evidence only.

---

## 1. Entry point — resolved

**The correct operator entry point is `/`, not `/operator`.** This corrects the earlier
suggestion that `/operator` is the unified console.

`api/frontend_routes.py` mounts **two distinct applications** on the one canonical origin:

| Path | Application | Source | Surfaces |
|---|---|---|---|
| `/` (+ `/novanet`, `/arkana`, `/solariun`, `/engineering-lab`, `/enterprise`, `/knowledge`, `/weaver`, `/about`, `/login`) | **Arkadia Console** — the unified console | `web/arkadia_console` | 9 declared + sign-in |
| `/operator` (+ `/operator/inspector`, `/work`, `/authority`, `/mie-lab`, `/security-verification`) | Boundary / authority inspector | `web/console` | 7 |
| `/n-atlas-lab`, `/n-atlas-tester` | N-ATLaS tester (same operator bundle) | `web/console` | 1 |

Observed live: `/` serves `assets/index-01x4UK2n.js` (195,604 B); `/operator` serves
`/operator/assets/index-BkqSAT5t.js` (241,914 B). Two separate bundles, two separate apps.

**Open it at:** `https://arkadia-qzu4.onrender.com/`

### Deployment identity — VERIFIED

```
GET /api/version -> source_revision 9195334c6baba0b9349a1d931bc5773614944cd1
                    revision_source RENDER_GIT_COMMIT
                    revision_conflict false
git rev-parse main -> 9195334c6baba0b9349a1d931bc5773614944cd1
```

Deployed revision **equals** current `main`. The reconciled PRs are in production.

| PR | Merge commit | On main |
|---|---|---|
| #582 Re-cut the stranded console UI | `960ce6c9` | yes |
| #578 Engineering Lab mission workspace | `9472cebf` | yes |
| #581 Bind approval to the operation | `bd1a453a` | yes |

Open PRs: **0**. So "the merging of all the PRs" is complete; nothing is pending.

### Served bundle carries the recovered UI — VERIFIED

Fixed-string markers in the served console bundle (env-injection robust, unlike asset hashes):

| Marker | Count |
|---|---|
| `Technical operations: task state, provider status` | 1 |
| `Mission workspace` | 1 |
| `This surface reads protected contracts` | 1 |
| `Encyclopedia Galactica` | 7 |
| `Surface scaffolded` | 1 |
| `Personal workspace and cognitive canvas` | 1 |

Negative control: `public_prism` -> 0 (retired build input absent).

---

## 2. Surface-by-surface — what the live console actually shows

Every surface was loaded in a browser against the canonical origin.

| Surface | Path | Anonymous state | Live evidence |
|---|---|---|---|
| Home | `/` | renders | Runtime block reads `9195334c…`, `one_reconciled_deployment`, `conflict: false` |
| NovaNet | `/novanet` | renders, real data | 1 transmission; 4 lenses; **651 public echoes** with honest "Showing 8 of 651" |
| Arkana | `/arkana` | composer renders; chat **works** | `POST /api/commune/resonance` -> 200, reply + `resonance 0.93` + 3 RAG refs + sources |
| Solariun | `/solariun` | **auth threshold** | protected |
| Engineering Lab | `/engineering-lab` | **auth threshold** | protected |
| SolSpire | `/enterprise` | **auth threshold** | protected (note: not `/solspire` — reserved API namespace) |
| Knowledge OS | `/knowledge` | **auth threshold** | protected |
| Weaver | `/weaver` | **auth threshold** | protected |
| About | `/about` | renders | full product-boundary + principles list |
| Sign in | `/login` | renders | real email/password form |

**The auth threshold is a real boundary, not a cosmetic redirect.** Protected surfaces render
`Protected surface / Sign in to continue` with no content behind it.

### Identity provider is genuinely wired — VERIFIED

`firebase-config.js` is injected at container start with a real public config
(`projectId arkadia-2d4a7`). A deliberately invalid credential is **refused by Google**:

```
POST identitytoolkit accounts:signInWithPassword
-> HTTP 400 {"message":"INVALID_LOGIN_CREDENTIALS"}
```

A decorative form could not produce a provider-side refusal. Sign-in is real; it requires a
real Arkadia account. **No test/demo credentials exist in the repository**, so the six
protected surfaces could not be walked with an authenticated identity in this pass.

---

## 3. Backend contract — declared vs served

`web/arkadia_console/src/lib/endpoints.ts` declares **35** paths.

**34 of 35 resolve on the live `app.openapi()`.** The single "miss" is a regex artifact
(`/canvas`), not a defect: the real route `/api/lab/engineering/canvas/{artifact_id}` is
served, and `labCanvas()` derives it correctly from the artifacts collection.

| Probe | Result |
|---|---|
| `GET /api/version` | 200 |
| `GET /health` | 200 `{"status":"radiant"}` |
| `POST /api/commune/resonance` | 200 (real reply) |
| `GET /api/transmissions` | 200 |
| `GET /api/echoes` | 200 |
| `GET /api/codex` | 200 (651 docs) |
| `GET /api/stellar-cartography` | 200 |
| `GET /api/knowledge/status` | 200 |
| `GET /api/knowledge/graph` | 200 |
| `POST /api/knowledge/search` | 200 (semantic hits) |
| `GET /api/lab/engineering/n-atlas/catalog` | 200 `configured:true status:AVAILABLE` |
| `GET /api/me`, `/api/me/*` | 401 (protected) |
| `GET /api/lab/engineering/*` | 401 (protected) |
| `GET /solspire/*` | 401 (protected) |
| `GET /api/approvals` | 401 (protected) |
| `GET /api/tts/status` | 200 — `engine: edge_tts`, `elevenlabs_active: false` |

`/api/commune/resonance` is **POST-only** (a GET 404 is not a defect).
`/api/arkana/threads` and `/api/codex/categories` are **absent** from the live schema — the
console does not call them (it uses `/api/commune/threads` and derives categories), so they
are correctly avoided rather than broken.

### Anonymous Knowledge OS reads — shared tier, not a leak

`GET /api/knowledge/status|graph` answer without an identity. The handlers use
`_optional_user_id()` (never raises), and `knowledge/graph.py::accessible_note_ids(None)`
selects `WHERE user_id IS NULL`. Measured: **42 nodes, owner histogram `{None: 42}`** — the
shared tier only. No private note is exposed anonymously.

Recorded observation (not a defect claim): `vault.embeddings: 0`, `pending_embeddings: 42`,
`graph.edges: 2` for 42 notes — the embedding pass has not completed on the deployed store.

---

## 4. Engineering Lab mission lifecycle — source-verified, UI-unwalked

`MissionWorkspace` is a real vertical slice wired to real endpoints, all of which are served:

```
POST /api/lab/engineering/sessions                          -> PROPOSED
POST /api/lab/engineering/sessions/{id}/authorize           -> AUTHORIZED
POST /api/lab/engineering/sessions/{id}/execute             -> READY_FOR_REVIEW
GET  /api/lab/engineering/sessions/{id}                     -> resume
```

The refusal-before-authorization path is asserted in source
(`"session must be AUTHORIZED or QUEUED to execute"`, `tests/test_lab_mission_workspace_contract.py:94`),
and the terminal state is rendered as a **proposal awaiting review**, never success.

Measured test result (dependencies installed: fastapi, requests, cryptography, pyyaml, httpx):

```
tests/test_lab_mission_workspace_contract.py
tests/test_canonical_frontend_routing.py
tests/test_console_endpoint_registry_contract.py
tests/test_console_legacy_route_coverage.py
tests/test_console_shell_nav_contract.py
tests/test_prism_console_ci_wiring.py
tests/test_aeas05_canonical_frontend_acceptance.py
tests/test_prism_home_entry_contract.py
-> 143 passed
tests/test_tool_execution_perimeter.py tests/test_console_authority_chain.py
-> 49 passed
```

**Limitation:** the mission lifecycle was **not** driven in the live UI, because it is behind
authentication and no credential was available. This is `UNKNOWN`, not `FAILING`.

---

## 5. Defect found — the `/operator` console makes claims that are now false

> **Status: REPAIRED.** This section is the *pre-repair* measurement, retained as
> provenance. The repair, its guard and its CI wiring are §9–§14. Read this section as
> what was found, not as current state.

`web/console` is a **second, unreconciled** application whose data is hardcoded, not read from
the substrate. Its own README says it was derived from `RECONCILED-BOUNDARY-MAP-01.md`, and the
map "has veto power". The map has since been overtaken by events:

| Location | Claim rendered live | Measured reality |
|---|---|---|
| `Layout.tsx:71` | `ae847dd · reconciled` | `main` is `9195334c`; `ae847dd` is an **ancestor**, not current |
| `approvalNotExecution.ts:27-29` | `deployed: false`, "NOT DEPLOYED; the live host still runs the pre-hardening collapse" | `api/approval_routes.py:212` "Does NOT execute the tool" **is on `main`**; `ae847dd` is an ancestor; live `POST /api/approvals/{id}/approve` is served |
| `executionNotWorkEvent.ts`, `workeventNotEvidence.ts`, `evidenceNotVerification.ts` | `deployed: false`, "NOT DEPLOYED; production UNVERIFIED" | the routes these describe are served on the live host |

This matters because the operator console's whole value proposition is truthful posture. A
surface that under-claims is not "safe by default" — it is **wrong**, and it contradicts the
primary console on the same origin.

The primary console (`web/arkadia_console`) is the one to trust: it reads live contracts and
its runtime block reports the true revision.

---

## 6. What is left — bounded gap list

| # | Gap | Evidence | Classification |
|---|---|---|---|
| G1 | **No operator credential exists**, so 6 of 9 surfaces were never seen authenticated | no test account in repo; Firebase refuses invalid creds | BLOCKED on human |
| G2 | `/operator` rendered stale, false posture claims | §5 | **REPAIRED** — §9–§14 (not deployed; no production acceptance claimed) |
| G3 | Solariun `memory` lens + Weaver `LabWorkLoop`/`ApprovalLedger` unverified in UI | behind auth | BLOCKED (G1) |
| G4 | SolSpire: 4 declared contracts unwired (`/solspire/proposals`, `workevents`, `enterprise/workspaces`, `voice/events`) | `NotYetWired` in `SolSpirePage.tsx:48-62` | PARTIAL by design |
| G5 | NovaNet Nexus Hub sub-views (IMS, Grove, Larder, distribution) unreconciled | `NotYetWired` `NovaNetPage.tsx:283` | PARTIAL by design |
| G6 | Lab mutating acts unwired (transition, run-agent, merge, deploy) | `NotYetWired` `EngineeringLabPage.tsx:81` | PARTIAL by design |
| G7 | Knowledge embeddings incomplete: 0 embeddings / 42 pending, 2 edges / 42 notes | live `/api/knowledge/status` | OBSERVED |
| G8 | No governed OpenHands / OpenClaw worker in the console | `grep` finds zero references in either frontend | MISSING (the Arkadia One vision item) |

---

## 7. Answers to the four questions asked

1. **Unified navigation — YES.** One shell, one nav, 9 surfaces, one canonical backend. Real
   navigation, not a landing page linking to separate apps.
2. **System surfaces — accessible / partial / missing.** Accessible and rendering: Home,
   NovaNet, Arkana, About. Accessible behind a real threshold: Solariun, Engineering Lab,
   SolSpire, Knowledge OS, Weaver. Partial by explicit design: the `NotYetWired` contracts
   (G4–G6). Missing: governed external workers (G8).
3. **Operational reality — mostly real.** Arkana returns genuine model output with RAG
   provenance. NovaNet and Knowledge OS read real stores. Auth is a genuine provider boundary.
   What is *not* proven: any authenticated surface, because no credential exists (G1).
4. **What's left — see §6.** The single highest-value bounded action is **G1**: supply an
   operator credential so the six protected surfaces can be walked. Everything else in the
   list is either by-design scaffolding or a small bounded repair (G2).

## 8. Non-claims

- Production **acceptance**: NOT CLAIMED.
- Authenticated behaviour of any surface: **UNKNOWN** (no credential).
- The mission lifecycle in the live UI: **UNKNOWN** (source- and test-verified only).
- G2's repair: **proposed, not performed** — discovery does not authorize mutation.

---

## 9. G2 — the operator console's claims were bound to nothing (REPAIRED)

**Date:** 2026-10-28 · **Base:** `9195334c` · **Branch:** `evidence/arkadia-one-console-walkthrough-01`

The read-only walkthrough found the operator console's stale revision. Following it
established that the stale revision was the **least** significant defect: the console's
claims were bound to no substrate at all, so three drifts had accumulated.

### 9.1 A frozen revision

`ae847dd · reconciled` was hardcoded in three files:

| File | Line |
|---|---|
| `web/console/src/components/Layout.tsx` | 71 |
| `web/console/src/lib/standing.ts` | 53 |
| `web/console/src/lib/grammar.ts` | 104 |

`git merge-base --is-ancestor ae847dd HEAD` → **true**, so it is an ancestor of `main`,
not the running revision. Measured live, the runtime reports
`source_revision 9195334c6baba0b9349a1d931bc5773614944cd1`. The stamp therefore
misreported every deployment after `ae847dd`.

### 9.2 The console contradicted itself — four false `deployed: false` flags

All four boundary instances carried `deployed: false` with "NOT DEPLOYED; the live host
still runs the pre-hardening collapse", while `standing.ts` in the **same bundle** said
"Boundary changes — DEPLOYED ... production-verified by F.1–F.4". One app, two opposite
claims about the same boundaries.

Measured against the live `/openapi.json`, **every surface the four instances name is
served**:

| Boundary instance | Declared surfaces | Live |
|---|---|---|
| `approvalNotExecution.ts` | `POST /api/approvals/request`, `POST /api/approvals/{id}/approve`, `POST /api/tools/{tool_name}/run` | all present |
| `executionNotWorkEvent.ts` | `POST /api/tools/{tool_name}/run`, `POST /api/job/create`, `GET /api/jobs`, `POST /solspire/workevents` | all present |
| `workeventNotEvidence.ts` | `POST\|GET /solspire/workevents`, `GET /solspire/workevents/{work_event_id}` | all present |
| `evidenceNotVerification.ts` | `GET /solspire/enterprise/workspaces/{enterprise_id}/control-room` | present |

So the four `deployed: false` flags were false. Corrected to `deployed: true`;
`productionVerified` stays `false` — no operator credential exists to verify the
separation as an authorized principal. That distinction is preserved, not collapsed.

### 9.3 The boundary itself moved — the superseded premise

`executionNotWorkEvent.ts` asserted "there is no durable execution → WorkEvent identifier
and no code path that would create one", citing
`test_workevent_model_has_no_execution_or_job_reference_field`.

**That test exists at no revision.** `grep -rn` over the whole tree returns 0, and
`git log --all -S` matches only commits that introduced and then superseded the phrasing.
What exists is its **opposite**:

```
tests/test_execution_workevent_boundary.py:222
def test_workevent_model_has_explicit_execution_causal_reference():
    fields = set(_wem.WorkEvent.__dataclass_fields__.keys())
    assert "execution_attempt_ref" in fields
```

Because PR #294 (`abac77db`, 2026-10-05, ancestor of `main`) added the bridge:

- `solspire/workevent_manager.py:39` — `WorkEvent.execution_attempt_ref: str | None`
- `solspire/workevent_manager.py:101` — unique index `idx_work_events_execution_attempt`
- `solspire/workevent_manager.py:220` — `get_by_execution_attempt()`
- `weaver/execution_workevent_bridge.py` — `capture_execution_workevent()`, one WorkEvent
  per terminal execution attempt
- `weaver/enterprise_orchestration.py:519` — invoked automatically on terminal transition

The boundary was an **absence**; it is now an **explicit, observational bridge**. The
console still rendered the pre-bridge world. Corrected, with the superseded reading kept
as provenance.

**Root cause:** the console is derived from a map, and nothing told it the map had moved.
The tests were updated for the bridge (65 passed across the four boundary files); the
console data was not.

### 9.4 Why it went unnoticed — nothing judged the console

- `grep -rln "web/console" tests/` → only unrelated `test_gate2_*.py`.
- No test asserted a posture flag matched reality.
- No test asserted a cited test name existed.
- `scripts/console_contract_domain.py` covers `web/arkadia_console` **only** — `web/console`
  is outside the derived domain, so `prism-console-contract.yml` never saw it.

## 10. The repair

**A. One revision source, read not remembered.** New `web/console/src/lib/revision.ts`
exports `MAP_DERIVED_FROM` (the map's derivation point, labelled as history) and
`useLiveRevision()`, which reads `GET /api/version → source_revision`. `Layout.tsx` renders
both, separately labelled. An unreadable probe prints "revision unavailable" — it never
falls back to a remembered SHA. The Dockerfile's inert build-arg was deliberately **not**
used: it explicitly warns it must not be mistaken for a revision.

**B. Posture corrected from the substrate.** Four `deployed: false` → `true`;
`productionVerified` remains `false` with the reason stated.

**C. Premise and citations corrected.** `executionNotWorkEvent.ts` now records the
explicit bridge, cites `test_execution_attempt_creates_one_causally_joined_workevent` and
`test_workevent_capture_does_not_mark_completion`, and retains the superseded reading as
provenance.

## 11. The guard

`tests/test_console_posture_currency.py` — **20 tests**, binding each claim to its
substrate:

1. Every cited evidence test must exist in the corpus (`git ls-files -- tests/`).
2. Every declared surface must be served by the canonical app's route table.
3. No boundary instance may claim an undeployed posture while its surfaces are live.
4. The revision may not be hardcoded outside `revision.ts`.
5. `MAP_DERIVED_FROM` must resolve to a real commit.

**Live negative control** — guard run against the restored pre-repair tree:

```
8 failed, 12 passed
  test_every_cited_evidence_test_exists[executionNotWorkEvent.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[approvalNotExecution.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[evidenceNotVerification.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[executionNotWorkEvent.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[workeventNotEvidence.ts]
  test_the_revision_is_not_hardcoded_outside_one_module
  test_the_map_derivation_point_is_a_real_commit
  test_the_running_revision_is_read_from_the_runtime
```

Restored byte-identically (`git status --porcelain` empty) → **20 passed**. The guard
detects exactly the measured defects and nothing else.

A first draft of the surface detector was **too loose** and failed on its own repair:
`"[^"]+"` matched a path named inside a prose note
(`"...POST /api/x/approve, POST /api/y/run). Production..."`). Tightened to `[^"\s]+`,
with the measured case recorded in the source.

## 12. CI wiring — the guard is now executed

`grep -rn test_console_posture_currency .github/workflows/` was **0**, so the guard held
only when a human ran it by hand. New gate
`.github/workflows/operator-console-posture.yml`: path-filtered, `workflow_dispatch`,
`permissions: contents: read`, installs `requirements.txt` (the guard imports `api.main`
for the route table).

`tests/test_console_posture_currency_ci_wiring.py` — **12 tests**, deriving the guard's
inputs from its own source **by AST** rather than restating them, and separating a **gate**
from an **incidental executor**: `sg-02-fe-2-v.yml` and `provider-routing.yml` run the whole
`tests/` tree so they execute the guard in passing, but neither names it, so neither is
selected by a change to it. Requiring a broad-suite workflow to name every input of every
test it happens to run would be absurd; requiring a dedicated gate to name its inputs is
the point. (Found by the guard's own first run — 8 failures, all three incidental executors
flagged.)

**Live negative controls against the real workflow file**, each restored byte-identically:

| Mutation | Result |
|---|---|
| executing step → `echo pytest …` | 1 failed (`test_a_dedicated_gate_exists_for_the_guard`) |
| drop `tests/**` from the filter | 1 failed (input coverage) |
| `continue-on-error: true` on the step | 1 failed (step can fail the run) |
| remove `workflow_dispatch` | 1 failed (dispatchable) |

**Composition check:** the guard text contains **none** of
`scripts/console_contract_domain.py`'s content needles, so it stays outside the derived
console-contract domain (59 files) and `prism-console-contract.yml` needs no edit — avoiding
the hazard where a new domain member reddens `main`.

## 13. Verification

**Build** — `npm --prefix web/console run build`: passes, 58 modules (was 57).
Baseline before the change reproduced `dist/assets/index-BkqSAT5t.js` (241.92 kB) —
byte-identical to what live `/operator` serves.

**Regression, by node identity not count** (the convention here — counts move with the
environment):

```
baseline 9195334c : 25 failed, 3603 passed, 30 skipped, 1 error
branch            : 25 failed, 3642 passed, 30 skipped, 1 error
failing/error node set sha256 (both) : 4733ab8f1e0071e5ce666003a1bf8ce82474e0b1f8cfa6c594c4882206ed6fdf
comm -3 base branch : empty (26 nodes each)
```

**Zero regression.** The `+39 passed` is fully attributed by `--collect-only` per file:

| File | delta |
|---|---|
| `test_console_posture_currency.py` | +20 (new) |
| `test_console_posture_currency_ci_wiring.py` | +12 (new) |
| `test_ci_gate_trigger_coverage.py` | +3 |
| `test_ci_suite_collection_continuation.py` | +2 |
| `test_workflow_injection_boundary.py` | +1 |
| `test_gate_filter_selection.py` | +1 |
| **total** | **+39** |

The `+7` outside my two files is the generic workflow-scanning suites gaining nodes by
construction from one new workflow file — not a regression signal.

`tests/test_ci_gate_trigger_coverage.py` + `tests/test_m02a_ci_gate_integrity.py`:
**164 passed**. Both new paths ADMITTED by `scripts/cp10_mutation_boundary_policy.py`.

## 14. Boundary — what this does NOT claim

- **No deployment.** Production still serves `9195334c`. This is a repository-source change.
- **No production acceptance.** `productionVerified` remains `false` on all four instances.
- **No operator credential** was used, held, or requested.
- **G1 and G8 untouched.** This is G2 only.
- The four **pre-existing** failures in `test_voice_asr.py` and the other baseline failures
  are unchanged on both trees and are **not** attributable to this change.

**Next permitted action:** sovereign review of the branch; merge authority is the human's.

---

## 15. Post-merge verification — the G2 repair is NOT on `main` (2026-10-28)

**Status:** CORRECTION. Recorded because a merge success is not integration verification.

The sovereign reported merging "the PR". Measured immediately after, from live evidence:

### 15.1 What actually advanced `main`

```
origin/main  9195334c  ->  6d299eb8
6d299eb8  lane-doc-currency: add the idle disposition so the guard is satisfiable
          for an empty lane (#584)
```

`6d299eb8` is **PR #584** (`gate-hygiene/lane-currency-idle-disposition-01`, merged
2026-10-28T16:02:38Z). Its diff is 9 files, all lane-currency work
(`scripts/lane_state.py`, `scripts/lane_state_refresh.py`,
`tests/test_lane_instruction_doc_currency.py`, four `AGENTS-0N-*.md`, `lane-state.json`,
one evidence doc). **None of it is the G2 repair.**

### 15.2 The G2 branch was never pushed

| Check | Result |
|---|---|
| `git ls-remote --heads origin \| grep arkadia-one-console-walkthrough-01` | **0 matches** |
| `gh pr list --state all` filtered to this branch | **0 PRs**, in any state |
| `git merge-base --is-ancestor <each of the 5 commits> origin/main` | **NOT in main** (all 5) |
| `git cat-file -e origin/main:web/console/src/lib/revision.ts` | **ABSENT** |
| `git cat-file -e origin/main:tests/test_console_posture_currency.py` | **ABSENT** |
| `git cat-file -e origin/main:.github/workflows/operator-console-posture.yml` | **ABSENT** |
| `git cat-file -e origin/main:docs/architecture/ARKADIA-ONE-MISSION-CONTRACT-01.md` | **ABSENT** |

The branch exists **only** in this workspace (`bf7712f6`). There was no PR to merge: the work
was committed locally and never pushed. `gh` is also unauthenticated in this environment
(`gh auth status` → not logged in), which is consistent — nothing was ever opened.

**No textual overlap** between `#584`'s 9 files and this branch's 12: `comm -12` on the two
changed-file lists is empty. So `#584` is not a partial landing of this work; the two are
disjoint.

### 15.3 The defect is live on `main` — measured, not inferred

The guard was run against a **detached worktree of `origin/main` (`6d299eb8`)** with full
dependencies installed:

```
8 failed, 12 passed
  test_every_cited_evidence_test_exists[executionNotWorkEvent.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[approvalNotExecution.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[evidenceNotVerification.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[executionNotWorkEvent.ts]
  test_no_boundary_instance_claims_an_undeployed_posture[workeventNotEvidence.ts]
  test_the_revision_is_not_hardcoded_outside_one_module
  test_the_map_derivation_point_is_a_real_commit
  test_the_running_revision_is_read_from_the_runtime
```

**This is the identical failure set as the pre-repair negative control in §11** — same 8 nodes.
That is the strongest available confirmation that the defect is unfixed on `main`, and it also
re-confirms the guard detects exactly the measured defects and nothing else.

Direct source checks on `origin/main` agree:

| Check | `origin/main` |
|---|---|
| `ae847dd` in `Layout.tsx` / `standing.ts` / `grammar.ts` | 1 hit each (still hardcoded) |
| `deployed:` in all four boundary data files | `false` in all four |
| dead citation `no_execution_or_job_reference_field` | still present |

### 15.4 Method note — a mid-pass environment reset

Partway through this verification the sandbox lost its Python environment: `pip list` reported
only `pip`, `pytest` and `fastapi` were unimportable, and no venv or alternate interpreter
existed. Reinstalling (`pytest`, `pyyaml`, then `requirements.txt`) was required to obtain a
trustworthy number.

This matters for reading the result: the **first** run of the guard on `main` reported
`12 failed`, and 4 of those were `ModuleNotFoundError: No module named 'httpx'` — an
environment artifact, not a defect. The reported figure is the post-install run, where those
4 pass. **Do not cite the 12-failure run**; it conflates a broken environment with a live
defect, which is precisely the mis-attribution class this record exists to prevent.

### 15.5 Disposition

- The G2 repair is **complete and verified on the branch**, and **absent from `main`**.
- The branch is **local only** and **not pushed**. Nothing is deployed; production remains at
  `9195334c` and still serves the defective `/operator` bundle.
- The next action is **not** another verification pass. It is to push the branch and open the
  PR, or to confirm that a different branch/PR was intended — the sovereign's report and the
  measured repository state disagree, and the disagreement is the finding.
