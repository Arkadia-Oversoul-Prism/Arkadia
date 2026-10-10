# Arkadia — Canonical Runtime Architecture

**Production platform:** Render  
**Canonical origin:** https://arkadia-qzu4.onrender.com  
**Canonical service:** `srv-db49jbh42hec73aj84qg`  
**Source:** `Arkadia-Oversoul-Prism/Arkadia`, branch `main`

## Deployment invariant

The primary Arkadia frontend, operator console, API, and runtime are built and served by one Render web service. The root `Dockerfile` builds both frontend applications and copies their output into the same FastAPI runtime image. Browser routes and API requests use the same origin; no frontend rewrite to a second backend is required.

| Surface | Canonical route | Responsibility |
|---|---|---|
| Prism / Solariun / Arkana / Canvas | `/` and frontend routes | Primary user-facing application |
| Operator console | `/operator/` | Governed engineering and operator interface |
| N-ATLaS tester | `/n-atlas-lab`, `/n-atlas-tester` | Focused validation surface |
| API | `/api/*` | FastAPI application routes |
| OpenAPI | `/openapi.json` | Runtime API schema |
| Revision identity | `/api/version` | Read-only deployed source revision |

## Build and deployment

Render service `srv-db49jbh42hec73aj84qg` tracks `main` with automatic deploy on commit. A successful source commit or provider deploy is not, by itself, runtime acceptance. Acceptance requires:

1. The deployed revision matches GitHub `main`.
2. Both frontend bundles build and are served from the canonical origin.
3. The live OpenAPI operation inventory reconciles with the source application.
4. Frontend routes, API responses, and authorization boundaries are probed over HTTP.
5. The resulting report records PASS, FAIL, BLOCKED, or UNKNOWN without inferring missing evidence.

## Required Render environment

Keep required production secrets configured in the Render service environment. Never place secret values in this repository or in the reconciliation artifact. The browser application uses only public Firebase web configuration; server-side credentials remain server-side.

The production CORS allowlist defaults to the canonical origin. Since the frontend and API share an origin, cross-origin browser access is not part of the normal production flow. Any additional origin requires an explicit, reviewed reason.

## Legacy deployment archive

Vercel routing files are retired from the active build configuration and preserved in `docs/archive/deployment/vercel-routing-2026-10-10.md` for historical reference only. Legacy Vercel observations and deployment evidence remain historical records; they do not define a production target or acceptance boundary.

Other integrations such as OpenClaw/bots may remain separate interface services, but they are not alternate canonical deployments of the Arkadia frontend/API runtime.
