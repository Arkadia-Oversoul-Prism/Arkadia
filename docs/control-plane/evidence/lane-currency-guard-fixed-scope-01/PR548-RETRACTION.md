# RETRACTION — #548 does not revert the guard

**This document retracts a specific, material claim made in `COMPOSITION-BLOCKERS.md` §2.2
and in the commit message of `9b109f74`.** The claim was wrong. The correction is recorded
here rather than by quietly editing the earlier document, because the earlier document is
already referenced in review.

**Measured:** 2026-10-25. `main` = `36f53be22d753ffe269f05cbf3fb39212f744207`.

---

## 1. What I claimed, and why it was wrong

**Claim (retracted):** "#548 reverts the guard — `git diff --stat origin/main
3da97fa5316f -- scripts/lane_state.py` → 29 insertions, **458 deletions** … Merging it as-is
would remove the authoritative live PR oracle."

**The command was the wrong comparison.** `git diff A B` is a **two-dot** diff: it compares
the two tips directly and therefore attributes *every* commit on `main` since the merge base
to the branch as deletions. It is not a statement about what the branch does.

**The correct comparison is three-dot against the merge base:**

```
merge-base(main, 548) = 04e1b83b89e5

git diff --stat 04e1b83b89e5 3da97fa5316f -- scripts/lane_state.py
 1 file changed, 12 insertions(+), 7 deletions(-)      <- #548's ACTUAL change

git diff --stat origin/main 3da97fa5316f -- scripts/lane_state.py
 1 file changed, 29 insertions(+), 458 deletions(-)     <- the WRONG comparison I used
```

The 458 "deletions" are commits that landed on `main` after the merge base — the
live-verification work — which #548 never had and never removed.

**This is the exact error my own recorded notes warn against:** *"Diff against the other PR's
own merge base, not against your HEAD … a one-file patch is not a composition."* I applied
that lesson to #492/#538 earlier in this workstream and then failed to apply it here.

## 2. The corrected facts

**#548's own diff** (three-dot, 10 files):

| status | file |
| --- | --- |
| A | `docs/control-plane/evidence/prism-l3-reference-search-owner-scope-01/EVIDENCE.md` |
| A | `docs/control-plane/evidence/prism-lane3-graph-traverse-edge-set-01/EVIDENCE.md` |
| M | `docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md` |
| M | `docs/control-plane/parallel-ui/lane-state.json` |
| M | `knowledge/graph.py` |
| M | `knowledge/search.py` |
| M | `scripts/lane_state.py` (12+/7−) |
| A | `tests/test_knowledge_graph_traverse_boundary.py` |
| M | `tests/test_knowledge_search_boundary.py` |
| M | `tests/test_lane_instruction_doc_currency.py` |

**Deleted files: 0.** **Workflows touched: none** (`git diff --name-status <mb> <head> --
.github/` → empty).

**What #548 actually changes in `lane_state.py`:** it adds an `idle` disposition
(`{"current", "deferred", "idle"}`), plus a guard that `doc_guard=idle` must not still list
open PRs. That is an **additive** change consistent with `main`'s design — not a removal.

**The actual merge, tested** (`git merge --no-commit --no-ff` on a `main` worktree):

- conflicted paths: **1** — `docs/control-plane/parallel-ui/lane-state.json`
- files deleted by the merge: **0**
- merged `scripts/lane_state.py`: guard symbols **8** (same as `main`), `"idle"` refs **2**
  (548's addition) → **main's guard survives and 548's change composes into it**
- merged `.github/workflows/lane-doc-currency.yml`: `--verify-live` refs **1** → survives

**So the merge preserves the authoritative live-PR oracle.** My earlier statement that "its
own checks would read green because the checker it removes is the one that would have flagged
the removal" is **withdrawn** — there is no removal.

## 3. What survives the retraction

The correction removes the *revert* finding. It does **not** clear #548.

**(a) The dead-pointer defect is real and independently confirmed.** In the merged tree
(conflict resolved to #548's side), `declared_pr` for lane 3 returns **#526** — closed
unmerged. And on that merged tree the gate now **fails loudly**, which is the correct
behaviour:

```
DRIFT PR #526 (lane 3 open_prs, lane 3 deferred_to_pr) is recorded as open but is CLOSED
without merging; the thread is dead -- re-measure the lane PRs and re-point the lane
...
EXIT=1
```

**(b) The self-referential green is real, but its cause is different from what I said.**
#548's own `lane-doc-currency` ran on 2026-10-16, when `main`'s workflow did not yet invoke
`--verify-live`. #548 does not touch the workflow, so it never removed the invocation — it
simply **predates** it. The distinction matters: this is a **stale green** (a green from an
older workflow, not evidence about the current gate), not a branch that disabled its own
check. A stale green is still not evidence about the merged result — the merged tree fails —
but the mechanism is staleness, not sabotage.

**(c) The dead pointer is in the lane-3 doc, not in `lane_state.py`.** #548 appends to
`AGENT-03-SOLARIUN-KNOWLEDGE.md`; the last `**Active PR:**` line in its tree is #526. Since
`declared_pr` takes `matches[-1]`, the appended prose must end with a live pointer.

## 4. Corrected disposition for #548

The condition is narrower than I stated, and the hazard is smaller:

| Earlier claim | Corrected |
| --- | --- |
| "reverts the guard; 458 deletions" | **withdrawn** — 12+/7− additive `idle` change; merge keeps the guard |
| "merging would delete the live PR oracle" | **withdrawn** — merged tree has all 8 guard symbols |
| "rebased so it stops reverting `lane_state.py`" | **not required** — it does not revert it |
| "dead pointer #526 in its tree" | **stands** |
| "green is self-referential" | **stands as stale** — predates `--verify-live`; the merged tree fails the gate |

**Measured condition:** #548 needs its lane-3 doc to end with a live `**Active PR:**` pointer,
and its `lane-state.json` conflicts with `main` (1 path) and must be reconciled on rebase. Its
`knowledge/` and test content is additive and does not conflict.

Whether that is worth doing versus closing #548 as superseded remains a human decision. It is
now a **bounded doc-and-snapshot reconciliation**, not a control-plane integrity risk.

## 5. Process note

I asserted a large, alarming number (458 deletions) from a command whose semantics I did not
check, in a workstream whose own memory explicitly records that two-dot diffs misattribute
unrelated advances. The number was reported to the human before it was verified against the
operation that would actually occur (the merge).

**What would have caught it, and should be standard:** before attributing deletions or
removals to a branch, run `git merge --no-commit --no-ff` in a scratch worktree and inspect
the result — the merge is the operation under review, and it reports conflicts and deletions
by path. I did eventually run it; it should have been the first step, not the last.

---

## 6. #553 — the repair surface is measured, and it is much larger than the label suggested

I first described the #553 repair as "add the missing inputs: `EXP-001.md`,
`OPENHANDS-MVP-01.md`, `tasks.seed.json`" — one input per workflow. **That was an
assumption, and it was wrong.** I proved it wrong by applying it in a scratch worktree at
`899d22424d78`: after adding exactly those three, the guard still reported **3 failed,
19 passed** — unchanged.

### 6.1 The actual gap

`test_a_workflow_selects_every_input_its_guard_reads` is parametrized per workflow and
checks **every history-dependent guard that workflow executes**, not just
`test_m02a_ci_gate_integrity.py`. Measured on the clean tree:

| workflow | guards it executes | inputs missing from `pull_request.paths` |
| --- | --- | --- |
| `provider-routing.yml` | several | **19** |
| `economic-seam-engine.yml` | several | **16** |
| `sg-02-fe-2-v.yml` | several | **28** |

`test_m02a_ci_gate_integrity.py` alone reads **55** inputs (`_guard_inputs`), and the
workflows were missing 15–23 of *those* before the other guards' inputs are counted.

### 6.2 A second, coupled constraint I had not accounted for

The repair is not confined to one filter. `tests/test_ci_gate_trigger_coverage.py::
test_push_and_pull_request_filters_are_identical` requires `push.paths` and
`pull_request.paths` to match. My first corrected attempt added the inputs to
`pull_request` only, and **broke that symmetry**:

- clean tree: `economic-seam-engine.yml` pr=38 push=38 symmetric **True**;
  `sg-02-fe-2-v.yml` pr=58 push=58 symmetric **True**
- after a `pull_request`-only edit: symmetry **False** on both

So the two failures I then saw were **caused by my own patch**, not pre-existing. Verified by
running the symmetry guard on the *unpatched* tree: **33 passed**.

`provider-routing.yml` is a special case — it has **no `push.paths` filter at all** (pr=53,
push=0), and that asymmetry passes on the clean tree, so its repair touches `pull_request`
only.

### 6.3 The proven repair

Adding each workflow's missing inputs to **every filter it has** (both events where both
exist; `pull_request` only where there is no `push.paths`) yields:

```
tests/test_history_depth_ci_wiring.py + tests/test_ci_gate_trigger_coverage.py
124 passed in 8.54s
```

**This is a shape proof, not a proposed patch.** It establishes that the gate is satisfiable
and what it costs; it does not mean the added inputs are the *right* ones, and it does not
authorize the change. The open design question — whether these three workflows should each
select 55+ inputs, or whether the guard's `_history_dependent_guards` inventory is
over-broad — is a real one and belongs to whoever owns #553.

### 6.4 Correction to §2 of `COMPOSITION-BLOCKERS.md` — the #553 acceptance criteria

I wrote that acceptance should require "the three new cases to pass". That stands, but it is
incomplete. Acceptance must also require:

- `test_push_and_pull_request_filters_are_identical` to still pass for every touched workflow
  (the coupling above);
- the guard to be **executed** in CI, not merely listed in a `paths` filter;
- the comparative baseline to be recorded;
- the pre-existing `test_ais_w2_living_gate_grove_handoff.py` failure to remain visible and
  separately classified.
