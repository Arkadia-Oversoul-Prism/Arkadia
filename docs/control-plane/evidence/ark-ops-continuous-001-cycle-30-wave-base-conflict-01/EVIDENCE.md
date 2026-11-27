# ARK-OPS-CONTINUOUS-001 — cycle 30: a base conflict is not a wave conflict

**Contract:** `ARK-OPS-CONTINUOUS-001`
**Milestone:** 2 of [#732](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/732) — composition and merge-wave dry-run
**Owner:** [#736](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/736) (exclusive owner of `scripts/pr_wave_dry_run.py`)
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471`
**Measured:** 2026-11-27, this workspace
**Authority:** read-only. No merge, no push to `main`, no deployment, no acceptance.

## 1. The gap

The dry-run composes candidate heads onto a base revision and reports each one as
`CLEAN`, `ALREADY_CONTAINED` or `CONFLICT`. Those three states cannot express the
difference between two conditions that need **opposite** responses:

| condition | what it means | the response |
| --- | --- | --- |
| the head does not merge into the **base** at all | one stale branch | rebase that branch; the queue composed fine |
| the head composes with the base and conflicts with an **earlier merge in the wave** | two pull requests disagree | adjudicate between the pair |

Both arrived as `CONFLICT`, and the conflict edge list cannot separate them: a base
conflict has no earlier merge touching its path, so `edges == []` — exactly what a
wave conflict with no overlapping merge would also produce. The printed line named the
absence of a cause rather than the presence of one:

```
CONFLICT #686 on AGENTS.md (after no overlapping merge)
```

so the headline `CLEAN=60 CONFLICT=4` read as *four pull requests do not compose with
the queue* when one of them simply cannot merge at all.

## 2. The measurement

`#686` is independently reported by GitHub as `mergeable=CONFLICTING`,
`merge_state=DIRTY` at head `330f5874`, and merges into `8f746f9e` with
`CONFLICT (content): Merge conflict in AGENTS.md`. It conflicts with the base and with
nothing in the queue.

```
$ python scripts/pr_wave_dry_run.py --base origin/main          # before
base 8f746f9e | 64 PRs composed in queue order
  CLEAN=60  CONFLICT=4
  CONFLICT #686 on AGENTS.md (after no overlapping merge)
  CONFLICT #687 on tests/test_gate2_production_observation.py (after [681])
  CONFLICT #728 on .github/workflows/canonical-render-browser-smoke.yml (after [689])
  CONFLICT #747 on docs/control-plane/parallel-ui/lane-state.json (after [684])

$ python scripts/pr_wave_dry_run.py --base origin/main          # after
base 8f746f9e | 64 PRs composed in queue order
  CLEAN=60  CONFLICT=3  CONFLICT_BASE=1
  CONFLICT #687 on tests/test_gate2_production_observation.py (after [681])
  CONFLICT #728 on .github/workflows/canonical-render-browser-smoke.yml (after [689])
  CONFLICT #747 on docs/control-plane/parallel-ui/lane-state.json (after [684])
  CONFLICT_BASE #686 on AGENTS.md -- does not merge into the base at all; rebase the
    branch, the queue is not the cause
```

Runtime 5.9 s. The three genuine wave conflicts and their edges are unchanged by the
repair, which is the control that the reclassification moved only the base case.

## 3. The repair

Measured, not inferred. `conflicts_at_base()` re-probes every head that conflicted in
the wave against the **base alone**, in a second throwaway worktree, and returns the
ones that fail there. Reclassification is therefore a measurement of the base, and it
does not depend on the edge set being computed correctly.

Two supporting changes, each because the old shape could hide the same defect:

- `changed_paths()` returned `[]` when `git merge-base` failed, so a head with no merge
  base reported `edges == []` — an unmeasurable attribution dressed as "no overlapping
  merge". It now raises `DryRunError`; the tool's contract is that no verdict is
  emitted rather than an unsound one.
- The empty-edge print says `UNATTRIBUTED: no earlier merge touched these paths`
  instead of asserting a cause it did not measure.

Packet changes are additive: `state_counts` gains `CONFLICT_BASE`, `base_conflicts` is
a new list, and `conflicts` keeps its existing meaning (wave conflicts only) so
consumers that read it are not silently re-scoped. The authority note now states that
a `CONFLICT_BASE` is not a queue-composition failure.

## 4. Controls

`tests/test_pr_wave_dry_run.py` — **17 passed** (14 before, +3).

| control | mutation of the real script | observed |
| --- | --- | --- |
| reclassification disabled (`if number in at_base:` -> `if False:`) | `test_a_head_that_conflicts_with_the_base_is_not_reported_as_a_wave_conflict` | `1 failed, 16 passed`; `base_conflicts` empty and `conflicts` gains `#9` |
| fail-closed reverted (`raise DryRunError` -> `return []`) | `test_an_unmeasurable_conflict_edge_fails_closed` | `1 failed, 16 passed`; `DID NOT RAISE DryRunError` |

Both mutations were applied to the real file and restored byte-identically
(`sha256 f2a1c757...` before and after; `17 passed` again).

The second test in the new group is the polarity control: `conflicts_at_base()` must
name `#9` **and not** `#11` in one call. A probe that returned every head, or none,
would satisfy the primary test's shape while measuring nothing.

## 5. What this establishes and does not

- **Established:** one of the four reported conflicts was a base conflict, not a
  queue conflict; the tool now measures and names the difference; the three genuine
  wave conflicts are unchanged.
- **Not established:** merge eligibility, M1-M13, branch protection, review
  sufficiency, or acceptance. A `CONFLICT_BASE` names a rebase task for one branch; it
  is not a review finding and it grants no authority.
- **Not measured:** whether `#686`'s rebase resolves its conflict. That is a change to
  `#686`'s branch, which this PR does not own.
