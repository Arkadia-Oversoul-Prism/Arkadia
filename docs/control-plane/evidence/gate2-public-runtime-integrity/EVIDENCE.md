# Gate 2 · Public Runtime & Evidence Integrity

**Status:** READY FOR REVIEW  
**Scope:** current main after Gate 1 merge  
**Authority:** human  
**Rule:** current runtime state must not be inferred from historical prose or stale deployment state.

## Current main

Gate 1 merged at `8f9d509ec4900408e13e15544192dba37fb08ff8`.

The current tree was inspected across the public contract, security boundary, Opportunity Radar capture, Solariun/SolSpire routing, frontend build configuration, and selected architecture records.

## Findings

### 1. Public surface coherence — PASS

The root README now describes Arkadia as an inspectable architecture rather than a finished product and points readers toward the public-surface contract, current code, Knowledge OS, Weaver, evidence, and Opportunity Radar.

### 2. Opportunity Radar projection — PASS

The Radar surface is a frontend projection backed by `opportunity_radar/SAPZ_CAPTURE_STATE.md` and `web/public_prism/src/data/opportunityRadar.ts`. No second database or authority path was introduced in the inspected surface. Unknown bidder status remains explicitly UNKNOWN.

### 3. Security evidence — PASS with documentation correction

The full-history secret scan passed on Gate 1's GitHub Actions run 36517612969. `SECURITY.md` on main still said the scan was pending, so this Gate 2 branch corrects that stale statement.

### 4. Production deployment parity — OPEN

A fresh Vercel deployment inventory was inspected on 2026-09-29.

The active production deployment observed is:

- deployment: `dpl_29GGe1PAb3VPtcHntMsAzTtmMc39`
- status: **READY**
- target: **production**
- production alias: `arkadia-prism.vercel.app`
- source ref: `main`
- source SHA: `5e26d0954157c81c2d0d919f5b6ea01943b7643d`

Current Git main is `8f9d509ec4900408e13e15544192dba37fb08ff8`.

Therefore production is confirmed reachable, but **not at current main**. The deployment boundary is now evidence-backed rather than inferred:

- current Git main: **8f9d509...**
- active production source: **5e26d095...**
- parity with current main: **FAILED / OPEN**
- no deployment or merge is claimed from this evidence pass.

A READY preview for the frontend calibration branch was also observed:

- deployment: `dpl_4nm8CG8DESAbiyG5WQSu5BBfv7ed`
- source ref: `aeas/frontend-brand-calibration`
- source SHA: `d9c5b74b13ba92b5b00b59d9b1130c138c589c58`

That preview is not production and does not establish main parity.

### 5. Production route reachability — PASS, but not production-parity evidence

The current production alias returned HTTP 200 for:

- `/`
- `/solariun`
- `/solariun/opportunity-radar`
- `/solspire`
- `/api/health`

These responses confirm route-level HTTP reachability. They do **not** prove that the deployed frontend corresponds to current main, nor do they prove browser-rendered UI correctness.

### 6. Runtime error surface — PASS for selected window

Vercel runtime-error aggregation for the project returned **no runtime errors in the selected 24-hour window** on 2026-09-29.

This is bounded evidence only. It does not substitute for browser/UI verification.

### 7. Frontend build — SUPPORTED, not independently rebuilt here

The repository contains the canonical Vite/pnpm build configuration and prior evidence records successful frontend builds, but this gate did not claim a fresh local build.

### 8. Historical references — EXPECTED

Historical references to prior Render endpoints and earlier checkpoints remain in archive/recon material. They are not treated as current operational configuration.

## Gate 2 closure criteria

1. Current main is merged and internally coherent. **PASS**
2. Security scan result is represented accurately. **PASS after this branch**
3. Current production deployment is verified against current main. **OPEN**
4. Public frontend route is verified against the current production build. **OPEN**
5. No stale operational claim is promoted to current truth. **PASS**
6. Production route reachability is evidenced. **PASS**
7. Browser-rendered UI and console/runtime behavior are independently verified. **OPEN**

## Reviewer decision point

Gate 2 is now a precise runtime handoff rather than a vague deployment concern. Production is reachable and operationally quiet in the selected error window, but it is demonstrably behind current main.

The next governed boundary is:

**current main → authorized deployment → production verification → browser/UI evidence**

**DON'T KNOW IS ALLOWED. The remaining unknown is now sharply bounded.**
