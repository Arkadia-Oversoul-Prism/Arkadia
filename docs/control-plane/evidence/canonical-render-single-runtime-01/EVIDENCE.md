# EVIDENCE — canonical-render-single-runtime-01

Status: IMPLEMENTED ON BRANCH · NOT DEPLOYED · NOT ACCEPTED
Canonical service: Render `Arkadia` (`srv-d9i1bar7uimc73asnv0g`)
Canonical endpoint: `https://arkadia-kw64.onrender.com`
Repository base at preparation: `main` / `24a00f856a0286cbb464a4b585117dd57a2646fa`
Branch: `canonical-render-single-runtime-01`

## Objective

Serve Arkadia's primary user-facing experience, the reconciled operator console,
the focused N-ATLaS tester, and the existing FastAPI backend through one Render
web-service deployment and one origin. Do not create another production service.

## Implementation on this branch

- Docker builds `web/public_prism` and `web/console` in the same multi-stage image.
- FastAPI serves the primary Arkadia SPA at browser root and its static assets at
  `/assets/*`.
- The operator console is mounted at `/operator/*`, with assets under
  `/operator/assets/*` to avoid collisions.
- `/n-atlas-lab` and `/n-atlas-tester` remain direct compatibility entry points
  to the same operator bundle.
- The root liveness payload remains available to non-browser probes; browser
  navigation requesting HTML receives the primary SPA.
- Unknown `/api/*` and `/solspire/*` paths remain 404s rather than falling
  through to the SPA.
- Existing source and APIs remain in place; no database, identity, authorization,
  execution, or evidence semantics are changed.

## Positive / negative controls added

The new routing tests exercise:
- primary SPA root and a deep link;
- primary static asset and root-level icon;
- operator console root and deep link;
- operator static asset and direct N-ATLaS route;
- an existing API route remains an API response;
- unknown API and SolSpire paths remain 404;
- missing build output does not synthesize a frontend response.

## Not yet established

- Tests and Docker build have not yet been run in CI for this branch.
- No deployment has been triggered by this change.
- No live browser observation has been completed against the proposed unified
  deployment.
- No route-by-route parity claim has been made.
- The Vercel alias and dormant Render static sites have not been retired.
- `web/public_prism` remains source for existing Solariun/Arkana/Canvas screens;
  archiving the source before route parity would remove required product behavior.
- Human production acceptance is `NOT CLAIMED`.

## Acceptance sequence

1. CI passes with the full test output and both frontend builds.
2. Review the emitted build/test evidence, including negative controls.
3. Human review/merge per repository governance.
4. Render deploys the merged revision to the existing `Arkadia` service.
5. Verify deployed revision, root UI, Solariun/Canvas routes, Arkana, operator
   console, N-ATLaS, same-origin API calls, auth, and backend health.
6. Only after those checks, retire the separate public-Prism deployments and
   update external aliases. Preserve `BLOCKED`, `UNKNOWN`, and `NOT CLAIMED`
   wherever observations do not justify a stronger verdict.
