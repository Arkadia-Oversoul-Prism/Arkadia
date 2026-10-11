# Capability Matrix — NovaNet hub & project Opportunity Radar (Workstream 2)

**Workstream:** 2 — NovaNet & project Opportunity Radar
**Branch:** `feat/prism-parallel-02-novanet-opportunity` (draft PR #420)
**Baseline `main` observed:** `8dcb78d2` (2026-10-11)
**Authority:** inspection and measurement only. No merge, deployment, or acceptance.
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (accepted, PR #419 @ `a29a9b8f`).

Every row below was read from the current backend source **and** cross-checked
against the deployed `/openapi.json` at `https://arkadia-qzu4.onrender.com`.
A route that exists only in source is marked as such; nothing is inferred from
the archived Prism usage.

Auth column legend: **auth** = `require_auth` (Bearer Firebase ID token, `401`
without identity); **sovereign** = `require_sovereign` (`access_level >= 3`, else
`403`); **header-key** = `x-sovereign-key` compared against `SOVEREIGN_KEY`;
**none** = no dependency on the handler.

---

## 1. NovaNet hub surface (owned by PR #418 — not edited here)

| Sub-view | Legacy source | Current route | Auth | Handler / source | Deployed | Status |
|---|---|---|---|---|---|---|
| Public field | `NovaNetPage.tsx` | `GET /api/transmissions` | none (public read) | `api/transmissions.py:103` | yes | **IMPLEMENTED by #418** |
| Echoes / Crystal Matrix | `NovaNetPage.tsx` | `GET /api/echoes` | none (public read) | `api/main.py:1660` | yes | **IMPLEMENTED by #418** |
| Nexus Hub lens | — | — | — | — | — | `NotYetWired` in #418 |
| IMS | `NexusIms*` (archive) | `GET /api/ims/inquiries` | **header-key** (`x-sovereign-key`) | `api/main.py:2089` | yes (`403` anon) | **BLOCKED** — see §2 |
| Grove | archive only | *no route* | — | `spiral_grove/` is a library, no `APIRouter` | **absent** | **NOT WIRED** |
| Larder | archive only | `POST /solspire/projects/{id}/living-larder/orders/{order_id}/bind` | auth (console router) | `solspire/console_router.py:690` | yes | **PARTIAL** — project-bound bind only, no larder read surface |
| Distribution | `DistributionPage` (archive) | `GET/POST /api/distribution/*` (6 routes) | **none** | `api/distribution.py:27` | yes | **NOT UI-READY** — see §2 |

## 2. Findings on the hub sub-views (measured, not assumed)

- **IMS `inquiries` is not Bearer-reachable.** The handler requires the
  `x-sovereign-key` header (`api/main.py:2089-2093`); the console's `apiClient`
  sends only `Authorization: Bearer …`. A lens pointing at it could only ever
  fail. #418 already states this honestly and renders `NotYetWired`; this matrix
  confirms it against source and against the live `403`. **Do not build an IMS
  lens without a contract change owned by the shell workstream.**
- **Grove has no HTTP contract.** `spiral_grove/` contains `models.py`,
  `registry.py`, `learning_path.py`, `learning_activity.py` and exports no
  `APIRouter`; `grep -rn grove api/main.py` is empty. A Grove sub-view has no
  backend to call — the correct state is *not wired*, not a mock.
- **Distribution routes are unauthenticated.** `api/distribution.py` has **zero**
  `Depends(...)` and no `x-sovereign-key` check; `GET /api/distribution/releases/{artist_id}`
  returned **200** anonymously on the live deployment. This is a pre-existing
  authorization observation, recorded here and **not repaired** — repairing it
  edits `api/distribution.py`, outside this workstream's owned paths.
- **Larder** is reachable only as a project-scoped *bind* action, not as a
  read surface. There is no `GET` larder endpoint.

## 3. Project Opportunity Radar (this workstream's slice)

**Contract:** `solspire/buyer_recon_router.py`, mounted under the `/solspire`
router (`prefix="/solspire"`, `dependencies=[Depends(require_auth)]`).

| Method | Path | Auth | Handler | Deployed | Status |
|---|---|---|---|---|---|
| GET | `/solspire/buyer-recon` | auth | `get_buyer_recon` | yes | WORKS (workspace scope) |
| POST | `/solspire/buyer-recon/entries` | auth | `create_buyer_recon_entry` | yes | **BROKEN (defect 1)** |
| PATCH | `/solspire/buyer-recon/entries/{entry_id}` | auth | `update_buyer_recon_entry` | yes | reachable; needs an existing entry |
| GET | `/solspire/buyer-recon/projects/{project_id}` | auth + owner | `get_project_buyer_recon` | yes | **BROKEN in combination (defect 2)** |
| POST | `/solspire/buyer-recon/projects/{project_id}/entries` | auth + owner | `create_project_buyer_recon_entry` | yes | **BROKEN (defects 1 + 2)** |
| PATCH | `/solspire/buyer-recon/projects/{project_id}/entries/{entry_id}` | auth + owner | `update_project_buyer_recon_entry` | yes | **BROKEN (defect 2)** |

### Measured defects (pinned, not repaired)

**Defect 1 — entry create arity mismatch.** `BuyerReconManager.create_entry`
(`solspire/buyer_recon.py:216-220`) supplies **34** values to a **33**-column
`buyer_recon_entries` table. Every create on every scope raises
`sqlite3.OperationalError: table buyer_recon_entries has 33 columns but 34 values
were supplied` → HTTP 500. No prospect can be captured anywhere.

**Defect 2 — one board per subject.** `buyer_recon_boards.subject_ref` is
declared `TEXT NOT NULL UNIQUE`, while `_project_board` keys the board on
`f"{workspace.id}:project:{project_id}"`. The UNIQUE is on the *subject*, not the
composite, so a subject holds exactly one board. Whichever scope is read second
raises `sqlite3.IntegrityError: UNIQUE constraint failed:
buyer_recon_boards.subject_ref` → HTTP 500. Because the workspace board
(`/solspire/buyer-recon`) is the natural first read, **the project radar is
unreachable for any subject who has opened the workspace board**.

Both were introduced at `5de6d476` (PR #199, 2026-10-02). Repairing either edits
`solspire/buyer_recon.py` — outside this workstream's owned paths. Recorded as a
proposed workstream; the tests pin the *current* measured state so a repair is a
visible, deliberate change.

### What is nevertheless verified and shipped here

- The **read contract** is real: route, auth, ownership enforcement (404 for a
  non-owner), the `STATUSES` vocabulary, the `UNKNOWN` default for an unverified
  commercial fact, and the reconnaissance-only authority block
  (`execution_authority: NONE`, `budget_authority: NONE`).
- Two frontend pieces are in place and neither declares a route:
  - `ProjectOpportunityRadar.tsx` — landed by the coordinator at `dd7d174f`, a
    read-only, prop-driven surface with distinct loading / auth / unavailable /
    error / ready states and no execute or spend control. Kept byte-identical.
  - `opportunityRadarContract.ts` — added by this pass; supplies the declared
    project-scoped `readPath` the surface consumes, the backend `STATUSES`
    vocabulary, the `UNKNOWN` / `NONE` sentinels, and handler-derived response
    shapes. Reads through no transport of its own.
- The read path is honest about every state and fabricates no buyer, price,
  budget, or success state.

## 4. Deferred / blocked register

| Item | Owner | Blocker | Next move |
|---|---|---|---|
| IMS lens | Workstream 1 | `x-sovereign-key` header vs Bearer-only client | shell owner decides the auth seam |
| Grove lens | Workstream 1 | no HTTP contract | none until a route exists |
| Distribution lens | Workstream 1 | no auth on 6 routes; sovereign-only repair | propose, do not execute |
| Larder read surface | Workstream 1 | no `GET` route | none until a route exists |
| Project radar create/coexist | sovereign | defects 1 & 2 in `solspire/buyer_recon.py` | sovereign-owned repair PR |
| Route / surface registration for the radar | Workstream 1 | this module declares no route | integration request, see evidence |
