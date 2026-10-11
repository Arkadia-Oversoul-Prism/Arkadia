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
