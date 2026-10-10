# Canonical Render Runtime Reconciliation — 2026-10-10

## Decision applied in this change set

The canonical production origin is `https://arkadia-qzu4.onrender.com`. The Render service metadata identifies the service as:

- Service: `Arkadia`
- Service ID: `srv-db49jbh42hec73aj84qg`
- Runtime: Docker web service
- Repository: `Arkadia-Oversoul-Prism/Arkadia`
- Branch: `main`
- Dockerfile: `./Dockerfile`
- Render SSH connection address: `srv-db49jbh42hec73aj84qg@ssh.oregon.render.com` (connection address only; no private SSH key was retrieved or stored)

Render's latest deployment metadata reports the deployment as `live`, commit `17b931b4fe6dd9b27749894dd0d9b1dc9a2e14f5`, deploy ID `dep-db54i61rn11c73d7cq10`, finished `2026-10-10T14:20:57.386641Z`. That commit matches the observed GitHub `main` SHA at the time of reconciliation.

## Repository changes in this branch

- Archived the three active Vercel configuration files under `archive/deployment/vercel/`; removed them from active deployment paths.
- Set production CORS default to the canonical same-origin Render URL.
- Changed Android default frontend/API origins to the canonical Render URL.
- Changed the default IMS offering callback to the canonical Render URL.
- Retargeted the Gate 2 production-observation scripts to the canonical Render URL.
- Updated the cloud architecture and CORS example documentation.
- Updated `architecture/runtime_manifest.yaml` with the observed Render service identity and deployed revision.
- Added `scripts/production_runtime_probe.py` and a GitHub Actions workflow to capture live OpenAPI, probe read-only GET routes, classify responses, and record anonymous/malformed-token behavior.

## Live runtime verification

**Not yet accepted.** The connected tools in this session can read Render service/deployment metadata, but do not provide a general arbitrary-URL HTTP client for the live Render origin. A direct web fetch of `/openapi.json`, `/api/version`, `/health`, and `/operator` was not accessible through the web reader. The new GitHub Actions runner is the network-capable capture path and must complete before route-by-route live findings are entered.

The workflow's JSON artifact is the intended fresh capture:
`artifacts/canonical-render-runtime/production-route-inventory.json`.

## Authorization matrix boundary

The probe will measure:
- anonymous request to `GET /api/operator/security-verification`;
- malformed Bearer token to the same endpoint;
- route behavior as observed from the deployed FastAPI application.

A valid low-privilege Firebase ID token is required to prove the **authenticated-but-unauthorized** case. No such token was available in this session. Therefore that matrix cell must remain `NOT TESTED` unless a dedicated low-privilege test identity/token is provided through a protected CI secret. A malformed token is not equivalent to an authenticated unauthorized identity.

## Acceptance criteria

Acceptance remains `NOT CLAIMED` until:
1. the live OpenAPI capture succeeds and is retained;
2. every runtime path/method is reconciled against source/router inventory, including source-only and runtime-only entries;
3. root, Solariun, Arkana/Canvas, Operator, and N-ATLaS frontend routes are checked on the canonical origin;
4. API routes are classified reachable, protected, failing, or absent;
5. anonymous, unauthenticated, and authenticated-but-unauthorized behavior is evidenced against the live service;
6. the captured deployed revision still matches the intended merged source revision;
7. the resulting evidence is reviewed.

No claim is made here that a code merge alone constitutes deployment verification or human acceptance.


## Addendum — fresh live capture (GitHub-hosted runner, 2026-10-10)

The first network-capable probe completed successfully on PR #401's earlier probe revision. Artifact: [canonical-render-runtime-probe.zip](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38061446944/artifacts/11673855296). The capture was made against the live production origin, not a local TestClient.

| Check | Observed result |
|---|---|
| `GET /openapi.json` | HTTP 200, JSON, 217,256 bytes |
| OpenAPI paths | 288 |
| OpenAPI operations | 331 |
| Read-only GET probes | 153 |
| Classified reachable | 37 |
| Classified protected (401/403) | 98 |
| Timeouts / unreachable | 3 |
| Resource-not-found / 404 | 6 in the initial classifier; these were dynamic resource sentinel 404s, not proof that the router path was absent |
| Request-shape rejected (400/422) | 9 |
| `GET /health` | HTTP 200, `{"status":"radiant","path":"/health"}` |
| `GET /api/version` | HTTP 200; reported source revision begins `17b931b4fe6d` |
| `GET /` | HTTP 200, Prism SPA HTML, 1,419 bytes |
| `GET /operator` | HTTP 200, operator-console SPA HTML, 807 bytes |
| `GET /solariun/opportunity-radar` | HTTP 200, Prism SPA HTML, 1,419 bytes |
| `GET /n-atlas-lab` | HTTP 200, operator-console SPA HTML, 807 bytes |
| `GET /n-atlas-tester` | HTTP 200, operator-console SPA HTML, 807 bytes |

The initial probe timed out on `GET /api/codex`, `GET /api/echoes`, and `GET /api/oracle-context`. These are **unresolved observations**, not confirmed endpoint failures. The probe was then hardened to retry timeouts and distinguish resource-level 404s from absent routes; its refreshed run is pending.

### Live authorization observations

- Anonymous request to `GET /api/operator/security-verification`: HTTP 401, `Authentication required`.
- Malformed Bearer token: HTTP 401, `Authentication required`.
- Authenticated but insufficiently privileged identity: **NOT TESTED**; no valid low-privilege Firebase token was available.

### Interpretation

The deployed unified UI and API surface are reachable on the canonical Render origin, and the runtime revision matched the observed main deployment at capture time. The 153 GET probes are not a complete acceptance test for all 331 operations: write methods were intentionally not invoked. The static source-route scanner is a partial comparison that reports exact local decorator matches and unmatched paths; nested `include_router` prefixes require explicit review. Production acceptance remains `NOT CLAIMED`.
