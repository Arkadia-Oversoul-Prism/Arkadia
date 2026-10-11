# AEAS-05 — Canonical Frontend Acceptance / Console Route-Contract Repair

Recorded 2026-10-11. Source of every claim below: live measurement in this
environment against `main` and the canonical runtime. Nothing here is a
production-acceptance claim.

## Starting state

- `main` = `a58f08498141a5a43c09682413a2fee4fba43cee` (PR #413 merge).
- PR #413 (`frontend/arkadia-console-01`, head `372ebf88`) merged at
  `2026-10-11T01:17:53Z`; merge commit `a58f0849…`.
- Live `GET /api/version` → `source_revision = a58f0849…`,
  `revision_source = RENDER_GIT_COMMIT`, `revision_conflict = false`. The
  deployed revision equals `main` — source↔runtime consistency observed.

## What browser acceptance found

Playwright (Python), read-only, against `https://arkadia-qzu4.onrender.com`:

| Surface | Hard load | Threshold / honest state |
| --- | --- | --- |
| `/` | 200 SPA | console identity present |
| `/engineering-lab` | 200 SPA | "Sign in to continue" + "Go to sign in" |
| `/login` | 200 SPA | `tab-signin`, `input-email-signin`, `input-password-signin`, `button-signin` all present |
| `/solariun`, `/knowledge`, `/weaver`, `/arkana` | 200 SPA | threshold where protected |
| **`/solspire`** | **404 raw JSON** | `{"detail":"Route not found"}` |

Arkana honest-state check: with all `/api/**` aborted via request interception,
the surface renders the empty conversation and does **not** fabricate a reply or
print "OBSERVED". With the backend up, `POST /api/commune/resonance` → 200 and
the reply shape (`reply`, `resonance`, `patterns`, `rag_refs`, `sources`,
`memory`) matches `lib/arkana.ts`.

## Defect

1. **Reserved-namespace collision.** `web/arkadia_console/src/lib/surfaces.ts`
   declared the SolSpire surface at `path: "/solspire"`. `/solspire` is a
   reserved backend API namespace — `solspire/console_router.py` sets
   `prefix="/solspire"`, and `api/frontend_routes.py::_RESERVED_PREFIXES`
   refuses to serve the SPA there. A hard load/refresh 404s; client-side
   navigation masks it.
2. **Wrong contract path.** `endpoints.solspireProjects` was
   `/api/solspire/projects` (404 live). The real path is `/solspire/projects`
   (present in the deployed `/openapi.json`).

Reproduced with `TestClient` against `api.main:app`: pre-repair `/solspire` →
404, `/solspire/projects` → 401 (backend handler, not SPA).

### Why CI did not catch it

The CP10 gate (`sg-02-fe-2-v.yml`, step "CP10 browser route verification")
drives the **Vite dev server** on port 5000. Vite serves the SPA for *every*
path, so `/solspire` read 200 in CI (run `38101361319`, head `a58f0849`) while
the canonical FastAPI origin 404s it. A dev-server browser gate cannot observe a
serving-path collision; only the FastAPI origin can.

## Change (PR #414, branch `aeas05/console-route-contract-01`)

- `surfaces.ts`: SolSpire surface path → `/enterprise` (no top-level backend
  route; only `/solspire/enterprise/*` exists, under the reserved prefix). The
  `/solspire/*` API contract is unchanged.
- `endpoints.ts`: `solspireProjects` → `/solspire/projects`.
- `sg-02-fe-2-v.yml`: CP10 unauthenticated probe → `/enterprise` and
  `/enterprise/projects`.
- `tests/test_canonical_frontend_routing.py`: binds every declared console
  surface path to the served SPA on the FastAPI origin, plus a reserved-namespace
  negative control.
- `tests/test_aeas05_canonical_frontend_acceptance.py`: binds the CP10 probe
  route to the declared surface table.

## Evidence

- Post-fix FastAPI route matrix (`Accept: text/html`): `/`, `/enterprise`,
  `/enterprise/projects`, `/engineering-lab`, `/solariun`, `/knowledge`,
  `/weaver`, `/login` → 200 SPA; `/solspire` → 404 (correct, reserved).
- Guard bites: restoring `path: "/solspire"` → `2 failed`
  (`surface path /solspire is not served (status 404)` and `collides with
  reserved backend prefix /solspire`); restored byte-identically → `4 passed`.
- Console build `corepack pnpm build` → success.
- Full suite, branch vs clean `main` worktree, same environment,
  `-rEf --continue-on-collection-errors`: **29 failing/error nodes on both,
  `comm -3` empty** — zero node-set delta (`+3 passed` = the 3 new guards).
- CP10 mutation-boundary judge (M02A): PASS, exit 0.

## Rollback readiness (archived Prism)

`archive/frontend/arkadia-prism/README.md` recovery steps were **stale** — they
claimed the Dockerfile and `api/frontend_routes.py` "name the retired path
`web/public_prism`"; after the console cutover both name `web/arkadia_console`.
Corrected in `91bceb0d`.

Rehearsal at `main` `a58f0849` in a detached worktree:

- `git mv archive/frontend/arkadia-prism/web/public_prism web/public_prism` succeeds.
- `corepack pnpm install --frozen-lockfile` succeeds.
- `corepack pnpm build` emits `dist/assets/index-BzLymmg4.js` (890.33 kB) — the
  same bundle hash observed served by the last measured Production deployment
  serving Prism (`c8abb28e4ac0`). The archive is bit-for-bit recoverable.

`git log --follow` on an archived file traverses the pre-archive history.

## Boundary classification

- current main resolved — VERIFIED
- source revision == deployed revision (`/api/version`) — VERIFIED
- console served artifact matches local build (marker oracle, app-bound) — VERIFIED
- console route reachability on the canonical origin — VERIFIED (post-fix, locally);
  production requires a deploy to reflect `/enterprise`
- deployment build output observed — BLOCKED (deployment-specific URL behind
  Vercel SSO; observed via the alias instead)
- browser-rendered UI correctness — OBSERVED for the pre-fix revision, NOT CLAIMED
  for the post-fix revision until deployed
- production acceptance — NOT CLAIMED (human authority)

## Next action

Human authorizes merge of PR #414 and a production deploy; then re-run
`python scripts/gate2_production_observation.py` and the browser probe against
the new deployed revision and confirm `/enterprise` serves the console SPA on
the canonical origin.

---

# Production acceptance (recorded 2026-10-11)

## Merge record

- PR #414 merged `2026-10-11T02:04:27Z`, **merge commit
  `c404150a1c26927c0c11e210d1b75e54a5653213`** (true two-parent merge:
  parents `a58f0849` + `5a330ec6`).
- `main` = `c404150a…` (origin/main, origin/HEAD, local main). No direct push to
  `main` was made; the change landed only through the PR.
- CI on the PR head `5a330ec6`: **14/14 check-runs success**. On the merge commit
  `c404150a`: `validate`, `browser` (Canonical Render Browser Smoke), `boot-syntax`,
  `Full-history secret scan` all `success`.
- The two `Vercel – console` / `Vercel – arkadia-prism` commit statuses are
  `failure` on `main` `a58f0849` as well — pre-existing, not attributable.

## Source contract (reviewed, not assumed)

Verified against the real `api.main` app with the built console present:

| Contract | Expected | Observed |
| --- | --- | --- |
| `/enterprise` | console SPA | `200`, `text/html`, `<!DOCTYPE` |
| every declared surface (`/`, `/arkana`, `/solariun`, `/engineering-lab`, `/enterprise`, `/knowledge`, `/weaver`, `/about`, `/login`) | console SPA | `200` SPA |
| `/solspire/projects` | backend handler, auth-gated | `401 {"detail":"Authentication required"}`, `application/json` |

`/solspire/projects` resolves to `solspire/console_router.py::list_projects`
(`APIRouter(prefix="/solspire")`, `Depends(require_auth)`).

## Regression controls (both defects are caught)

1. **Reserved-path collision** — `test_console_surface_paths_avoid_reserved_namespaces`
   pins `_RESERVED_PREFIXES` and rejects a surface on a reserved namespace.
   Negative control proven: restoring `path: "/solspire"` → `2 failed`.
2. **Surface shadowed by a real backend route (raw JSON)** — the reserved list is a
   static denylist that cannot see a surface placed on a *real, non-reserved*
   handler. Demonstrated gap: a `/dashboard` handler returns `{"backend":"json"}`
   at `200` while the synthetic guard stays green. Added
   `test_console_surface_paths_are_not_shadowed_by_a_backend_route`, which scans
   the real `api.main` route table (`starlette` `Route.matches`, `method=GET`), so
   every declared surface is proven not shadowed. Negative control
   `test_shadowing_detector_flags_a_non_reserved_backend_route` flags `/dashboard`
   and stays silent on an unrouted path. Verified on the live table: all nine
   surfaces unshadowed; `/health` correctly reported shadowed.
3. `test_every_console_surface_path_is_served_as_the_spa` — binds each declared
   surface to the served SPA on the FastAPI origin.
4. `test_cp10_gate_route_targets_a_declared_console_surface` — binds the CP10
   gate's probe route to the declared surface table.

## Deployment verification

- `/api/version` → `source_revision = c404150a1c26927c0c11e210d1b75e54a5653213`,
  `revision_source = RENDER_GIT_COMMIT`, `revision_conflict = false`,
  `canonical_deployment = one_reconciled_deployment`. **Live == `main`.**
- The GitHub deployment API still shows the newest Vercel **Production** record as
  `c8abb28e4ac0` (2026-10-10), which predates this merge. That record is a Vercel
  project, not the canonical Render runtime; the canonical runtime's own revision
  probe is authoritative here and reads `c404150a`.
- Served console bundle `assets/index-C_4Sk6d5.js` (30,875 B) is **sha256-identical**
  to a local build of `c404150a`
  (`9774fba8a48240808fff79e653568aa738541b1fd484f91692c25f0f622c7ea0`).
- Gate-2 marker oracle: **VERIFIED** (`local build marker set matches deployed:
  True`), control literal `Enter the enterprise layer.` → 0 (expected absent),
  `last-modified` = the merge deploy time.

## Browser acceptance — canonical origin (22/22)

Playwright, read-only, against `https://arkadia-qzu4.onrender.com`:

- `/enterprise` → `200`, console SPA (not raw JSON), auth threshold "Sign in to
  continue" rendered.
- Every declared surface → `200` SPA.
- `/solspire/projects` → `401 application/json` (backend handler, auth-gated) —
  not the SPA, not `404`.
- Protected surfaces (`/engineering-lab`, `/weaver`, `/knowledge`, `/solariun`,
  `/enterprise`) all render the threshold when unauthenticated; no leakage.
- `/login` exposes `tab-signin`, `input-email-signin`, `input-password-signin`,
  `button-signin`.
- Arkana honest state: with `/api/**` aborted, no fabricated observation output;
  with the backend up, `POST /api/commune/resonance` → `200` with
  `reply/resonance/patterns/rag_hits/rag_refs/sources/memory`.
- No console errors during the run.

## Rollback readiness

`archive/frontend/arkadia-prism/` (158 files, incl. `pnpm-lock.yaml`) is intact on
`main`; the only change across the merge is the corrected README recovery
procedure + rehearsal note. Rehearsal (recorded above) builds
`assets/index-BzLymmg4.js`, the exact bundle the last Prism-serving deployment
served — the archive is bit-for-bit recoverable.

## Boundary classification (post-deploy)

- current main resolved — VERIFIED
- live revision == main (`/api/version`) — VERIFIED
- alias reachable — VERIFIED
- served artifact == local build of the deployed revision — VERIFIED
- marker-set oracle — VERIFIED
- canonical-origin browser acceptance (routes, gating, Arkana states) — OBSERVED, PASS
- main → Vercel-deployment-record identity — STALE (record predates merge; the
  Vercel record is not the canonical Render runtime)
- deployment build output observed via a deployment-specific URL — BLOCKED
  (Vercel SSO); observed via the canonical alias instead
- **production acceptance — ACCEPTED (live observations passed; human authority
  remains final)**

