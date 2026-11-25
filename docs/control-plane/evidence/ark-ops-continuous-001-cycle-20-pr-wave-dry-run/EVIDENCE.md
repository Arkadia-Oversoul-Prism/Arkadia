# ARK-OPS-CONTINUOUS-001 — cycle 20: the queue is composed, not assumed

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Milestone:** 2 of [#732](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/732) — composition and merge-wave dry-run
**Base:** `main` @ `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`
**Measured:** 2026-11-25, this workspace
**Authority:** read-only. No merge, no push to `main`, no deployment, no acceptance.

## 1. The gap this closes

Milestone 1 ([#733](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/733)) reports a
changed-path **overlap** map and says so: *"Composition is a conservative changed-path overlap
map, not a claim of semantic conflict."* An overlap is not a conflict. Two pull requests can edit
one file in different regions and compose cleanly; two pull requests can edit different files and
still compose into a red tree. Neither question is answered by the overlap map, and neither is
answered by GitHub's per-PR `mergeable` field, which only ever describes one branch against its
base.

`scripts/pr_wave_dry_run.py` answers both. It composes candidate heads onto a base revision in a
throwaway worktree, in queue order, and lets `git merge` decide.

## 2. Textual composition — 56 open pull requests

```
python scripts/pr_wave_dry_run.py --base main
base fd0a4fdc | 56 PRs composed in queue order
  CLEAN=53  CONFLICT=3
  CONFLICT #687 on tests/test_gate2_production_observation.py (after [681])
  CONFLICT #724 on AGENTS.md (after [686])
  CONFLICT #728 on .github/workflows/canonical-render-browser-smoke.yml (after [689])
```

Runtime: **4.8 s**. Reproduced independently by the manual `git merge --no-edit` loop that
produced this evidence, which reported the same three conflicts and the same three paths.

Each conflict has exactly one edge, and the nature of each differs:

| Pair | Path | Nature |
| --- | --- | --- |
| #681 / #687 | `tests/test_gate2_production_observation.py` | both **append** at EOF (+185 / +125, 0 deletions). Mechanical concatenation. |
| #686 / #724 | `AGENTS.md` | #686 appends (+37/−0); #724 appends and rewrites 2 lines (+4/−2). Mechanical, but the rewritten lines need a decision. |
| #689 / #728 | `.github/workflows/canonical-render-browser-smoke.yml` | **genuine**: both repair the same workflow (+26/−4 vs +82/−17). Requires adjudication, not concatenation. |

A CLEAN composition is a textual fact about one ordering. It is not merge authorization, not
M1–M13 eligibility, and not a test result.

## 3. Aggregate regression — the composed tree

The 53 clean merges were composed into one tree and the full suite was run on it and on `main`, in
the same environment, with `-rEf --continue-on-collection-errors`.

| Tree | Result | Failing/error nodes | Node-set sha256 |
| --- | --- | --- | --- |
| `main` `fd0a4fdc` | 20 failed, 4253 passed, 22 skipped, 1 error | 21 | `4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916` |
| composed (53 PRs) | 15 failed, 4835 passed, 23 skipped, 1 error | 16 | `d1e9dae2b76a413ff834afdd78cbbb83f7b4e9e484f9ba13106200846d0d5edc` |

Passed counts are **not** comparable: the wave adds tests. Attribution is by node identity.

**Nine nodes the wave repairs** — `test_gov04_bounded_merge_delegation::test_bounded_merge_is_exact_head_and_protected_fail_closed`,
`test_identity_spine_w1::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` (archived
A.I.S path), `test_m01_persistence::test_deletion_propagates_to_durable_corpus`,
`test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key`,
`test_m05_files::test_update_file_supports_rename`,
`test_solspire_r1_governance_convergence` (2), `test_solspire_r3_execution_runtime` (1),
`test_static_ingestion_idempotency::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`.

**Four nodes the wave introduces.** Each is a composition defect that no single pull request could
have observed, because every one of them is green against the tree it was built on:

1. `test_repo_hygiene_gitignore::test_engineering_lab_event_log_is_not_tracked` — **repaired in this
   cycle.** #688 adds a guard whose invariant is that `data/engineering_lab/agent_events.jsonl` is
   not tracked; #718 committed that exact 45-line generated artifact (`c25e9d0a`), a file its own
   branch never reads. Neither PR is wrong alone: #718 lands a runtime log silently, #688 passes.
   Together, `main` goes red. Repaired by removing the artifact from #718
   (`290eb96e`). Paired control: the same composition of #718 + #688 measured **1 failed, 20 passed**
   before the repair and **21 passed** after.
2. `test_http_error_contract::test_the_record_does_not_describe_repaired_debt` — #718 records
   `api/main.py` as unrepaired 5xx-disclosure debt; #729 repairs the eight handlers in that module.
   The record becomes stale the moment the repair lands. **Open** — needs a decision on which PR
   owns the record.
3. `test_prism_ui_inventory_currency::test_every_declared_surface_is_accounted_for_and_every_claim_is_resolvable`
   and `::test_planted_defect_reverting_one_repaired_row_is_reported` — #707 judges the console
   inventory; #704 declares a ReasoMate surface the inventory does not account for
   (`surface 'reasomate' at /reasomate is not accounted for in the inventory`). **Open** — the
   content-derived-domain hazard already recorded in `AGENTS.md`, now with two live PRs on each side.

## 4. What this does and does not establish

- **Established:** the queue is textually composable in 53 of 56 cases; the three conflicts and
  their edges are named; the composed tree repairs 9 nodes and introduces 4, of which 1 is now
  repaired and 3 are recorded open with their owning pairs.
- **Not established:** merge eligibility, M1–M13, branch protection, review sufficiency, deployment
  state, or acceptance. The tool composes commits; it does not judge them.
- **Not measured:** whether a different queue order composes more than 53 cleanly. Conflict pairs
  are symmetric in the three observed cases, so order is unlikely to help, but that is an inference,
  not a measurement.

## 5. Guards added

`tests/test_pr_wave_dry_run.py` (14 tests), each with a control that proves the detector bites:

- **A shared file is not a conflict.** Negative control against milestone 1's shape: the test
  temporarily treats any path overlap as a conflict and asserts this node reddens. Measured:
  `1 failed, 13 passed` under the overlap-as-conflict variant, `14 passed` restored.
- **Mention is not execution.** `echo pytest tests/…` must not count as a gate executing the guard.
  Measured: `1 failed, 12 passed` when the executing step is rewritten to `echo pytest …`.
- **Selection is the `paths` filter, not a mention elsewhere.** Measured: `1 failed, 13 passed` when
  the test path is removed from both filters.
- **`continue-on-error` cannot hide the gate.** Measured: `1 failed, 11 passed`.
- **Fail-closed.** An unresolvable base or a missing head SHA raises rather than emitting an empty
  clean wave; a merge that fails without a conflict raises rather than being reported as CLEAN.
- **Read-only.** No `push`, no `/merge`, no `auto_merge`, no `merge-async` in the source, with a
  control that feeds the detector those forms and asserts each is reported.
- **Cleanup.** The scratch worktree is removed and the caller's `HEAD`/`status` are byte-identical
  afterwards.

`.github/workflows/pr-wave-dry-run.yml` executes the guard, is dispatchable, selects the script,
the guard and itself on both `pull_request` and `push`, and has no `continue-on-error`.

## 6. Next action

1. Human: decide the three textual conflicts (#681/#687 concatenate; #686/#724 concatenate then
   adjudicate the 2 rewritten `AGENTS.md` lines; #689/#728 require a composed rewrite of one
   workflow).
2. Human: decide ownership of the two open composition defects (`#718 ↔ #729` record staleness;
   `#707 ↔ #704` inventory drift).
3. Weaver: re-run `scripts/pr_wave_dry_run.py` after any wave lands and compare node sets, not
   counts.
