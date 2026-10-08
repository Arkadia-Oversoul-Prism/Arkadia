# WORKSTREAM STATE — gate-hygiene/repair-two-standalone-stale-pins

**Pass:** 2
**Observed:** 2026-10-08T22:06Z (pass 1) / 2026-10-08T23:43Z (pass 2 — see §Pass 2 below)
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

---

## Pass 2 — open-PR inventory re-measured; a transient external CI flake, not a regression

**Observed:** 2026-10-08T23:43Z. **Head:** `99dc2e19` (base unchanged, `24a00f85`).

### The inventory moved, so the standalone claim was re-measured — not inherited

`GET /pulls?state=open` now returns **15**, not the 14 recorded in pass 1 (`#362`
`chore/natlas-provider-forensics` arrived). The standalone claim is load-bearing, so it was
re-verified against the **current** population rather than copied forward. For each of the 15,
`GET /pulls/{n}/files`: **zero** touch `tests/test_identity_spine_w1.py`,
`tests/test_m02_reasomate_truth.py`, or `web/public_prism/src/pages/NodeEntry.tsx` — except
this PR itself. Both nodes remain unowned. The claim survives the population change.

```
#337 files=5   #347 files=3   #349 files=4   #351 files=4   #355 files=1   #357 files=5   #361 files=13
#338 files=25  #348 files=2   #350 files=3   #354 files=4   #356 files=4   #358 files=8   #362 files=1
```

### Two checks went red on a docs-only commit — diagnosed, not attributed

At head `99dc2e19` (`AGENTS.md` + this directory only, no code) two N-ATLAS checks reported
`failure`: `beta-beta-02-hausa` and `bundle-beta-evidence`. A docs-only commit cannot change
runtime behaviour, so the failure was investigated before being reported either way.

The failing step emitted its own structured evidence:

```json
{"schema":"ARKADIA-NATLAS-EVIDENCE-001","status":"FAILED",
 "reason":"external runtime did not return usable inference","errors":[]}
```

`errors: []` — the probe recorded **no** transport or contract error. The discovery step had
just returned `HTTP 200` with the Space `RUNNING` on `zero-a10g`. The governed outcome was
therefore "the Space did not answer with usable inference in the window", i.e. an external
Hugging Face Space dependency, not a repository defect.

**The decisive measurement is a same-branch A/B on the same workflow:**

```
2026-10-08T23:22:15Z  success  4ae866f5  gate-hygiene/repair-two-standalone-stale-pins
2026-10-08T23:34:43Z  failure  99dc2e19  gate-hygiene/repair-two-standalone-stale-pins
```

`4ae866f5..99dc2e19` is docs-only, so the two runs differ by no executable input. One passed,
one failed. The delta is external and transient.

**Negative control (proves the re-run is evidence, not luck):** `gh run rerun 37860209404
--failed` on the **identical** commit `99dc2e19` → all four jobs `success`
(`beta-beta-01-english`, `beta-beta-02-hausa`, `bundle-beta-evidence`,
`native-arkadia-golden-workflow`). An unchanged tree producing pass-then-fail-then-pass is a
flaky external dependency; a real regression does not heal on re-run.

**Classification:** `beta-*` / `bundle-beta-evidence` failure at `99dc2e19` = **external
transient flake (HF Space `koladeodunope-ednai-natlas-runtime`)**. **Not attributable to this
PR**, and not to any commit. It has failed on `main`-lineage branches before
(`0e6ef310`, 2026-10-08T06:19Z) for the same reason.

### Final gate state at `99dc2e19`

All **7** check-runs `success`; `mergeable: true`, `mergeable_state: clean`; combined commit
status `success`.

```
native-arkadia-golden-workflow  success      beta-beta-01-english  success
bundle-beta-evidence            success      beta-beta-02-hausa    success
Vercel Preview Comments         success      Full-history secret scan  success
validate                        success
```

`native-arkadia-golden-workflow` reports `skipped` when the beta matrix is not selected; after
the re-run it executes and passes. Do not read a `skipped` conclusion as a pass.

### Pass 2 next-action block

- **Current state:** unchanged from pass 1 — two stale pins repaired, one production
  `ReferenceError` fixed, 0 new failing nodes; all gates green on `99dc2e19`.
- **Evidence:** this section, plus the check-run/`gh run view` output quoted above.
- **Blockers:** none.
- **Authorized action:** sovereign review and merge of PR #363.
- **Forbidden actions:** merging; re-pinning `test_no_firebase_persistence_in_gate`;
  touching CE-01; and — new this pass — **retrying an external-flake failure as if it were a
  code defect**. Re-run once, record the A/B, classify `external transient`, stop.
- **Completion condition:** PR #363 merged by the sovereign; a fresh heartbeat then
  re-measures the fingerprint from the new `main`.
