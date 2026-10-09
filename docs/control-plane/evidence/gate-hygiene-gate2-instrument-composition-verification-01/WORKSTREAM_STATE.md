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

## Pass 2 — main drift correction + precision fix (2026-10-09)

**main has moved since this branch was authored.** The pass-1 table recorded
`current main resolved = VERIFIED @ a47ea928`. Live `origin/main` is now
`d466e13786a3925d26fd3f7eafb631c9cdc9dad1` (5 commits ahead: `8e5815d3` →
`d466e137`, the runtime-Firebase-config series). `a47ea928..d466e137` touches only
`entrypoint.sh`, `web/public_prism/index.html`, `web/public_prism/src/lib/firebase.ts`
— **none of the Gate-2 instrument files**. The composed content of #378 remains
orthogonal to the drift, but the pass-1 row is now **STALE**, not VERIFIED.

**Newest Production deployment vs main:** the newest Production deploy remains
`a47ea9281743` (id `6957911584`), so `deploy SHA == main` is **False**; the boundary
**main → deployment identity** is now **STALE** at `d466e137` (the deploy predates the
5 Firebase commits). Deployment-URL observation stays **BLOCKED** (SSO).

**Precision fix to the pass-1 "blob-identical except EVIDENCE.md" claim.** The claim is
true only of the *Gate-2 instrument files*. Head `aa6f4d2c` (#368) vs `19dca505` (#378)
differ on 10 paths; the Gate-2 files among them are byte-identical:
`scripts/gate2_production_observation.py` `4db472176d`, `vercel.json` `ccebe6abbd`,
`tests/test_gate2_production_observation.py` `412734789f` — SAME on both heads. The other
paths are **main-drift, not a #368↔#378 design difference**: #368 branched at
`43c3e2b1`, #378 at `a47ea928`, and the operator-security surface
(`api/operator_security_routes.py`, `web/console/src/surfaces/SecurityVerification.tsx`,
`tests/test_operator_security_verification.py`, `web/console/src/{auth/AuthContext,
components/Layout,main}.tsx`, `.github/workflows/n-atlas-developer-lab.yml`,
`docs/verification/OPERATOR_SECURITY_CONTROL.md`) landed between those bases. Only
`docs/.../gate-hygiene-gate2-instrument-composition-01/EVIDENCE.md` is a genuine #378-side
difference.

## Pass 2 — independent reproduction (evidence-only)

| Check | Result |
|---|---|
| full suite @ `main` `d466e137`, run **alone** (not concurrent) | **15F/1842P/17S/1E**, node set `bfcfe592…`/`ed5e4714…`, 16 nodes |
| full suite @ composed `main+#368+#378` (`/tmp/compose`) | **15F/1862P/17S/1E**, **identical** 16-node set |
| full suite @ #368-only (post-#366 head) | **identical** 16-node set |
| CP10 judge on composed branch diff | **PASS** (exit 0) |
| `agents_md_encoding_audit.py` on composed tree | `alterations=0`, `cyrillic=0`, oracle `6c43218a48a4` reproduced |
| `py_compile api/main.py` (composed) | OK, 2450 lines (budget 2600) |

**Measurement-hygiene finding:** a *concurrent* full-suite run produced 17 nodes /
33 skipped plus a spurious
`test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable`
failure and a `test_steward_filter.py` failure — both absent from a clean serial re-run,
and `test_corruption_origin_is_re_derivable` passes in isolation on **both** trees. That
node runs `git show` over AGENTS.md history; under parallel git load it can mis-attribute
the first corrupt revision. Do **not** run independent full suites concurrently in one
clone; the artifact reproduces as a phantom one-node delta and would be mis-read as a
regression. Standing rule (already in `main`'s AGENTS.md): compare the failing/error node
**set**, never the counts.
