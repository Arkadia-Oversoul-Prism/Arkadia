# WORKSTREAM STATE — gate10 CP10 allowlist deploy/ + growth/

**Pass:** 1 (revive)
**Branch:** `gate10/cp10-deploy-allowlist-revive-01`
**PR:** #399
**Base main:** `17b931b4fe6dd9b27749894dd0d9b1dc9a2e14f5`
**Status:** READY FOR MERGE (sovereign review required)

## Next bounded task
After #399 merges, `main` returns to a green CP10 completeness invariant. The two
regressions recorded on `main` are separate, pre-existing, and owned:
1. Voice order-dependence (8 nodes, sqlite closed-database) — needs a
   test-isolation fix, not a substrate change.
2. Static-ingestion ADR pin (`ADR-016` now exists) — test-side literal pin.

Each must be its own branch/PR; neither belongs to this allowlist workstream.

## Do not
- Do not widen CP10 by removing surfaces the repo genuinely tracks.
- Do not reclassify `REGISTERED_ARCHITECTURAL_DEBT` to pass the gate.
- Do not fold the voice/static fixes into this PR.
