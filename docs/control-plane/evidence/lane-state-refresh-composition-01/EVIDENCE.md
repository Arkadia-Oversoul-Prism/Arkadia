# Lane-state refresh composition: #569 is a strict subset of #568

**Measured:** 2026-10-25, `main` `36f53be22d753ffe269f05cbf3fb39212f744207`.
**Base of this branch:** the same `main` SHA.
**Verdict:** COMPOSITION FINDING — no source change proposed. `#569` is superseded by
`#568`; do not merge `#569`.

This pass changes no source file. It records a measurement that prevents a merge from
landing a partial repair and leaving `main` red. It is a decision record, not an
implementation.

---

## 1. The defect on `main`

`scripts/lane_state.py --check --verify-live` **fails on `main`** (exit 1). Two PRs the
snapshot claims are open are provably closed without merging, and that check
(`_pr_state_findings`) is **not** scoped by `doc_guard` — it blocks on every lane.

```
$ GH_TOKEN=<clone credential> python3 scripts/lane_state.py --check --verify-live
live PR state: 16 PR(s) read ... (14 claimed-open + declared doc pointers)
base main: 68acf89f3045a01b0ba04038fabac4edfb5f937e (current: 36f53be22d753ffe269f05cbf3fb39212f744207)
doc-guard lanes: ['1', '2']; deferred: ['3', '4']
  DRIFT PR #508 (lane 4 open_prs) is recorded as open but is CLOSED without merging; the thread is dead
  DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging; the thread is dead
exit=1
```

`main`'s snapshot is `base_main 68acf89f…`, `observed_at 2026-10-25T04:48:21Z`. The
blocking check runs in CI (`.github/workflows/lane-doc-currency.yml`, step
`run: python scripts/lane_state.py --check --verify-live` with `GH_TOKEN: ${{ github.token }}`),
so this is a real red gate, not a local artifact.

Live PR state at measurement: `#508` closed unmerged; `#563` closed unmerged.

## 2. Two open PRs repair it, and they are not equivalent

Both `#569` and `#568` modify `docs/control-plane/parallel-ui/lane-state.json`. Measured
by running the guard **against each PR's own head tree** (not against `main`):

| Tree | guard `--check --verify-live` | blocking DRIFT |
|---|---|---|
| `main` `36f53be2` | **exit 1** | `#508`, `#563` |
| `#569` head `d75ba224` | **exit 1** | `#508` |
| `#568` head `b72ea7b1` | **exit 0** | none |

`#569`'s snapshot is `observed_at 2026-10-25T13:26:10Z`; `#508` closed at
`2026-10-25T15:23:40Z`. **The drift post-dates the refresh.** `#569` clears `#563` and
misses `#508` by ~2 hours.

`#568`'s snapshot is `observed_at 2026-10-25T15:24:13Z` — it observes the `#508` closure.

## 3. #569 is a strict subset of #568

Compared claim-by-claim (every PR number in `open_prs` plus each `deferred_to_pr`):

```
#569 claims: [499, 508, 525, 535, 547, 548, 549, 550, 553, 554, 555, 562, 564]
#568 claims: [499,      525, 535, 547, 548, 549, 550, 553, 554, 555, 562, 564]
#569-only:   [508]        <- the drift #568 already clears
#568-only:   []
```

The only claim `#569` carries that `#568` does not is exactly the dead PR the gate
rejects. There is no information in `#569` that `#568` lacks.

## 4. Why this is not a conflict to reconcile — it is a supersession

A textual merge of the two branches on `lane-state.json` produces **4 conflict markers**
(measured: `git merge-tree <base> d75ba224 b72ea7b1`). The conflict is not the interesting
part; the interesting part is that resolving it in `#569`'s favour *reintroduces* the
`#508` drift. There is no correct merge of these two snapshots: the newer measurement
strictly contains the older one, so `#568`'s file is the answer and `#569` should be
closed as superseded.

## 5. What `#568` does beyond the refresh

`#568` (`gate-hygiene/lane-guard-fixed-scope-01`) is the guard change whose *effect*
clears the drift: the enforced lane set is derived from a constant
(`scripts/lane_guard_domain.py`) rather than from `doc_guard`, so lanes 3 and 4 are
judged on every run instead of being hidden behind a deferral. That is why the same
snapshot that yields two `NOTE`s on `main` yields zero findings on `#568` — the notes
become blocking, and the snapshot is refreshed to satisfy them.

Independently verified in a worktree at `b72ea7b1`:

- `python3 -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py tests/test_lane_guard_fixed_scope.py tests/test_lane_guard_stacked_pr.py -q -rEf`
  → **83 passed**
- `python3 scripts/lane_state.py --check --verify-live` → **exit 0**,
  `lane instruction docs consistent with snapshot (4 enforced lanes)`
- all **7** check-runs on `b72ea7b1` are `completed/success` (`test`, `Full-history secret
  scan`, `lane-doc-currency`, `console-contract`, `verdict-step-integrity`, `boot-syntax`,
  `trigger-coverage`)

## 6. Related: `#550` edits a lane-1 exclusive file

Recorded here because it is the same class of finding and was measured in the same pass,
**not** because it is in scope for repair.

`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §1 gives lane 1 exclusive ownership
of `web/arkadia_console/src/App.tsx` and lists lane 4's `must not edit` as including
"shared tokens, shared shell tests". PR `#550` (branch
`integration/prism-recursive-recovery-01`, labelled a lane-4/recursive-recovery slice)
**modifies `web/arkadia_console/src/App.tsx`** and `src/components/Shell.tsx`, and adds
lane-4 feature components.

This is an ownership-boundary observation for the sovereign, not a defect this pass may
repair: the change may be legitimate (the shell seam owner may have delegated it), but the
contract as written does not record such a delegation. No action taken.

## 7. Regression boundary

This branch adds one markdown file under `docs/control-plane/evidence/` and changes no
executable surface. Expected node-set delta: **zero**. Verified:

- `printf '<path>' | python3 scripts/cp10_mutation_boundary_policy.py --judge` → exit 0
  (`Mutation boundary PASS`), so the new path is admitted without an allowlist edit.

## 8. Remaining uncertainty / not claimed

- **Not** claimed: that `#568` is mergeable *right now*. Its head is `b72ea7b1` against
  base `bebb6ed4`; `main` has since advanced to `36f53be2`. Mergeability must be
  re-checked at merge time per the contract's step 4.
- **Not** claimed: production or runtime behaviour of anything. This is a repository-source
  measurement.
- **Not** claimed: that the guard's blocking scope (`_pr_state_findings` judged across all
  lanes while `doc_guard` gates only the doc-pointer findings) is intended. That asymmetry
  is *observed*, and it is the mechanism that makes a lane-3/4 snapshot refresh
  gate-blocking. Whether it is the desired design is the sovereign's call.

## 9. Recommended disposition (sovereign action)

1. Merge **`#568`** — it clears the `main` drift, refreshes the snapshot to a post-`#508`
   observation, and makes the gate self-consistent across all four lanes.
2. Close **`#569`** as superseded by `#568` (strict subset; see §3). Merging it first
   would leave `main` red for `#508`, and merging it second would require a resolution
   that reintroduces the drift.
3. Review the `#550` / lane-1 ownership observation in §6.

No merge, deploy, or acceptance is performed or claimed by this pass.
