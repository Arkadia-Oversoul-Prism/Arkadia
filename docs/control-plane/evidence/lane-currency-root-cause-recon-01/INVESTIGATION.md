# Lane currency / lane-state — root-cause and scope investigation

**Class:** reconnaissance and design investigation. **No implementation, no merge authority.**
Nothing in this document changes repository behaviour.

- **Repository:** `Arkadia-Oversoul-Prism/Arkadia`
- **Base main:** `36f53be22d753ffe269f05cbf3fb39212f744207` (2026-10-25T08:46:11+01:00, PR #566)
- **Observed at:** 2026-10-26T01:30Z
- **Branch:** `gate-hygiene/lane-currency-root-cause-recon-01`
- **Guarded surface:** `tests/test_lane_instruction_doc_currency.py`,
  `docs/control-plane/parallel-ui/lane-state.json`, `scripts/lane_state.py`,
  `scripts/lane_state_refresh.py`, `.github/workflows/lane-doc-currency.yml`
- **Open PR cluster:** #567, #568, #569, #570, #571, #572 (all draft, all base `main`
  except #568 which is based on #567's branch)

---

## 1. Headline findings

| # | Finding | Classification |
|---|---|---|
| F1 | Main's lane-doc gate is **latently red**, not green. It last ran on `3a1088c5` where it passed; the `#508`-dead-pointer defect was introduced **downstream of that run**, and `main`'s HEAD touches no trigger path, so no run has observed it. | VERIFIED (by measurement) |
| F2 | A **fresh `lane_state_refresh` alone clears the gate to exit 0** on main's *unmodified* guard code. The refresh PRs are therefore data repairs, not guard repairs. | VERIFIED |
| F3 | Main's guard **enforces only lanes 1 and 2** (`doc_guard`-derived); lanes 3 and 4 are reported as non-blocking NOTEs. The gate can be green while a lane instruction points at a dead thread. | VERIFIED |
| F4 | PR #567's new scope guard `tests/test_lane_guard_scope_boundary.py` is **executed by nothing** on its own tree — no step, no `paths` filter, and not in the derived domain (module absent on its base). | VERIFIED |
| F5 | PR #568's green is **data plus semantics**: its own code on main's stale snapshot still exits 1 with 8 DRIFTs. It reaches exit 0 only with a fresh refresh. | VERIFIED |
| F6 | PR #568 **amends the lane docs it judges**, in the same commit that extends judgement to those lanes. The edits are reference corrections, but they are self-exempting in form. | VERIFIED (form); see §6 for the boundary argument |
| F7 | The lane-doc-currency gate **cannot fire on #567** — none of its four files is a trigger path. | VERIFIED |
| F8 | #568 is **stacked on #567's branch**, and #568 is itself the PR that adds a stacked-PR guard. Measured: it descends from #567 and contains `main`. | VERIFIED |
| F9 | The "shallow clone" failure mode is **not** main's current failure. Offline `--check` on pristine main exits **0** with a full clone. | VERIFIED |

---

## 2. F1 — the gate is latently red, and why "last run green" is not a pass

`main`'s HEAD `36f53be2` touches exactly one path:

```
docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md
```

That path matches **none** of `lane-doc-currency.yml`'s trigger paths. The newest
`Lane Doc Currency` run on record is at `3a1088c5` (2026-10-25T05:13:04Z,
conclusion `success`). `3a1088c5` is the parent of `36f53be2`:

```
3a1088c5  Lane-currency guard: isolate the repair onto current main (#565)
36f53be2  docs(evidence): correct the superseded §6/§7 figures ... (#566)
```

**The `#508` dead-pointer defect is downstream of the last run.** `#508` closed
unmerged at `2026-10-25T15:23:41Z` — roughly ten hours *after* the passing run.
`main`'s snapshot still records `#508` as open, so on main's own data the guard
would now report a dead lane PR.

I did not execute the live gate against pristine main's stale snapshot (that would
have written a GitHub-querying run into the record), so the exact drift list at
`36f53be2` is **UNKNOWN**. What is measured is: (a) the trigger-path analysis
above, (b) `#508` closed at 15:23:41Z, (c) `main`'s snapshot still lists `#508` as
open, and (d) the control in §5 where the same code on that same snapshot emits
`PR #508 (lane 4 open_prs) is recorded as open but is CLOSED without merging`.
Together those establish latently red. The classification of (d) as *main's*
state rather than a PR artifact is the one inferential step, and it is flagged
here rather than asserted.

**The general lesson is the one already recorded in AGENTS.md for a different
gate:** a path-filtered guard with no run at a revision has *no* execution there.
"Last run was green" is a statement about an older tree, not about `main`.

---

## 3. F2 — the repair is data, not code

This is the single most load-bearing measurement in the pass, because it
determines what the cluster of PRs actually is.

```
main code + freshly refreshed snapshot (observed_at 2026-10-26T01:32:01Z, base_main 36f53be2)
  -> 2 NOTEs, 0 DRIFTs, EXIT=0
```

The two remaining NOTEs are lanes 3 and 4 — reported, not blocking (see §4):

```
NOTE lane 3 (AGENT-03-SOLARIUN-KNOWLEDGE.md) declares PR #450, which is CLOSED without
     merging -- ... (lane not owned by this guard; reported, not blocking)
NOTE lane 4 (AGENT-04-ARKANA-WEAVER-LAB.md) declares PR #428, which is MERGED -- ...
     (lane not owned by this guard; reported, not blocking)
```

So on **unmodified main**, one refresh run takes the gate from red to green. No
guard-code change is required to clear the gate. The competing PRs are therefore
**not** alternative guard repairs; they are alternative snapshot refreshes with
different scope.

---

## 4. F3 — main's enforced set is lanes 1–2 only

Pristine main, offline:

```
base main: 68acf89f3045a01b0ba04038fabac4edfb5f937e (current: 36f53be2...)
doc-guard lanes: ['1', '2']; deferred: ['3', '4']
lane instruction docs consistent with snapshot (2 guarded lanes)
EXIT=0
```

The enforced set is derived from `doc_guard`, which `lane_state_refresh.py`
computes from **live open PRs**: a lane becomes `deferred` when some open PR
touches one of its owned code paths *and* its doc. Two consequences:

1. **A lane whose doc points at a dead thread can be invisible to the gate.**
   Lanes 3 and 4 are exactly that state on main — the two NOTEs above — and the
   guard exits 0.
2. **A PR can remove its own lane from judgement** by touching that lane's paths
   and doc. This is the scope inversion `#567`'s `lane_scope_probe.py` is built to
   detect, and #568 repairs by replacing the derivation with the literal
   `CANONICAL_LANES = ("1", "2", "3", "4")`.

This is the *same* defect class AGENTS.md records for `test_prism_console_ci_wiring.py`
and for the CP10 allowlist: **the activity under judgement decides the scope of
judgement.** Here it is sharpened — the scope is derived from GitHub PR traffic at
refresh time.

---

## 5. F5 — #568's green decomposes into data + semantics

The tempting reading is that #568 fixes the guard, so it should be green. I
tested that by holding the data fixed and varying only the code.

| Code | Snapshot | Result |
|---|---|---|
| main | main's stale snapshot (`68acf89f`, still lists `#508`) | EXIT 0 — `doc_guard` defers lanes 3–4, hiding the `#450`/`#428` pointers |
| main | fresh refresh | EXIT 0 — dead pointers gone |
| **#568** | **main's stale snapshot** | **EXIT 1, 8 DRIFTs** |
| #568 | #569's snapshot (`13:26:10Z`, still lists `#508`) | EXIT 1, 6 DRIFTs |
| #568 | own snapshot (`15:24:13Z`) | EXIT 0 |
| #568 | fresh refresh | EXIT 0 |

Row 3 is the decisive one: **#568's code, run against the data that is on `main`,
exits 1 with eight drifts.** Its green on its own head is not evidence that the
guard code alone repairs `main`. #568 reaches exit 0 because it carries a
corrected snapshot *and* amended lane docs (§6).

This matters for merge order. Merging #568 does not, by itself, guarantee a green
`main` — it depends on its snapshot still being accurate at merge time, which the
`#508`-closed-at-15:23:41Z chronology shows is a moving target.

---

## 6. F6 — #568 amends the docs it judges

#568's parallel-ui diff is exactly three files:

```
docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md
docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md
docs/control-plane/parallel-ui/lane-state.json
```

The two doc edits are appended "Status — 2026-10-25 (lane reference re-measurement)"
blocks that supersede the stale pointers, and each explicitly says so:

> Supersedes every earlier pointer in this document. Re-measured against live GitHub
> state, not carried forward: the `#450` pointer above is **closed without merging** ...

> This block also supplies the `**Active branch:**` pointer this document previously
> lacked, which the guard requires.

**Boundary argument, stated so it can be contested.** The edits are reference
corrections: they change no task, no ownership, and no scope, and the same
correction would be forced on anyone who turned the gate on. But the *form* is
self-exempting — #568 widens judgement to lanes 3–4 and simultaneously edits lanes
3–4's docs, and the stale pointers it fixes were non-blocking on main precisely
because lanes 3–4 were deferred. The correct sequencing is that **the doc
correction and the scope widening are separately reviewable**, so that a reviewer
can ask "would this lane be green if the doc were not touched?" — which, per §5
row 3, is measurably **no**. I recommend the human split or explicitly accept
this pairing rather than let it land as one green unit.

I have **not** adjudicated whether the amendments are correct; that is lane
ownership and belongs to the lane owners.

---

## 7. F4 / F7 — #567's guard is executed by nothing, and the gate cannot fire on #567

`#567`'s four files:

```
docs/control-plane/evidence/lane-currency-guard-authority-boundary-01/DESIGN-INVESTIGATION.md
docs/control-plane/evidence/lane-currency-guard-authority-boundary-01/INCIDENT.md
scripts/lane_scope_probe.py
tests/test_lane_guard_scope_boundary.py
```

**Not one is a trigger path of `lane-doc-currency.yml`.** Its `paths` filters name
`docs/control-plane/parallel-ui/**`, `scripts/lane_state.py`,
`scripts/lane_state_refresh.py`, and two test files — none of which #567 touches.
So the lane gate does not run on #567 at all.

Independently: `tests/test_lane_guard_scope_boundary.py` is the acceptance test
for the scope repair, and on #567's own tree it is named by **no** workflow step
and by **no** `paths` filter. It is not in the derived domain either, because
`scripts/lane_guard_domain.py` does not exist on #567's base. The file is
therefore a guard that nothing executes — the exact shape AGENTS.md records for
`test_boot_syntax_boundary.py` at `f9ced6b6` and for the console contract at
`17988afd`.

The fix shape already exists in the cluster: `lane_guard_domain.py` derives the
domain from `git ls-files` at call time, and the workflow runs
`python -m pytest -q $(python scripts/lane_guard_domain.py)`. But note that this
is the **content-derived domain** hazard recorded in AGENTS.md: a domain derived
from the repository grows silently, and a sibling branch adding a matching file
composes into a red `main`. `#567` and `#568` are exactly such a sibling pair —
which is F8.

---

## 8. F8 — #568 is stacked, and it is the PR that adds the stacked-PR guard

```
git merge-base --is-ancestor origin/gate-hygiene/lane-guard-authority-boundary-01 \
    origin/gate-hygiene/lane-guard-fixed-scope-01   ->  YES (568 descends from 567)
git merge-base --is-ancestor origin/main \
    origin/gate-hygiene/lane-guard-fixed-scope-01   ->  YES (568 contains main)
```

#568's base is #567's branch. Merging #568 through the ordinary green-check path
would land #567's commits with review covering only the child — and #568 ships
`tests/test_lane_guard_stacked_pr.py`, whose own docstring names this:

> lane repair PR #568 targets #567's branch, and #567's own body records that
> merging it "would itself require authorization" — so merging the child lands an
> unauthorized parent through the ordinary green-check path.

The guard is correct about the hazard and is itself an instance of it. This is not
a defect in #568; it is a **merge-order constraint** for the sovereign: #567 must
be resolved before #568, or the pair composed into one PR.

---

## 9. F9 — the shallow-clone story is not main's current failure

Pristine main offline `--check` exits **0** in a full clone:

```
base main: 68acf89f... (current: 36f53be2...); guarded paths: ... lane-state.json
doc-guard lanes: ['1', '2']; deferred: ['3', '4']
lane instruction docs consistent with snapshot (2 guarded lanes)
EXIT=0
```

So `clone_is_shallow` (#572's addition) addresses a *different* failure mode than
the one main is currently in. A truncated ancestry makes
`git merge-base --is-ancestor` unable to walk past the graft, so merged-ness reads
UNKNOWN and the guard exits 1 — a real hazard, and correctly classified as an
*unprovable* rather than a pass. But it is not what makes `main` latently red,
which is the `#508` data staleness of §2. Conflating the two would misattribute
the repair.

---

## 10. PR inventory and measured contributions

| PR | Head | Base | Files | Gate runs at head | What it contributes |
|---|---|---|---|---|---|
| #567 | `bebb6ed4` | `main` | 4 (+1044) | lane-doc-currency **absent** | scope probe + scope guard + incident/design docs |
| #568 | `686dd44a` | #567 branch | 20 (+2592 −101) | `lane-doc-currency` success | derived domain, `CANONICAL_LANES`, stacked-PR guard, snapshot + 2 doc amendments |
| #569 | `d75ba224` | `main` | 2 (+152 −12) | `lane-doc-currency` success (run `40164716935`, 2026-10-25T05:13:04Z) | snapshot refresh clearing the `#508` drift |
| #570 | `3d4e3aa7` | `main` | 2 (+311 −41) | — | snapshot refresh, wider |
| #571 | `fd1b1ca9` | `main` | — | — | snapshot refresh |
| #572 | — | `main` | — | — | `clone_is_shallow` |

**Claim check — #571's "strict subset".** I re-derived the claimed-PR sets from the
snapshots directly rather than accepting the PR body:

```
#569 claims: [499, 508, 525, 535, 547, 548, 549, 550, 553, 554, 555, 562, 564]  (13)
#568 claims: [499,      525, 535, 547, 548, 549, 550, 553, 554, 555, 562, 564]  (12)
#569-only: [508]        #568-only: []
568 ⊂ 569 (strict subset): True      569 ⊂ 568 (strict subset): False
```

The subset relation holds in the direction `#568 ⊂ #569`. Any PR body claiming the
reverse is **CONTRADICTED** by this measurement.

**Scope-shrink observation.** Main's `doc_guard` is
`{'1':'current','2':'current','3':'deferred','4':'deferred'}` with
`deferred_to_pr {'1':None,'2':None,'3':548,'4':555}`. After a refresh it becomes
`{'1':'current','2':'deferred','3':'deferred','4':'deferred'}` with
`deferred_to_pr {'1':None,'2':564,'3':548,'4':555}` — lane 2 moved from `current`
to `deferred`, i.e. **a refresh can shrink the enforced set from two lanes to
one.** A refresh is therefore not scope-neutral: it can reduce what the guard
examines while still reporting success.

---

## 11. Authority boundary

Nothing here is an implementation proposal, and nothing here is authorized by
discovery. The following are recorded as **PROPOSED, not executed**, each requiring
sovereign authorization:

- **P1** — Decide the merge order of #567 → #568 (or compose them), since #568 is
  stacked on #567 and ships the stacked-PR guard. Merge-order is sovereign.
- **P2** — Decide whether #568's doc amendments may land in the same PR that
  widens judgement to those docs (§6).
- **P3** — Choose among the competing refresh PRs (#569/#570/#571). Measured:
  a refresh alone clears the gate, so this is a data choice, not a guard choice.
- **P4** — Wire #567's `test_lane_guard_scope_boundary.py` into an executing gate
  (or into the derived domain). It currently runs nowhere.
- **P5** — Consider whether a refresh should be allowed to shrink the enforced set
  (§10). This is a guard-semantics change and touches the scope of judgement.

**No production, deployment, or acceptance claim is made.** No runtime observation
was performed; all measurements are local repository and read-only GitHub API
evidence. The live gate was deliberately not executed against pristine main (§2).

---

## 12. Method and reproducibility

Every number above is reproducible from a full clone at `36f53be2` with a
read-only GitHub token:

```bash
# F2 / F9 — offline and refreshed, on unmodified main
git worktree add --detach /tmp/wtmain 36f53be2
cd /tmp/wtmain && python3 scripts/lane_state.py --check          # -> EXIT 0
GH_TOKEN=... python3 scripts/lane_state_refresh.py --write
GH_TOKEN=... python3 scripts/lane_state.py --check --verify-live # -> EXIT 0

# F5 — hold data fixed, vary code
cp scripts/lane_state.py  /tmp/wtmain/scripts/lane_state.py   # #568 code, stale data
GH_TOKEN=... python3 scripts/lane_state.py --check --verify-live # -> EXIT 1, 8 DRIFTs

# F7 — does the gate fire on #567?
gh api repos/.../pulls/567/files --jq '.[].filename'   # none is a trigger path

# F8 — stacking
git merge-base --is-ancestor origin/gate-hygiene/lane-guard-authority-boundary-01 \
    origin/gate-hygiene/lane-guard-fixed-scope-01
```

CP10 boundary check for this document's own paths:

```
printf 'docs/control-plane/evidence/lane-currency-root-cause-recon-01/INVESTIGATION.md\n' \
  | python3 scripts/cp10_mutation_boundary_policy.py --judge   # -> PASS, exit 0
```

**Evidence states used:** VERIFIED (directly measured), CONTRADICTED (measurement
conflicts with a claim), UNKNOWN (not measured, and named as such), PROPOSED
(recorded, not executed). No finding here is promoted to VERIFIED by repetition.

---

## 13. Verification of this change

This document is the entire change. No code, test, workflow, snapshot, or lane
instruction was modified — the working tree carries one new untracked directory.

```
python3 -m pytest tests/test_lane_instruction_doc_currency.py \
                  tests/test_lane_currency_ci_wiring.py -q -rEf   -> 49 passed in 0.32s
python3 -m pytest tests/architecture -q                            -> 11 passed in 1.60s
printf '<this file>\n' | python3 scripts/cp10_mutation_boundary_policy.py --judge
                                                                   -> PASS, exit 0
git status --porcelain                                             -> docs-only
```

**Regression boundary.** The 49 targeted lane tests and 11 architecture tests are
the guard's own suite, executed on the *unmodified* code they judge. Because the
change is additive documentation under a new evidence directory, no existing test
node can change state. No full-suite pass was run: per the contract a second
full-suite run is not affordable in one pulse, and a docs-only addition is
attributable by construction rather than by a suite delta.

**Authorization boundary.** Reconnaissance only. Nothing here is proposed as
executed work; §11 lists the five items that require sovereign authorization, and
none was performed. No merge, no deploy, no acceptance claim.

