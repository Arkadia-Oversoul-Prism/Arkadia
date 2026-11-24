# Lane-state completeness oracle — EVIDENCE

**Contract:** ARK-OPS-CONTINUOUS-001 (rev. 2026-11-22)
**Branch:** `gate-hygiene/lane-state-completeness-oracle-01`
**Base `main`:** `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Authority:** implementation, tests, evidence. No merge, no deployment, no acceptance.
**Status vocabulary:** PASS / FAIL / BLOCKED / UNKNOWN / OBSERVED / NOT CLAIMED.

---

## 1. Measured defect

`scripts/lane_state.py --check --verify-live` is the lane instruction-doc currency
guard. It judged **one direction only**: a PR the snapshot claims is open must be
open (`_pr_state_findings`) and a lane doc's declared pointer must be live
(`_declared_pointer_findings`). Nothing compared the snapshot with a **fresh
derivation**, so a lane PR that is open but absent from the snapshot was invisible.

Measured 2026-11-22 at `main` `034d8879`, working tree clean:

```
$ python scripts/lane_state.py --check
base main: b842892b... (current: 034d8879...); guarded paths: AGENT-01..04, lane-state.json
doc-guard lanes: ['1', '2', '3', '4']; deferred: []
lane instruction docs consistent with snapshot (4 guarded lanes)
exit 0
```

The committed snapshot recorded **every lane idle** (`open_prs: []`) and
`unassigned_open_prs` holding only `#669`. A fresh derivation over live GitHub
state returned:

```
$ python scripts/lane_state_refresh.py            # dry run
lane 1: doc_guard=current  active=#678 open=[678]
lane 2: doc_guard=current  active=#677 open=[677]
lane 3: doc_guard=current  active=#679 open=[679]
lane 4: doc_guard=current  active=#680 open=[680]
unassigned open PRs: [675, 681, 682, 683]
```

Two false statements were therefore live and green:

1. **Four lane-owned PRs were omitted** from the snapshot, and all four lane docs
   declared `**Active thread:** none`. A successor agent reading a lane doc would
   have been told the lane was free while its work was in flight — the continuity
   failure the lane model exists to prevent, in the direction the guard could not see.
2. **`#669` was recorded as an open PR while MERGED** (`bec86f3d`).
   `unassigned_open_prs` was written by the derivation and read by **no** check:
   `grep -rn unassigned_open_prs scripts/lane_state.py` had no reader.

## 2. Repair

| File | Change |
|---|---|
| `scripts/lane_state.py` | `_unassigned_state_findings()` judges every `unassigned_open_prs` record as a claimed-open PR (OPEN / MERGED / CLOSED_UNMERGED / UNKNOWN, failing closed). `_derivation_findings()` compares the snapshot's per-lane `open_prs` with a fresh derivation **in both directions**, using the same `lane_state_refresh.build()` the snapshot is written from, so snapshot and gate cannot disagree about how lane assignment is decided. Both are wired into `--verify-live`; the completeness read fails closed on a missing token, a transport error, or an unreadable aggregate config. |
| `docs/control-plane/parallel-ui/lane-state.json` | Re-derived from live PR state (`--write --base-main 034d8879`), not hand-edited. |
| `docs/control-plane/parallel-ui/AGENT-0{1,2,3,4}-*.md` | Appended status blocks (last-wins) naming each lane's live PR and branch, so the docs and the snapshot agree. |
| `tests/test_lane_instruction_doc_currency.py` | 12 new nodes: two negative controls, three positive controls, a fail-closed control, a wiring assertion, and an offline floor. |

### 2.1 The self-carrier exclusion is load-bearing

A PR that edits a lane doc is itself an open PR changing lane-owned paths, and its
number does not exist when the snapshot is written. A completeness rule without an
exclusion is therefore **unsatisfiable for every lane-doc change** — the same
structural trap as asserting that a recorded tip equals the current tip.
`_self_branch()` reads `GITHUB_HEAD_REF` / `GITHUB_REF_NAME` and excludes the PR
carrying the change. Both polarities are measured in
`test_the_completeness_oracle_excludes_the_pr_that_carries_the_snapshot`.

### 2.2 What is deliberately *not* required

Completeness is required for **lanes**, not for `unassigned_open_prs`. Lane
ownership is a claim the snapshot makes about lanes, so an omitted lane PR is a
defect. The unassigned list is a catch-all; requiring every currently-open unowned
PR to be listed would make the snapshot unsatisfiable for any change that is itself
such a PR. The unassigned field is still judged for **truthfulness** (a claimed-open
record must be open).

## 3. Verification

### 3.1 The detector bites on the live defect (negative control, real tree)

Before the refresh, with only `scripts/lane_state.py` changed:

```
$ python scripts/lane_state.py --check --verify-live
  DRIFT PR #669 (unassigned_open_prs) is recorded as open but is MERGED (merge commit bec86f3d)
  DRIFT lane 1: open PR #678 changes this lane's owned paths but the snapshot does not record it
  DRIFT lane 2: open PR #677 changes this lane's owned paths but the snapshot does not record it
  DRIFT lane 3: open PR #679 changes this lane's owned paths but the snapshot does not record it
  DRIFT lane 4: open PR #680 changes this lane's owned paths but the snapshot does not record it
exit 1
```

### 3.2 After the refresh (positive control)

```
$ python scripts/lane_state.py --check
lane instruction docs consistent with snapshot (4 guarded lanes)     exit 0

$ python scripts/lane_state.py --check --verify-live
live PR state: 8 PR(s) read ... (4 claimed-open + 4 unassigned + declared doc pointers)
live open-PR derivation: 8 open PR(s) read ... (self branch excluded: None)
lane instruction docs consistent with snapshot (4 guarded lanes)     exit 0
```

### 3.3 Suites

```
$ python -m pytest tests/test_lane_instruction_doc_currency.py -q          78 passed
$ python -m pytest tests/test_lane_instruction_doc_currency.py \
                   tests/test_lane_currency_ci_wiring.py tests/architecture -q  101 passed
$ printf '%s\n' <changed paths> | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

Node-count attribution is by `--collect-only` per file, not inferred from the
delta. The full-suite failing/error **node set** is compared against `main`
`034d8879` in the same environment; see §4.

### 3.4 Runtime proof in CI (not a source-level claim)

PR #684, head `40a720c254901c72d101a18bc871d972e5d400b4`, workflow
`lane-doc-currency.yml`, run **45007168106** — `completed / success`. The
`--verify-live` step executed (it is not skipped) and printed:

```
live PR state: 8 PR(s) read from Arkadia-Oversoul-Prism/Arkadia
  (4 claimed-open + 4 unassigned + declared doc pointers)
live open-PR derivation: 9 open PR(s) read from Arkadia-Oversoul-Prism/Arkadia
  (self branch excluded: 'gate-hygiene/lane-state-completeness-oracle-01')
doc-guard lanes: ['1', '2', '3', '4']; deferred: []
lane instruction docs consistent with snapshot (4 guarded lanes)
```

This is the load-bearing proof of §2.1: the derivation saw **9** open PRs
(including this one) and excluded exactly the carrier, so the completeness rule
is satisfiable on the tree that writes the snapshot.

Final check-runs on head `6b537af7`: **10 success** (`lane-doc-currency`, `test`,
`console-contract`, `posture-currency`, `boot-syntax`, `Full-history secret scan`,
`provider-forensics`, `bundle-beta-evidence`, `beta-beta-01-english`,
`beta-beta-02-hausa`) and **1 failure**: `native-arkadia-golden-workflow`, which
failed on the live external provider —
`ModelUnavailable: N-ATLaS Gradio runtime error: provider emitted error event with
null/empty data`, node `test_natlas_developer_lab.py::test_native_natlas_route_live_external_gradio`.
The same workflow **passed** on the previous head (`40a720c2`) minutes earlier, so
it is intermittent and is evidence about the provider, not about this tree; no
path in this change touches it.


## 4. Regression measurement

Baseline and branch measured in this environment, same command:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Tree | Result |
|---|---|
| `main` `034d8879` (detached worktree, same environment) | **145 failed, 2712 passed, 23 skipped, 144 errors** in 189.45s |
| branch head (same command, same environment) | **145 failed, 2724 passed, 23 skipped, 144 errors** in 188.80s |

Failing/error **node set** (sorted, deduplicated):

```
289 nodes
sha256 d462e3c0d1096aa599e321c215035e3cdeed10a3e1c793e5ec16a0812551bba8   (main)
sha256 d462e3c0d1096aa599e321c215035e3cdeed10a3e1c793e5ec16a0812551bba8   (branch)
comm -3 main branch  ->  (empty)
```

**Zero node-set delta.** The `+12 passed` is exactly the new nodes:
`--collect-only` on `tests/test_lane_instruction_doc_currency.py` reports
**66** on `main` and **78** on the branch.

The absolute failure count (145F/144E) is this environment's dependency-set debt,
not a property of the tree: the same command on the same SHA reports far fewer
nodes where the full application dependency set is installed. Only the node
**identity** comparison is environment-independent, which is why it is the claim.


## 5. Operating consequence (recorded, not hidden)

The snapshot now records live lane threads, so a merge of any recorded PR makes
the snapshot stale and the guard will report it on the next run that touches a
guarded path. That is the **intended** signal — a lane thread closed and the
snapshot still claims it open — and the repair is
`python scripts/lane_state_refresh.py --write` plus a re-pointed lane doc, in one
change. The lane-doc-currency workflow is path-filtered to
`docs/control-plane/parallel-ui/**`, `scripts/lane_state*.py`, the two lane test
files and itself, so an ordinary code merge does not run it.

## 6. Non-claims

- No merge, no deployment, no production verification, no acceptance.
- The guard is proven against the live PR state **as measured at 2026-11-22T09:12Z**;
  the eight open PRs may merge while this PR is in review, which would make this
  branch's snapshot stale. Re-measure before merge; a re-derivation in the same
  change is the repair.
- `--verify-live` requires GitHub read access. It fails closed (UNKNOWN) without
  it; it is not silently skipped.

## 7. Next authorized action

1. Human review of this draft PR.
2. If any recorded PR merges first: re-run
   `python scripts/lane_state_refresh.py --write`, re-point the affected lane docs,
   and re-run `--check --verify-live` before merge.
3. Merge execution remains human-only (GOV-03).

## 8. Second pass (2026-11-24) — the documented repair command could not repair

§7's step 2 told the operator to run `python scripts/lane_state_refresh.py --write`.
Measured on this branch's own head, that command produced a snapshot its own guard
rejects. The exclusion that makes the completeness rule satisfiable existed on the
**judging** side only (`lane_state._self_branch`); the **writing** side had none.

### 8.1 The measurement, before any change to the tool

At `main` `bb19aabd`, on branch `gate-hygiene/lane-state-completeness-oracle-01`
(head `7ca6e99a`), with the snapshot as it stood at `034d8879`:

```
$ GITHUB_HEAD_REF=gate-hygiene/lane-state-completeness-oracle-01 \
  python scripts/lane_state.py --check --verify-live
  DRIFT PR #677 (lane 2 open_prs) is recorded as open but is MERGED (7da3affb)
  DRIFT PR #678 (lane 1 open_prs) is recorded as open but is MERGED (bb19aabd)
  DRIFT lane 1 (AGENT-01-SHELL.md) declares PR #678, which is MERGED ...
  DRIFT lane 2 (AGENT-02-NOVANET-OPPORTUNITY.md) declares PR #677, which is MERGED ...
  DRIFT lane 1: open PR #685 / #692 / #704 changes this lane's owned paths but
                the snapshot does not record it
  DRIFT lane 2: open PR #708 changes this lane's owned paths but the snapshot
                does not record it
  DRIFT lane 1/2: PR #678 / #677 is recorded as an open lane PR but a fresh
                  derivation does not assign it to this lane
exit 1        # 10 findings
```

Running the documented repair (`--write --base-main bb19aabd`) then produced:

```
carrier branch ... (no exclusion existed, so nothing was reported)
unassigned open PRs: [675, 681, 682, 683, 684, 686, ...]      # 684 = this PR
```

The snapshot recorded **its own PR** as an open unassigned PR. `#684` merges, and
that record immediately reads "recorded as open but is MERGED" — the guard reddens
the revision the repair produced. This is the self-reference trap §4 closed for
lane assignment, still open for `unassigned_open_prs`, and open for the whole
derivation because the tool, unlike the guard, had no notion of a carrier.

### 8.2 The repair

| Change | Why |
|---|---|
| `lane_state_refresh._self_branch()` | mirrors `lane_state._self_branch` (`GITHUB_HEAD_REF`, then `GITHUB_REF_NAME`) |
| `lane_state_refresh.exclude_carrier()` | filters the carrier out of the open-PR list **and** its file map, returning the excluded numbers so a dry run reports what it withheld |
| `main()` applies it before `build()` and `merge_history()` | so lane assignment, `active_pr`, `merged_prs` and `unassigned_open_prs` all see the same filtered set the guard compares against |
| snapshot re-derived at `bb19aabd`, lane docs 1 and 2 re-pointed | §7 step 2 executed |

### 8.3 Verification

```
$ GITHUB_HEAD_REF=gate-hygiene/lane-state-completeness-oracle-01 \
  python scripts/lane_state_refresh.py --write --base-main bb19aabd
carrier branch 'gate-hygiene/lane-state-completeness-oracle-01' excluded (PRs [684])
lane 1: doc_guard=current active=#704 open=[685, 692, 704]
lane 2: doc_guard=current active=#708 open=[708]
lane 3: doc_guard=current active=#679 open=[679]
lane 4: doc_guard=current active=#680 open=[680]

$ python scripts/lane_state.py --check                        -> exit 0
$ python scripts/lane_state.py --check --verify-live          -> exit 0, zero DRIFT
$ python -m pytest tests/test_lane_instruction_doc_currency.py \
    tests/test_lane_currency_ci_wiring.py \
    tests/test_lane_aggregate_pr_classification.py -q
  111 passed
```

Six nodes were added (`grep -c '^def test_'` 69 -> 75; 105 -> 111 passed).

**Live negative control.** Removing the `exclude_carrier` call from `main()` and
re-running the wiring test reddens exactly one node:

```
$ python -m pytest tests/test_lane_instruction_doc_currency.py -k write_path
1 failed, 83 deselected   # test_the_write_path_actually_applies_the_exclusion
```

The file was restored byte-identically afterwards. Testing `exclude_carrier` alone
would not have caught this: the defect is a `--write` that does not call it, so the
control drives the real command and reads the snapshot it wrote, in both polarities
(carrier named -> absent; no branch named -> present).

`test_both_self_branch_readers_agree_across_the_environment_matrix` asserts the two
copies of the exclusion agree over five environment shapes, because the same value is
now read in two places and a silent drift between them would restore the defect.

### 8.4 Non-claims

- Repository-source and live-PR-state claims only. No merge, deployment or acceptance.
- The snapshot is measured at `main` `bb19aabd`; the lane PRs it records can merge
  while this is in review, which makes it stale again. The repair for that is the
  command that now works.
- `--verify-live` needs GitHub read access and fails closed (UNKNOWN) without it.
