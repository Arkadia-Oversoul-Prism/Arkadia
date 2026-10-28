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
| G2 | `/operator` renders stale, false posture claims | §5 | DEFECT — bounded repair |
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
