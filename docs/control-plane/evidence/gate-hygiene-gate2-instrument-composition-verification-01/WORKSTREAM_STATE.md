# WORKSTREAM STATE — gate-hygiene-gate2-instrument-composition-verification-01

## Current state

**Active workstream (agent-selected, non-duplicative):** independent verification of the
active Gate-2 PR **#378**, mounted on its own bounded branch. #378 is the current tip of a
5-PR same-subject cluster (#366, #368, #370, #378) repairing the Gate-2 production-observation
instrument.

**Boundary reconstruction at this pass (2026-10-09):**

| Boundary | State | Evidence |
|---|---|---|
| current main resolved | **VERIFIED** | `main` `a47ea92817436675c15d472ca80f39d7295e880a` |
| main -> deployment identity | **VERIFIED** | newest Production deploy `a47ea9281743`, id `6957911584`, ref == sha == main |
| deployment build output observed | **BLOCKED** | deployment-specific URL → 302 SSO (Vercel Deployment Protection) |
| marker-set oracle | **NOT OBSERVED** | alias serves Console (`<title>Arkadia Console</title>`); markers describe arkadia-prism |
| build <-> source lineage | **UNKNOWN** | `source_lineage_closed = false` (candidates `a47ea928`/`d2dd0e75` straddle build-input commit `b3834ecf`) |
| production acceptance | **NOT CLAIMED** | human authority |

## Finding

The composed **content** of #378 is verified: 39 gate2 tests pass, architecture 11/11,
CP10 judge PASS, full-suite failing/error node set byte-identical to `main`
(`bfcfe592…` / `ed5e4714…`, 16 nodes). The #366 marker-oracle repair works — the harness
no longer emits a false `SG-04 REGRESSION`.

The composed **premise** is stale: PR #368 merged #366 into its own branch at `9837213f`
(2026-10-09 08:12Z), ~5 h **before** #378 was created (13:22Z). #368's head `aa6f4d2c`
carries both repairs (`4db47217…`); a plain `git merge pr368` onto `main` is conflict-free
and keeps both. #378's head is blob-identical to #368 **except** for its own EVIDENCE.md.
#378's body's "pre-#366 base" / "plain merge loses a repair" / "composed blob `cf09b073…`"
claims do not hold.

## Next bounded task (proposed, not executed)

Correct the #378 body's stale claims (or record the finding and let the sovereign choose
#368 vs #378 for merge). Merge one of the pair, not both.

## Authority boundary

No merge, no self-authorization. #378 / #368 / #366 / #370 remain open for sovereign
decision. This branch is evidence-only.
