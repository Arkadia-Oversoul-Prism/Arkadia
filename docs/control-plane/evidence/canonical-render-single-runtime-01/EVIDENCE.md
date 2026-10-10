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

## CI measurements (GitHub Actions, 2026-10-09)

On the implementation tree before this evidence-only update:

- `tests/test_canonical_frontend_routing.py`: **2 passed**.
- N-ATLaS provider tests: **8 passed, 1 skipped**.
- Operator console TypeScript + Vite production build: **success**.
- Docker build of the combined image: **success**; both frontends built (3,447 Prism modules and 56 console modules) and both dist directories copied into the final image.
- N-ATLaS external beta validation: English and Hausa beta jobs and evidence bundling **success**.
- Full-history secret scan: **success**.
- Vercel checks remain **failure** due the provider's build-rate-limit response. Those checks are not the canonical Render Docker build and do not establish a Render failure.

The workflow is configured to rerun the route tests, frontend build, and Docker image build when this evidence directory changes.

## Not yet established

- No production deployment has been triggered by this change.
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

---

## ADDENDUM — attribution and current status (2026-10-10)

> Appended by a later pass. The findings above are **preserved unchanged**; this addendum
> records attributable observations made after them and reconciles the packet's status line.
> It does not erase the original scope, which was branch-bound and pre-deployment.

### Status reconciliation

The header still reads `IMPLEMENTED ON BRANCH · NOT DEPLOYED · NOT ACCEPTED`. That was true when
written. Since then the consolidation commit `43c3e2b` (#371) is an **ancestor of `main`
`f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`**, so "on branch" is superseded at the source level.
**Deployment and acceptance remain `NOT CLAIMED`** — a merged build is not a deployed runtime, and
a deployed runtime is not acceptance.

### Attributed observations (read-only, 2026-10-10)

Host + path observations only. The Render service-to-hostname mapping was **not** inspected and
remains `UNKNOWN`. These observations are the basis for requiring runtime-identity evidence
(ADR-016); they do not resolve canonical ownership.

| Host | Observation | Reading |
|---|---|---|
| `arkadia-qzu4.onrender.com` | 287 OpenAPI paths; `/` (`Accept: text/html`) → 1419-byte Prism SPA; `/operator` → Console SPA; `/solariun/opportunity-radar` → Prism SPA; app bundle references no external backend | **Strongest observed unified-runtime candidate** |
| `arkadia-kw64.onrender.com` | 286 OpenAPI paths; `/` → JSON liveness; `/operator` → 404; `/solariun/*` → 404; no `/api/operator/security-verification` | Conflicting, apparently older runtime |
| `arkadia-prism.vercel.app` | `/api/heartbeat` → HTTP 200 `text/html`, 789 bytes (SPA shell), not backend JSON | Legacy split artifact |
| `arkadia-prism-jklhb9use-arkadia-prism.vercel.app` | `/api/heartbeat` → 302 → `vercel.com/sso` (Deployment Protection) | Not observable without provider auth |

### Outstanding uncertainty

- Which Render service owns which hostname: `UNKNOWN` (needs Render access).
- Actual running revision on any host: `UNKNOWN` (no revision metadata endpoint existed at
  observation time; see `GET /api/version`).
- Whether `qzu4` or `kw64` is the intended production custom domain: `UNKNOWN`.
- Human production acceptance: `NOT CLAIMED`.
