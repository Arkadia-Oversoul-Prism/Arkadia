# Lane-state drift: reconnaissance and root-cause audit

**Workstream:** audit / lane-state-drift-audit-01
**Branch:** `audit/lane-state-drift-01`
**Base main:** `36f53be22d753ffe269f05cbf3fb39212f744207`
**Observed:** 2026-10-27
**Type:** read-only audit. **No source change is proposed by this document.**
**Status:** IMPLEMENTED (measurement complete). Production acceptance NOT CLAIMED.

This record exists because the parallel-UI lane workstream's *hand-transcribed* state
drifted, and because the corrected narrative the repair shipped with carries a figure
that does not reproduce. It measures both, and it separates the drift from the
transcription error about the drift.

---

## 1. Objective and method

**Objective.** Measure (a) the extent of the lane-state drift that motivated the
`lane-currency-truth-01` repair, and (b) its root cause, including why the repair's own
description of the drift is not reproducible.

**Method.** Live reads only: the GitHub REST pulls API (read-only `GET`), local `git`
ancestry, and the repository's own guard (`scripts/lane_state.py --check --verify-live`).
No writes to any lane doc, snapshot, guard, workflow, or test. No merge, no deploy.

**Revisions under examination.** Each is named because evidence binds to a revision:

| Role | Revision | Note |
|---|---|---|
| Current main | `36f53be2` | audit base |
| Snapshot live on 2026-10-24 | `341867eb` (2026-10-15) | `base_main` `7580bd8f`, `observed_at` 2026-10-15T02:20:00Z |
| Snapshot shipped by the repair | `3a1088c5` (2026-10-25) | `base_main` `68acf89f`, `observed_at` 2026-10-25T04:48:21Z |

The snapshot that was live on 2026-10-24 is the one at `341867eb`: it entered `main` in
the #540 merge and was replaced by `3a1088c5` on 2026-10-25. `git log --
docs/control-plane/parallel-ui/lane-state.json` on `main` returns exactly these two
commits, so there is no third revision to consider.

---

## 2. F1 — the drift is real, and larger than recorded

The snapshot at `341867eb` listed ten PRs under `open_prs`:

```
#492, #507, #526, #527, #528, #529, #534, #536, #537, #538
```

Measured live, one field at a time:

| PR | `merged` | `merged_at` | `closed_at` |
|---|---|---|---|
| #492 | **True** | 2026-10-15T17:05:11Z | 2026-10-15T17:05:11Z |
| #507 | False | — | 2026-10-15T20:42:44Z |
| #526 | False | — | 2026-10-15T20:41:55Z |
| #527 | False | — | 2026-10-15T20:42:57Z |
| #528 | False | — | 2026-10-15T20:31:00Z |
| #529 | False | — | 2026-10-15T20:42:51Z |
| #534 | False | — | 2026-10-15T20:43:03Z |
| #536 | False | — | 2026-10-15T20:43:08Z |
| #537 | False | — | 2026-10-15T20:42:01Z |
| #538 | False | — | 2026-10-15T20:04:08Z |

**Result: 1 merged / 9 closed-without-merging / 0 still open.**

`merged_at` is immutable once set and none of the nine carries one, so this reading is
also the state at 2026-10-24 — the drift was already complete on the day it was
described. Independent ancestry corroboration: `7030ccb2` (#492's merge commit) is an
ancestor of `main`; the other nine are not, and 8 of the 9 have a `merge_commit_sha`
GitHub reports as non-ancestral while `merged == false` (the two with a null
`merge_commit_sha`, #534 and #538, are the same case with no commit to test).

---

## 3. F2 — the recorded figure is "three", and it is not derivable from any measurement

Four tracked sites state that three of the ten never merged. All four were introduced by
the **same commit**, `3a1088c5` (PR #565) — none predates it:

| Site | Text |
|---|---|
| `scripts/lane_state.py:49` | "all ten PRs the snapshot listed under ``open_prs`` were closed, and three of those ten had never merged" |
| `scripts/lane_state.py:295` | "ten PRs recorded under ``open_prs`` were closed -- three of them never merged" |
| `.github/workflows/lane-doc-currency.yml:63` | "all ten PRs the snapshot recorded as open had closed, three of them unmerged" |
| `docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md:63` | "all ten PRs the committed snapshot listed under `open_prs` had closed (three unmerged)" |

Candidate readings tested against the live API, all rejected:

| Reading | Value | Matches "three"? |
|---|---|---|
| `merged == true` | 1 | no |
| `merge_commit_sha == null` | 2 | no |
| `merge_commit_sha` is an ancestor of `main` | 1 | no |
| closed-without-merging | **9** | no |
| `head.sha` is an ancestor of `main` | 0 | no |

The count is **non-reproducible from the live repository**. It is not a differently-worded
true statement: nine of the ten are closed-unmerged, so "three" understates the drift
threefold and, by implying seven merged cleanly, mis-describes the cohort's disposition.

One plausible origin was found and is recorded as a **hypothesis, not a finding**: at
`341867eb` exactly **three** lanes carried a `deferred_to_pr` (lane 2 → #492, lane 3 →
#526, lane 4 → #536). Three deferred lanes is a quantity that exists; "three unmerged
PRs" is not. Conflating them is the kind of substitution a hand-transcribed sentence
makes. It is not proven.

---

## 4. F3 — the machine-readable artifact already carried the correct number, unenforced

The repaired snapshot (`3a1088c5`, schema `arkadia.lane-state/1.2`) records:

```
closed_unmerged: [507, 526, 527, 528, 529, 534, 536, 537, 538]      # nine entries
```

That is exactly the measured set. So the *measurement* path was correct and the *prose*
was wrong — the error is a transcription defect, not an oracle defect.

Two enforcement gaps let it stand:

1. `grep -n "closed_unmerged" scripts/lane_state.py` → **0 matches**. The guard never
   reads the field. `tests/test_lane_instruction_doc_currency.py:245` requires the field
   to *exist*, but nothing cross-checks it against `open_prs` or against prose.
2. `grep -n "unassigned_open_prs" scripts/lane_state.py` → **0 matches**. The snapshot
   records six unassigned open PRs; the guard ignores the field entirely.

Nothing in the repository relates the prose figure to the artifact, so a prose figure can
be wrong indefinitely while every test stays green — which is what happened.

**A sharper consequence.** On the shipped snapshot the two sets do not intersect at all:

```
claimed-open (open_prs ∪ deferred_to_pr) = [499, 508, 525, 535, 547, 548, 549, 550,
                                            553, 554, 555, 562, 563, 564]
merged_prs                               = [420, 421, 422, 423, 425, 426, 427, 428,
                                            429, 430, 431, 492]
intersection                             = []
```

`_liveness_findings` iterates claimed-open PRs and looks each up in `merged_prs`; with an
empty intersection it has **nothing to test**, so the local-ancestry oracle returns `[]`
for the shipped snapshot — not because the snapshot is sound, but because the two lists
were curated apart. The guard's own docstring calls this the check "a stale snapshot
cannot defeat". Measured, on this snapshot, it is vacuous.

---

## 5. F4 — the snapshot was born stale, before it was consumed

`341867eb` landed on `main` at 2026-10-15T18:15:21+01:00 (**17:15:21Z**). Its
`observed_at` is 2026-10-15T02:20:00Z, and **#492 merged at 17:05:11Z** — ten minutes
before the snapshot landed, and the snapshot still listed #492 under `open_prs`.

So at least one entry was already wrong at the moment of commit. The remaining nine
closed ~3 hours later (20:04Z–20:43Z). The snapshot was therefore not merely
"eventually stale": it was **drift-at-commit** for #492 and stale-within-hours for the
rest. The push run of the gate at that revision (`341867eb`, 2026-10-15T17:15:25Z) is
`failure`, consistent with this.

---

## 6. F5 — root cause: the gate is filtered to the drift's *symptom*, not its *cause*

`.github/workflows/lane-doc-currency.yml` triggers on `pull_request` and `push` to
`main`, path-filtered to:

```
docs/control-plane/parallel-ui/**
scripts/lane_state.py
scripts/lane_state_refresh.py
tests/test_lane_instruction_doc_currency.py
tests/test_lane_currency_ci_wiring.py
.github/workflows/lane-doc-currency.yml
```

The event that *causes* lane-state drift is a lane PR being merged or closed. Such an
event touches **none** of those paths. It is also not a `schedule`.

Measured consequence — every run of this workflow on record, all events:

| Created | Event | Conclusion | Head branch |
|---|---|---|---|
| 2026-10-27T01:44:26Z | pull_request | failure | `gate-hygiene/lane-freshness-shallow-clone-01` |
| 2026-10-26T22:23:28Z | pull_request | success | `gate-hygiene/lane-guard-fixed-scope-01` |
| 2026-10-26T08:25:55Z | pull_request | failure | `feat/prism-l2-field-completeness-01` |
| 2026-10-15T17:15:25Z | **push** | failure | `341867eb` |
| 2026-10-25T05:13:04Z | **push** | success | `3a1088c5` |

There are exactly **two** `push` runs in the workflow's history, and they are the two
commits that edited the snapshot. Between 2026-10-15 and 2026-10-25 — the entire window
in which all nine PRs closed and every lane instruction went dead — the gate executed on
`main` **zero times**. The gate ran only when someone changed the file the drift lives
in, which is precisely the change a drifting lane does not make.

**Root cause, stated plainly:** the drift detector is path-filtered to its own state
file. The condition it detects is produced by events (lane PR merged/closed) that are
invisible to that filter, and no schedule substitutes. So the detector can only fire
*after* a human has already noticed and edited the snapshot — i.e. it cannot be the thing
that notices.

---

## 7. F6 — the oracle is scoped to the snapshot's own claims, so it cannot see under-counting

`_pr_state_findings` requires every **claimed-open** PR to be live-open. The claim set is
derived by `claimed_open_prs(state)` **from the snapshot itself**. The decision table is
total over that set and fails closed — but the set is the snapshot's opinion, so a PR
that is live-open and *absent* from the snapshot is never judged.

Measured now at `36f53be2`:

```
claimed (open_prs ∪ deferred_to_pr) = 14
live open PRs                       = 25
unclaimed open PRs                  = 13
```

The guard's verdict on that state is exit **1**, but only for two *over*-claims
(`PR #508 (lane 4 open_prs)` and `PR #563 (lane 3 open_prs)`, both closed-unmerged). The
13 unclaimed live-open PRs produce no finding at all. Combined with the documented
one-directional local oracle (ancestry proves *merged*, never *closed*), the guard has:

- no way to detect an under-count (live-open but unrecorded),
- no way to detect a closed-unmerged PR by local means,
- and (F3) no consumer for the two fields that would carry both facts
  (`closed_unmerged`, `unassigned_open_prs`).

This is the "silent second continuity hole" the guard's own docstring names, measured
rather than restated: the hole is not only that local ancestry cannot prove *closed* —
it is that the authoritative oracle is bounded by the very list it is meant to audit.

---

## 8. F7 — dead-thread pointers are reported as non-blocking, and the exemption reasons past the case that matters

Guard output on current `main`:

```
NOTE lane 3 (AGENT-03-SOLARIUN-KNOWLEDGE.md) declares PR #450, which is CLOSED without
     merging -- ... (lane not owned by this guard; reported, not blocking)
NOTE lane 4 (AGENT-04-ARKANA-WEAVER-LAB.md) declares PR #428, which is MERGED -- ...
     (lane not owned by this guard; reported, not blocking)
```

Lane 3's pointer is the same defect class the workstream exists to prevent — a successor
agent sent to a closed thread — and it is reported, not blocked, because lanes 3 and 4
are "deferred". `_liveness_findings`' docstring justifies the exemption with "a deferred
doc naming its *previous* merged wave is expected". That reasoning covers lane 4
(#428 is merged) but **not** lane 3: #450 is closed *without* merging, which is a
different state and the one the lane model must never name.

Measured at `68acf89f`, the four lane docs declare: lane 1 → #507 (CLOSED-UNMERGED),
lane 2 → #430 (MERGED), lane 3 → #450 (CLOSED-UNMERGED, last-wins), lane 4 → #428
(MERGED, per the guard). Two of four lane instructions point at dead threads; the
mechanism flags both, blocks neither.

---

## 9. F8 — a truncated clone makes the liveness oracle silently vacuous (separate; PR #572's repair)

Measured on `main` `36f53be2` in a `--depth=1` clone
(`git rev-parse --is-shallow-repository` → `true`):

```
base main: 68acf89f... (current: unknown -- not resolvable)
  DRIFT current main is not resolvable (shallow or detached clone?); snapshot
        freshness is UNKNOWN, not a pass
exit 1
```

The *freshness* path already names a truncated clone correctly (`scripts/lane_state.py:592`,
from `3a1088c5`) and fails closed. The gap is in `_liveness_findings`, and it has two
distinct shapes that are worth separating because only the second is repairable by the
`clone_is_shallow` guard PR #572 adds:

**(a) Commit absent.** `commit_is_present` returns false and the function already emits
`PR #<n> cannot be adjudicated -- merge commit <sha> is not in this clone (shallow
checkout?); liveness is UNKNOWN, not a pass` (`lane_state.py:249`). Fails closed. On this
snapshot, however, it is unreachable: the intersection of claimed-open and `merged_prs` is
empty (§4), so no claimed PR ever has a commit to look up.

**(b) Commit present but unwalkable — the silent pass.** A grafted checkout can hold the
commit object while `merge-base --is-ancestor` cannot walk to it. Constructed directly and
verified two-sided, planting the exact case `_liveness_findings` exists to catch (a
recorded-merged PR the snapshot still claims open — here #492, whose merge commit
`7030ccb2f264…` is in lane 2's `merged_prs`):

```
python3 -c "... ls._liveness_findings(planted_state, repo=Path(...))"

full clone     findings=1  ['lane 2: PR #492 is recorded as open but its merge commit
                            7030ccb2 is already an ancestor of HEAD -- the snapshot is
                            stale; re-measure the lane PRs']
shallow clone  findings=0  []
```

In the shallow clone the object is present (`git cat-file -t` → `commit`) and
`merge-base --is-ancestor` exits **1**, which the code reads as "not an ancestor" — the
verdict for a PR that is *not* merged. So a defect the guard catches in a full clone is
**silently passed** in a truncated one, in the direction the check exists to catch. This
is `scripts/lane_state.py:187`'s own warning ("a silent pass in exactly the direction that
…") arriving by a path it does not cover.

PR #572 (`gate-hygiene/lane-freshness-shallow-clone-01`) adds `clone_is_shallow()` and
splits this branch out; it is the authority for that repair. Its current `failure` on
`Lane Doc Currency` is its own mid-repair state, not a regression of `main`. The CI gate
uses `fetch-depth: 0`, so shape (b) affects the local-operator path, not the gate — which
is why it did not surface as a red `main`.

---

## 10. Root cause, consolidated

The lane-state mechanism has one measurement defect and one structural defect, and the
recorded narrative conflates them:

1. **Measurement (F1, F3).** The snapshot is hand-transcribed and refreshed only when a
   pulse chooses to run `lane_state_refresh.py --write`. The machine-readable artifact
   was eventually correct (`closed_unmerged` holds the right nine numbers) but is read by
   nothing; the prose was wrong and is read by everyone.
2. **Structure (F5).** The only automated detector is path-filtered to the state file it
   audits, and has no `schedule`. It therefore cannot fire on the events that produce
   drift. Measured: zero `main` executions across the entire 10-day window in which the
   drift completed.
3. **Scope (F6, F7, F8).** The authoritative oracle is bounded by the snapshot's own
   claim list, so it cannot see under-counting; the local-ancestry oracle is **vacuous on
   the shipped snapshot** because claimed-open and `merged_prs` do not intersect; dead-
   thread pointers on deferred lanes are reported but never block; and a truncated clone
   turns an unwalkable merge commit into a silent pass rather than an UNKNOWN.

So the "guard" has three independent ways to be inert at once — a path filter that cannot
see the triggering event, a claim set that never overlaps the list it audits, and a clone
shape that converts a catch into a pass — while every one of its tests is green and its
output is well-formed. That is the property worth carrying forward: **a guard's silence
is not evidence of soundness, and this one had no negative control for silence.**

The "three unmerged" figure (F2) is a **fourth, independent** defect: a transcription
error in the repair's own description, shipped into four tracked sites, whose correct
value the repair's own snapshot already recorded. It is worth separating because it is
the reason this audit was requested, and because it is the cheapest to guard — a test
binding prose counts to `closed_unmerged` would have caught it, and no such test exists.

---

## 11. What is NOT claimed

- **No source change is proposed or made here.** Findings F5–F8 are recorded as
  *proposed, classified, dependency-linked* work. Execution requires sovereign
  authorization; discovery does not authorize execution.
- **PR #572 is not adjudicated.** It is cited as the authority for the shallow-clone
  claim (F8); this audit does not verify its repair.
- **The "three deferred lanes" origin hypothesis (F2) is not proven** and is recorded as
  a hypothesis.
- **No lane doc, snapshot, guard, workflow, or test was modified.** The only write is
  this evidence file.
- Production acceptance remains **NOT CLAIMED**. This workstream does not deploy.

---

## 12. Proposed bounded follow-ons (not executed)

Each is independent, small, and separately authorizable. None is performed here.

| # | Proposal | Scope | Blocked on |
|---|---|---|---|
| P1 | Correct the four "three unmerged" sites to the measured **nine**, dated, and state which measurement supersedes them | prose only, 4 files | sovereign authorization (edits `main`'s shipped prose) |
| P2 | Bind prose counts to `closed_unmerged` in the guard's test, with a negative control feeding the wrong count | `tests/test_lane_instruction_doc_currency.py` | P1 (same file family) |
| P3 | Make the guard read `closed_unmerged` and `unassigned_open_prs`, so a refresh cannot re-list a dead PR or silently drop a live one | `scripts/lane_state.py` + tests | sovereign authorization; authority surface |
| P4 | Give `lane-doc-currency.yml` a `schedule` (or trigger it from lane-PR closure), so drift is detected by time rather than by a human editing the snapshot | one workflow | sovereign authorization; widens an execution surface |
| P5 | Make a closed-unmerged declared pointer on a deferred lane blocking, or state explicitly why it stays a NOTE | `scripts/lane_state.py` | depends on P3 |
| P6 | Assert the local-ancestry oracle is **non-vacuous**: `claimed_open_prs(state) ∩ merged_prs(state)` must be non-empty for a snapshot that records any merged lane PR, with a negative control on an empty intersection. Today it is empty, and the oracle silently returns `[]` | `tests/test_lane_instruction_doc_currency.py` | none (test-only) — the cheapest of the six |

P6 is the one that would have surfaced the whole class: it does not need the guard
rewritten, only a test that notices when the oracle has nothing to look at. It is
test-only and therefore executable inside a normal lane pulse once authorized.

The §8.2 design tension the repair already recorded — a gate whose blocking scope is
derived from a field its own refresher writes — is a *precondition* for P3, not a
separate item. It remains the sovereign's call.

---

## 13. Reproduction

```bash
# 1. The snapshot live on 2026-10-24, and its ten claimed-open PRs
git show 341867eb:docs/control-plane/parallel-ui/lane-state.json | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(d['observed_at'], d['base_main'])
print(sorted({p['number'] for l in d['lanes'].values() for p in l['open_prs']}))"

# 2. Liveness of each (read-only; needs a token)
for n in 492 507 526 527 528 529 534 536 537 538; do
  curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/pulls/$n" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['number'], d['merged'], d['merged_at'], d['closed_at'])"
done
# expected: 1 merged (#492), 9 closed-unmerged

# 3. The correct figure, recorded in the repair's own snapshot
python3 -c "import json; d=json.load(open('docs/control-plane/parallel-ui/lane-state.json')); print(d['closed_unmerged'])"
# expected: 9 entries

# 4. The four sites asserting 'three'
git grep -n "three of those ten\|three of them never merged\|three of them unmerged\|three unmerged" origin/main

# 5. The guard's verdict on current main, and its claim-vs-live gap
python3 scripts/lane_state.py --check --verify-live      # exit 1, 2 DRIFT, 2 NOTE
python3 -c "
import json,urllib.request,os
d=json.load(open('docs/control-plane/parallel-ui/lane-state.json'))
claimed={p['number'] for l in d['lanes'].values() for p in l['open_prs']}
claimed|={l['deferred_to_pr'] for l in d['lanes'].values() if l.get('deferred_to_pr')}
r=json.load(urllib.request.urlopen(urllib.request.Request(
  'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/pulls?state=open&per_page=100',
  headers={'Authorization':'Bearer '+os.environ['TOKEN']})))
print('claimed',len(claimed),'live-open',len(r),'unclaimed',len([p for p in r if p['number'] not in claimed]))"

# 6. Gate execution history: two push runs, ten days apart, both editing the snapshot
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/actions/workflows/lane-doc-currency.yml/runs?per_page=15"

# 7. Truncated-clone behaviour (separate defect)
git clone -q --depth=1 <repo> /tmp/shallow && cd /tmp/shallow && python3 scripts/lane_state.py --check
```

---

## 14. Glance

```
ARKADIA ENGINEERING — AUDIT
LANE-STATE DRIFT · RECONNAISSANCE
The drift is real but larger than recorded: of the ten PRs the 2026-10-15
snapshot listed as open, ONE merged and NINE never did — not three.
Tests: guard exit 1 on main (2 DRIFT, 2 NOTE); CP10 --judge PASS on this path
Regression: none (docs-only; no source, test, or workflow change)
PR: #<n>
Status: IMPLEMENTED (measurement complete; no change proposed)
ACTION: sovereign review required — P1..P5 are proposed, none executed
```
