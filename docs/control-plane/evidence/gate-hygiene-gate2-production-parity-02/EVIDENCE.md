# GATE-02 — Production Parity: deployment identity resolved, build observation BLOCKED

Pass: `gate-hygiene/gate2-production-parity-02`
Date: 2026-09-30 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Repository: `Arkadia-Oversoul-Prism/Arkadia`

## 1. Why this pass exists

Gate 2 was open on **production parity**. The handoff state required that a production
deployment be tied to a specific main SHA and that the resulting runtime behaviour be
independently observed. The previous Gate-2 evidence pass (`46c58fa`,
`gate2-public-runtime-integrity/EVIDENCE.md`) recorded route reachability only and
explicitly declined to claim parity.

This pass advances exactly one boundary: **resolve the deployment identity for current
main** — and then stop at the provider boundary that prevents observing it.

## 2. Deployment identity — RESOLVED (VERIFIED)

Queried via the GitHub Deployments API (the repository's own record of deployments, not
inferred prose):

```
GET /repos/Arkadia-Oversoul-Prism/Arkadia/deployments?environment=production&per_page=10
GET /repos/Arkadia-Oversoul-Prism/Arkadia/deployments/6749238709/statuses
```

The newest Production deployment is bound to **exactly the current main tip**:

| Field | Value |
| --- | --- |
| deployment id | `6749238709` |
| environment | `Production` |
| `ref` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| `sha` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| creator | `vercel[bot]` |
| created_at | `2026-09-30T01:23:16Z` |
| status | `success` |
| `environment_url` | `https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app` |
| status description | `Deployment has completed` |
| status created_at | `2026-09-30T01:23:17Z` |

Corroborating commit status on the main tip:

```
GET /repos/.../commits/002b189dd95e41c9b4f4cca33d08b4121453d289/status
  state: success   total_count: 1
  Vercel   success   2026-09-30T01:23:16Z
```

**Result:** the main→deployment link is now established from provider records.
`ref == sha == current main`. This is the link Gate 2 was missing.

This does **not** establish production parity on its own — it establishes the *identity*
of the deployment produced from current main. Observation is the next link (see §3).

## 3. Deployment build observation — BLOCKED (provider auth boundary)

The deployment-specific URL recorded by Vercel is not publicly readable:

```
GET https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app/
  → HTTP 302
  → https://vercel.com/login?next=/sso-api%3Furl%3D...arkadia-prism-ey2ozd5u4...
```

This is **Vercel Deployment Protection (SSO)**. The deployment is not anonymous-readable,
so its build output (asset manifest) cannot be observed without a Vercel credential that
this run does not hold.

Classification: **BLOCKED** — actionable external boundary (provider authentication).
Per contract this is not a puzzle to route around: no workaround was attempted.

## 4. Production alias — reachable, but does not close the parity chain

```
GET https://arkadia-prism.vercel.app/   → HTTP 200
```

The alias `index.html` references:

- `assets/index-CHFFyuSc.js`
- `assets/index-C2whHMVB.css`

The alias is reachable, but reachability alone cannot bind the alias to the `002b189`
deployment in this pass. Vercel assigns the Production alias to the newest Production
deployment, but that is **provider behaviour, not an observation made here**.

Classification: **UNKNOWN** — the alias→`002b189` binding is not directly observed.

### Asset-hash comparison is not a valid parity oracle

Carried forward from the SH-05 pass and re-affirmed: the build output is
environment-dependent. Injecting `VITE_API_BASE_URL` changes the emitted asset hash
(`index-xiYlcBh3.js` → `index-DIKNxYlc.js`) with no source change. Therefore an
alias-vs-local hash mismatch **must not** be reported as source divergence, and a hash
match would not by itself prove parity either. The oracle is unusable in both directions.

### HTTP 200 on any route is not evidence of application correctness

Root `vercel.json` rewrites `/(.*)` → `/index.html`. Consequently `/api/health` — which
`git log -S` shows never existed as a backend route — returns `200 text/html` (the SPA
shell) exactly as any non-existent path does. Route-level 200 responses on this project
are a property of the rewrite, not of the application. The prior pass's route-reachability
results must be read with this caveat.

## 5. Boundary classification for this pass

| Boundary | State |
| --- | --- |
| current main resolved | **VERIFIED** — `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| main → Production deployment identity | **VERIFIED** — deployment `6749238709`, `ref == sha == main` |
| deployment build output observed | **BLOCKED** — Vercel Deployment Protection (SSO) |
| alias serves the `002b189` deployment | **UNKNOWN** — not directly observed |
| browser-rendered UI correctness | **UNKNOWN** — no browser observation performed |
| production acceptance | **NOT CLAIMED** — human authority |

**Parity is NOT claimed.** The chain is now:

```
main SHA  ✓ VERIFIED
  → deployment SHA  ✓ VERIFIED (provider record, ref == sha)
    → deployment observation  ✗ BLOCKED (provider auth)
      → alias binding  ? UNKNOWN
        → UI/runtime observation  ? UNKNOWN
          → acceptance  — human sovereign
```

## 6. Exact handoff required to close Gate 2

One of:

1. A Vercel credential with access to project `arkadia-prism` — sufficient to read the
   `002b189` deployment's build output and confirm the alias binding; or
2. The Vercel Deployment Protection setting relaxed for this project (so the deployment
   URL becomes anonymous-readable); or
3. A browser/runtime observation performed by a party that holds such access, returning
   the deployment URL, asset manifest, route results and console state.

Absent one of these, no stronger claim than §5 is justified. Repeating this pass cannot
convert `BLOCKED`/`UNKNOWN` into `VERIFIED`.

## 7. Regression boundary

No product code was changed by this pass. This artifact is documentation only.
