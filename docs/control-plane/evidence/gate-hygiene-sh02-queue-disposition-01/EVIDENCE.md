# EVIDENCE — `gate-hygiene` / SH-02 queue disposition, pass 2026-09-29 (hour 21:06Z)

> Docs-only. No test, source, workflow, governance, or constitutional file is modified.
> `api/main.py` untouched (2519 / 2600 lines, `py_compile` clean).

## 1. Objective and scope

`SH-02` is "migrate the 35 stale source-level string assertions
(`STALE_ASSERTION`) in bounded batches". This pass answers one bounded question, because the
previous pass left the queue's *denominator* ambiguous and the ambiguity is itself the blocker:

> **How many of the 35 `STALE_ASSERTION` nodes still represent open work, and which
> sub-workstream owns each one?**

Doing a repair batch first would have re-created the failure mode the contract forbids
(§ `NO SELF-EXPANSION`, § `PRESERVE CONTINUITY`): the ledger says 35, the live suite says 26
red, and three open PRs already carry 12 of them. The denominator had to be settled on
evidence before another batch is selected.

**Completion condition.** Every one of the 35 nodes is assigned exactly one disposition,
derived from measured node-level evidence at a stated SHA, with the derivation reproducible
from the repository alone.

**Regression boundary.** Documentation only — the fingerprint must be byte-identical before
and after.

**Authority boundary.** No merge, no push to `main`, no force-push, no product decision.

## 2. Base identity

| item | value |
|---|---|
| `BASE_MAIN` | `df7a99a067382401c00de5e7bbaaac0125ba2088` |
| provenance | merge of PR #131, `2026-09-29 16:03:23 +0100` |
| local `main`/`origin/main`/`origin/HEAD` | all at `df7a99a` |
| working tree | clean at branch point |
| clone | **complete** — `df7a99a` has **two parents** (`94afda6`, `ddb30d0`); root `9ab26fc`; 1393 commits reachable. *Corrected in a later pass — see §11.* |

> **Correction (later pass).** An earlier revision of this section recorded the clone as
> **grafted** (`df7a99a` with no parents) and, on that basis, declared every
> *"`X` is an ancestor of `df7a99a`"* claim **unverifiable**. **That premise was wrong**, and
> the conclusions drawn from it are withdrawn. See §12 for the measurement. The two bullets
> below are retained struck through only to keep the correction legible.

~~The graft is load-bearing for two claims in the open ledger:~~

- ~~`git merge-base` against any older SHA is **vacuous**~~ — **false**: `git merge-base` is
  well-defined here (`git merge-base a26af408 df7a99a` → `a26af408`).
- ~~The open ledger repeatedly reasons *"`X` is an ancestor of `df7a99a`"* … **That statement
  cannot be verified in this clone.**~~ — **false**: it is verifiable and it is **true**.

## 3. Method (reproducible)

```bash
# BASE fingerprint — the node list, not the count, is the fingerprint
cd <clean worktree at df7a99a>
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort > /tmp/fails_main.txt

# Per-branch fingerprints (same command, same interpreter, in the PR worktrees)
#   /tmp/wt-gate-w2-living-gate-grove-handoff            b8e6afc  (PR #133)
#   /tmp/wt-gate-hygiene-sh02d-prism-interior-shell-...  90544c9  (PR #135)
#   /tmp/wt-gate-hygiene-sh02e-agent-run-capability-...  a919651  (PR #136)
#   /tmp/wt-gate-hygiene-sh02f-solspire-p1-experience-...28686cb  (PR #137)
```

Class and candidate-set membership were read from the ledger table itself
(`BASELINE_TEST_DEBT_CLASSIFICATION.md` Appendix A, nine 4-column rows), not from prose. A
node's disposition is `red_on_main` (present in the base fingerprint) intersected with
coverage (`base_nodes − branch_nodes`, i.e. nodes the branch **fixes**).

Nodes that are **absent from the ledger but red on `main`** are reported separately in §6 —
they are outside the 35 and must not be folded into an "SH-02 batch".

## 4. Result — 35 nodes, four dispositions, zero residue

| disposition | count | meaning |
|---|---|---|
| **GREEN on `main`** | **19** | already repaired by merged commits; no action, ever |
| **IN_OPEN_PR** | **12** | carried by a green, unmerged, already-reviewed PR; finish by merging |
| **RESIDUAL** | **4** | no open PR; needs a **decision**, not a batch |
| **open SH-02 repair batch** | **0** | ← the measured answer |

19 + 12 + 4 = 35. **The SH-02 candidate set is exhausted.** There is no sixth batch of
"plain `STALE_ASSERTION` string assertions" left to select — which is precisely what the
previous pass's "next bounded task" assumed existed.

### 4.1 GREEN on `main` — 19 nodes (do not re-do)

Repaired by already-merged work; all appear green in the base fingerprint.

| ledger node | likely repair |
|---|---|
| `test_ais_w6_future_skills_challenge.py::test_w6_is_self_guided_and_timed` | #132 batch 4 (merged) |
| `test_prism_pass_c_surface_ownership.py` ×6 | `SH-02b` (#127, merged) |
| `test_solariun_experience_consolidation_01.py` ×3 | #125 batch 2 (merged) |
| `test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication` | merged (see §5) |
| `test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence` | merged (see §5) |
| `test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream` | merged (see §5) |
| `test_weaver_mvp2_08.py::test_nexus_novanet_canonical_routing_intact` | SCC batch 1 |
| `test_weaver_sci_boundary_01.py` ×3 | SCC batch 1 |
| `test_weaver_sci_contract_01.py` ×2 | SCC batch 1 |

### 4.2 IN_OPEN_PR — 12 nodes (finish by merge, not by a new batch)

Every carrier branch is based on `df7a99a`; none needs a rebase onto current `main`.

| PR | branch @ head | nodes fixed | ledger rows |
|---|---|---|---|
| **#133** | `gate-w2/living-gate-grove-handoff` @ `b8e6afc` | 5 | 3, 4, 5, 6, 8 |
| **#135** | `gate-hygiene/sh02d-prism-interior-shell-rebase-01` @ `90544c9` | 3 | 10, 11, 12 |
| **#136** | `gate-hygiene/sh02e-agent-run-capability-onboarding-repair` @ `a919651` | 2 | 1, 2 |
| **#137** | `gate-hygiene/sh02f-solspire-p1-experience-01-repair` @ `28686cb` | 2 | 22, 23 |

The four rows that sum to 12 across identifiers 1–12 and 22–23 are a **decisive corroboration**:
PR #139 independently reported "SH-02 batch 6: repair Living Gate / W2 stale assertions
(nodes 3-8)" (5 nodes + the `F-01` one deliberately left red) and this measurement reproduces
the **same row ids** from the ledger's *left column*, with no shared inputs.

**Deviation from the current "safe sequence".** PR #139 records
`#133 → #138 → #135 → #136 → #137 LAST`. That sequence is correct for `#135`/`#136` (both
touch the classification ledger) but it places **`#137` after `#136` on a textual-conflict
basis only**. `#137` is the smallest carrier (2 nodes, `+` docs) and is the **only** PR that
touches `tests/test_solspire_p1_experience_01.py`, so it cannot collide with `#133`/`#135`/`#136`
on *content*; it already requires the union-append resolve. Merging a 2-node carrier earlier
retires rows 22–23 sooner and reduces the conflict surface for the larger carriers. **Flagged
for the sovereign; not acted on** — merge order is sovereign authority, and reordering it is a
consequential action outside this workstream.

### 4.3 RESIDUAL — 4 nodes; none is a batch candidate

| node | why it is not a batch | owner |
|---|---|---|
| `test_steward_filter.py::test_blocks_identity_claims` | asserts `steward_filter("You have transcended") is None`; `weaver/filters/steward.py:30-34` forbids `"transcendent"`, not `"transcended"` | **`F-02`** |
| `test_steward_filter.py::test_allows_mythic_with_action` | asserts `"The field resonates. I will do this."` passes; Rule 4 (`strict=True`) blocks it because `mythic_count = 4 > len(text)/100 = 0.33` and Rule 3 never runs | **`F-02`** |
| `test_steward_filter.py::test_compress_to_choices` | asserts `"More noise" not in compressed`; `compress_to_choices` splits on `"\n"` and never removes the sentence | **`F-02`** |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | the `sessionStorage` proxy no longer measures its "no cloud persistence" intent | **`F-01`** (already logged; `#133` deliberately leaves it red) |

`F-01` was already recorded by PR #133 as a deliberate non-repair awaiting a sovereign call.
`F-02` is new and is registered below. Neither belongs in `SH-02`: `SH-02` is scoped to
*assertions drifted from intact behaviour*, and in all four of these the behaviour itself is in
question.

## 5. A correction to the recorded SG-04 premise (`SH-08` scope)

While testing §4 I re-measured the SG-04 cluster. **§11.1's mount measurement reproduces
exactly**, and my first draft of this section asserted the opposite; it was wrong and is
corrected here. Recorded as a self-caught contradiction rather than silently dropped.

```bash
git show origin/main:web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx \
  | grep -c '<ActivityRuntime'                      # 0   — mounts: none
grep -n 'ActivityRuntime' web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx
# 4:import ActivityRuntime from './ActivityRuntime' # dangling import only
git stash list                                      # empty
```

So the merge **did** drop the mount, exactly as §11.1 found.

But §11.1's **proposed reclassification** of ledger rows 24–26
(`spiral_grove_chambers`, `spiral_grove_frontend_projection`,
`spiral_grove_learning_path_projection`) from `STALE_ASSERTION` to `CONTRADICTION` is **not
reproducible as a red state** on live `main`:

```bash
python -m pytest \
  tests/test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication \
  tests/test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence \
  tests/test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream -q
# 3 passed
```

All three are green on the same tree where the mount is absent. The mechanism is visible in the
assertion bodies: each asserts a **machine-readable marker plus a rewording-tolerant regex**
for the downstream staging prose —

```python
assert re.search(r"Evidence submission, assessment, and capability-state "
                 r"(?:mutation|updates) remain (?:explicit|separate explicit) downstream stages\.", chamber)
```

— which is the characteristic shape of an **already-migrated `SH-02` assertion**, and which the
inline-surface `CapabilityChamber.tsx` that `main` carries satisfies.

**Corrected dispositions for rows 24–26: `GREEN on main`** (already counted in §4.1), not
`CONTRADICTION`. This narrows `SH-08` to **4 open nodes, not 7** — the four in
`tests/test_spiral_grove_activity_runtime.py`, which are absent from the ledger and do fail
on `main` (§6). PR #138's canonical-header finding (`73b8868 → ff80b8c`) is a separate,
untouched node and is unaffected by this measurement.

**What this changes for the sovereign.** The `SH-08` choice is *not* "revert a merge that
broke both suites" — the SG-03 restraint property and its three suite assertions are green.
The live question is only whether `<ActivityRuntime/>` (an existing, unreferenced component,
plus a never-implemented `data-testid="activity-surface-*"` contract) should be re-mounted
ahead of the inline surface `main` ships. That is a **product/UI decision on a CP10-fenced
path**, and it is OUT_OF_SCOPE here.

**What this does not do.** It does not touch `web/public_prism/**`, does not reclassify the
ledger file, and does not overrule `SH-08`. It records that a proposal in §11.1 was tested
against the live tree and did not reproduce, so the sovereign is not asked to adjudicate a
premise the repository contradicts.

## 6. Out-of-scope red nodes (reported, not worked)

26 `main` red nodes in total: 4 ledger `RESIDUAL` (§4.3) + 4 SG-04 nodes absent from the
ledger + 18 nodes whose ledger class is `DRIFT` / `ENV-ARTIFACT` / absent. The 18 are
**excluded by the workstream scope** ("excludes DRIFT, SH-08 governance contradictions, and
product-decision nodes") and are listed here only so a future pass does not mistake them for
unclaimed `SH-02` work.

| class | nodes |
|---|---|
| `DRIFT` | `test_engineering_scheduler_bootstrap.py` ×2, `test_identity_spine_w1.py` ×1, `test_m02_reasomate_truth.py` ×1, `test_spiral_grove_registry.py` ×2 |
| `ENV / ARTIFACT` | `test_gate_serve_script.py` ×1, `test_gate_status.py` ×1 (`SH-05`, sovereign call) |
| absent from ledger | `test_solspire_r1_governance_convergence.py` ×2, `test_solspire_r2_github_mutation.py` ×1, `test_solspire_r3_execution_runtime.py` ×1, `test_spiral_grove_activity_runtime.py` ×4 |

Two `DRIFT` rows are recorded in the ledger as *"REAL_DEFECT, workflows inert for `main` CI"*
(`solspire-r{1,2,3}-validation.yml` trigger only on `push` to `recon/solspire-r0`). That is a
separate workstream and is not opened here.

## 7. Preconditions verified before any write

| precondition | result |
|---|---|
| canonical clone on `main`, remote consistent | **pass** |
| `BASE_MAIN` is a real commit | **pass** — `df7a99a`, PR #131 merge |
| working tree clean at branch point | **pass** |
| protected architecture suite | **11 / 11 pass** |
| boot code (`api/main.py`) compiles, within budget | **pass** — 2519 / 2600 |
| dependency availability | **pass** — `requirements.txt` installed; `pytest --continue-on-collection-errors` required for the 2 documented collection errors |
| no repository evidence contradicts assumed state | **pass** — one prior claim *corrected* (§5), none contradicted silently |

## 8. Verification states

| item | state | basis |
|---|---|---|
| `BASE_MAIN` = `df7a99a` | **VERIFIED** | live `git log`, three refs agree |
| 35-node dispositions (§4) | **VERIFIED** | base + 4 branch fingerprints, node-name intersection |
| 19 nodes green on `main` | **VERIFIED** | absent from base failure fingerprint; `test_stellar`-style positive re-run not repeated per node |
| 12 nodes covered by open PRs | **VERIFIED** | per-branch `base_nodes − branch_nodes` |
| §5 SG-04 mount measurement (`mount=0`) | **VERIFIED** | `git show origin/main:…` piped to `grep -c '<ActivityRuntime'` → `0` |
| §5 corrected dispositions for ledger rows 24–26 | **VERIFIED** | 3/3 nodes pass on live `main` |
| §5 `SH-08` narrowed to 4 nodes | **VERIFIED** | 4 `test_spiral_grove_activity_runtime.py` nodes red and absent from ledger |
| `SH-08` re-mount decision | **BLOCKED** | product/UI decision on CP10-fenced path; out of scope |
| PR merge ordering (§4.2) | **ESCALATED** | collision measured elsewhere; reordering is sovereign authority |
| clone completeness / ancestor claims "`X` is an ancestor of `df7a99a`" | **VERIFIED** (§11.1) | complete clone; `git merge-base --is-ancestor a26af408 df7a99a` → true; distance 149 |
| `F-02` provenance (§11.2) | **VERIFIED** | red at root commit `9ab26fc`; both files byte-identical to genesis |
| `74f5494` / `1b63994` / `06ad5f2` SG-04 mount claim (§11.3) | **VERIFIED** | mount=1/1/1 on branch, 0 on `main`; `06ad5f2` is an ancestor of `main` |
| `vite build` | **BLOCKED** | environment (no npm registry access) |
| full-suite fingerprint | **VERIFIED** | `32 failed / 1025 passed / 13 skipped / 2 collection errors` |

## 9. Regression comparison

| check | base `df7a99a` | this pass (`+ docs`) |
|---|---|---|
| full suite | 32 failed / 1025 passed / 13 skipped / 2 errors | **identical** |
| `tests/architecture` | 11/11 | **identical** |
| `api/main.py` | 2519 lines, `py_compile` clean | **identical** |

Documentation-only change ⇒ fingerprint must not move. It did not.

## 10. Remaining uncertainty

1. The 19 "GREEN on `main`" attributions name the *likely* repair PR by batch grouping; the
   node membership (green vs red) is measured, the **attribution** is inferred from ledger
   metadata. Attribution does not affect the disposition.
2. ~~§5 corrects a historical-SHA measurement. The historical SHAs (`74f5494`, `1b63994`,
   `06ad5f2`) are unverifiable in the grafted clone; only the live-tree reading is proven.~~
   **Resolved — §11.** The clone is complete; the SHAs are verifiable and the claim reproduces.
3. `#137`'s early-merge proposal (§4.2) is an optimisation, not a correctness claim.
4. ~~`F-02` (§4.3) is registered on reading alone; the three nodes were not bisected to confirm
   which commit introduced the divergence.~~ **Resolved — §11.** Bisected: red at the root commit.

## 11. Correction pass — two premises falsified, both uncertainties resolved

A later heartbeat re-measured this PR's own load-bearing premises before doing anything else.
Two were **wrong**, and the claims resting on them are withdrawn. The disposition in §4 is
**unchanged** — neither correction moves a node between dispositions.

### 11.1 The clone is **not** grafted — the `UNKNOWN` was a tooling artifact

```bash
git rev-list --count HEAD                       # 1393
git log -1 --format='%P' df7a99a                # 94afda6… ddb30d0…   (two parents)
git rev-list --max-parents=0 HEAD               # 9ab26fc  (root)
git rev-parse --is-shallow-repository           # false
cat .git/info/grafts                            # No such file or directory
ls .git/objects/info/alternates                 # absent
```

The `df7a99a has no parents` reading that §2 recorded is **not reproducible in a plain
clone of `main`**. No graft, no shallow boundary, no alternates. Whatever produced it, it was
an artifact of that pass's inspection, not a property of the repository — and §2 generalised
it into "every ancestor claim is unverifiable here", which was the error.

Consequences, all now **measured rather than deferred**:

```bash
git merge-base --is-ancestor a26af408 df7a99a   # true
git rev-list --count a26af408..df7a99a          # 149   — matches the ledger exactly
git log -1 --format='%h %s' d48ad0e             # d48ad0e Merge pull request #97 …
git merge-base --is-ancestor d48ad0e origin/main  # true
git diff --name-only d48ad0e^1 d48ad0e | grep -v '^$' | wc -l   # 24
git diff --name-only d48ad0e^1 d48ad0e | grep -v '^$' \
  | python3 scripts/cp10_mutation_boundary_policy.py --judge   # PASS, exit 0
```

So the two claims §2 withdrew are **restored as verified**:

- `a26af408` **is** an ancestor of `df7a99a`, 149 commits apart (PR #139's claim — true).
- `d48ad0e` resolves, is the merge of PR #97, is an ancestor of `main`, and its 24-path diff
  **passes** the current CP10 policy judge (`--judge` → exit 0). The AGENTS.md note that this
  gate "failed on `main` at `d48ad0e`" reflects the *historical* allowlist, not current policy.
  Both historical claims are now closed, not carried.

Note: `d48ad0e` is a **merge commit**, so `git show d48ad0e` yields *no* paths (0, not 24) and a
judge run fed from it would pass vacuously on an empty list. The diff must be taken against
`d48ad0e^1`. Recorded because the vacuous form is a false-green trap for this gate.

### 11.2 `F-02` is **older than the repository's history** — bisected, not inferred

§10.4 left `F-02` "registered on reading alone". Bisected:

```bash
git log --all --oneline --follow -- weaver/filters/steward.py   # 9ab26fc  (root commit only)
git log --all --oneline --follow -- tests/test_steward_filter.py # 9ab26fc  (root commit only)

git show 9ab26fc:weaver/filters/steward.py       | sha256sum    # 17080e23… == live file
git show 9ab26fc:tests/test_steward_filter.py    | sha256sum    # 4d7b2921… == live file

git worktree add --detach /tmp/wt-root 9ab26fc
python -m pytest tests/test_steward_filter.py -q   # 3 failed, 5 passed
```

`9ab26fc` is the **root commit**, and both files are byte-identical to it. The three nodes are
**red at the root commit**, on a tree with no parents.

This is the strongest possible answer to §10.4, and it **strengthens** the §4.3 disposition
rather than altering it: `F-02` is not a divergence introduced by any commit. The filter and
its test were authored together, contradictorily, at genesis, and have never been reconciled.
There is no "which commit regressed it" to find — the question is void.

Three genuine behaviour divergences (unchanged from §4.3, each re-confirmed on live `main`):

| node | assertion | implementation |
|---|---|---|
| `test_blocks_identity_claims` | `"You have transcended"` → `None` | `forbidden_identity` lists `"transcendent"`, not `"transcended"` — substring miss |
| `test_allows_mythic_with_action` | `"The field resonates. I will do this."` passes | Rule 4 (`strict=True`) blocks it: `mythic_count = 4 > len(text)/100 = 0.33`; Rule 3 never runs |
| `test_compress_to_choices` | `"More noise" not in compressed` | `compress_to_choices` splits on `"\n"`, never on sentences — the whole input is one line |

### 11.3 The three historical SG-04 SHAs resolve and the claim reproduces

§10.2 called `74f5494`, `1b63994`, `06ad5f2` "unverifiable in the grafted clone". They resolve,
and the mount claim that `SH-08`/§5 rests on **reproduces exactly**:

```bash
for c in 74f5494 1b63994 06ad5f2 origin/main; do
  echo "$c mount=$(git show $c:web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx | grep -c '<ActivityRuntime')"
done
# 74f5494 mount=1   1b63994 mount=1   06ad5f2 mount=1   origin/main mount=0
```

`06ad5f2` is an ancestor of `main` (the SG-04 branch was merged), and the mount is present on
the branch and absent on `main`. §5's finding is therefore **independently corroborated**, and
the `SH-08` premise is stronger than this PR originally claimed.

### 11.4 What this changes

| item | before | after |
|---|---|---|
| clone | "grafted"; ancestor claims **UNKNOWN** | **complete**; ancestor claims **verified** |
| `a26af408` ancestry / `d48ad0e` CP10 | unproven, carried | **verified** (§11.1) |
| `74f5494` / `1b63994` / `06ad5f2` | unverifiable | **resolved**; mount claim reproduces (§11.3) |
| `F-02` provenance | "registered on reading alone" | **bisected** — red at the root commit (§11.2) |
| §4 disposition (19 / 12 / 4 / 0) | — | **unchanged** |

`F-02` and `SH-08` remain **sovereign/product decisions**. This pass did not act on either, and
did not repair any green node. Baseline fingerprint re-measured this pass and **unchanged**:
`32 failed / 1025 passed / 13 skipped / 2 errors`; `tests/architecture` **11/11**;
`api/main.py` **2519 / 2600**, `py_compile` clean.

## 12. Authority

Human sovereign merges. This pass did **not** merge, push `main`, force-push, or make a
product decision. It proposes `F-02` and a reduced `SH-08` scope for sovereign adjudication.
No new mutation or authorization path is created.
