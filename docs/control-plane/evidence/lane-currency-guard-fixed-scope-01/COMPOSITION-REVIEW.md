# Composition review before the release decision — bounded final review

**Scope:** the release decision for `gate-hygiene/lane-guard-fixed-scope-01` (PR #568).
**Method:** read-only composition on detached worktrees. Nothing merged, reverted,
retargeted, or deployed. Every claim below is a measurement taken this pass.

**Head examined:** `bd1cd592ccf4a290360bab17a961a534779be9a1` — *not* `76f6d87a`. See §1.

---

## 1. Drift: the branch head moved after my repair, and the gate is now RED

Three commits were pushed onto this branch by a later pulse, on top of my `76f6d87a`:

| Commit | Subject | Author |
| --- | --- | --- |
| `4edb5afa` | Lane gate: derive the executed guard inventory from the corpus, not a fixed list | openhands |
| `1af22160` | evidence: record the CI runtime proof for the derived lane-guard invocation | openhands |
| `bd1cd592` | lane guard: report a stacked PR, the half of merge-safety ancestry cannot see | openhands |

**PR #568's current head is `bd1cd592`, and its `lane-doc-currency` check is
`failure`** (run `40189191536`, job `121156336482`). My earlier report described
`76f6d87a`, where all 12 checks passed. That statement is superseded: it is true of a
revision that is no longer the head.

The failure is **not** a crash. It is the guard doing its job:

```
DRIFT PR #508 (lane 4 open_prs) targets base branch 'feat/engineering-acceptance-authority',
not 'main'; it is STACKED, so merging it would land its base branch's commits unreviewed
##[error]Process completed with exit code 1.
```

### 1.1 That finding is a true positive — verified

| Check | Result |
| --- | --- |
| `#508` base ref | `feat/engineering-acceptance-authority` (`ef82cb9e2d05`) |
| is that base an ancestor of `main`? | **No** |
| commits in the base that are **not** in `main` | **17** |
| commits in `main` that are not in the base | 41 |

So merging #508 as it stands would land 17 unreviewed commits. The finding is correct,
and it is exactly the hazard the new check was written to surface.

## 2. The later commits found a real gap in my repair — confirmed

The commit message for `4edb5afa` claims: *at `76f6d87a` the derived domain is 4 guards
while the gate executed 3 and filtered 3, so `tests/test_lane_guard_scope_boundary.py` —
the acceptance test for the scope repair — was executed by no workflow.*

Independently verified:

```
$ git show 76f6d87a:.github/workflows/lane-doc-currency.yml | grep pytest
run: python -m pytest -q tests/test_lane_instruction_doc_currency.py
run: python -m pytest -q tests/test_lane_currency_ci_wiring.py
run: python -m pytest -q tests/test_lane_guard_fixed_scope.py
$ git cat-file -e 76f6d87a:tests/test_lane_guard_scope_boundary.py   # exists
```

**True.** #567 added the scope-boundary acceptance test, and my repair never wired it into
any workflow — the same selection-versus-execution defect I had just fixed for my own new
guard, committed one layer out. The later pass replaced the fixed list with
`scripts/lane_guard_domain.py`, derived from the corpus, now executed as
`pytest -q $(python scripts/lane_guard_domain.py)`. Current domain: **5** guards, all
executed and all filtered.

This is a defect **in my repair**, and it is recorded as such rather than absorbed.

## 3. The #548 / #555 pointer traps — measured, and one is worse than reported

I previously flagged these from source inspection. Composition makes it concrete.

`declared_pr()` takes `matches[-1]` — **the last pointer in the document wins.** An
appended status block therefore *overrides* everything above it. Both PRs append.

### 3.1 #548 — confirmed trap, and a merge conflict

| Check | Result |
| --- | --- |
| last pointer in `AGENT-03` after composition | **`#526`** |
| `#526` live state | **closed, not merged** |
| merge into the repair branch | **CONFLICT** — `AGENT-03-SOLARIUN-KNOWLEDGE.md` **and** `lane-state.json` |
| gate on the composed tree (doc conflict resolved, snapshot re-measured) | **exit 1** |

The composed tree is red with a correct finding:

```
DRIFT lane 3 (AGENT-03-SOLARIUN-KNOWLEDGE.md) declares PR #526, which is CLOSED without
merging -- the lane instruction points a successor agent at a dead thread
```

**So: #548 must not be merged after the repair without re-pointing lane 3.** It conflicts
textually *and* semantically. A merge that resolved the conflict by taking "both sides"
still resolves `declared_pr` to `#526`, because #548's block is last.

### 3.2 #555 — the trap does NOT fire, but only by ordering luck

| Check | Result |
| --- | --- |
| merge into the repair branch | auto-merges the doc; conflicts only on `lane-state.json` |
| last pointer in `AGENT-04` after composition | `#553` — a **live** draft |
| `#536` | present at line 3 as prose ("Supersedes PR #428 … and `#536`, which is closed") |
| gate on the composed tree | **exit 1**, but for `#508`, **not** for a dead pointer |

My repair's appended block sits *below* #555's line-3 edit, so it wins. That is correct
**today** and fragile by construction: it depends on block order, and `declared_pr`'s
last-match rule is not obvious to whoever appends the next block. Recorded as a hazard,
not as a defect in #555.

## 4. The stacked dependency between #567 and #568 — real, and now load-bearing

#568 was branched from #567 and depends on it in two distinct ways:

1. **Content.** `tests/test_lane_guard_fixed_scope.py` loads `scripts/lane_scope_probe.py`,
   which #567 adds. Applied onto `main` without #567:
   `2 failed, 12 passed` — `FileNotFoundError: scripts/lane_scope_probe.py`.
2. **Ordering.** #568 is currently based on #567's branch, so #567 must merge first (or
   the two must merge together). This is visible in the PR metadata: #568's base is
   `gate-hygiene/lane-guard-authority-boundary-01`.

**Merge order is therefore not a preference: `#567` → `#568`.** Merging #568 alone is not
a coherent state, and the incident record in #567 must not be rewritten by the repair —
your point 2, and the repository agrees: #567 carries `INCIDENT.md` and
`DESIGN-INVESTIGATION.md`, #568 carries the control repair and its evidence. Distinct
paths, distinct purposes, no overlap.

## 5. `main` is still red, and for a different reason

Measured on `origin/main` `36f53be2` (unmodified):

```
doc-guard lanes: ['1', '2']; deferred: ['3', '4']
DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging
MAIN EXIT=1
```

`main` remains red, judging **2** lanes. This is the pre-repair state and it is expected:
the repair is not merged. It also confirms the repair is doing real work — post-repair the
same invocation judges **4** lanes and passes.

## 6. Findings that bear on the release decision

| # | Finding | Severity | Status |
| --- | --- | --- | --- |
| 1 | #568's head `bd1cd592` has a **failing** `lane-doc-currency` check | blocking | true positive; needs a lane-4 disposition for #508, or #508 retargeted |
| 2 | `#548` re-introduces a dead pointer (`#526`) and **conflicts** | blocking for #548, not for #568 | measured |
| 3 | `#555`'s trap does not fire, by block ordering only | hazard | recorded |
| 4 | #568 depends on #567 (content + base) | ordering constraint | measured |
| 5 | The later commits repaired a real gap **in my repair** | quality | confirmed, recorded |
| 6 | `main` `36f53be2` is red, judging 2 lanes | expected | unchanged |

## 7. Recommendation

**Hold the merge of #568**, as you proposed — and note that the blocker is now different
from the one we discussed. It is not only the #548/#555 traps; the branch head itself
carries a red gate on a *correct* new finding about #508.

The bounded path I would take, in order:

1. **Disposition #508's base.** It is stacked on a branch carrying 17 commits not in
   `main`. Either retarget it to `main` (its owner's call) or explicitly authorize the
   whole stack. Until then the new check reports it, correctly, on every run.
2. **Merge `#567` first**, then `#568`. Order is load-bearing (§4).
3. **Re-point lane 3 before #548 merges** (§3.1), or accept that #548 lands red.
4. **Do not merge #568 to make a gate green.** It currently does the opposite: it makes
   visible two hazards that were invisible. That is the property worth protecting, and it
   is the reason I am not proposing to suppress the #508 finding to get a green check.

Nothing here is authorized by this review. It is a measurement, and the release decision
remains yours.
