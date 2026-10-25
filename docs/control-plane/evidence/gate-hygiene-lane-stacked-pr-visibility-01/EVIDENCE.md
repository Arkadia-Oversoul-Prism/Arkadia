# Lane guard — a stacked PR is a composition hazard the liveness oracle cannot see

Bounded slice on PR #568 (`gate-hygiene/lane-guard-fixed-scope-01`).
Measured 2026-10-25 against `main` `36f53be22d753ffe269f05cbf3fb39212f744207`.

## Defect

`scripts/lane_state.py` judged a claimed-open lane PR by its **state** (open /
merged / closed) and never by its **base**. A PR whose base branch is another
branch is *stacked*: merging it lands the base branch's commits as well, and the
review of the child covers only the child.

The liveness oracle cannot see this. It proves merged-ness from local ancestry
(`git merge-base --is-ancestor`), and a stacked PR and an unstacked one have
**identical ancestry** from the lane's point of view. Whether a PR is safe to
merge *as advertised* therefore had two halves, and only one was checked.

The snapshot could not even report it: `lane_state_refresh.py` recorded
`number`, `branch`, `head_sha`, `draft`, `updated_at`, `title` — and not `base`.

## Measured hazard, live

The repaired guard reports exactly one finding on live `main`, and it is a true
positive:

```
DRIFT PR #508 (lane 4 open_prs) targets base branch
'feat/engineering-acceptance-authority', not 'main'; it is STACKED, so merging
it would land its base branch's commits unreviewed
```

Ancestry measurement, not inference:

| measurement | result |
| --- | --- |
| `gh pr view 508 --json baseRefName` | `feat/engineering-acceptance-authority` |
| `git merge-base --is-ancestor ef82cb9e origin/main` | **fails** — base carries unmerged commits |
| `git log --oneline origin/main..ef82cb9e` | **>=8 commits** beyond main |

So merging #508 would land at least eight commits that #508's own review never
covered. The ordinary path shows none of this: the PR is `MERGEABLE`, its checks
are green, and its diff against its base is exactly what it advertises.

The same hazard applies to **PR #568 itself**, which this slice advances:
`gh pr view 568` -> `base=gate-hygiene/lane-guard-authority-boundary-01`, and
`git merge-base --is-ancestor origin/gate-hygiene/lane-guard-authority-boundary-01
origin/main` fails. It is disclosed on the PR body, not silently repaired: base
retargeting is a governance decision, not a guard fix.

## Repair

| file | change |
| --- | --- |
| `scripts/lane_state.py` | `DEFAULT_BRANCH` constant; `_base_branch_findings()`; called from the `--verify-live` path |
| `scripts/lane_state_refresh.py` | record `base_ref` on every open-PR entry |
| `docs/control-plane/parallel-ui/lane-state.json` | re-measured (`--write`) so the field exists |
| `tests/test_lane_guard_stacked_pr.py` | 6 tests: the detector, its controls, and the producer->consumer pin |

The default branch is a **constant**, not a snapshot field, so a snapshot cannot
redefine what counts as unstacked. A record with no readable base is reported as
`UNKNOWN` — fail closed, never assumed unstacked. A record that is *absent* is
left to `_pr_state_findings`, so one fact is not reported as two findings.

The producer records an absent `base` as `None` rather than raising: a crash
there would abort the whole snapshot and hide every other lane's state. Found by
measurement — the first cut used `pr["base"]["ref"]` and the probe's synthetic
fixture (which omits `base`) turned **19 passed** into **6 failed**. That was a
real producer defect, not a fixture defect.

## Evidence

```
python -m pytest tests/test_lane_instruction_doc_currency.py \
  tests/test_lane_currency_ci_wiring.py tests/test_lane_guard_fixed_scope.py \
  tests/test_lane_guard_scope_boundary.py tests/test_lane_guard_stacked_pr.py -q -rEf
-> 87 passed
python -m pytest tests/architecture -q   -> 11 passed
python scripts/lane_state.py --check --verify-live   -> exit 1, 1 DRIFT finding
```

Node attribution: `--collect-only` on the new file is **6** nodes; the delta is
exactly that, and the file is content-derived into the lane-guard domain
(`scripts/lane_guard_domain.py` finds it via the `lane-state.json` needle).

## Boundary

Read-only with respect to GitHub. No merge, no retarget, no deployment. The
finding is **reported**, not repaired: re-pointing #508 or #568 at `main` is a
human decision. `main` is untouched.
