# EVIDENCE — gate-hygiene / current-tip composition batch 01

Bounded objective: measure, on the **current** `main` tip, whether the open
uncovered-debt PR cluster composes into a green tree, and record the integration
hazard that distorted an earlier measurement. Evidence-only; no product code,
workflow, or authority surface is changed.

Status: **IMPLEMENTED** (repository-source measurement). No production claim.

## 1. Revision under measurement

| Field | Value |
|---|---|
| BASE_MAIN | `a47ea92817436675c15d472ca80f39d7295e880a` (2026-10-09 10:56:38 +0100) |
| Subject | Add read-only operator security verification control |
| Python | 3.13 · pytest 9.1.1 |
| Env | `PYTHONPATH=archive/legacy_python`, `-p no:randomly`, `--continue-on-collection-errors -rEf` |

## 2. Baseline fingerprint (`main` @ `a47ea928`)

Full-suite run on the unmodified tip:

- **16** failing/error nodes (`3 collection errors` semantics preserved by
  `--continue-on-collection-errors`).
- outcomes fingerprint `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`
- ids fingerprint `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833`

Every actionable node is owned by an open PR; two are sovereign-reserved:

| Node | Owner |
|---|---|
| `test_m02a_ci_gate_integrity.py::test_allowlist_*` (3) | #354 |
| `test_engineering_lab_api.py::test_lab_*` (2) | #356 (authority surface — sovereign review) |
| `test_solspire_r1/r3_*` (3) | #357 |
| `test_identity_spine_w1.py`, `test_m02_reasomate_truth.py` (2) | #363 |
| `test_steward_filter.py` (3) | #365 |
| `test_ais_capability_profile_onboarding.py::test_home_*` (1) | #347 |
| `test_autonomy.py` (ERROR) | CE-01 · weaver.autonomy module/package collision · **sovereign-reserved** |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | F-01 · proxy-invalidation · **unowned / awaiting sovereign decision** |

## 3. Composed tree — faithful application

The batch **#354 + #356 + #357 + #363 + #365 + #347** was applied onto a detached
worktree at `a47ea928` in that order, each via `git apply --3way`.

**Critical:** every one of these PRs also touches the shared `AGENTS.md` tail,
so each produces a `UU AGENTS.md` conflict. `AGENTS.md` is excluded from the
patch application (`--exclude=AGENTS.md`) because resolving it is not part of
this bounded task and its content is governed separately (the insertion-only
constraint recorded in repo memory).

Result on the faithful composed tree:

```
tests/test_m02a_ci_gate_integrity.py
tests/test_engineering_lab_api.py
tests/test_solspire_r1_governance_convergence.py
tests/test_solspire_r3_execution_runtime.py
tests/test_steward_filter.py
tests/test_identity_spine_w1.py
tests/test_m02_reasomate_truth.py
tests/test_ais_capability_profile_onboarding.py
tests/architecture
-> 124 passed
```

Full suite on the composed tree:

```
1 failed, 1857 passed, 20 skipped, 2 warnings, 1 error
ERROR  tests/test_autonomy.py                                   (CE-01, sovereign-reserved)
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate  (F-01, unowned)
```

- **2** nodes remain — exactly the two sovereign-reserved nodes.
- outcomes fingerprint `f607dffd1abda8bc667897a4366c6afe1498ae6e5b02635ff682cbc6daeb2ad1`
- ids fingerprint `48e2b758b3194bd267e7babf13609b3467ff46985a879c72a55ad5201f44b3a9`
- architecture fitness: **11 passed** (`main` @ `4550531` recorded 2805-line budget debt separately).
- CP10 boundary judge (`scripts/cp10_mutation_boundary_policy.py --judge`) on the
  composition: **PASS** (exit 0).

Node delta vs baseline: **16 → 2** (`-14`), with **0** unexplained new nodes.

## 4. Integration hazard — a chained `--3way` apply silently drops files

The measurement above is only reachable because the hazard below was diagnosed
and corrected. A first pass applied the same PRs **without** `--exclude=AGENTS.md`
in a single chained loop. `git apply --3way` reported:

```
U AGENTS.md
```

and stopped applying the **remaining files** of that PR — silently. Concretely,
#356's `tests/test_engineering_lab_api.py` and #357/#363's test files never
landed, yet the loop printed a per-PR "applied" line. The composed tree then
reported **7 failed**, which would have been misread as "the batch does not
compose / introduces regressions."

Corrected run (excluding `AGENTS.md`): **124 passed**, and the full suite leaves
only the two reserved nodes.

**Rule for the next pass:** when composing PRs that share `AGENTS.md`, verify
each PR's own files are present after apply (`git status --porcelain`) rather
than trusting the loop's success text; a `UU` on a shared file truncates a
chained `--3way` application. Measure the *faithful* tree, then attribute.

## 5. Gate-2 state re-derivation (must not be inherited)

`scripts/gate2_production_observation.py` re-run at `a47ea928`:

- **main → deployment: VERIFIED.** Newest Production deployment
  (`id=6957911584`) has `ref == sha == a47ea928…`, so the deployment record
  names the source SHA exactly.
- **Deployment build output: BLOCKED** — the deployment-specific
  `environment_url` is behind Vercel Deployment Protection (302 → SSO). This is
  a provider-auth boundary, not repository work.
- **Alias** `https://arkadia-prism.vercel.app/`: HTTP **200**.
- **Marker-set oracle: NOT OBSERVED / soundness defect.** The alias resolves to
  the **Console** application, not the **Prism** application the marker list
  describes; scoring one app's artifact against another's markers yields the
  false-absence signals recorded in prior passes. PR **#366**
  (`gate2-marker-oracle-soundness-01`) owns this repair and is not yet merged,
  so the harness on `main` still carries it.

Gate-2's earlier `UNKNOWN` (last-mile deploys landing on Render) is **RESOLVED**
by this re-derivation; the remaining boundary is provider-SSO (`BLOCKED`), not
repository work. Per the contract, `BLOCKED`/`UNKNOWN` are never promoted to
`VERIFIED` by repetition.

## 6. Authority boundary

- No product code, workflow, mutation path, authorization path, or governance
  surface is changed by this record.
- Merging the batch is **sovereign-only**. `#356` repairs a pin over
  `api/lab_routes.py`, an authority surface; `#354` touches the CP10 boundary
  policy. This document measures and reports; it does not merge or authorize.
- No push to `main`; the change is delivered as a branch → PR for human review.

## 7. Remaining uncertainty

- The composition was measured by patch application, not by merging the PR
  branches. A clean `--3way` proves no textual conflict; the tests prove the
  composed tree passes, but branch ancestry (`main` has moved since several PR
  bases) is not itself proven mergeable by this method.
- The 16-node baseline includes collection-error semantics; the recorded
  `tests/fixtures/baseline_node_set.txt` (10 nodes) differs from the live
  measurement and is owned by the open reconciliation workstream.
