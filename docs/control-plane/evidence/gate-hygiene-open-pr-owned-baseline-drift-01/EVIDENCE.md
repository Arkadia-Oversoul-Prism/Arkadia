# EVIDENCE — gate-hygiene/open-pr-owned-baseline-drift-01

Bounded workstream: **reconcile the recorded baseline test-debt node set with a live `main`
measurement**, attribute the newly-recorded nodes to the open pull requests that repair
them, and make the reconciliation *compositional* so a future addition cannot be silently
absorbed. Test-side and evidence only — no production code, no merge, nothing pushed to
`main`.

## 1. Reconstruction (live evidence)

| item | value |
|---|---|
| canonical repo | `https://github.com/Arkadia-Oversoul-Prism/Arkadia` |
| BASE_MAIN (`origin/main`) | `441379913d1b03ceb6a5af45ea543ca6762cb482` — "Expose null Gradio error diagnostics (#360)" |
| clone | not shallow; working tree carried this pass's edits (prior automation session) |
| open PRs at start | 12 (see §5) |
| observation timestamp | `2026-10-08T07:1xZ` |

The live tip was re-derived from three independent sources and they agree: `git log -1`,
`git rev-parse origin/main`, and the GitHub API `branches/main` all report
`441379913d1b03ceb6a5af45ea543ca6762cb482`.

## 2. The recorded set was a subset of the live debt — 10 recorded, 17 live

A live full-suite run on `main` `44137991` (`python -m pytest tests/ -q -rEf
--continue-on-collection-errors`, `PYTHONPATH=archive/legacy_python`) reports:

```
16 failed, 1776 passed, 22 skipped, 2 warnings, 1 error in 143.13s
```

**17** failing/error nodes. `tests/fixtures/baseline_node_set.txt` recorded **10**. The 7
unrecorded nodes are each repaired by an open PR, so they are baseline debt a merge will
remove — not regressions:

> Re-measured at `44137991` (this pass's independent verification): `main` itself is
> **16F / 1772P / 22S / 1E**; the 1776P figure above is this *branch* (the +4 passed are the
> four new guard functions). The failing/error node set is identical on both sides.

| node | owner PR |
|---|---|
| `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | #347 |
| `test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]` | #355 |
| `test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | #356 |
| `test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` | #356 |
| `test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix` | #354 |
| `test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface` | #354 |
| `test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface` | #354 |

The attribution is recorded machine-readably in
`tests/fixtures/open_pr_owned_drift_node_set.txt` (`<node id>\t<owner PR>`), so the next pass
does not re-derive it and a node that leaves `main` without its owner merging is visible.

### 2.1 Independent verification of the attribution (this pass)

Every attributed node was re-checked by checking out each owner's head and running the node
there — a node fails on `main` and must pass at its owner's head, or the attribution is only
a claim:

| owner PR | head verified | node(s) run | result |
|---|---|---|---|
| #347 | `3f3024d9` | `test_home_is_offer_led_and_keeps_arkadia_entry_points` | 1 passed |
| #354 | `536a8c43` | `test_m02a_ci_gate_integrity.py` (file) | 64 passed |
| #355 | `73104fdf` | `test_ci_gate_trigger_coverage.py` (file) | 48 passed |
| #356 | `1bfbcc4f` | `test_engineering_lab_api.py` (file) | 5 passed |

All 7 attributed nodes pass at their owners' heads. The 10 era-set nodes are **not** uniformly
unowned: PR #357 (head `4c3d8fb8`) repairs three of them —
`test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver`,
`…::test_r1_weaver_governance_is_canonical`, and
`test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
(fail on `main`, 3 passed at #357's head). The remaining seven era-set nodes
(`test_autonomy.py` ERROR, `test_steward_filter.py`, `test_identity_spine_w1.py`,
`test_m02_reasomate_truth.py`, `test_ais_w2_living_gate_grove_handoff.py`) have no open-PR
owner — `gh pr view <n> --json files` across #337–#360 shows no PR touching them, so they
remain pre-existing era debt. Either way the recorded set shrinks on merge: whether a node is
repaired by a drift-set owner or an era-set owner, the next pass must re-measure rather than
reuse this pair.

## 3. Canonical fingerprint (fixture and a live run agree)

```
python scripts/baseline_fingerprint.py <log>
  failing/error nodes : 17 (16 failed, 1 error)
  outcomes fingerprint: 26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798
  ids fingerprint     : 571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224
```

The same pair is produced from `tests/fixtures/baseline_node_set.txt` and from the live run
log, and the fingerprints are unchanged when the run is repeated in this environment (two
independent full runs, same node set).

Superseded pairs remain reproducible from era-correct fixtures rather than prose:
`6c7bf821…`/`2bc35996…` from `superseded_baseline_node_set_18.txt` and
`9a54f5b4…`/`124bfdfd…` from `superseded_baseline_node_set_10.txt`. Every superseded value
is excluded by `test_superseded_fingerprints_are_not_reproducible`.

## 4. Compositional guard (rejects a silently-absorbed node)

`test_live_node_set_is_the_era_set_plus_the_open_pr_owned_set` asserts the strong relation

```
LIVE_NODE_SET == SUPERSEDED_10_NODE_SET | OPEN_PR_OWNED_SET
```

with `SUPERSEDED_10_NODE_SET` still a subset of `LIVE_NODE_SET` (the 2026-10-04 pass only
*removed* entries, this pass *adds*). A node in the recorded set owned by neither the era set
nor an open PR would mean a new failure was silently absorbed into the baseline instead of
being attributed. `test_era_set_composition_rejects_an_unattributed_node` is the negative
control: it feeds the same predicate a synthetic recorded set carrying an unattributed node
and confirms the predicate flags it. `test_open_pr_owned_nodes_are_all_recorded_baseline_debt`
and `test_open_pr_owned_entries_each_name_a_pr` are the mirror guards — a listed node that
`main` does not fail, or an entry with no owner PR, fails.

## 5. Open-PR inventory (`state=open`, measured)

| PR | head | base | mergeable | files |
|---|---|---|---|---|
| #358 gate-hygiene: measured composability of the uncovered-debt PR cluster (#354-#357) | `0e6ef310` | `f96d5fd2` | unstable | 8 |
| #357 gate-hygiene: re-pin SolSpire R1/R3 contracts after convergence drift | `4c3d8fb8` | `f96d5fd2` | unstable | 5 |
| #356 gate-hygiene: align Engineering Lab boundary guard with the N-ATLaS surface added by #353 | `1bfbcc4f` | `f96d5fd2` | unstable | 4 |
| #355 GATE-10: n-atlas workflow must be selected by its own file | `73104fdf` | `f96d5fd2` | clean | 1 |
| #354 GATE-10: admit tracked deploy/ surface to CP10 allowlist | `536a8c43` | `f96d5fd2` | unstable | 4 |
| #351 feat: establish Gate 01 portfolio initiative slice | `c34efd53` | `ff3f6d42` | unstable | 4 |
| #350 gate01: ARK-$200K-G01 plan + proof-test proposal (documentation-only) | `14a0db25` | `af3a3541` | unstable | 3 |
| #349 content: build governed Voice of Belonging cadence pipeline | `3b1460f4` | `af3a3541` | unstable | 4 |
| #348 gate-hygiene/post-merge-verification-07 | `2d88868c` | `af3a3541` | clean | 2 |
| #347 test(gate-hygiene): re-pin drifted landing-headline assertion (repin-01) | `3f3024d9` | `af3a3541` | unstable | 3 |
| #338 AEAS browser runner 01 | `903acf41` | `17e626cd` | **dirty** | 25 |
| #337 AEAS-01 native Engineering Lab operator surface | `acf13ff1` | `af3a3541` | unstable | 5 |

#358 is the recorded carrier of the §2 attribution; #354/#355/#356 carry the CP10/CI-gate
repairs; #347 carries the landing-headline re-pin. None is merged by this pass.

## 6. Verification

```
python -m pytest tests/architecture -q                       -> 11 passed
python -m pytest tests/test_baseline_fingerprint.py -q       -> 28 passed
python -m pytest tests/test_m02a_ci_gate_integrity.py -q     -> 3 failed, 61 passed
python -m py_compile api/main.py                             -> ok (2462 / 2600 lines)
```

The full-suite failure node-set is **unchanged** between `main` and this branch: the branch
touches only `tests/`, fixtures and docs, and the fingerprint file's own tests all pass
(24 → 28 collected tests; +4 guard functions). No node enters or leaves the failing set.

## 7. Baseline debt NOT fixed here (recorded, attributed)

The run reports 17 failing/error nodes; every one is a distinct bounded workstream owned by
an open PR (§2) or a pre-existing `main` debt:

- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_*` (3 nodes) — the CP10 `LEGIT`
  allowlist omits the tracked `deploy/` surface (4 paths: `deploy/n-atlas-server/{Dockerfile,
  README.md,app.py,requirements.txt}`, tracked by `e074a63b`). This is exactly the
  allowlist-omission defect class `AGENTS.md` documents, and it is **owned by open PR #354**
  which admits the `deploy/` surface. Not re-fixed here to avoid a second, conflicting
  mutation of `scripts/cp10_mutation_boundary_policy.py`; the node is recorded as debt.
- `tests/test_steward_filter.py` (3 nodes), `test_ais_w2_living_gate_grove_handoff.py`,
  `test_identity_spine_w1.py`, `test_m02_reasomate_truth.py`, `test_solspire_r1_*` (2),
  `test_solspire_r3_execution_runtime.py` — pre-existing era debt, each already documented in
  prior evidence and repaired by its own workstream.
- `ERROR tests/test_autonomy.py` — the CE-01 `weaver.autonomy` module-vs-package collision,
  **reserved to the sovereign**; not touched.

## 8. Boundary

No merge, no push to `main`, no force-push, no production code change. The working branch is
`gate-hygiene/open-pr-owned-baseline-drift-01`; the human sovereign decides what becomes
canonical.
