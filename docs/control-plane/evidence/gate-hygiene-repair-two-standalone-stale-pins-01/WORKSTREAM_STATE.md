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

---

## Pass 3 — the pending measurement is done, it reproduces §4 byte-exactly, and the proposed next task is already owned

**Observed:** 2026-10-08T22:06Z. **BASE_MAIN:** `24a00f85` (unchanged).
**Head:** `c63c5f13` (`c63c5f131dc82b7a65a531f0ceb6e5be57eca3aa`), base unchanged.
**Open PRs:** 16 (was 15 in pass 2; `#364` arrived).

### 1. The full-suite fingerprint is now measured — and it confirms the recorded values

Pass 2 left this as its only pending item. It is now complete, run as a single backgrounded
command (`-rEf --continue-on-collection-errors`, the flag without which a collection error is
invisible to a line-based extractor — see the `-rf` lesson in `AGENTS.md`).

```
main @ 24a00f85  16 failed / 1775 passed / 19 skipped / 1 error   17 nodes  147.93s
#363 @ c63c5f13  14 failed / 1777 passed / 19 skipped / 1 error   15 nodes  144.81s
```

| convention | base `24a00f85` | head `c63c5f13` |
|---|---|---|
| outcomes sha256 | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` | `9a6239ae3aeb4a51d7629ff5a1cd65faaea461b3f1eb697171c84fcd6b01e8c1` |
| ids sha256 | `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224` | `0ea4bdd37ee6edbbeba45ce535eee885af76ce851bb0fbf34bd2fe226e3cdf31` |

The base pair is **byte-identical to the values `EVIDENCE.md` §4 already published**, re-derived
in a separate run — the recorded fingerprint reproduces. The node-set delta is exactly the two
in-scope nodes and nothing else:

```
base-only   tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
base-only   tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
branch-only (new regressions)  <none>
```

`-2 failed / +2 passed / 0 new nodes` — PR #363 is regression-free on the full suite, now
measured at the branch head rather than inherited from a prior pass.

### 2. The CP10 nodes are #354-owned, and this PR's own diff passes the boundary judge

Measured directly, not inferred from file-ownership alone. The PR's own changed paths are
admitted by the gate it is judged by:

```
git diff --name-only 24a00f85..HEAD | python scripts/cp10_mutation_boundary_policy.py --judge
  -> Mutation boundary PASS   (exit 0)
```

The full tracked corpus still fails, on exactly one path:

```
git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge
  -> Unexpected path outside legitimate surfaces: deploy/n-atlas-server/Dockerfile   (exit 1)
```

`deploy/` is the surface PR **#354** admits. So the three `test_m02a_ci_gate_integrity` nodes are
#354-owned pre-existing debt on `main`, not an effect of adding an evidence directory — a
result that file-ownership alone could not have distinguished from a self-inflicted reddening.

### 3. The proposed next bounded task is already implemented by open PR #361 — do not duplicate it

Pass 2 proposed `gate-hygiene/reconcile-open-pr-owned-fingerprint-01` as the next task. Measured
this pass: **open PR #361 is that task, already written.** `gate-hygiene/open-pr-owned-baseline-
drift-01` reconciles `tests/fixtures/baseline_node_set.txt`, attributes the drift to the open PRs
that repair it, and adds the era/drift/ownership fixtures plus ~380 lines of guard.

Its proposed 17-node fixture is **byte-identical to this pass's independent base measurement** —
same sha256 `26c2b4c7…`, same node set. Two independent measurements of `main @ 24a00f85` agree,
which is the strongest available confirmation short of a merge.

**Composition was measured, not asserted.** #361's patch was applied onto this PR's tree
(`git apply` of `git diff 441379913d1b pr361deep`, clean):

```
tests/test_baseline_fingerprint.py + tests/test_agents_md_encoding_adjudication.py
  -> 54 passed, 2 skipped   (composed tree)
```

No textual conflict and no semantic breakage. One caution for the next pass: #361's guards are
*set-membership* assertions, not exact-set equalities, so this PR's repairs do not redden them —
but a *future* PR that leaves the two repaired nodes failing **would**, because #361's fixture
records them as expected debt. That is a merge-order property of #361, not a defect in it.

**Decision: no new PR is opened.** Creating one would duplicate #361's scope, which the
continuity rule forbids. The proposed task is reclassified as `ALREADY_OWNED (#361)`.

### 4. The true stable remainder after the cluster merges

Subtracting every open-PR-owned node and this PR's two repairs, the residual unowned debt is
**5 nodes**, and each is a recorded, deliberate non-repair:

```
ERROR  tests/test_autonomy.py                                    CE-01 weaver.autonomy module-vs-package
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_compress_to_choices
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
```

`test_autonomy.py` reports only as `ERROR` on the base run, consistent with the CE-01 collision
interrupting collection; it is reserved to the sovereign. The `test_steward_filter` trio and the
`LivingGate` persistence node are pre-existing `main` debt with a recorded reason not to re-pin.

### 5. Pass 3 gate state at `c63c5f13`

All **7** check-runs `success`; `mergeable: true`, `mergeable_state: clean`; combined commit
status `success`.

```
Vercel Preview Comments  success    beta-beta-01-english     success
native-arkadia-golden-workflow success    beta-beta-02-hausa  success
bundle-beta-evidence     success    Full-history secret scan  success
validate                 success
```

### Pass 3 next-action block

- **Current state:** two stale pins repaired, one production `ReferenceError` fixed, full suite
  measured at the branch head — `0` new failing nodes, base fingerprint reproduced byte-exactly.
- **Evidence:** this section; `EVIDENCE.md` §4 (independently re-derived). Node-set sha256 base
  `26c2b4c7…` / head `9a6239ae…` (outcomes), `571e599f…` / `0ea4bdd3…` (ids).
- **Blockers:** none. No credential or dependency blocker this pass.
- **Authorized action:** sovereign review and merge of PR #363.
- **Forbidden actions:** merging; opening a duplicate of #361; re-pinning
  `test_no_firebase_persistence_in_gate`; repairing CE-01; fixing any PR-owned node; treating a
  fingerprint from the other convention as a non-reproduction.
- **Completion condition:** PR #363 merged by the sovereign. The next heartbeat then re-derives
  `main`'s fingerprint and, once the #354/#355/#356/#357/#361 cluster has merged, re-measures
  whether #361's recorded set still describes the tree (its own instruction: "re-measure, not
  reuse").
