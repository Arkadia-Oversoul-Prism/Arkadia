# EVIDENCE — prism-l1-lane-instruction-doc-currency-01

Lane 1 (shell / navigation / integration seam) bounded slice.
Branch: `feat/prism-l1-lane-doc-currency-01`.

## Objective

Repair the Lane-1 lane instruction-doc drift and give it a continuous guard.

## Measured defect (pre-repair)

Measured 2026-10-15, base `main` `7580bd8f0ca2925518d78775f9a323ff0df8bc66`,
GitHub REST `pulls` API, read-only:

- `AGENT-01-SHELL.md` declared **Active branch** `feat/prism-next2-01-shell-contract-map`
  and **Active PR #429**. PR #429 is `state=closed merged=true`.
- `AGENT-02` declared #430 (`closed merged=true`); `AGENT-04` declared #428
  (`closed merged=true`); `AGENT-03`'s wave header named #431 (`closed merged=true`)
  but carried a later dated status block naming **#450** as the authoritative
  pointer (last declaration wins) — #450 is `closed merged=false`, i.e. closed
  without merge. Every one of the four docs' authoritative pointers named a
  closed thread.
- Lanes 1, 2 and 3 also declared base revision
  `f390526ab14e122fef358ef9b9e1cd438509463c`; lane 4 carries no base-revision field.

A successor agent reading a lane doc would resume a **merged** thread. This is
the continuity failure the lane-doc format exists to prevent.

Live lane threads at the base revision (all `state=open`):

| lane | open PRs | branch(es) |
|---|---|---|
| 1 | #507, #529 | `feat/prism-l1-legacy-route-coverage-01`, `feat/prism-l1-lens-strip-keyboard-01` |
| 2 | #492, #528, #538 | `feat/prism-next7-02-pipeline-strip`, `feat/prism-l2-*`, `fix/prism-l2-*` |
| 3 | #526, #527, #534, #537 | `fix/knowledge-traverse-edge-dedup-01`, `feat/prism-l3-*`, ... |
| 4 | #536 | `feat/prism-l4-run-artifact-trace-01` |

Merged wave PRs (measured, all `merged=true`, closed): #420, #421, #422, #423,
#425, #426, #427, #428, #429, #430, #431.

## Scope (and ownership boundary)

Lane instruction docs are **lane-owned**. `SHARED-CONTRACTS.md` row 1 assigns
the shared shell instruction to Lane 1, so this pulse repairs **only**
`AGENT-01-SHELL.md`. It deliberately does **not** touch:

- `AGENT-02` — owned and already being repaired by open PR **#492**
- `AGENT-03` — owned and already being repaired by open PR **#526**
- `AGENT-04` — owned and already being repaired by open PR **#536**
- `SHARED-CONTRACTS.md` — held by open PR **#496**

Those lanes are recorded in the snapshot as `doc_guard: "deferred"` naming the
owning open PR. The deferral is **enforced, not silent**: a deferral is valid
only while the named PR is open, so it cannot become a permanent exemption.

## Change

1. `docs/control-plane/parallel-ui/lane-state.json` — new machine-readable
   snapshot of the four lane threads: base revision, observed time, per-lane
   open PRs with full 40-char head SHAs, merged PRs, and doc disposition.
   Single source of the pointer truth; docs are judged against it.
2. `scripts/lane_state.py` — the guard. Compares each doc's declared
   `**Active branch:**` / `**Active PR:**` against the snapshot (last
   declaration wins, so a later dated status block supersedes the wave header),
   and validates deferrals. `--check` exits non-zero on drift.
3. `tests/test_lane_instruction_doc_currency.py` — fitness test over the real
   snapshot and real docs, with negative controls.
4. `docs/control-plane/parallel-ui/AGENT-01-SHELL.md` — pointer repaired to the
   live Lane-1 thread (#507), base revision updated, superseded pointers
   recorded.
5. `.github/workflows/lane-doc-currency.yml` — continuous execution surface
   (the guard previously ran only by hand).

## Proof

```
python -m pytest tests/test_lane_instruction_doc_currency.py -q -rEf   -> 15 passed
python scripts/lane_state.py --check --base-main 7580bd8f...           -> exit 0
```

Guard run against the **unrepaired** lanes 2/3/4 in the current tree (lane 1 is
repaired in this branch, so it no longer reports; the pre-repair lane-1 finding
took the same shape with `PR #429`):

```
DRIFT lane 2 (AGENT-02-...): declares PR #430, which is not an open lane PR in the snapshot (open: [492, 507, 526, 527, 528, 529, 534, 536, 537, 538])
DRIFT lane 3 (AGENT-03-...): declares PR #450, which is not an open lane PR in the snapshot (open: [...])
DRIFT lane 4 (AGENT-04-...): declares PR #428, which is not an open lane PR in the snapshot (open: [...])
DRIFT lane 4 (AGENT-04-...): no **Active branch:** pointer
exit=1
```

Lanes 2/3/4 are deliberately left doc-unrepaired (lane ownership — see above);
they are recorded `deferred` in the snapshot, so the top-level `--check`
invocation judges only the `current` lane 1 and exits 0.

### Live negative control

Reverting the **real** `AGENT-01-SHELL.md` to its pre-repair pointers and
re-running the fitness test reddens exactly the two live-corpus nodes:

```
FAILED ...::test_live_guarded_docs_agree_with_the_snapshot
FAILED ...::test_lane_one_shell_doc_does_not_name_a_merged_pr
2 failed, 13 passed
```

Restore → `15 passed`. A synthetic fixture would not prove the detector reads
the real file; this control does.

## Regression boundary

Measured this pass by `--collect-only` diff across two worktrees (`main`
`7580bd8f` vs this branch), which is how a `+N` delta is attributed:

| | main | branch | delta |
|---|---|---|---|
| whole suite | 3132 collected | 3154 collected | **+22** |
| `tests/test_lane_instruction_doc_currency.py` | (absent) | 15 | +15 |
| `test_ci_gate_trigger_coverage.py` | 90 | 93 | +3 |
| `test_workflow_injection_boundary.py` | 46 | 47 | +1 |
| `test_ci_suite_collection_continuation.py` | 93 | 95 | +2 |
| `test_gate_filter_selection.py` | 47 | 48 | +1 |

`+22` = the 15 new nodes **plus 7** the generic workflow-scanning suites gain by
construction from one new workflow file. That is the whole delta; no other file
changes node count.

- `tests/architecture` — **11 passed** (measured, unchanged).
- CP10 mutation boundary — all six new/modified paths judged ADMITTED
  (`cp10_mutation_boundary_policy.py --judge`, measured).
- `tests/test_m02a_ci_gate_integrity.py` + the four scanner suites —
  **351 passed** (measured).
- No shared/other-lane file was edited.
- `api/main.py` untouched (boot-code rule not triggered).

## Remaining uncertainty

- The snapshot is a hand-refreshed mirror; it is not self-updating from GitHub.
  The guard is read-only and never fetches. Refresh the snapshot by re-measuring
  the lane PRs with the GitHub reads API (read-only) on any pulse that advances a
  lane. When the snapshot's `base_main` falls behind live `main`, the guard
  reports freshness — but it does not itself detect a moved `main`. This is
  recorded, not repaired.
- The lane-2/3/4 deferrals clear when #492/#526/#536 merge; the disposition
  check forces that reclassification.

## Authorization

Draft PR only. No merge, deployment, or acceptance is authorized by this
workstream. Human merge authority is final.
