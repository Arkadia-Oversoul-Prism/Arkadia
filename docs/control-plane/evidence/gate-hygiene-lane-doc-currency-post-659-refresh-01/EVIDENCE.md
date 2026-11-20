# EVIDENCE — lane-doc-currency refresh after #659 (gate-hygiene)

**Pass:** `gate-hygiene/lane-doc-currency-post-659-refresh-01`
**Measured:** 2026-11-16, `main` = `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`
**Disposition:** `main` was RED on its own `lane-doc-currency` gate; repaired by re-deriving the
lane-state snapshot. Docs-only change, no source or authority surface touched.

---

## 1. Defect — `lane-doc-currency` is red on `main` itself

Live check-run on the current `main` head (`f9bd8da9`) reports
`lane-doc-currency` = **failure** (run `43923618303`, `event=push`). Reproduced locally:

```
$ python scripts/lane_state.py --check
  DRIFT snapshot is stale: 1 commit(s) since it was recorded (0f174e90) changed a
  guarded lane doc (docs/control-plane/parallel-ui/AGENT-01-SHELL.md,
  ...AGENT-04-ARKANA-WEAVER-LAB.md) -- re-measure the lane PRs and refresh the
  snapshot (first: 51a19ae6)
exit=1

$ python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q -rEf
FAILED tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main
1 failed, 66 passed
```

This is not branch-caused: it is the state of canonical `main`.

## 2. Root cause — a lane PR edited its own doc without refreshing the snapshot

`_freshness_findings` anchors its staleness window on **the newest commit that touched the
snapshot file**, then asks whether any commit in `(reference, current_main]` touched a guarded
lane doc. The window is therefore sound only while every doc edit is accompanied by a snapshot
refresh *in a commit that is an ancestor of `main`*.

Measured facts:

| Fact | Value |
|---|---|
| newest commit touching `lane-state.json` in `19697a6a..main` | `0f174e90` (#658) — the reference point |
| commits after the reference touching a guarded lane doc | **1** — `51a19ae6` (#659) |
| `51a19ae6` files | `AGENT-03-SOLARIUN-KNOWLEDGE.md`, `tests/test_knowledge_graph_health_read_boundary.py`, evidence doc |
| `lane-state.json` in `51a19ae6` | **absent** (`git diff 51a19ae6^ 51a19ae6 -- lane-state.json` → empty) |

`#659`'s commit message states "The lane doc and the shared lane-state snapshot are updated in this
same commit". The doc **was** updated; the snapshot **was not**. The message's claim is not
supported by the commit's file list — a stale citation, recorded here rather than reconciled.

## 3. Why the gate passed on the PR but failed on `main` — the structural mechanism

`lane-doc-currency` ran on PR #659 (run `43668645764`, head `da103a23`, `pull_request`, **success**).
It fails only after the merge. The two runs measure **different windows**:

| Context | `base_main` / reference | Guarded-doc commits in the window |
|---|---|---|
| PR #659 at `da103a23` | snapshot `base_main` = `19697a6a` (the PR's own base) | **0** — the branch's doc edit is not yet in `main`'s ancestry |
| merged `main` at `51a19ae6`+ | reference = `0f174e90` | **1** — the merge landed the doc edit after the reference |

On the PR branch the snapshot's `base_main` equals the PR's base and the branch's own doc edit is
unreachable from it, so the freshness window is empty and the gate is green. The merge makes the
doc edit reachable from `main`, and the same guard then reports it. **A lane PR cannot observe this
defect in its own CI run; only the composition can.** This is the same class already recorded for
the console-contract and economic-seam derived domains.

## 4. Repair — re-derive, do not hand-edit (precedent: PR #613)

`scripts/lane_state_refresh.py --write` is the derivation. Hand-editing the snapshot produces a
file that disagrees with the next refresh.

```
$ python scripts/lane_state_refresh.py --write --base-main f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a
lane 1: doc_guard=idle  active=#None open=[] merged=[423, 425, 426, 427, 429, 588, 610]
lane 2: doc_guard=idle  active=#None open=[] merged=[420, 430, 492]
lane 3: doc_guard=idle  active=#None open=[] merged=[421, 431, 621]
lane 4: doc_guard=idle  active=#None open=[] merged=[422, 428, 601, 605, 620]
unassigned open PRs: [657]
wrote docs/control-plane/parallel-ui/lane-state.json
```

Diff: **4 lines, 1 file** — `observed_at`, `base_main`, and PR #657's `head_sha` / `updated_at`.
No lane's `open_prs`, `merged_prs`, `active_pr`, or `doc_guard` changed (all four lanes were and
remain `idle`; #657 remains `unassigned_open_prs`).

## 5. Proof

| Check | Before | After |
|---|---|---|
| `python scripts/lane_state.py --check` | exit **1** (DRIFT) | exit **0** |
| `python scripts/lane_state.py --check --verify-live` | — | exit **0** (`doc-guard lanes ['1','2','3','4']; deferred []`) |
| `tests/test_lane_instruction_doc_currency.py` + `tests/test_lane_currency_ci_wiring.py` | **1 failed, 66 passed** | **67 passed** |
| `tests/architecture` | — | **11 passed** |
| `--collect-only` node count | 67 | **67** (unchanged — data-only repair, no new nodes) |

Negative control (the guard's own decision function, driven directly): the pre-repair snapshot blob
plus `current_main = f9bd8da9` returns the staleness finding; the repaired blob returns `[]`. The
same function is what `--check` and the fitness test call, so the repair is proven against the
decision surface rather than against a re-implementation.

## 6. Attribution — node identity, not counts

`--collect-only` is **67** on both trees, so no node was added or removed. The single node that
changed state is
`tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main`
(FAILED → passed). No other node in the two suites moved. Architecture is 11/11.

## 7. Scope and boundaries

- Changed path: `docs/control-plane/parallel-ui/lane-state.json` (plus this evidence record).
- CP10 mutation-boundary judge on both paths: **PASS**.
- No source file, test file, workflow, authority surface, or governance document was edited. The
  lane docs themselves were **not** touched — only the derived snapshot.
- Not repaired here (separate bounded workstreams, recorded not executed):
  - `console-contract` is also red on `main` (`f9bd8da9`, run `43923778351`): the authenticated
    mission harness fails on `authorization record did not report human origin`
    (`web/arkadia_console/exercise_mission_workspace.py:154`). It is intermittent across revisions
    (green at `ced8eaed`/`51a19ae6`, red at `0f174e90`/`f9bd8da9`) and touches
    `lab/engineering_lab/runtime.py` authorization semantics — an authority surface.
  - `Canonical Render Browser Smoke` is red on `main` (run `43923778266`) and has been failing since
    at least `2026-11-06`; it is a production-runtime observation, not repository-source debt.

## 8. Recurrence risk (recorded, not repaired)

The defect is structural: a lane PR that edits its own doc must also refresh the snapshot **in the
same commit**, and the guard cannot detect the omission until after the merge (see §3). Every lane
PR in this repository carries that obligation, and `#659`'s own commit message asserted it was met
while the file list shows it was not. A guard that judges the *merged* tree cannot be satisfied by a
branch that is green on its own base. Closing the class would need the gate to compare the doc edit
against the snapshot refresh within the PR's own commit range — a change to what the gate judges, so
it is a separate bounded workstream for sovereign review. Discovery does not authorize execution.

## 9. Disposition

`main` `lane-doc-currency` red → repaired in source. The branch is a **draft**; under GOV-03 merge
execution is human-only. No merge is performed or claimed here.
