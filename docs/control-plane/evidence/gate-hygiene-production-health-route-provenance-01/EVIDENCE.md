# Gate 2 — production health route provenance

**Gate:** GATE-02 (HUMAN-ORIGIN AUTHORITY / production parity boundary)
**Workstream:** `gate-hygiene/production-health-route-provenance-01`
**BASE_MAIN:** `002b189dd95e41c9b4f4cca33d08b4121453d289`
**Classification:** VERIFIED (repository layer) — runtime confirmation BLOCKED on deploy identity

## 1. Finding

The deployment contract pointed at a health endpoint that **did not exist in the
application**, and the repository's own monitoring instructions therefore
resolved to a 404.

Measured on live production during this pass:

```
GET https://arkadia-kw64.onrender.com/api/heartbeat   -> 200  {"status":"radiant","resonance":0.99}
GET https://arkadia-kw64.onrender.com/                -> 200  {"message":"Arkadia Mind is breathing."}
GET https://arkadia-kw64.onrender.com/api/ark-date    -> 200
GET https://arkadia-kw64.onrender.com/health          -> 404  {"detail":"Not Found"}
```

`git log -S'@app.get("/health")' -- api/main.py` returns **nothing**: the route
never existed in the backend, at any revision.

### Independent confirmation via a non-vacuous oracle

The finding was re-derived from the deployed service's own OpenAPI document —
which, unlike the SPA catch-all in §3, is a real oracle:

```
GET https://arkadia-kw64.onrender.com/openapi.json   -> 200  (171202 bytes)
  info.title        : Arkadia Mind — Cycle 11
  operations        : 274
  exact "/health"   : ABSENT
  "/api/heartbeat"  : present
```

The only `/health` substrings in the deployed schema are
`/api/knowledge/graph/health` and `/api/knowledge/providers/health` — unrelated
routes. The deployed backend genuinely serves no `/health`.


## 2. Three independent repository surfaces already assumed it existed

| surface | evidence |
|---|---|
| rate limiter | `api/rate_limit.py` — `EXEMPT_PREFIXES` exempts `"/health"` from rate limiting |
| deployment doc | `DEPLOYMENT_GUIDE.md` — "`GET /health` - Health check"; `curl https://your-app.onrender.com/health` |
| operator runbook | `UPTIMEROBOT_SETUP.md` — Render free tier sleeps after 15 min; the documented remedy is an uptime monitor |

An exemption and an operator instruction naming a path that no route serves is a
silent contract violation: a monitor configured faithfully from the repository
would report the service **down** while the service was healthy.

## 3. The existing Gate-2 evidence claimed a 200 that proves nothing

`docs/control-plane/evidence/gate2-public-runtime-integrity/EVIDENCE.md` §5 lists
`/api/health` among paths that "returned HTTP 200" on the production alias.

Measured this pass on `https://arkadia-prism.vercel.app`:

```
/api/health                     -> 200  text/html  997 bytes
/this-path-does-not-exist-xyz   -> 200  text/html  997 bytes   (identical)
/solariun                       -> 200  text/html  997 bytes   (identical)
```

The frontend is a Vite SPA whose catch-all returns the same 997-byte shell for
**every** path. A 200 from that host is therefore **vacuous** — it is not evidence
that any API route exists. The §5 claim is true as written and carries no
provenance weight; it should not be read as route-existence evidence.

## 4. Repair

`api/main.py` — one route, added adjacent to the canonical liveness signal:

```python
@app.get("/health")
async def health():
    # Projection of the canonical /api/heartbeat liveness signal, not a second
    # liveness path: the status is read from heartbeat() so the two endpoints
    # cannot disagree. /health exists because the deployment contract already
    # points at it — api/rate_limit.EXEMPT_PREFIXES exempts "/health", and
    # DEPLOYMENT_GUIDE.md directs operators to probe it.
    return {"status": (await heartbeat())["status"], "path": "/health"}
```

**Design constraint — one liveness authority.** `/health` does not define its own
status. It reads `heartbeat()`'s value, so the two endpoints cannot drift. It
introduces no second liveness path, no second authority, and no mutation path.
The response surface is deliberately bounded to liveness only: a monitor endpoint
is unauthenticated by necessity and must not publish detail the canonical signal
does not already publish.

## 5. Evidence

```
tests/test_production_health_route.py        5 passed
tests/architecture                          11 passed
CP10 mutation boundary --judge (full set)    PASS
python -m py_compile api/main.py             OK
api/main.py line budget                      2529 / 2600
```

### Baseline comparison — no regression

Both trees measured with identical flags (`--continue-on-collection-errors -p no:randomly`):

| tree | result | failing nodes |
|---|---|---|
| BASE_MAIN `002b189` | 20 failed / 1041 passed / 11 skipped / 2 errors | 22 |
| this branch | 20 failed / **1046** passed / 11 skipped / 2 errors | **22** |

Set comparison of failing nodes: **zero newly failing, zero newly passing.** The
passed count rises by exactly 5 — the new tests. No other fingerprint movement.

## 6. Falsifiability — negative controls

Each assertion was proven to fail when the behaviour it guards is broken. The
mutation was applied to `api/main.py`, measured, then restored **byte-identical**
(`diff -q` confirmed).

| control | mutation | result |
|---|---|---|
| NC-0 | none (repaired tree) | 5 passed |
| NC-1 | route renamed away — the original defect | 4 failed / 1 passed |
| NC-2 | `/health` hardcodes its own status (drift from canonical) | 1 failed / 4 passed |
| NC-3 | `/health` also returns `resonance` + `key_count` (unbounded surface) | 1 failed / 4 passed |
| NC-4 | restored | 5 passed, `api/main.py` byte-identical |

NC-1 is the incident replay: removing the route reproduces the 404 condition and
reddens four assertions. NC-2 and NC-3 are the forward guards — they make the
*projection* and the *bounded surface* properties falsifiable, not just existence.

## 7. What this does NOT establish

- **It is not production parity.** This is a repository-layer repair. Production
  still runs the previously deployed revision until a human deploys.
- **The live 404 will persist until redeploy.** No deployment was performed and
  none is claimed. Deployment identity remains a separate, unresolved boundary.
- **No deploy identity was obtainable this pass.** No `VERCEL_TOKEN` /
  `RENDER_API_KEY` is present in the environment, so the deployed revision SHA
  could not be resolved. The `main SHA -> deployment SHA` link stays **UNKNOWN**.
  Per the contract, `UNKNOWN` is not promoted to `VERIFIED` by repetition.

## 8. Remaining uncertainty

- **This change moves PR #143's operation-signature oracle.** Measured exactly:

  | tree | operations | digest |
  |---|---|---|
  | deployed (`5e26d095…`) | 274 | `d1797f9c…e30b` |
  | this branch | **275** | `359677ac…3301` |

  The delta is exactly one row, `GET /health :: Health ::`; nothing else is added
  or removed. PR #143 (`gate-hygiene/gate2-production-parity-02`) uses that digest
  to assert *deployed matches main*. Because this branch adds one operation, that
  oracle will report a mismatch **until this branch is merged and redeployed** —
  which is the correct and expected reading, not a defect in either change. PR
  #143's own tests are synthetic (`_spec`-built) and hardcode no operation count,
  so the two changes do not conflict; only the live measurement shifts.
- `DEPLOYMENT_GUIDE.md` additionally documents `GET /status`, `POST /oracle`,
  `GET /threads` — **none of which exist** in the current application. That page
  appears to describe a legacy Replit-era surface. Recorded here as a
  **discovered** defect, deliberately **not** repaired: it is outside this
  bounded scope and does not gate the health-route invariant. It is a candidate
  for its own bounded pass.
- `railway.json` sets `healthcheckPath: /api/heartbeat` and `openclaw/render.yaml`
  sets `/health`. Both now resolve against real routes, but neither config governs
  the actual Render service, whose health-check path could not be read without
  provider credentials.

## 9. Regression boundary

No authority, governance, identity, or mutation surface is touched. One additive
route on the canonical liveness signal plus one additive test module. No existing
test modified, no `AGENTS.md` byte modified, no second authority path created.
