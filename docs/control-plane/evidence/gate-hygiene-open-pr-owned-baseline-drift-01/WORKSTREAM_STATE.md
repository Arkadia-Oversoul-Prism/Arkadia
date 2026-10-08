# WORKSTREAM_STATE â€” gate-hygiene/open-pr-owned-baseline-drift-01

| field | value |
|---|---|
| base main | `441379913d1b03ceb6a5af45ea543ca6762cb482` |
| branch | `gate-hygiene/open-pr-owned-baseline-drift-01` |
| objective | reconcile the recorded baseline test-debt node set to a live `main` measurement; attribute the 7 newly-recorded nodes to their owner PRs; make the reconciliation compositional (era set âˆª open-PR-owned set) |
| change set | `tests/fixtures/baseline_node_set.txt` (10 â†’ 17), `tests/fixtures/open_pr_owned_drift_node_set.txt` (new), `tests/fixtures/era_set_open_pr_owned_node_set.txt` (new â€” era-set ownership), `tests/fixtures/superseded_baseline_node_set_10.txt` (new archival), `tests/test_baseline_fingerprint.py` (guards), health docs, this evidence |
| architecture | 11/11 (`tests/architecture -q`) |
| fingerprint tests | 33 collected / **33 passed in every clone regime** (24 before; +9 guard functions: 6 incl. the live depth probe whose gate was repaired in Â§10, and 3 for the era-set ownership moved out of prose in Â§13) |
| full suite (`main` baseline) | 16F / 1772P / 22S / 1E â€” 17 failing/error nodes (branch: 1778P, +6 new guards) |
| canonical fingerprint | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` (outcomes) / `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224` (ids) |
| superseded pair (10 nodes) | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` / `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |
| superseded pair (18 nodes) | `6c7bf8218fd1e0ae9bc970653e98c18b3a78b69a5c4920dac9f4747c033e4648` / `2bc35996b21de6529ffffab63446c8bd7295c388e841a2807101d189eaf7da01` |
| failure node-set delta | **none** â€” `tests/`, fixtures, docs only; no node enters or leaves the failing set |
| `api/main.py` | untouched, compiles, 2462 / 2600 |
| open PRs at pass start | 12 (#337â€“#358) |
| depth-1 clone addendum | a depth-1 clone (the automation's shape) *reported* **21** nodes (not 18); the four extras are the `test_agents_md_encoding_adjudication.py` nodes named as `DEPTH1_CLONE_DEPENDENT_NODES` (the earlier single-node count was measured as wrong and corrected). **Superseded by the depth-repair row below**: those four nodes are now repaired and the depth-1 clone reports the same 17 nodes as a full-history one. |
| depth-repair (this pass) | the four `DEPTH1_CLONE_DEPENDENT_NODES` now decline (`skip`) when their pinned `AGENTS.md` revision is unresolvable, and the CLI summary node accepts the documented undecided exit `2`. The fingerprint probe's "must fail in a bare clone" pin is superseded by "must not fail in **any** clone regime". Measured: full history **17** nodes, `--depth 1` clone of this head **17** nodes, node-set sha256 `26c2b4c7â€¦` **identical** (`-4 / +0`). Test/evidence only. |
| probe gate repair (Â§10) | the live probe's `--is-shallow-repository` predicate was `true` in *both* the automation's partial clone and a true `--depth 1` clone, so the probe failed its own assertion (empty failed set) instead of skipping. Re-gated on whether `AGENTS.md` history is absent (â‰¤ 1 revision) and both directions are now asserted. Measured: 30 passed in both regimes; 1 failed on the branch's own CI before. |
| era-set ownership (Â§13) | the measured fact that #357 repairs three of the era set's ten nodes was prose-only; it is now `tests/fixtures/era_set_open_pr_owned_node_set.txt` plus three guards. Negative control: appending a bogus entry to the fixture â†’ `3 failed, 30 passed`; restored â†’ `33 passed`. `era_set âˆª drift == the recorded 17`. |
| status | IMPLEMENTED â€” ready for sovereign review |
| independent re-verification (Â§11) | re-derived from a fresh clone: canonical pair reproduced from a live `main` run; all 7 drift-set nodes re-run at their owner heads (all pass); compositional guard proven by editing the recorded fixture itself (2 failed, 28 passed), not just the predicate |

## Deterministic next action

- **Current state**: branch `gate-hygiene/open-pr-owned-baseline-drift-01` carries a bounded,
  test-side baseline reconciliation; 33/33 fingerprint tests pass in **every** clone regime
  (automation partial clone, full history, and a true `--depth 1` clone); architecture 11/11.
  The latest pass (§13) moved the era-set open-PR ownership out of prose into
  `tests/fixtures/era_set_open_pr_owned_node_set.txt` plus three guards, and pinned the
  recorded counts to the fixtures so the two cannot drift apart.
  This pass replaced the single-node depth-1 pin with the measured four-node set
  (`DEPTH1_CLONE_DEPENDENT_NODES`) and added a live probe that asserts the set against the
  clone's real failures, so the fixture is reconstructable from the automation's own depth-1
  clone as well as from a full-history one â€” and the naming is now falsifiable rather than
  merely structural. A follow-on pass repaired the probe's own gate predicate (Â§10), which had
  keyed on `--is-shallow-repository` â€” a flag `true` in both regimes â€” and therefore failed
  instead of skipping in the automation clone.
- **Evidence**: `docs/control-plane/evidence/gate-hygiene-open-pr-owned-baseline-drift-01/EVIDENCE.md` (Â§8 set addendum, Â§10 probe-gate repair, Â§11 independent re-verification of the attribution and the compositional guard, Â§12 depth-repair pass removing the last clone-depth dependence).
- **Proposed (not executed) follow-on**: the fingerprint guard is not a trigger path or run target in any workflow (`grep -rn baseline_fingerprint .github/workflows/` returns 0), so the compositional guarantee holds only when invoked by hand. Wiring it into a workflow is a separate bounded task, deliberately not widened into here.
- **Depth-repair pass (`653151be`)**: the four `DEPTH1_CLONE_DEPENDENT_NODES` no longer fail in a
  history-absent clone (they decline), and the probe that *required* those failures is superseded
  by "must not fail in any regime". Decisive measurement: a true `git clone --depth 1` of this head
  yields the **same 17 nodes** and the same node-set sha256 as a full-history run, so the
  fingerprint is now clone-depth independent. Test/evidence only.
- **Blockers**: none for this branch. The 3 `test_m02a_ci_gate_integrity.py::test_allowlist_*`
  failures remain `main` debt owned by open PR #354; the `test_autonomy.py` ERROR is the
  sovereign-reserved CE-01 collision.
- **Authorized next action**: sovereign review and merge of this PR. Then re-measure `main`
  and, with #347/#354/#355/#356 (drift-set owners) and #357 (repairs three era-set solspire
  nodes) merged, expect the recorded set to shrink â€” re-run the
  fingerprint pass rather than reuse this pair.
- **Pass 13 addendum (base advance, no rebase)**: `main` moved
  `44137991 → 24a00f85` (two natlas HF-auth commits, `lab/engineering_lab/natlas.py` only).
  Disjoint from this change set, so `mergeable=MERGEABLE` / `mergeStateStatus=CLEAN` and no
  conflict exists. A `git rebase origin/main` was started and **aborted** — rewriting the 13
  recorded commits would need a force-push, which this contract forbids; the branch
  fast-forwards `edc18b98 → 7c4955e6` with no force and the merge commit absorbs main's
  advance. Both trees re-measured this pass: `main` `24a00f85` = `16F/1772P/22S/1E` (17 nodes)
  and this head = `16F/1781P/22S/1E` (17 nodes) — **same canonical pair**
  `26c2b4c7…`/`571e599f…`, zero node delta. On a non-rebased branch `git diff
  origin/main..HEAD` lists `lab/engineering_lab/natlas.py`; that is absence, not a revert.
  Recorded in `EVIDENCE.md` §14.
- **Pass 13 addendum corrections (`d71bcfbd`, `d585e5cb`)** — two defects in this pass's *own*
  notes, corrected in place rather than left standing:
  (1) the head figure was quoted as `16F/1781P/22 errors`; the summary reads **22 skipped,
      1 error**. Exactly one error (`tests/test_autonomy.py`, sovereign-reserved CE-01). Only
      decidable under `-rEf`; under `-rf` the `ERROR` line is hidden and the tree fingerprints
      as 16 nodes — a subset, not a baseline.
  (2) an intermediate `mergeStateStatus: UNSTABLE` was drafted as a pre-existing Vercel
      failure. **Measured, not remembered:** all 8 checks on the head are success (including
      `Vercel – console` and `Vercel – arkadia-prism`) and the settled state is
      `MERGEABLE`/`CLEAN`. The `UNSTABLE` is transient registration lag — **reproduced** on the
      second push of this pass (`UNSTABLE, UNSTABLE, CLEAN`). Read per-check truth from
      `commits/<sha>/check-runs` + `commits/<sha>/status`; poll merge state until it settles.
  (3) the 17 live node **ids** diff clean against `tests/fixtures/baseline_node_set.txt`
      (prefix-stripped, zero delta) — the recorded set is literally the same list, not merely
      hash-consistent.
- **Forbidden**: merge, force-push, push to `main`, fixing the CP10 allowlist here, touching
  `weaver/autonomy`.
