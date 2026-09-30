# WORKSTREAM STATE — gate hygiene / Gate-2 production health route provenance

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.

## Pass record — 2026-09-30 (heartbeat)

- **Reconstructed:** `git ls-remote origin main` = `002b189dd95e41c9b4f4cca33d08b4121453d289`.
  Working clone on `main`, clean. BASE_MAIN recorded as that SHA. **Main did not move
  during this pass.**
- **Credential:** `github_token` works for read + API. No `VERCEL_TOKEN` /
  `RENDER_API_KEY` in the environment ⇒ deploy identity stays unreachable (see below).
- **Open PR queue (live, all MERGEABLE CLEAN, none draft):** #142, #143, #144, #145,
  #146, #147, #148, #149, #150, #151, #152.
- **Continuity decision:** PR #143 `gate-hygiene/gate2-production-parity-02` is the
  active Gate-2 PR, but it is *scoped to runtime observation* — an observation
  harness, not a code repair. This pass found a **repository-layer defect** (a
  contract-pointed route that does not exist) which #143 observes but cannot fix.
  Contract rule 11 directs non-consequential follow-on work to a **separate bounded
  branch**; that is this branch. No duplicate of #143's work; its harness is reused
  as an oracle (§ below) rather than reimplemented.
- **Publication:** PR opened — sovereign review. No merge, no force-push, `main` untouched.

## Fingerprint (measured this pass, not remembered)

```
BASE_MAIN 002b189 (clean)     : 20 failed / 1041 passed / 11 skipped / 2 errors   (22 nodes)
002b189 + this branch         : 20 failed / 1046 passed / 11 skipped / 2 errors   (22 nodes)
  added                       : none
  removed                     : none
  passed delta                : +5  (exactly tests/test_production_health_route.py)
architecture                  : 11/11
CP10 mutation boundary        : PASS (exit 0)
py_compile api/main.py        : pass    (api/main.py = 2529 / 2600 lines)
vite build                    : environment-blocked (no npm registry access)
```

Measured with `--continue-on-collection-errors -p no:randomly`. Both collection errors
(`test_autonomy.py`, `test_render_codex.py`) are pre-existing baseline debt, unchanged.

> Measurement trap (still binding): without `--continue-on-collection-errors` the two
> collection errors abort the session and the run looks clean. Always pass the flag and
> compare failing nodes **by name**, never by count alone.

## The bounded task

**Defect:** the deployment contract pointed at `/health`, which no route served.
Production returned **404** on `/health` while `/api/heartbeat` returned 200.

**Repair:** one additive route in `api/main.py`, a projection of the canonical
`/api/heartbeat` signal. No second liveness authority, no second mutation path.

**Guard:** `tests/test_production_health_route.py` (5 tests), proven falsifiable by
four negative controls (NC-1 route-removed, NC-2 status-drift, NC-3 unbounded surface,
NC-4 restore byte-identical).

Full detail: `EVIDENCE.md` in this directory.

## Reusable oracle discovered this pass (do not reimplement)

`scripts/gate2_backend_observation.py` (from PR #143) is a read-only operation-signature
digest over the deployed `/openapi.json`. It is the non-vacuous oracle for "does the
deployed backend actually serve route X". Use it instead of trusting an HTTP 200 from
the Vercel alias.

**Critical interaction — this branch moves that digest.** Deployed = 274 operations /
`d1797f9c…e30b`; this branch = **275** / `359677ac…3301`. Delta is exactly
`GET /health :: Health ::`. PR #143 will therefore report *deployed ≠ main* until this
branch merges **and** redeploys. That is the expected reading, not a defect.

**Vacuous-oracle warning (recorded so it is not repeated):** `https://arkadia-prism.vercel.app`
returns the **same 997-byte `text/html` shell with HTTP 200 for every path**, including
paths that do not exist. A 200 from that host proves nothing about route existence.
Any Gate-2 evidence citing a Vercel 200 as route-existence evidence is carrying no
provenance weight. The pre-existing
`docs/control-plane/evidence/gate2-public-runtime-integrity/EVIDENCE.md` §5 does this
for `/api/health`; the claim is true but vacuous.

## Boundary classification for this pass

| boundary | state |
|---|---|
| repository-layer repair (route exists, projection holds, guard falsifiable) | **VERIFIED** |
| main SHA → deployment SHA (needs provider credential) | **UNKNOWN** |
| production serving `/health` | **FAILED** (404, until redeploy) |
| production parity with current main | **FAILED / OPEN** (unchanged by this pass) |

Deployment is **not** self-authorized: no `VERCEL_TOKEN` / `RENDER_API_KEY` present, and
deployment is a consequential external action reserved to the sovereign. This pass did
not deploy and claims no production change.

## Next bounded task (candidates, not yet authorized)

1. **`DEPLOYMENT_GUIDE.md` legacy-surface adjudication** — the page documents
   `GET /status`, `POST /oracle`, `GET /threads`, none of which exist. Either the doc is
   stale (correct it) or the routes regressed (restore them). Must be adjudicated before
   editing: a documented-but-absent route is the *same class* of defect as this pass.
   Discovered, deliberately not repaired here — outside this bounded scope.
2. **Gate-2 deploy identity** — remains `BLOCKED` on provider credential. Not actionable
   without sovereign-supplied access.
