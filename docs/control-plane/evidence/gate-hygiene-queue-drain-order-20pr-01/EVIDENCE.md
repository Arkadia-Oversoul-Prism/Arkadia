# gate-hygiene — open-PR queue (20) : drain order, conflict root cause, measured delta

Pass: `gate-hygiene/queue-drain-order-20pr-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of PR #141)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence pass. **No source, test, or governance change.**

Supersedes the *scope* (not the method) of PR #158
(`gate-hygiene/open-pr-queue-merge-order-map-01`), which measured **16** PRs (#142–#157).
The live queue is **20** PRs (#142–#161). #143 and #147 were not in #158's map, and #143 is
the one PR in the queue that must not merge.

---

## 1. Why this pass exists

#158 answered the three pre-merge questions for the queue as it stood. The queue has since
grown by four PRs (#158, #159, #160, #161 — including #158 itself) and #143/#147 are now
visible. Two consequences:

1. The drain order in #158 predates the four newest PRs.
2. **#143 was omitted from #158's "clean at every step" sequence.** This pass measures that
   sequence *with* #143 and finds it conflicts — and identifies #143 as the sole cause.

## 2. Method

- **M0 — unshallow.** Mandatory (per #158 §2). Clone must be unshallowed or
  `git diff origin/main...prNN` silently returns empty file lists.
- **M1 — live queue.** `gh pr list --state open` with a working token. A read-only or absent
  token makes this step `BLOCKED`; it does not make the queue 16.
- **M2 — real composability.** `git merge --no-ff` each PR head, in order, onto a worktree cut
  from `origin/main`. Abort only on conflict. Three-way merge against accumulated result.
- **M3 — delta by node set, not count.** Compare `FAILED`/`ERROR` node sets between a clean
  `main` baseline and the composed tree. A count can hide churn; a set difference cannot.

Reproduction:

```bash
git worktree add -f --detach /tmp/wt_drain origin/main
cd /tmp/wt_drain
for n in 157 156 155 151 152 153 154 142 144 145 146 148 149 150 158 159 160 161; do
  git merge --no-ff --no-edit -m "compose PR #$n" origin/pr/$n
done
```

## 3. Conflict root cause — #143, and only #143

| sequence | result |
|---|---|
| **all 20 PRs** (157…161, incl. #143 and #147) | **CONFLICT: `AGENTS.md` at #150** (then cascades) |
| **18 PRs** — the drain set below, **excluding #143 and #147** | **clean at every step** |

`#143 + #150` conflicts. `#147 + #150` conflicts. `#143 + #147` is **clean** — which is why
#158, whose sequence carried #147, did not surface the conflict: #147 is *stacked on* #143's
branch (`base = gate-hygiene/gate2-production-parity-02`), so #143's `AGENTS.md` bytes reach
the tree through #147. Excluding #147 excludes #143's version transitively.

All three PRs rewrite the **same** region: the EOF "Gate 2 production parity" section that
#147 appends and #150/#143 both rewrite.

## 4. Independent reproduction of the encoding oracle

#155 and #151 both adjudicate the `AGENTS.md` encoding question. This pass re-ran **#151's own
instrument** (`scripts/agents_md_encoding_audit.py`) against each candidate's bytes, so the
verdict is reproduced from the artifact rather than cited.

| candidate | bytes | lines | corrupted | Cyrillic | Latin-1 cruft | verdict |
|---|---|---|---|---|---|---|
| `main` (`002b189`) | 27301 | 382 | **50** | 182 → 0 | 0 → 2 | corrupted — **recoverable** |
| **#150** | 29528 | 411 | 0 | 0 | 3 | **CORRECT** |
| #143 | 35811 | 481 | 0 | 0 | **594** | **WRONG — double-encoded** |
| #147 | 36650 | 498 | **50** | 188 → 6 | 4 → 6 | **SUPERSEDED — restores corruption** |

Byte counts match #155's table exactly. The decisive signals:

- **#143 is not a repair.** It removes the 50 Cyrillic-corrupted lines but replaces them with
  **594** Latin-1/Ext cruft codepoints — text has been *re-encoded*, not recovered. Its
  rendered output is visibly wrong: `# Arkadia тАФ Agent Memory` becomes
  `# Arkadia čéąÉąż Agent Memory`, and the `→` arrows become `čéą¢ąó`. #155 classifies this as
  double-encoded; the cruft count is the mechanical form of that.
- **#147 re-introduces the corruption it claims to remove.** `git diff origin/main...pr147 --
  AGENTS.md` is `+116/-0` — it adds 116 lines and deletes **no** corrupted byte. Its recovered
  Cyrillic count only falls 188 → 6 because the appended (clean, authored) section dilutes the
  ratio, not because anything was repaired.
- **#150 is the repair.** `+79/-50` — it removes the corrupted region and its rendered output
  is correct (`—`, `→`, `·`).

**Independent verdict: merge #150; do not merge #143; close #147 as superseded.**
Corroborates #151 and #155 by reproduction, not by citation.

## 5. Recommended drain order

**Merge order is free** for the 18-PR drain set — every pairwise overlap is non-conflicting,
and the set merges cleanly in the order below. The order is chosen for review convenience
(evidence-only PRs first, behavioural PRs last), not because the tree requires it.

```
157  156  155  151  152  153  154  142  144  145  146  148  149  150  158  159  160  161
```

| cluster | PRs | note |
|---|---|---|
| `AGENTS.md` encoding | **#150** | merge this one; **exclude #143, #147** |
| `api/main.py` | #153, #154 | disjoint hunks ~450 lines apart — no conflict, order free |
| frontend | #160 | `vite.config.js` shadow removal + `manualChunks` |
| evidence-only | #142, #145, #155, #158, #159, #161 | docs only |

**#143 must not merge with its current `AGENTS.md`.** If #143's substantive work (the Gate 2
production-parity observation harness: `scripts/gate2_*.py` + 2 tests) is wanted, it must be
re-cut on a branch whose `AGENTS.md` is #150's bytes, or rebased after #150 lands.

## 6. Measured delta — zero regression

Clean `main` baseline and the composed drain tree, both run with
`pytest tests/ -q --continue-on-collection-errors`, comparing **node sets** (M3):

| tree | failed | passed | skipped | errors | failing nodes |
|---|---|---|---|---|---|
| clean `main` `002b189` | 20 | 1039 | 13 | 2 | 22 |
| drain set (18 PRs) + #159 repair | 18 | 1091 | 15 | 1 | 19 |

**Fixed by the queue (in baseline, absent from drain):**

```
ERROR tests/test_render_codex.py                                        (PR #149)
FAILED tests/test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move  (PR #148)
FAILED tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence               (PR #148)
```

**Introduced by the queue: NONE.** The set difference is empty — the queue is
regression-free by node identity, not merely by count.

`ERROR tests/test_autonomy.py` is present in both trees and is unchanged pre-existing baseline
debt (`load_autonomy_config`).

## 7. The #159 repair is load-bearing — land it with #154 + #156

#159 ships the repair as a patch file rather than applying it. Measured:

| tree | `tests/test_documented_route_contract.py` |
|---|---|
| drain set, unpatched | **1 failed / 8 passed** |
| drain set + `health-row-doc-repair.patch` | **9 passed** |

The repair touches `DEPLOYMENT_GUIDE.md` (`+5/-4`) — the documented health-route row. It is
**not** a #159-only change: #156 authors the contract test and #154 changes the route, so the
repair's precondition is #154 + #156 jointly on the tree. #159's PR body should say so, and
the patch must be **applied** (not merely attached) before or during #159's merge, or the
drain set lands 1 node red.

## 8. Architecture fitness

```
python -m pytest tests/architecture -q   ->  11 passed
```

Green on the composed drain tree. No new architectural debt; no `LAYER_MAP` change.

## 9. What this pass does not do

- It does **not** apply the #159 repair to `main` or to any PR branch.
- It does **not** merge, push to `main`, or force-push.
- It does **not** edit `AGENTS.md`, any test, any source file, or any governance surface.
- It does **not** re-adjudicate the #143/#147/#150 question beyond reproducing the oracle.
- It does **not** endorse the wording of #150's appended EOF section — that is a presentational
  call for the sovereign, as #151 and #155 both state.

## 10. Classification

`IMPLEMENTED` — evidence exists and is reproducible; the drain order is measured; the
regression delta is zero by node identity. Merge remains human-only.

**Sovereign actions requested:** merge **#150**; exclude **#143** and **#147**; apply #159's
patch when #154 + #156 land; drain the remaining 18 in any order.
