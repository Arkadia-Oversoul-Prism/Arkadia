# WORKSTREAM STATE — gate-hygiene/repair-two-standalone-stale-pins

**Pass:** 1
**Observed:** 2026-10-08T22:06Z
**BASE_MAIN:** `24a00f856a0286cbb464a4b585117dd57a2646fa` (`git log -1 origin/main`)
**Branch:** `gate-hygiene/repair-two-standalone-stale-pins`
**Status:** `IMPLEMENTED` — ready for sovereign review

## Objective

Repair the two full-suite failures that no open PR owns, and settle whether they are
test-side stale pins or evidence of a production defect.

## Live inventory at pass start

Measured via `GET /pulls?state=open` with the `github_token` secret; repo permissions
`{admin, maintain, push, triage, pull}` - **not read-only**, so no credential HARD STOP.
**Open PRs: 14.**

Standalone claim, verified per PR with `GET /pulls/{n}/files`: **zero** of the 14 open PRs
touches `tests/test_identity_spine_w1.py`, `tests/test_m02_reasomate_truth.py`, or
`web/public_prism/src/pages/NodeEntry.tsx`. The two nodes in scope are unowned.

Ownership of the *other* 12 failing nodes, likewise measured:

```
PR #357  owns tests/test_solspire_r1_governance_convergence.py, tests/test_solspire_r3_execution_runtime.py
PR #356  owns tests/test_engineering_lab_api.py
PR #355  owns .github/workflows/n-atlas-developer-lab.yml  (test_ci_gate_trigger_coverage node)
PR #347  owns tests/test_ais_capability_profile_onboarding.py
PR #354  owns scripts/cp10_mutation_boundary_policy.py     (test_m02a_ci_gate_integrity nodes)
unowned  test_steward_filter.py (3), test_ais_w2_living_gate_grove_handoff.py (1),
         test_autonomy.py (CE-01 collection error, reserved to the sovereign)
```

Full open-PR inventory:

```
#362  chore/natlas-provider-forensics
#361  gate-hygiene/open-pr-owned-baseline-drift-01
#358  gate-hygiene/open-pr-cluster-composability-01
#357  gate-hygiene/solspire-r1-r3-contract-repin
#356  gate-hygiene/lab-boundary-natlas-surface-01
#355  gate10/n-atlas-workflow-self-trigger-01
#354  gate10/cp10-allowlist-deploy-surface-01
#351  gate01/portfolio-initiative-slice
#350  gate01/ark-200k-portfolio-substrate-plan
#349  feat/voice-of-belonging-content-pipeline
#348  gate-hygiene/post-merge-verification-07
#347  gate-hygiene/landing-headline-repin-01
#338  aeas-browser-runner-01
#337  aeas-01-native-operator-surface
```

`#337`/`#338` are a measured dependency pair (component + its browser instrument) and must not
be composed as if independent - recorded in `#358`'s manifest, not re-derived here.

Composition note: `#358`'s guard reads a **frozen JSON manifest** of a measured PR population,
not the live PR list, so adding this PR cannot redden it.

## CI state at PR open (measured)

PR **#363**, head `20008f0cb110497d695ed7ad2b12213c4b92fd5a`, base `main` @ `24a00f85`.
All 7 check-runs **completed / success**: `native-arkadia-golden-workflow`,
`bundle-beta-evidence`, `Vercel Preview Comments`, `beta-beta-01-english`,
`beta-beta-02-hausa`, `Full-history secret scan`, `validate`. Workflow runs on the branch:
`security-secret-scan` success, `N-ATLAS external beta validation` success,
**`SG-02-FE.2-V` success** — the CP10 mutation boundary actually executed, because this PR
touches `web/public_prism/**`, one of its trigger paths. `mergeable: true`.

Note: `Vercel - arkadia-prism` / `Vercel - console` are known **failure on `main` itself**, so a
Vercel failure here would not be attributable to this PR. Neither appears in this run's
check-runs.

Glance posted: PR #363 comment `6070974327`.

## Next-action block

- **Current state:** two stale pins repaired; one production `ReferenceError` fixed; zero new
  failing nodes; build green.
- **Evidence:** `EVIDENCE.md` (this directory). Base node-set sha256
  `26c2b4c7…`, branch `9a6239ae…`, delta exactly the two repaired nodes.
- **Blockers:** none for this pass.
- **Authorized action:** sovereign review and merge of this PR.
- **Forbidden actions:** merging (human only); touching
  `test_no_firebase_persistence_in_gate`; forcing `AIS_CAPABILITIES`/`GROVE_DOMAINS` into
  `NodeEntry`; repairing CE-01 (`weaver.autonomy`); fixing PR-owned nodes.
- **Completion condition:** PR merged by the sovereign, then a fresh heartbeat reconstructs
  state from `main` and re-measures the fingerprint.

## Next bounded task (proposed, not executed)

`gate-hygiene/reconcile-open-pr-owned-fingerprint-01` — after the open gate-hygiene cluster
(#347, #354, #355, #356, #357, #358, #361) merges in its governed order, re-derive the baseline
node set and reconcile `tests/fixtures/baseline_node_set.txt`. Not started: it depends on
merges this pass may not perform.
