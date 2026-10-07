# Gate-07 — composed-batch integration review (PRs #329, #331, #332, #334, #335, #336)

**Workstream:** `gate07/batch-integration-review-01`
**Authority:** review + evidence only. No merge, no push to `main`, no mutation of any subject
PR, no scope expansion.
**Status:** IMPLEMENTED — integration measured; one released serialization constraint identified;
subject PRs are individually mergeable today; the constraint applies only to a *batch* merge.

## 1. Why this pass exists

Six open GATE-07 PRs (#329, #331, #332, #334, #335, #336) each declare a green check-run and
`mergeable: true`, and five of the six are **test-only or docs-only**. But *mergeable* is a
Git textual property, not a semantic one — the repository has paid for this lesson twice
(`AGENTS.md`: "Git conflict-free is not proof of semantic compatibility"; "a merge can invent a
state present in neither parent"). No pass has ever composed this batch and executed it. This
pass reconstructs the batch, merges it, resolves the one real conflict, and measures the
composed tree against a freshly re-measured baseline.

## 2. Reconstruction (live, this pass)

| item | measured value |
|---|---|
| canonical `main` | `74e8ea53a30213db8783e6733679d2f11903de0b` |
| batch base (all subject PRs) | `main` @ `17e626cd27f8ea1e31f711fb787e6c7e5027ec70`, i.e. `4587890..#333` |
| subject PRs | #329 `9c7c5764`, #331 `be1f3f05`, #332 `2a2a8fa1`, #334 `3a29fdea`, #335 `ef5df651`, #336 `0dc5383d` |
| #330 | verification-only companion of #329 (`main`/`4587890`); carried in the compose as a README-only no-op for #329's ancestry |
| composed tip | `90e80b5c1abc4dd3178240ecb7a5481efba6f14d` (see §3) |

Changed-path inventory was read from each PR's diff against its own base, not from PR prose.
Two checks are worth stating because they correct a stale reading:

- **#336 is four files, not thirty-two.** `git diff origin/main pr336` shows 32 paths and
  −7091 lines because #336's own base is `17e626c`, which already removed the `solspire/voice_*`
  tree that `74e8ea5` then re-added. `git diff 17e626c pr336` shows the real change: 4 files,
  +370 lines, `weaver/engineering_router.py` +16. A future pass must diff against the PR's base,
  not `main`.
- **#331 and #335 are not duplicates and not redundant.** Both edit
  `.github/workflows/arkadia-engineering-scheduler.yml` and
  `tests/test_scheduler_trajectory_conformance.py`, but add disjoint tests:
  #331 adds `test_session_reports_status_and_move_before_any_failure_exit` (+2 ordering
  negative controls) and writes the outcome **before** the FAILED early-exit; #335 adds the
  `Session report` step's blocker surface (`test_session_report_surfaces_router_blockers`,
  `test_session_report_runs_even_after_a_failure_exit`, `test_session_report_states_an_absent_session_result`,
  `test_negative_control_pre_fix_report_is_silent`). Neither test name appears in the other.
  A former plan to open a "dedup verification" PR over #331/#335 is therefore **unfounded** —
  recorded here as `CONTRADICTED`, not executed.

## 3. The one real conflict, and its resolution

The composed merge is clean for #329→#331→#332, then:

```
Auto-merging .github/workflows/weaver-mvp2-validation.yml
CONFLICT (content): Merge conflict in .github/workflows/weaver-mvp2-validation.yml
```

**#329 and #334 both add their guard file to the same two lists in
`weaver-mvp2-validation.yml`** — the `on.push.paths` filter and the `on.pull_request.paths`
filter — and #334 also appends its test to the existing `Engineering-router status truthfulness
guard` step's `run:` block, at the exact position #329 inserted a whole new step. Three regions
conflict.

The resolution is a **union**: on both path filters, keep #329's `test_attention_truthfulness.py`
and `test_worker_attention_composition.py` *and* #334's `test_router_schema_vocabulary_closure.py`;
in the job steps, keep the truthfulness step's `run:` block *including* the closure-guard line
(so #334's own wiring stays intact), and keep #329's separate
`Worker→attention composition seam guard` step. This is the same union the repository already
applies to the sibling `gate07/scheduler-*` workflow in #335. The resolved file is committed
verbatim as `weaver-mvp2-validation.resolved.yml`; its composed blob is
`a37b4b911b93a474605462749648b73155a5afce`.

The resolved workflow parses (`yaml.safe_load` → triggers `push`, `pull_request`,
`workflow_dispatch`).

## 4. Measurement — the composed tree

Composed in a throwaway worktree of `main` + {#329,#330,#331,#332,#334,#335,#336}, clocking the
0.27 s timezone-sensitive test with `TZ=America/New_York` so its date word is correct.

**GATE-07 guard set (the six files the batch adds or touches):**

```
python -m pytest -q -rEf \
  tests/test_attention_truthfulness.py tests/test_worker_attention_composition.py \
  tests/test_router_schema_vocabulary_closure.py tests/test_engineering_router_status_truthfulness.py \
  tests/test_engineering_scheduler_bootstrap.py tests/test_scheduler_trajectory_conformance.py
=> 81 passed, 1 xfailed
```

**Full suite, composed vs baseline, same environment:**

```
main   (74e8ea5) : 10 failed, 1703 passed, 20 skipped, 1 error
composed (batch) : 10 failed, 1737 passed, 20 skipped, 1 xfailed, 1 error
```

Failing/error **node set** sha256 (identity, not counts):

```
92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413   (11 nodes, main AND composed)
```

The node set is **byte-identical** — regression is **unchanged**. `+34 passed` is exactly the
batch's new passing tests (#334's `test_router_schema_vocabulary_closure.py` + #336's added
`test_engineering_router_status_truthfulness.py` cases + #329's composition guard), and the
`1 xfailed` is #329's strict xfail of the router cleaner-stop contract, which is expected.

**Architecture fitness:** `python -m pytest tests/architecture -q` → **11 passed** on the
composed tree (and on `main`).

**The 11 baseline nodes** are pre-existing main debt, unrelated to this batch, and are recorded
not fixed: `test_autonomy.py` (CE-01 collection error), `test_ais_capability_profile_onboarding.py`,
`test_ais_w2_living_gate_grove_handoff.py`, `test_identity_spine_w1.py`,
`test_m02_reasomate_truth.py`, `test_solspire_r1_governance_convergence.py` (×2),
`test_solspire_r3_execution_runtime.py`, `test_steward_filter.py` (×3).

> The published baseline (`804/54/12/2` at `6038989`) does not reproduce in this environment, as
> the repository already records. Attribution here is made from the sorted `FAILED`/`ERROR` node
> list only — the technique the repository records as correct.

**CP10:** all 30 changed paths across the batch resolve under the policy `LEGIT` allowlist
(`docs/`, `tests/`, `weaver/`, `.github/`, and root `[^/]+\.md$`); this pass adds only
`docs/control-plane/`. The composed tree touches no path outside the allowlist, so
`--judge` is `PASS`.

## 5. Defects surfaced, correctly scoped out of this pass

Both were already recorded by the subject PRs and are **not** this pass's to repair:

- **Router "clean stop" contract (flips #329's strict xfail).** `select_next_move()` always emits
  a blocker when it finds no routable move, so a genuinely complete trajectory composes a pushed
  HIGH `WEAVER_BLOCKED` every idle hour. #329 pins it as a strict xfail; repairing it changes the
  router's blockers contract and needs its own bounded workstream.
- **Live trajectory vocabulary.** `TRAJECTORY-CONSOLE-COMPLETION-01.yaml` still routes to
  `NO_LEGAL_MOVE` because G12-A/G12-C sit at `merged_acceptance_pending`, a status the router does
  not recognize. #332 records the vocabulary decision and #334 pins the seam; **neither edits the
  live trajectory**, so a future session will still hit this until the decision in #332 is executed
  under authorization. Observed live this pass (`ARKADIA_ENGINEERING_TRAJECTORY=…CONSOLE-COMPLETION-01.yaml`)
  → `status: NO_LEGAL_MOVE`, one blocker naming both moves.

## 6. Authorization boundary

- Review only. **No merge; the sovereign merges.**
- Individually, every subject PR is mergeable against `main` today (the conflict is only between
  #329 and #334 when composed).
- If the sovereign merges two or more of these PRs, #329 and #334 **must not be merged in the
  order either alone advertises as conflict-free** — GitHub will present the same three
  conflicts. Merge the batch as a reviewed whole using §3's union so no guard is dropped from
  either path filter.
