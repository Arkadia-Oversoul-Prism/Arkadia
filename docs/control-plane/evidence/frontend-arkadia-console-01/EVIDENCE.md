# Arkadia Console rebuild — archive Prism, scaffold the canonical frontend

Bounded objective: replace the user-facing experience with a new frontend built
around the product architecture, while preserving the backend, governance,
APIs, and source history, and keeping the retired Prism UI recoverable.

## Baseline (Phase 0 — freeze and inventory)

- `main` = `eb63342d1951e638b8952f4b66ea1308f052ed2f` == `origin/main`.
- Live canonical runtime `https://arkadia-qzu4.onrender.com` reported
  `source_revision == eb63342d…`, `revision_conflict: false` — source and runtime
  were consistent at the start of the work.
- Existing frontend: `web/public_prism` — 135 files, ~30k LOC, React + Vite + TS
  + Tailwind, pnpm@10.26.1 / node 24.x.
- Serving path: `api/frontend_routes.py::configure_frontends` mounts the built
  SPA at `/` and `/assets` from the canonical FastAPI origin.
- Image build: `Dockerfile` `frontend-build` stage builds `web/public_prism`;
  `entrypoint.sh` writes the runtime Firebase Web config into its `dist/`.
- Full-suite baseline (measured on `eb63342d` in this environment): 52
  failing/error nodes (43 failed / 9 collection-error files), 1989 passed.

## Changes

Archive (via `git mv`, history preserved):

- `web/public_prism` -> `archive/frontend/arkadia-prism/web/public_prism`
- `archive/frontend/arkadia-prism/README.md` records the layout and a recovery
  procedure (move back, repoint the two serving/build paths, rebuild).

New frontend — `web/arkadia_console/` (React + Vite + TS + Tailwind, React 18,
Firebase 12, pnpm@10.26.1 / node 24.x):

- Application shell (`components/Shell.tsx`), one shared aurora field, persistent
  navigation (vertical drawer on desktop, tab strip on mobile).
- Product surfaces (`src/pages/*`): Home, Arkana, Solariun, Engineering Lab,
  SolSpire, Knowledge OS, Weaver, About — declared once in `src/lib/surfaces.ts`.
- Router (`src/lib/router.ts`): one `resolvePath` / `routeForSurface` over the
  declared surface paths; section routes like `/solariun/<lens>` resolve.
- Authenticated API client (`src/lib/apiClient.ts`) with failure classification
  (AUTH_REQUIRED / FORBIDDEN / NETWORK_ERROR / SERVER_ERROR / …), bearer
  propagation, and no JSON content-type on multipart bodies.
- `src/lib/apiConfig.ts`: same-origin by default (ADR-016), `VITE_API_BASE_URL`
  and an Android bridge as the only overrides; no hardcoded remote fallback.
- Firebase bootstrap (`src/lib/firebase.ts`) reads the runtime-injected public
  config; protected surfaces render an explicit unauthenticated state rather
  than a simulated one.
- Unknown/partial states (`components/ui.tsx`, `useHydration.ts`): a surface
  distinguishes loading / auth-required / backend-unavailable / not-yet-wired.
  It never renders mock inference, authorization, execution, or evidence data.

Repointed serving and build paths (the old path is removed everywhere it is
served or built):

- `Dockerfile`, `entrypoint.sh`, `api/main.py::root`, `api/frontend_routes.py`
- `.github/workflows/{sg-02-fe-2-v, canonical-render-browser-smoke,
  canonical-render-runtime-probe, n-atlas-developer-lab}.yml`
- `scripts/{github_push.py, prism_coherence_check.py, gate2_browser_observation.py}`
- `scripts/{gate2_alias_app_binding.py, gate2_production_observation.py}`:
  `web/arkadia_console` registered as an enumerable frontend; the Prism entries
  are retained as historical lineage keys (the Gate-2 marker semantics are a
  separate workstream and were deliberately not altered).
- The ~40 source-level tests that pin the archived Prism UI now read it at its
  archive location; the two tests that pin the served dist now target the
  console.

Guard: `tests/test_frontend_arkadia_console_rebuild_01.py` (11 tests) asserts the
console is canonical (scaffold, surfaces, Dockerfile, entrypoint, backend root,
route mounting), that Prism is preserved with its build inputs and recovery
instructions, and that the old path is gone — with negative controls.

## Verification

- `corepack pnpm build` in `web/arkadia_console`: PASS — 61 modules,
  `dist/assets/index-*.js` 27.04 kB (gzip 8.54 kB).
- Full suite, branch: 52 failing/error nodes; `main`: 52. `comm -3` on the
  sorted node sets is empty — zero node-set delta, i.e. no regression and no
  repaired node. The 6 nodes that differ from the pre-change baseline were shown
  to fail identically on a clean `main` worktree.
- Architecture suite: 11 passed.
- CP10 mutation-boundary judge over the 248 changed paths: PASS.
- `python -m py_compile api/main.py api/frontend_routes.py`: PASS.

## Boundaries held

- No production cutover. The canonical runtime still serves the deployed
  revision; this change is repository-source only and has not been deployed.
- Authentication unchanged — no bypass, no weakened authorization.
- Backend contracts and persistence untouched.
- Proposal, approval, execution, and verification remain distinct (the Weaver
  surface states this and reads real approval records).

## Not claimed

- Production parity or acceptance. Confirming the new frontend on the canonical
  runtime requires a deployment and a live observation (`GET /api/version`
  matching the merged SHA plus a browser read), which is a human-authorized step.
- The Gate-2 harness marker semantics were Prism-only in this revision; binding
  the observation to the observed app is AEAS-05
  (`docs/control-plane/evidence/aeas05-canonical-frontend-acceptance-01/`).
