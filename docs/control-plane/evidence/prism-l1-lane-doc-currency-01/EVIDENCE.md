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
- `AGENT-02` declared #430, `AGENT-03` declared #431, `AGENT-04` declared #428 —
  all `closed merged=true`.
- All four docs declared base revision `f390526ab14e122fef358ef9b9e1cd438509463c`.

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

Guard on the **pre-repair** docs (all four), before the repair:

```
DRIFT lane 1 (AGENT-01-SHELL.md): declares PR #429, which is not an open lane PR
DRIFT lane 2 (AGENT-02-...): declares PR #430, ...
DRIFT lane 3 (AGENT-03-...): declares PR #431, ...
DRIFT lane 4 (AGENT-04-...): declares PR #428, ...
DRIFT lane 4 (AGENT-04-...): no **Active branch:** pointer
exit=1
```

### Live negative control

Reverting the **real** `AGENT-01-SHELL.md` to its pre-repair pointers and
re-running the fitness test reddens exactly the two live-corpus nodes:

```
FAILED ...::test_live_guarded_docs_agree_with_the_snapshot
FAILED ...::test_lane_one_shell_doc_does_not_name_a_merged_pr
2 failed, 12 passed
```

Restore → `15 passed`. A synthetic fixture would not prove the detector reads
the real file; this control does.

## Regression boundary

- `tests/test_lane_instruction_doc_currency.py` is new (+15 nodes).
- `tests/architecture` — **11 passed** (unchanged).
- CP10 mutation boundary — all new paths PASS (`cp10_mutation_boundary_policy.py --judge`).
- `tests/test_m02a_ci_gate_integrity.py`, `test_ci_gate_trigger_coverage.py`,
  `test_workflow_injection_boundary.py`, `test_gate_filter_selection.py` —
  219 + 141 passed (the new workflow is admitted; a new workflow adds passing
  nodes to the generic scanners by construction).
- No shared/other-lane file was edited.
- `api/main.py` untouched.

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
