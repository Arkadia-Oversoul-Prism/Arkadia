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

The Vercel project has a READY production deployment for the pre-Gate-1 main commit `5e26d095...`. A current READY preview exists for the Gate 1 branch, but the merged Gate 1 commit has not been independently verified as the production deployment.

The available Vercel deployment history also shows the recent production deployment path was affected by the Free-plan deployment-rate limit. Therefore:

- current Git main: **8f9d509...**
- latest verified production deployment observed: **5e26d095...**
- production parity with Gate 1: **UNKNOWN / NOT YET VERIFIED**
- no production deployment is forced by this gate.

### 5. Frontend build — SUPPORTED, not independently rebuilt here

The repository contains the canonical Vite/pnpm build configuration and prior evidence records successful frontend builds, but this gate did not claim a fresh local build. Existing repository guidance records the sandbox's registry/toolchain limitation.

### 6. Historical references — EXPECTED

Historical references to prior Render endpoints and earlier checkpoints remain in archive/recon material. They are not treated as current operational configuration. Active production configuration inspected here points to the current Render endpoint.

## Gate 2 closure criteria

1. Current main is merged and internally coherent. **PASS**
2. Security scan result is represented accurately. **PASS after this branch**
3. Current production deployment is verified against current main. **OPEN**
4. Public frontend route is verified against the current production build. **OPEN**
5. No stale operational claim is promoted to current truth. **PASS**

## Reviewer decision point

Gate 2 is ready for review as a bounded evidence correction. It should not be called fully closed until production parity is independently verified.

**DON'T KNOW IS ALLOWED. The deployment boundary is the unknown.**
