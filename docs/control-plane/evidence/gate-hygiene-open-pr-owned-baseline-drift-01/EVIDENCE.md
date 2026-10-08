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

## 8. Addendum — the depth-1 clone's extra nodes: four, not one (this pass, 2026-10-08)

The clone-depth guard above named **two** nodes, and both were described as ones that
*skip* without a pinned revision. But a bare-clone run does not only skip: a **depth-1**
clone — the shape the hourly automation's SDK actually produces — changes the outcome of
**four** `test_agents_md_encoding_adjudication.py` nodes at once, so that clone reports
**21** failing/error nodes while the recorded set carries 17. An earlier revision of this
addendum named a single node; the live probe below **contradicted** that and the count was
corrected. A single-node pin understated the divergence.

| clone | `git rev-parse --is-shallow-repository` | `git rev-list --count HEAD` | nodes | extra nodes |
|---|---|---|---|---|
| full history | `false` | 2281 | **17** | — |
| depth-1 | `true` | 1 | **21** | the four adjudication nodes below |

Measured on `main` `44137991` with `python -m pytest tests/ -q -rEf
--continue-on-collection-errors`:

- full history → the recorded 17-node set, exactly
- depth-1 → `20 failed, 1767 passed, 23 skipped, 1 error` (**21** nodes; the +4 are the
  adjudication extras)

The four extras, and why each fails once history is absent:

| node | mechanism |
|---|---|
| `test_corruption_origin_is_re_derivable` | `git log -- AGENTS.md` is empty → `first_corrupt` stays `None` → assertion fires (the in-test `pytest.skip` guard is bypassed) |
| `test_live_file_verdict_matches_its_state` | the audit CLI looks up `<oracle_rev>:AGENTS.md`, absent here, so it exits non-zero |
| `test_cli_summarises_the_oracle_without_crashing` | same CLI path, its `returncode in (0, 1)` assertion fails |
| `test_exit_code_does_not_call_a_divergent_clean_file_verified` | `_rev("AGENTS.md", ORACLE_REV)` is `None`, so its `assert oracle is not None` fails |

The two nodes the guard already named are in the same file but take a different path: they
read `GATE2_PARENT_REV` and `pytest.skip` when it is absent, so they never enter the set.
These four instead dereference absent history and **fail**.

The extra nodes were therefore **not** named anywhere, and the fixture was not reconstructable
from the automation's own clone. The hardening replaces the single-node constant with
`DEPTH1_CLONE_DEPENDENT_NODES` (a four-tuple), adds
`test_depth1_clone_dependent_nodes_are_named_as_a_set_not_a_single_node`, extends
`test_recorded_set_excludes_the_clone_depth_dependent_node` to assert all four stay out of
the recorded set, and — the load-bearing part — adds a **live probe**,
`test_depth1_clone_nodes_are_exactly_the_extra_failures_in_a_bare_clone`. The probe runs the
four nodes in the *current* clone: in a depth-1 clone it asserts the failed set equals the
named four; in a full-history clone it skips with a stated reason. A list that is only
asserted structurally is a list nobody checks; the probe is what makes the naming falsifiable.

**Live verification (this pass).** The probe was run in the automation's actual depth-1 clone
(`git clone --depth 1`, `/tmp/shallow_probe`): `test_depth1_clone_nodes_are_exactly_the_extra_failures_in_a_bare_clone`
**passed**, and the full `tests/test_baseline_fingerprint.py` file there reported **30
passed** (the depth branch executing, not skipping). A **negative control** — the named set
reduced to three with the fourth removed — makes the probe **fail** in that same clone,
proving it detects exactly the understatement the single-node version carried.

> **Corrected at §10 below.** The sentence that followed here —
> "On a full-history clone the file reports **29 passed, 1 skipped** (the depth branch
> skipped)" — is **superseded**. The gate predicate it relied on (`--is-shallow-repository`)
> does not discriminate the regime the probe asserts about, so in the hourly automation's own
> clone the probe **failed** rather than skipping. §10 repairs the probe and states the
> measured result.

Fingerprint tests: 29 → **30** collected. No node enters or leaves the recorded set, and no
production file is touched.

## 9. Boundary

No merge, no push to `main`, no force-push, no production code change. The working branch is
`gate-hygiene/open-pr-owned-baseline-drift-01`; the human sovereign decides what becomes
canonical.

## 10. Addendum — the probe's gate predicate was wrong (this pass, 2026-10-08)

§8's live probe used `git rev-parse --is-shallow-repository` to decide "is this the depth-1
clone?". **That predicate does not discriminate the regime the probe asserts about**, and the
consequence was self-contradictory: on the branch's own CI (and in the hourly automation's
clone) `tests/test_baseline_fingerprint.py` reported **29 passed, 1 failed** — the probe
itself red — while the PR claimed a falsifiable probe.

### Root cause

The automation does not produce a *true* depth-1 clone; it produces a **partial / treeless
shallow clone**. Measured in this run's workspace clone:

| property | hourly automation clone | true `git clone --depth 1` |
|---|---|---|
| `git rev-parse --is-shallow-repository` | `true` | `true` |
| `git rev-list --count HEAD -- AGENTS.md` | **26** | **1** |
| pinned revisions resolve (`ORACLE_REV` `6c43218a48a4` etc.) | **yes** | **no** |
| the four nodes' outcome | **all pass** | all fail |

So `--is-shallow-repository` is `true` in *both* regimes, while the four nodes turn on whether
the **pinned revisions resolve** — a property of the history actually present, not the shallow
flag. The old branch skipped only when the flag was `false`, so in the automation clone it
entered the depth branch, found the four nodes passing, and failed its
`assert failed == set(DEPTH1_CLONE_DEPENDENT_NODES)` with an empty set.

### Repair

The live branch is now gated on **whether `AGENTS.md` history is absent**
(`git log --format=%H -- AGENTS.md` <= 1 revision), which is the property the probe actually
describes. Both branches are asserted, so the complement §8's docstring promised but never
implemented now exists:

- history absent -> `failed == set(DEPTH1_CLONE_DEPENDENT_NODES)` (unchanged claim)
- history present -> `failed == set()` (the four adjudication nodes must pass)

### Measured result

| clone | before | after |
|---|---|---|
| hourly automation (partial, 26 revs of `AGENTS.md`) | **29 passed, 1 failed** | **30 passed** |
| true `git clone --depth 1` | 30 passed | **30 passed** |

The file now reports **30 passed in every clone regime** — a uniformly falsifiable probe,
rather than one that skips in the regime it was written to describe.

**Negative control (re-run).** With the named set reduced to three
(`set(list(DEPTH1_CLONE_DEPENDENT_NODES)[:3])`), the probe **fails** in the true depth-1 clone
with the four real node names in the message; restored, it passes. The detector still detects
the understatement §8 designed it for.

### Regression boundary

Full suite on the branch, `python -m pytest tests/ -q -rEf
--continue-on-collection-errors`:

| tree | nodes | outcome |
|---|---|---|
| `main` `44137991` | **17** | `16 failed, 1772 passed, 22 skipped, 1 error` |
| branch head | **17** | `16 failed, 1778 passed, 22 skipped, 1 error` |

Node **set** is byte-identical to `main` (sorted `FAILED`/`ERROR` names compared); the
`+6 passed` are the guard file's added assertions plus the previously-skipped depth branch now
executing. **Zero regression.** `python -m py_compile api/main.py` -> OK; no production file and
no `api/main.py` line touched. No node enters or leaves the recorded set.

**Files changed in §10:** `tests/test_baseline_fingerprint.py` (probe predicate + complement
branch), this evidence doc. No other path.

## 11. Addendum — independent re-verification of the attribution and the guard (2026-10-08)

A fresh clone re-derived every claim in §2/§4 from live evidence rather than repeating the
recorded pair.

### 11.1 The canonical pair reproduces from a live `main` run

`python -m pytest tests/ -q -rEf --continue-on-collection-errors` on `main` `44137991`
yielded `16 failed, 1772 passed, 22 skipped, 1 error`; `scripts/baseline_fingerprint.py` on
that log reproduced **17** nodes and the canonical pair `26c2b4c7…` / `571e599f…` exactly.
`tests/fixtures/baseline_node_set.txt` hashes to the same pair, so fixture and live run agree.

### 11.2 Each of the 7 drift-set nodes was re-run at its owner's head

Checked out each owner head (`git worktree add --detach`) and ran the *named node* there —
not the whole file — so the pass/fail is attributable to that node:

| owner PR | head | node(s) run | result |
|---|---|---|---|
| #347 | `3f3024d9` | `test_home_is_offer_led_and_keeps_arkadia_entry_points` | 1 passed |
| #355 | `73104fdf` | `test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]` | 1 passed |
| #356 | `1bfbcc4f` | `test_lab_mutation_endpoints_are_exactly_the_lab_state_set`, `test_lab_router_is_read_only_and_authenticated` | 2 passed |
| #354 | `536a8c43` | `test_allowlist_admits_every_tracked_top_level_prefix`, `test_allowlist_covers_every_tracked_surface`, `test_delegated_verdict_admits_every_tracked_surface` | 3 passed |
| #357 | `4c3d8fb8` | `test_r1_solspire_builders_delegate_to_weaver`, `test_r1_weaver_governance_is_canonical`, `test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | 3 passed |

All 7 drift-set nodes fail on `main` and pass at their owner's head, so the attribution is a
measured fact, not a claim. #357 independently repairs three *era*-set nodes (the same three
its §2.1 entry names), confirming the era set is not uniformly unowned.

### 11.3 The compositional guard was proven against a real recorded-set edit

§4's negative control feeds the *predicate* a synthetic set. That is weaker than editing the
fixture the guard reads. This pass did the stronger thing: appended
`FAILED tests/test_somewhere.py::test_a_new_unexplained_failure` to
`tests/fixtures/baseline_node_set.txt` and re-ran the guard file. Measured:

```
FAILED tests/test_baseline_fingerprint.py::test_live_node_set_reproduces_the_canonical_fingerprint
FAILED tests/test_baseline_fingerprint.py::test_live_node_set_is_the_era_set_plus_the_open_pr_owned_set
2 failed, 28 passed
```

So a future node added to the recorded set without an era-set or open-PR owner **fails the
guard at the file it edits** — the "must FAIL rather than be silently absorbed" property is
demonstrated, not just asserted. Reverted; the fixture is byte-identical to its committed
state.

### 11.4 Live verification recap

```
python -m pytest tests/test_baseline_fingerprint.py -q   -> 30 passed
python -m pytest tests/architecture -q                   -> 11 passed
```

Branch head `c6a18de5`; PR #361 open, `mergeable/clean`, six checks green (incl. Full-history
secret scan). No merge, no push to `main`, no production file touched.

## 12. Follow-on pass (`653151be`): remove the clone-depth dependence entirely

§8 *recorded* the depth-1 divergence — a bare clone carried **21** failing/error nodes
against the recorded 17, the four extras being `DEPTH1_CLONE_DEPENDENT_NODES` — and §10
repaired the probe's own gate so it asserted the set in both regimes. Both were honest, but
both left the four adjudication nodes *failing* in a history-absent clone. A clone that
cannot resolve the history a test needs is not evidence of a defect; it is a checkout
incapable of adjudicating. Reporting four false verdicts from it is the same defect class
this workstream removes, one level down.

This pass repairs the four nodes (test-side only; the audit instrument is untouched) and
supersedes the "must fail in a bare clone" pin with the stronger, depth-independent
invariant: **none of the four may fail in any clone regime.**

### 12.1 The repair (tests/test_agents_md_encoding_adjudication.py)

| node | before | after |
|---|---|---|
| `test_corruption_origin_is_re_derivable` | asserted "no corrupt revision in history" from absent history | `skip` when `CORRUPTION_COMMIT` does not resolve |
| `test_live_file_verdict_matches_its_state` | read exit `(0, 1)` as the verdict; a depth-1 checkout exits `2` | `skip` when `ORACLE_REV` does not resolve |
| `test_cli_summarises_the_oracle_without_crashing` | pinned `returncode in (0, 1)` | accepts the documented undecided exit `2`; `(0, 1, 2)` |
| `test_exit_code_does_not_call_a_divergent_clean_file_verified` | `assert oracle is not None` from absent history | `skip` when `ORACLE_REV` or `CORRUPTION_COMMIT` does not resolve |

Each already used `pytest.skip` elsewhere in the file for the same condition; the repair
makes the guard uniform rather than special-casing four nodes. The three "already skips when
the revision is unavailable" nodes (`test_gate2_parent_*`, `test_shadow_*`) and
`test_corruption_origin_is_re_derivable`'s pre-existing history check are the precedent.

### 12.2 The probe supersession (tests/test_baseline_fingerprint.py)

`test_depth1_clone_nodes_are_exactly_the_extra_failures_in_a_bare_clone` previously asserted
`failed == set(DEPTH1_CLONE_DEPENDENT_NODES)` in a history-absent clone — i.e. it *required*
four failures. That assertion is the thing this pass removes, so it is superseded by
`failed == set()` in **both** regimes (plus an explicit `errored == set()`), run with `-rEf`
so a collection error is visible. The named tuple is retained: the guard below still checks
the names are absent from the recorded set, and the probe still runs those exact nodes, so a
node that regressed to failing in *either* regime is caught. The depth-dependence is removed,
not relocated.

### 12.3 Measurement — the failing-node set is now identical across clone depths

Composed head `653151be74f1719fd167093cc834ce1f6d27cc49`, full suite, `python -m pytest
tests/ -q -rEf --continue-on-collection-errors -p no:cacheprovider`,
`PYTHONPATH=archive/legacy_python`:

| regime | result | failing/error nodes | node-set sha256 |
|---|---|---|---|
| full history (worktree) | 16F / 1778P / 22S / 1E | **17** | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` |
| `git clone --depth 1` (of this head) | 16F / 1774P / 26S / 1E | **17** | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` |

`diff` of the two sorted node lists is empty; the sha256 of each equals the canonical
outcomes fingerprint recorded in the fixture. The +4 skipped in the depth-1 clone are exactly
the four repaired nodes — 0 failed, matching the new invariant. Before the repair the same
depth-1 clone carried **21** nodes; the delta is `-4 / +0`.

Direct per-file runs, both regimes:

```
full history : tests/test_agents_md_encoding_adjudication.py -> 18 passed, 5 skipped
depth-1      : tests/test_agents_md_encoding_adjudication.py -> 14 passed, 9 skipped (was 4 failed)
full history : tests/test_baseline_fingerprint.py           -> 30 passed
```

Architecture `tests/architecture -q` -> 11 passed. `api/main.py` untouched, `python -m
py_compile` OK, 2462 / 2600.

### 12.4 Composition note (why the probed repair and the probe moved together)

This head adds one commit to the same bounded workstream. §8/§10 of this document and the
`DEPTH1_CLONE_DEPENDENT_NODES` comment block pinned the *failure* of these four nodes; the
repair is the event that removes it. That is not two independent changes but one, so it ships
in one pass rather than as a contradiction the next reviewer would have to reconcile. The
hashes in §2 remain valid (the full-history node set is unchanged); the "21 nodes" figures in
§8 and §10 are superseded by the 17-vs-17 measurement above, and the comment blocks were
updated to say so.

### 12.5 Live verification recap

```
python -m pytest tests/test_baseline_fingerprint.py      -> 30 passed (both regimes)
python -m pytest tests/architecture -q                   -> 11 passed
full suite, full history                                 -> 17 nodes  (canonical fingerprint)
full suite, --depth 1 clone of this head                 -> 17 nodes  (identical sha256)
```

No merge, no push to `main`, no production file touched. Branch
`gate-hygiene/open-pr-owned-baseline-drift-01`, head `653151be`, PR #361.

## 13. Addendum — era-set ownership moved from prose into a guard (2026-10-08)

§2/§11 record the measured fact that the era set is **not** uniformly unowned: PR #357 repairs
three of its ten nodes. That fact lived in prose only. Nothing read it, so a later pass could
re-list the three as unowned — or drop them when #357 merges — and no test would notice. This
pass makes the attribution inspectable and checked.

### 13.1 What was added

| path | change |
|---|---|
| `tests/fixtures/era_set_open_pr_owned_node_set.txt` | new — the three era-set nodes and their owner PR, `<node id>\t<owner PR>` |
| `tests/test_baseline_fingerprint.py` | `ERA_SET_OPEN_PR_OWNED_SET` + `_fixture_node_ids()` helper; three guard functions |

The two fixtures partition disjointly: `open_pr_owned_drift_node_set.txt` carries the seven
nodes a live run added *beyond* the era set, the new one carries the three era-set nodes an
open PR repairs, and `era_set ∪ drift == the recorded 17`.

### 13.2 The guards, and what each one stops

- `test_era_set_open_pr_owned_nodes_are_in_the_era_set` — every entry names an era-set node
  (a node the era fixture does not carry would describe ownership of non-era debt), names an
  owner PR (an entry with no owner could never be cleared on merge), and is disjoint from the
  drift fixture.
- `test_era_set_ownership_is_reported_for_every_era_set_open_pr` — the split is derived
  (`10 = 3 owned + 7 unowned`) and the three owned nodes are asserted to still be live debt.
- `test_recorded_counts_are_derived_from_the_fixtures_not_prose` — pins the recorded counts
  (`16 failed`, `1 error`, `17` nodes, `10/3/7` era split, `7` drift) and re-derives them from
  the fixtures, so a fixture edit that leaves a stale count fails instead of shipping.

### 13.3 Negative control — the guards detect the defect they claim to detect

Appended `tests/test_nonexistent.py::test_not_era_debt\t999` to the new fixture and re-ran the
guard file:

```
FAILED tests/test_baseline_fingerprint.py::test_era_set_open_pr_owned_nodes_are_in_the_era_set
FAILED tests/test_baseline_fingerprint.py::test_era_set_ownership_is_reported_for_every_era_set_open_pr
FAILED tests/test_baseline_fingerprint.py::test_recorded_counts_are_derived_from_the_fixtures_not_prose
3 failed, 30 passed
```

Restored, `33 passed` (was 30; the three new guard functions). The negative control is the
same shape as §11.3 — edit the fixture the guard reads, not the predicate.

### 13.4 Independent measurement of `main` alone (the "1776 vs 1772" prose)

§2 shows `16 failed, 1776 passed, ...` while §2's note and §11.1 both say `main` is
`16F / 1772P / 22S / 1E`. Re-measured this pass to settle which is which:

| tree | measured | fingerprint |
|---|---|---|
| `main` `44137991` (full suite) | `16 failed, 1772 passed, 22 skipped, 1 error` — **17 nodes** | `26c2b4c7…` / `571e599f…` |
| composed tree (`main` + this branch) | `16 failed, 1778 passed, 22 skipped, 1 error` — **17 nodes** | `26c2b4c7…` / `571e599f…` |

So `main` alone is `1772P` and the branch is `1778P` (+6 = this pass's three guards plus the
three added in §11/§12); the §2 `1776` figure was an earlier branch state. The `main` figure
and the composed figure differ only in the passed count, which is not a fingerprint input, so
the canonical pair is unaffected. Recorded because the pass's own prose carried both numbers
without saying which tree each described.

### 13.5 Boundary and observability gap (recorded, not acted on)

Test/evidence only — no production file, no `api/main.py`. `python -m py_compile api/main.py`
-> OK.

**Observability gap, recorded as proposed work (not executed):** `grep -rn
baseline_fingerprint .github/workflows/` returns **0** — this guard file is not a trigger path
or a run target in any workflow, so the compositional guarantee holds only when the guard is
invoked by hand. The same is true of the sibling `tests/test_ci_gate_trigger_coverage.py`
(#355), which exists precisely to assert workflow trigger coverage. Wiring the fingerprint
guard into a workflow is a bounded follow-on; it is out of scope for this reconciliation and
is left as a proposal rather than silently widened into.

### 13.6 Live verification recap

```
python -m pytest tests/test_baseline_fingerprint.py -q   -> 33 passed
python -m pytest tests/architecture -q                   -> 11 passed
full suite on `main` `44137991`                          -> 17 nodes (canonical pair)
```

No merge, no push to `main`, no production file touched. PR #361.
