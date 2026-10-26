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

---

## 7. The `idle` disposition — measured semantics, and one real weakening

The retraction in §1–§4 removed the "guard removal" finding. It does **not** mean #548's `idle`
change is inert. Measured on the merged tree (`main` + #548, `lane-state.json` resolved to
#548's side), driving `lane_state.py --check --verify-live` with a fabricated lane-3 state:

### 7.1 `idle` downgrades a blocking dead-pointer finding to a non-blocking NOTE

| lane 3 `doc_guard` | EXIT | total DRIFT | **lane-3 DRIFT** | lane-3 NOTE |
| --- | --- | --- | --- | --- |
| `current` | 1 | 7 | **2** | 0 |
| `deferred` | 1 | 6 | **1** | 1 |
| `idle` | 1 | 5 | **0** | 1 |

Isolated to lane 3 alone (all other lanes cleaned, `open_prs=[]`, `base_main` current):

- `doc_guard=current` → `DRIFT lane 3 … declares PR #526, which is CLOSED without merging …`
  **plus** `DRIFT lane 3 … declares PR #526, which is not an open lane PR in the snapshot`
- `doc_guard=idle` → the same dead-pointer text appears as
  `NOTE lane 3 (…) … (lane not owned by this guard; reported, not blocking)`

**Mechanism:** `_declared_pointer_findings(state, records, failure, lanes=current_lanes(state))`
is scoped to `current_lanes()`, which is defined as `doc_guard == "current"`. An `idle` lane
therefore leaves the blocking set, and the same finding is re-emitted through the `advisory`
list, which prints `NOTE` and does **not** contribute to the `findings` list or the exit code.

So `idle` is **not** merely descriptive. It converts a blocking dead-pointer finding into
advisory output for that lane.

### 7.2 Why this is bounded, not alarming

Two measured facts keep it from being the "silent self-exemption" hazard:

1. **`idle` is not automatically producible.** `scripts/lane_state_refresh.py` is untouched by
   #548 (`git diff --name-status <mb> 3da97fa5316f -- scripts/lane_state_refresh.py` → empty)
   and writes only `"deferred"` or `"current"` (line 267). Reaching `idle` requires a human or
   agent to hand-edit the snapshot.
2. **It is guarded against the obvious abuse.** #548 adds
   `if disposition == "idle": if lane.get("open_prs"): findings.append("doc_guard=idle but lane
   still lists open PRs")` — verified firing (`DRIFT lane 3: doc_guard=idle but lane still lists
   open PRs` when `open_prs=[548,549]`).

### 7.3 But the abuse it does *not* guard against is the one that matters

The `open_prs` guard only fires when the lane **still lists** open PRs. Setting
`doc_guard="idle"` **and clearing `open_prs`** — exactly the state a lane would be in after its
work merged — passes that check and leaves the lane outside `current_lanes()`. A lane whose doc
still names a closed PR (#526 here) then produces a NOTE rather than a DRIFT, and the lane stops
being judged as active work.

That is a **deliberate, arguable design**: an idle lane's stale historical pointers are not
active work. But it is an **authority reduction reachable through the snapshot**, and #548
ships it with tests that pin only the *positive* cases
(`test_idle_lane_has_no_open_pr_and_is_not_guarded_as_active_work`,
and the vocabulary assertion `must be 'current', 'deferred', or 'idle'`). There is **no test
asserting that an idle lane's dead pointer still blocks, or that idle cannot be used to escape
a dead-pointer finding.**

**Recommendation (not a decision):** #548's reconciliation should either (a) keep `idle` but add
a test pinning the escape path — an idle lane with a closed declared pointer must still be
reported in a way that fails the gate, or (b) drop `idle` in favour of `deferred`/`current` and
re-propose it as its own bounded change with its authority effect stated explicitly. This is a
design question for #548's owner; I have not edited either branch.

## 8. Making the merge-tree check repeatable

The §5 process note asks for this to be a standard step, not an ad hoc response. The check is
mechanical:

```
# 1. merge-base and the branch's OWN change
MB=$(git merge-base origin/main <head>)
git diff --name-status "$MB" <head>          # what the branch actually does

# 2. the operation under review, in a scratch worktree
git worktree add --detach /tmp/wt origin/main
cd /tmp/wt && git merge --no-commit --no-ff <head>
git diff --cached --name-only --diff-filter=D   # files the MERGE deletes
git diff --name-only --diff-filter=U            # conflicted paths

# 3. read the MERGED WORKING TREE for the symbols at issue
grep -c "<symbol>" <path>                       # NOT `git show :N:` (conflict stages only)

# 4. clean up
git worktree remove --force /tmp/wt
```

Steps 2–3 are the ones I skipped; step 1 alone produced the retracted claim, and step 3 done
with `git show :N:` produced a second near-miss. Both are now recorded in project memory.

---

## 9. `idle` is not speculative — it is in use, it suppresses a live finding, and it is unnecessary

§7 established that `idle` downgrades a blocking finding to a NOTE. The obvious follow-up
question is whether `idle` is *needed*. Measured on the merged tree (`main` + `3da97fa5316f`),
it is **not** — and it is actively suppressing a finding that is a snapshot defect, not a doc
defect.

### 9.1 `idle` is in use, on lane 2

| revision | lane 2 `doc_guard` | lane 2 `open_prs` |
| --- | --- | --- |
| `main` | `current` | `[564]` |
| `3da97fa5316f` (#548) | **`idle`** | **`[]`** |

So #548 is not proposing an unused state — it **converts lane 2** from `current`+`[564]` to
`idle`+`[]`, and its snapshot `note` states the rationale:

> "Lane 2 is idle: #545 is merged and #528 is closed unmerged; **no lane-2 source PR remains
> open**. Do not revive closed PR references."

### 9.2 The premise of that note is false at the merged revision

`#564` — "Lane 2: the NovaNet public field states its page bound", head branch
`feat/prism-l2-field-completeness-01` — is **open** (`state=open`, `merged=false`,
`merged_at=null`). It was **created 2026-10-24T12:35:43Z**; #548's last commit is
**2026-10-16T04:41:16Z**.

The `idle` state was therefore correct **when written** and became stale eight days later.
That is ordinary staleness — but it is exactly the condition the guard exists to detect, and
`idle` makes the guard unable to report it.

### 9.3 Measured effect on lane 2

Lane 2's doc declares `declared_pr = 564` (verified by running `declared_pr` on the merged
tree). With #548's shipped state:

| lane 2 state | lane-2 DRIFT findings |
| --- | --- |
| `idle` + `[]` (as shipped by #548) | **0** |
| `current` + `[]` (same, one field changed) | **1** — `declares PR #564, which is not an open lane PR in the snapshot` |
| `current` + `[564]` (the state on `main`) | 0 |

The single field `doc_guard` is the difference between the guard reporting a stale lane
pointer and reporting nothing.

### 9.4 And `idle` is unnecessary — the refresh already produces the correct state

`scripts/lane_state_refresh.py` cannot emit `idle` (line 255: `lane["doc_guard"] = "deferred"
if lane.get("deferred_to_pr") else "current"`). Running it on the merged tree **overwrites**
the hand-written `idle` with a derived disposition:

```
before:  lane 2  doc_guard=idle      open_prs=[]
after:   lane 2  doc_guard=deferred  open_prs=[564]  deferred_to_pr=564
guard:   doc-guard lanes: ['1']; deferred: ['2','3','4']
         lane instruction docs consistent with snapshot (1 guarded lanes)
```

The canonical, derived state **needs no `idle` at all**. `idle` is a hand-maintained
exemption that the repository's own refresh mechanism would never produce and immediately
discards.

### 9.5 Recommendation, now evidence-based

§7 offered two options as a design preference. The measurements make the case concrete:

**Option B is the supported one — remove `idle` from this integration.** Reasons, in order of
weight:

1. **It is unnecessary.** The refresh derives `deferred`/`current` and produces a clean gate
   without it (§9.4).
2. **It is already suppressing a real finding**, on lane 2, through ordinary staleness (§9.3).
3. **It is unreachable by the canonical mechanism**, so it can only be introduced or removed
   by hand-editing the snapshot — an exemption with no derivation path (§9.4).
4. **Its escape path is unpinned.** #548's tests cover only positive cases; nothing asserts
   that an idle lane with a closed declared pointer still fails the gate (§7.3).

**Option A** (retain `idle`, preserve pointer enforcement) remains defensible, but it must
carry the negative test named in the acceptance criterion: *a lane may be excluded from
active-work enforcement without silently losing reference-integrity enforcement.* Under that
criterion, `idle` as shipped does **not** pass.

### 9.6 Acceptance criterion (recorded verbatim, as the governing condition)

> A lane may be excluded from active-work enforcement without silently losing
> reference-integrity enforcement.

Until an implementation and its tests demonstrate that property — or `idle` is removed from
this change — **#548 remains held**.

I have edited neither branch. This is a measured recommendation, not a decision.

---

## 10. Option A is implementable — measured, with a biting control

§9 recommended Option B (remove `idle`) on the grounds that it is unnecessary and already
suppressing a finding. That leaves Option A (retain `idle`, preserve pointer enforcement) as
a **claim** unless it is shown to be implementable. It is. This section records the proof so
the owner has both options measured rather than one measured and one asserted.

### 10.1 The repair is one scoping line

The escape exists because the blocking check is scoped to `current_lanes()`:

```python
owned = current_lanes(state)            # scripts/lane_state.py:830 — idle lanes excluded
```

Option A extends `owned` to include `idle` lanes, so an `idle` lane keeps its declared-pointer
check while remaining outside active-work judgement:

```python
owned = current_lanes(state) + [
    n for n in _lane_numbers(state)
    if state['lanes'][n].get('doc_guard') == 'idle'
]
```

### 10.2 Measured effect on the patched tree

| lane 3 state | lane-3 findings | classification |
| --- | --- | --- |
| `idle` + `[]` — **the escape path** | **1** | `DRIFT … declares PR #526, which is CLOSED without merging` |
| `current` + `[]` — control | 2 | DRIFT ×2 |
| `idle` + `[548]` | 3 | includes `DRIFT lane 3: doc_guard=idle but lane still lists open PRs` |

The escape is closed: `idle`+`[]` goes from **0** blocking findings (unpatched) to **1**.

### 10.3 The control bites — and only after it was fixed

The first version of the control asserted `'lane 3' in out and 'CLOSED without merging' in out`.
It **passed on the unpatched tree**, so it was not a control: the dead-pointer text appears in
a `NOTE` on the unpatched tree and a `DRIFT` on the patched tree, and a substring check cannot
distinguish them. This is the same "control that fires for the wrong reason" failure recorded
earlier in this workstream.

The corrected control asserts the **classification**, not a substring:

```
_classify(out) -> 'blocking' if the dead-pointer line starts with DRIFT
                  'advisory' if it starts with NOTE
```

Result:

| tree | control outcome |
| --- | --- |
| unpatched merged tree | **1 failed, 2 passed** — `an idle lane escaped reference integrity: its dead-pointer finding was 'advisory', not blocking` |
| patched (Option A) tree | **3 passed** |

Plus a self-contained control (`test_control_detects_the_advisory_form`) that feeds the
classifier both shapes, so the detector cannot be disarmed by editing the fixture.

### 10.4 Option A introduces no regression

`tests/test_lane_instruction_doc_currency.py` failing-node **sets**, compared by node identity:

| tree | failing nodes |
| --- | --- |
| unpatched merged tree (baseline) | 4 — `test_lane_one_shell_doc_does_not_name_a_merged_pr`, `test_live_guarded_docs_agree_with_the_snapshot`, `test_live_pointer_check_agrees_with_the_committed_docs`, `test_snapshot_exists_and_is_well_formed` |
| patched (Option A) tree | **identical 4** |

`diff` of the two sorted node sets is empty. The 4 baseline failures are pre-existing on the
merged tree and are not attributable to the patch.

*(One transient during measurement: an early patched run showed 5 failures because my own test
harness had left `lane-state.json` mutated between runs. Re-run on a restored snapshot: 4
failures, node-identical to baseline. Recorded because a leaked fixture is easy to misread as
a regression — which is exactly how it read for one run.)*

### 10.5 Both options, measured

| | Option A — retain `idle`, enforce pointers | Option B — remove `idle` |
| --- | --- | --- |
| Escape closed | **yes** (1 blocking DRIFT; control bites) | n/a — state removed |
| New failures | **none** (node-identical to baseline) | none (fewer states) |
| Cost | 1 scoping line + 1 regression test | remove the `idle` branch + its 2 tests; reconcile lane 2 to the derived state |
| Residual concern | keeps a state with no derivation path (hand-edit only) | none identified |
| Needs | the negative test above | lane 2 pointer correction (needed either way — #564 is open) |

**My recommendation remains Option B**, but now with the qualification that Option A is
*proven implementable at low cost* rather than merely defensible. If the owner wants `idle`
retained, §10.1–10.4 give the exact repair and the test that must accompany it.

**Neither option has been applied to any branch.** Both were built and measured in scratch
worktrees, which have been removed.

---

## 11. Option B is now measured too — and it is the cheaper of the two

§10 proved Option A. Option B was still a **preference**. This section closes that asymmetry,
so the owner is choosing between two measured designs rather than one measured and one argued.

### 11.1 What Option B actually is

Three edits, all bounded:

1. `scripts/lane_state.py` — remove `idle` from the disposition vocabulary:
   `{"current", "deferred", "idle"}` → `{"current", "deferred"}`, delete the `idle` branch,
   drop the `idle` sentence from `_disposition_findings`' docstring.
2. `docs/control-plane/parallel-ui/lane-state.json` — reconcile lane 2 to the state the
   repository's own refresh already derives: `deferred`, `deferred_to_pr = 564`,
   `open_prs = [564]`.
3. `tests/test_lane_instruction_doc_currency.py` — re-point the one vocabulary assertion
   (`must be 'current', 'deferred', or 'idle'` → `must be 'current' or 'deferred'`).

### 11.2 Option B closes the escape by making it unrepresentable

`idle` is no longer a legal disposition, so the §7/§9 escape **fails closed**:

```
DRIFT lane 3: doc_guard must be 'current' or 'deferred', got 'idle'
```

That is a stronger property than Option A's. Option A keeps the escape representable and
**blocks** it; Option B removes the representation, so the escape cannot be re-introduced by a
future snapshot edit without failing validation.

### 11.3 The live guard and lane 2

- **Live guard intact.** With `--verify-live`, a `current` lane 3 pointing at closed #526 still
  produces both findings (`declares PR #526, which is not an open lane PR` **and**
  `CLOSED without merging`), exit 1. `--verify-live` remains present in
  `.github/workflows/lane-doc-currency.yml`.
- **Lane 2 is repaired, not merely silenced.** It is now `deferred`, owned by **open #564** —
  the state `lane_state_refresh.py` derives. No `idle`, no suppressed finding.

### 11.4 No regression, by node identity

| tree | `test_lane_instruction_doc_currency.py` |
| --- | --- |
| unpatched merged tree (baseline) | **4 failed / 34 passed** |
| Option B (with the companion test edit) | **4 failed / 34 passed — node-identical** |

`diff` of the sorted failing-node sets is empty. The 4 are pre-existing on the merged tree.

Without the companion test edit there is exactly **one** new node —
`test_disposition_check_flags_an_unknown_disposition`, which pins the old vocabulary string
`"must be 'current', 'deferred', or 'idle'"`. That is the expected coupling, not a defect: the
test asserts the vocabulary Option B intentionally changes. `test_ci_gate_trigger_coverage.py`
is **93 passed** on the Option B tree.

### 11.5 The two options, both measured

| | Option A — retain `idle` | Option B — remove `idle` |
| --- | --- | --- |
| Escape closed | yes — **blocked** at the enforcement boundary | yes — **unrepresentable** (validation fails closed) |
| Escape re-introducible by snapshot edit | **yes** | **no** |
| New failures | none (node-identical) | none (node-identical, with companion test edit) |
| Files touched | 1 (`lane_state.py`) + 1 test | 1 (`lane_state.py`) + snapshot + 1 test |
| Lane 2 | still needs pointer repair | repaired to the derived state |
| Residual | keeps a state with no derivation path | none identified |

### 11.6 Recommendation

**Option B.** It is no longer merely preferable in principle — it is measured to be as safe as
Option A on regression, strictly stronger on the escape (unrepresentable rather than blocked),
and it removes a state whose only producer is a hand edit. Option A remains a proven fallback
with a known residual.

**Neither option has been applied to any branch.** Both were built and measured in scratch
worktrees, since removed; the working tree is clean and matches `HEAD`.

## 12. Harness faults recorded as part of the reproduction standard

Three faults were hit during §10–§11. All three are recorded because each can produce a
confident wrong answer, and the standard for a trustworthy reproduction should name them.

1. **A substring assertion cannot distinguish a blocking finding from an advisory note.** The
   same dead-pointer text is emitted as `NOTE` (advisory) or `DRIFT` (blocking) depending on
   the lane's disposition. A control asserting `'lane 3' in out and 'CLOSED without merging' in
   out` **passed on the unpatched tree** and proved nothing. Controls must assert the
   **classification** (line prefix), and should include a self-contained case feeding the
   classifier both forms.
2. **A leaked fixture can make a regression appear real — or conceal one.** An early patched
   run reported 5 failures against a baseline of 4; the extra failure was a `lane-state.json`
   left mutated by the previous run. The harness had also mutated the **real repository's**
   snapshot (caught by `git status`, restored with `git checkout --`). Restore mutated state in
   a `finally:` block, and verify `git status` is clean before comparing node sets.
3. **Running pytest from the wrong working directory tests the wrong tree.** The guard resolves
   its paths relative to the **current** directory, so `pytest /tmp/wtX/tests/...` invoked from
   the main repository resolved against the main repository and "passed" while testing the
   wrong tree. Always `cd` into the candidate worktree and pass a **relative** path.

**One environment note, for reproduction:** midway through this session the interpreter's
`site-packages` was reset and `pytest`/`pyyaml` disappeared (`python3 -m pytest` →
`No module named pytest`). They were reinstalled from the repository's own `requirements.txt`.
The baselines in §10 and §11 were therefore **re-measured in the restored environment**;
the §11 baseline (4 failed / 34 passed) reproduces the §10 baseline exactly, so the comparison
holds. Any future pass that cannot reproduce this should check the environment before
attributing a difference to the change.

---

## 13. Integration review — the three questions, and two corrections to this record

Read-only. `main` = `36f53be2`. No merge, revert, deployment, or repository mutation.

### 13.1 Live heads (queried this pass)

| PR | state | head | base | mergeable_state |
| --- | --- | --- | --- | --- |
| #548 | open, **draft** | `3da97fa5` | `04e1b83b` | `dirty` |
| #553 | open, **draft** | `899d2242` | `04e1b83b` | `dirty` |
| #565 | **merged** | `a671c4e4` | `68acf89f` | — |
| #566 | **merged** | `a9bc2c45` | `3a1088c5` | — |
| #567 | open, draft | `bebb6ed4` | **`36f53be2` (main)** | `clean` |
| #568 | open, draft | `a1679a3a` | **`bebb6ed4` (#567 head)** | `clean` |

Two structural facts, both material:

1. **#566 is merged** — its merge commit is `36f53be2`, which **is** `main` (compare → `identical`,
   `ahead_by 0`, `behind_by 0`). #566 is no longer a pending decision; it is part of the baseline.
   Its merge is recorded at `2026-10-25T07:46:12Z`.
2. **#568 is stacked on #567, not on `main`.** `#568.base.sha == #567.head.sha`. Reviewing #568 in
   isolation measures a diff against #567, not against `main`; the pair must be composed in order.

### 13.2 CORRECTION A — `idle` is not in `main`; #548 introduces it

Measured across revisions:

| revision | `lane_state.py` contains `"idle"` |
| --- | --- |
| `main` (`36f53be2`) | **no** |
| `#548` (`3da97fa5`) | **yes** (2 refs) |
| `#567` (`bebb6ed4`) | **no** |
| `#568` (`a1679a3a`) | **no** |

`main`'s vocabulary is already `must be 'current' or 'deferred'`. **`idle` exists only inside
#548.** This sharpens §7–§11 rather than overturning them: the finding is not "the repository has
a weakened state" but "#548 *adds* a weakened state to a tree that does not have one." That
makes Option B the smaller change in the integration sense — the merge simply does not take the
`idle` branch — and it means §11.2's "fails closed" property is already the property of `main`.

### 13.3 CORRECTION B — the 4 baseline failures were an artifact of the #548 merge, not of `main`

§10.4 and §11.4 measured a baseline of **4 failed / 34 passed** for
`tests/test_lane_instruction_doc_currency.py`. That measurement was taken on a worktree with
#548 merged in. Measured on **`main` itself**, and on the **#567→#568 composed tree**:

| tree | result |
| --- | --- |
| `main` (`36f53be2`) | **37 passed** |
| `#567` then `#568` composed | **37 passed** |

Both are **37 passed, zero failures**, with identical (empty) failing-node sets. The 4 failures
belong to the #548 tree alone. My §10–§11 comparisons were valid **for choosing between Option A
and Option B within #548's tree**, but the phrase "pre-existing on the merged tree" in §10.4/§11.4
is wrong: they are pre-existing **on #548**, not on `main`. Corrected here.

### 13.4 Question 1 — does the exact candidate contain the Option B edits?

**#568 already carries Option B's vocabulary removal.**

- `scripts/lane_state.py` in #568: `if disposition not in {"current", "deferred"}` — no `idle`
  branch; vocabulary message reads `must be 'current' or 'deferred'`.
- `tests/test_lane_instruction_doc_currency.py:537` in #568 asserts the same string.

So the `idle` removal is **not outstanding work on #568**. It is outstanding only as a
*rejection of #548's* `idle` branch, which the #567/#568 stack never takes.

One divergence to record, not a defect: #568's lane 2 is **`current` + `[564]`** — identical to
`main`. That is a third state, not the `deferred`+`[564]` I proposed in §11.1. It is **also
correct**: `declared_pr(lane 2) == 564` and #564 is open, so `current`+`[564]` is consistent and
produces no finding (verified: composed tree reports *lane instruction docs consistent with
snapshot (4 enforced lanes)*). My `deferred` edit was a valid alternative, not a requirement.
`lane_state_refresh.py` does derive `deferred` for lane 2, so the two states differ in *how* the
lane is described, not in whether the pointer is enforced.

### 13.5 Question 2 — does the composed tree preserve the measured behavior?

Composed `main` + `#567` + `#568` in a scratch worktree (`git merge --no-edit`, stack order):

- **Conflicts: 0.** Deletions by the merge: **none**.
- `idle` absent from the composed `lane_state.py` (0 refs).
- **`idle` fails closed** in the composed tree:
  `DRIFT lane 3: doc_guard must be 'current' or 'deferred', got 'idle'` (exit 1).
- **Live oracle preserved**: `--verify-live` reports *lane instruction docs consistent with
  snapshot (4 enforced lanes)*; the guard still detects a `current` lane 3 pointing at a closed
  PR (`DRIFT lane 3 … declares PR #548, which is not an open lane PR in the snapshot`).
- `test_lane_currency_ci_wiring.py` + `test_lane_guard_fixed_scope.py` +
  `test_lane_guard_stacked_pr.py`: **46 passed**.

### 13.6 Question 3 — heads, merge-bases, and checks across the set

- **#567 base = `main`** (`36f53be2`); **#568 base = #567 head**. Neither is in `main`
  (`git merge-base --is-ancestor #567 main` → **false**), so the stack is genuinely unmerged and
  its composition has never been exercised on `main`.
- **#548 and #553 share base `04e1b83b`**, which **is** an ancestor of `main` — both are stale
  against current `main` and both report `mergeable_state: dirty`. Their recorded bases are not
  the current main, so any "checks green" statement about them describes an older tree.
- **#553 remains independently blocked** — the CI-wiring defect is a true positive, and its
  repair surface (§6) is 19/16/28 missing inputs with the push/pull_request symmetry constraint.
  Composing #553 with the #567/#568 stack has **not** been measured and is not implied by
  anything above.
- **#567/#568 checks** were green at `a1679a3a` (7/7). That establishes the stack's own gate
  passes at its head; it does **not** establish release acceptance, and it does not cover the
  composition with #553.

### 13.7 What this changes

- **#548's `idle` is an addition, not a pre-existing condition** (§13.2) — so Option B for #548
  is "do not take the branch", and the escape never reaches `main`.
- **The #567→#568 stack already implements the Option B property** and composes cleanly (§13.4,
  §13.5). No Option B edit is outstanding there.
- **The baseline in §10/§11 was #548-tree-specific** (§13.3). `main` and the composed stack are
  both **37 passed**.
- **Lane 2 needs no change** in the #567/#568 candidate; my §11.1 `deferred` edit was an
  alternative, not a requirement (§13.4).

Read-only review only. Nothing merged, closed, reverted, retargeted, or deployed. Scratch
worktrees removed; working tree clean and equal to `HEAD`.

---

## 14. Amendments — three claims in this record are superseded

§13.2, §13.3 and §13.4 corrected the substance. The affected sentences earlier in this record
are annotated here rather than rewritten, so the sequence of what was believed and when stays
readable. Where a claim is superseded, this section is authoritative.

| § | claim as written | superseded by |
| --- | --- | --- |
| §9.1 | "`idle` is in use, on lane 2" | True **of #548's tree only**. `idle` is absent from `main` (`36f53be2`), `#567`, and `#568`; **#548 introduces it** (§13.2). The heading reads as though the repository had `idle`; it does not. |
| §9.5, §11.6 | "It is already suppressing a real finding", "removes a state whose only producer is a hand edit" | Correct **within #548's tree**. Since `main` has no `idle`, the finding is "#548 *adds* a weakened state to a tree that does not have one" — a branch-introduced regression, not a pre-existing repository condition. |
| §10.4, §11.4 | "The 4 are pre-existing on the merged tree" | **Wrong.** The 4 failures belong to the **#548 tree alone**. `main` (`36f53be2`) and the `#567`+`#568` composition are each **37 passed, zero failures** (§13.3). The Option A/B comparison remains valid *within* #548's tree; the attribution to `main` does not. |
| §11.1, §11.5 | "reconcile lane 2 to the derived state" | **Not required.** In the `#567`/`#568` candidate lane 2 is `current` + `[564]`, identical to `main`, and that is **also correct**: `declared_pr(lane 2) == 564` and #564 is open, so it is consistent and produces no finding (§13.4). The `deferred` edit was a valid alternative, not a requirement. |
| §11.5 | "Lane 2 — still needs pointer repair" | Superseded by the row above. Lane 2 needs no change in the `#567`/`#568` candidate. |
| §9.4, §11.2 | "the canonical derived state needs no `idle` at all" | Still correct, and now weaker than the fact that matters: `main`'s vocabulary is **already** `must be 'current' or 'deferred'`. No Option B patch is needed to obtain the fail-closed property; it is obtained by **not admitting #548's branch**. |

**What is not superseded.** The measurements themselves stand: `idle` downgrades a blocking
`DRIFT` to an advisory `NOTE` (§7); the escape is reachable by `idle` + cleared `open_prs`
(§7.3); Option A closes it at the enforcement boundary (§10); Option B makes it unrepresentable
(§11); and the three harness faults are real (§12). Only the *attribution* of `idle` to the
repository, and of the 4 failures to `main`, were wrong.

### 14.1 Corrected statement of the #548 finding

> **#548 introduces a disposition (`idle`) that `main` does not have, and that disposition
> converts a blocking dead-pointer finding into a non-blocking note for the lane that adopts it.
> The preferred disposition is therefore not to admit that change.** Preserving the fail-closed
> vocabulary requires no patch to `main`.

### 14.2 A credential disclosure I must report

While pushing after a `terminal reset` cleared the `gh` session, a `git push` failure message
printed the credential embedded in the `origin` URL:

```
fatal: could not read Password for 'https://<credential>@github.com/...': terminal prompts disabled
```

Facts, established by hash comparison (values never printed):

- The **exposed credential is the pre-existing one already embedded in `remote.origin.url`**
  (40 chars, prefix `ghu_`), **not** the `GITHUB_TOKEN` environment variable. The two are
  different values (`sha256[:16]` `a3dc4732…` vs `de53f291…`).
- It was exposed in **this session's command output**, which is retained in the conversation
  log — not in a repository file. `.git/config` was not written with a new credential, and no
  shell history file exists.
- The subsequent one-shot push (`git push https://${GITHUB_TOKEN}@…`) put the **env token** on a
  command line. That token is **masked by the platform** in tool output (`<secret-hidden>`), and
  it is a different value from the exposed one.

**Recommended action, for the human:** the credential embedded in `origin` (prefix `ghu_`) has
been displayed in a session log and should be treated as **disclosed** — rotate or revoke it, and
replace the embedded-credential remote with a credential-safe path (`gh auth login` plus the
`!gh auth git-credential` helper, or an SSH remote). I have **not** changed the remote, rotated
anything, or written any credential; that is an authorization decision.

A better operational note than the one in §13.7: prefer a credential helper over a URL-embedded
token, and prefer **not** to place a token on a command line at all — a `fatal:` message can echo
the URL back into the log, as happened here.

---

## 15. #553's open design question — measured, and the detector is over-broad

§13.6 recorded #553 as independently blocked with its repair design unresolved: expand the
workflow's selected inputs, or narrow the history-dependent guard? Measured this pass on #553's
own tree (`899d2242`, base `04e1b83b`). Read-only; scratch worktree removed.

### 15.1 The failing nodes

`tests/test_history_depth_ci_wiring.py` on #553's tree: **3 failed, 19 passed** — all three are
`test_a_workflow_selects_every_input_its_guard_reads[<workflow>]`, for
`economic-seam-engine.yml`, `provider-routing.yml`, and `sg-02-fe-2-v.yml`. In every case the
demanded guard is the same one:

```
sg-02-fe-2-v.yml judges tests/test_m02a_ci_gate_integrity.py, which reads
enterprises/eden-food-systems/tasks.seed.json, but does not select it in its
pull_request paths filter.
```

### 15.2 What the detector treats as an "input"

`_guard_inputs()` walks the guard's AST and takes **every string constant that names a tracked
path** (`ast.Constant`, value in `git ls-files`, not `tests/`). For
`tests/test_m02a_ci_gate_integrity.py` that is **55 paths**.

But the guard reads almost none of them. Measured: of the 55, exactly **1** appears in a
filesystem-reading call (`docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml`). The other
**54** are *string payloads* — changesets handed to `evaluate_changed_paths()` as data, e.g.:

```python
_EDEN_OPS_02_CHANGESET = [
    "enterprises/eden-food-systems/tasks.seed.json",   # a string, never opened
    ...
]
ok, msg = evaluate_changed_paths(_EDEN_OPS_02_CHANGESET)
```

The guard's verdict is a function of that **list of strings**, not of the files' contents.

### 15.3 Empirical confirmation — the three demanded paths are not inputs

Mutating each demanded file's **content** and re-running the guard:

| path | before | after content edit | verdict changes? |
| --- | --- | --- | --- |
| `enterprises/eden-food-systems/tasks.seed.json` | 68 passed | 68 passed | **no** |
| `musical-intention-engine/OPENHANDS-MVP-01.md` | 68 passed | 68 passed | **no** |
| `musical-intention-engine/06-EXPERIMENTS/EXP-001.md` | 68 passed | 68 passed | **no** |

All three are **false positives**. Editing the file changes nothing the guard asserts, so
demanding the workflow select it protects no property.

*A control flaw in my own first run, recorded:* I compared the full pytest summary line, which
includes a duration (`68 passed in 0.30s` vs `0.32s`), so two of the three read as "DIFFERS".
Comparing the **pass/fail counts** only gives the correct answer. Same class as the substring
fault in §12 — assert the invariant, not the surrounding text.

### 15.4 The design question, answered

**Option "expand" is not viable.** The detector demands, per workflow, **29** (economic-seam),
**52** (provider-routing), and **35** (sg-02) additional paths — 116 selections total — for files
whose contents the guard never reads. Adding them would widen three workflows' triggers
permanently to satisfy an over-broad detector, and would have to be repeated for every guard that
names a path as data.

**Option "narrow the guard" is the correct repair**, and the narrowing is precise: a path literal
is an *input* only if the guard **reads** it. The mechanical form is to resolve the literal to a
filesystem read (a `read_text`/`open`/`read_bytes` call, or a `Path(...)` expression that is then
read) rather than accepting any tracked-path constant. That reduces this guard's input set from
**55 to 1**, which is what the guard's verdict actually depends on.

The predicate must stay conservative in the safe direction: a guard whose read is indirect
(helper function, table-driven path) could be under-detected, so the narrowing needs its own
**negative control** — a guard that reads a path indirectly must still be reported — or it trades
a false positive for a false negative, which is the worse error for a coverage guard.

**This is a proposal, not a change.** `tests/test_history_depth_ci_wiring.py` is #553's own
artifact and part of its review surface; narrowing it alters what #553 asserts, so it belongs to
#553's decision and needs the same measurement-against-baseline discipline as everything else
here. Nothing was modified.

### 15.5 Composition with the #567/#568 stack remains unmeasured

Unchanged from §13.6. #553 touches 50 files including `weaver/autonomy/`, `weaver/engineering_*`,
and 12 test modules; the stack touches `scripts/lane_state*.py`, `scripts/lane_guard_domain.py`
and the lane tests. The two sets are disjoint, which is **textual** compatibility only. Composing
them creates a new candidate whose behavior is not established by any measurement in this record.

---

## 16. The #553 narrowing is NOT safely implementable — a measured reversal

§15.4 recommended "narrow the predicate: a path literal is an input only if the guard *reads*
it," and flagged that the narrowing must stay conservative or it trades a false positive for a
false negative. I built it and measured it. **The flag was correct and the recommendation is
withdrawn.** Measured on #553's tree (`899d2242`); read-only, scratch worktree removed.

### 16.1 The naive read-only predicate is a false-negative machine

A first cut — a literal counts only if it appears inside a `read_text`/`open`/`read_bytes` call
— takes `tests/test_m02a_ci_gate_integrity.py` from **55 inputs to 1**, which looked like the
intended outcome. Applied across the corpus it drops **268** literals over ~95 guards, **40 of
them to zero**.

Those zeros are not all spurious. `tests/test_ais_w2_living_gate_grove_handoff.py` binds nine
paths to names and reads them through a local helper:

```python
GATE = ROOT / "archive/.../LivingGate.tsx"
def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")
src = _r(GATE)
```

The literal never sits inside the read call, so the naive predicate reports **0** inputs.

### 16.2 Mutation proves that is a genuine input

Removing a literal the guard asserts from `LivingGate.tsx`:

| | result |
| --- | --- |
| before | **1 failed, 9 passed** |
| after removing `onEnterSpiralGrove?: () => void;` | **3 failed, 7 passed** |

`LivingGate.tsx` **is** a genuine content dependency. The naive predicate's `0` is a **false
negative**, not a cleanup.

### 16.3 A dataflow-aware predicate still fails

Adding name→reader propagation (bind `X = ROOT / "path"`, follow `X` into a reader call) keeps
151 of 316 literals, drops 165, and reduces **40 guards to zero**. It *still* misses
`LivingGate.tsx`, because the read goes through a **user-defined helper** (`_r`), not a
recognised reader name. Following that edge requires resolving arbitrary call chains — which is
the whole problem, not a detail.

| predicate | kept / 316 | guards → 0 | keeps `LivingGate.tsx`? |
| --- | --- | --- | --- |
| current (any tracked-path constant) | 316 | 0 | yes |
| naive read-only | 48 | 40 | **no — false negative** |
| dataflow + name propagation | 151 | 40 | **no — false negative** |

### 16.4 The corrected conclusion

**Both narrowing attempts introduce false negatives on a file that mutation testing proves is a
real input.** For a coverage guard this is the worse error: the guard would stop demanding a
workflow select a file whose edit changes what the guard asserts — silently, and in the direction
of less coverage. The false positive is loud (a red gate); the false negative is silent.

So the §15.4 recommendation is **withdrawn**. What survives from §15 is the *finding*, which is
independent of the repair: the three reported failures are false positives, and "expand the
inputs" would add 116 selections for files whose contents the guard never reads.

**What a sound repair would require, stated as a requirement rather than a design:** the
predicate must be *sound* (never omit a genuine input) before it may be *precise* (omit
non-inputs). Reaching soundness here needs whole-program reachability — resolving helper calls
like `_r` — or a different mechanism entirely, such as the guard **declaring its inputs
explicitly** and a test checking the declaration against observed reads. Neither is a one-line
change, and neither has been implemented or measured.

**#553's repair design is therefore open again, and now bounded by a measured negative result**
rather than by a preference. The proposal in §15.4 must not be implemented as written.

---

## 17. Credential remediation — status, sweep, and a blast-radius warning

### 17.1 What has been done

- **Embedded credential removed from the remote.** `git remote set-url origin
  https://github.com/Arkadia-Oversoul-Prism/Arkadia.git`. `origin` now contains **no** userinfo;
  `git config --get-regexp '^remote\.'` returns no credential-bearing line.
- **No leftover copies.** `grep -rl "ghu_" .git/` → **0 files**. `.git/config` carries no
  credential. No `~/.git-credentials` and no `~/.config/gh/hosts.yml` exist. A sweep of every
  `.git/config` in the sandbox found **no other credential-bearing remote**.
- **Fingerprint recorded for revocation** (value never printed): prefix `ghu_`, length 40,
  `sha256 a3dc473209386a767fcab1f68f5c31681dc91daa17b9ba9f7c813b3575a07a22`.
- **The plaintext is no longer on disk**, so liveness cannot be tested from here. Removal from
  the remote is a **mitigation**, not revocation, and is not evidence that revocation happened.

### 17.2 I cannot revoke it

`gh` is unauthenticated in this sandbox (`gh auth status` → not logged in), and
`/applications/grants` returns **404**. There is no revocation surface available to an agent
here. Revocation is a human action in GitHub Settings.

### 17.3 Blast radius — read this before revoking

The exposed credential and this environment's `GITHUB_TOKEN` are **both** `ghu_`-shaped GitHub
App user access tokens (40 chars, different values):

| | prefix | length | `sha256[:16]` |
| --- | --- | --- | --- |
| exposed (was in `origin`) | `ghu_` | 40 | `a3dc473209386a76` |
| environment `GITHUB_TOKEN` | `ghu_` | 40 | `7c38436be5f49fa7` |

The only installation visible to the environment token is **`openhands-ai` (id 156585514)** on
`Arkadia-Oversoul-Prism`, and the environment token is currently **valid** (`/user` → 200).

**Therefore:** if the exposed credential and the environment token were minted by the *same*
app authorization, revoking that authorization **wholesale will very likely revoke this
environment's own credentials too** — the agent platform would lose push and API access
mid-session. Two safer routes:

1. **Revoke the specific token** if GitHub offers a per-token revocation for that app
   authorization, leaving other tokens intact; or
2. **Accept the broader revocation deliberately** and re-authenticate afterward, expecting the
   environment's credentials to be invalidated and re-issued.

This is stated as a consequence to plan for, not as a reason to skip revocation. The exposure is
real and the token should be treated as disclosed.

### 17.4 Residual risk

The value appeared in this session's tool output, which is retained in the conversation record.
Mitigations applied: removed from the remote, confirmed absent from `.git/`, no credential
store written, no shell history file exists. **Residual:** the session transcript itself, and any
provider-side log of the tool call. Neither is reachable from here, and neither is cleared by
anything done in this pass.
