# Lane instruction-doc currency truth repair (EVIDENCE)

**Workstream:** gate-hygiene / lane-currency-truth-01
**Branch:** `gate-hygiene/lane-currency-truth-01`
**Base main:** `68acf89f3045a01b0ba04038fabac4edfb5f937e`
**Observed:** 2026-10-24
**Status:** MERGED as `3a1088c5` (PR #565, squash) onto `68acf89f`; superseded PR #563 closed.
Exact-head reconciliation performed (§4). Production acceptance NOT CLAIMED
(this workstream does not deploy). **§6 and §7 carry superseded figures — read §10 first.**

---

## 1. What was actually wrong

The guard was not merely failing. It was **measuring the wrong thing**, and that
hid a second, worse defect.

### 1.1 Defect A — repository movement read as lane-state staleness

`scripts/lane_state.py` decided freshness with a SHA-equality test:

```
snapshot.base_main == current main
```

`main` advances for reasons that change nothing the snapshot records. Measured at
`main` `68acf89f` against the snapshot's `04e1b83b`: **31** commits had landed,
exactly **two** touched `docs/control-plane/parallel-ui/`, and the four lane docs
still agreed with the snapshot — yet the guard exited `1`.

A rule that fires on every unrelated merge cannot be satisfied by any correct
snapshot. The guard was therefore not protecting freshness; it was reporting
repository activity, and an operator's only recourse was to ignore it.

### 1.2 Defect B — the deferral mechanism laundered dead pointers

This is the more serious finding, and Defect A is what kept it hidden.

`check_lane_docs` deliberately skips a lane whose doc is mid-repair by another
open PR (a *deferral*). That is right for the snapshot-agreement property. But the
deferred doc's own `**Active PR:**` pointer was then **judged by nobody** — and
that pointer is precisely what a successor agent reads.

Measured live at `68acf89f`:

| Lane | Doc | Declared PR | Live state | Who installed it |
|---|---|---|---|---|
| 1 | `AGENT-01-SHELL.md` | #507 | **CLOSED, unmerged** | pre-existing |
| 2 | `AGENT-02-NOVANET-OPPORTUNITY.md` | #430 | **MERGED** | pre-existing |
| 3 | `AGENT-03-SOLARIUN-KNOWLEDGE.md` | #526 | **CLOSED, unmerged** | open PR **#548** |
| 4 | `AGENT-04-ARKANA-WEAVER-LAB.md` | #428 | **MERGED** | pre-existing |

> **Superseded at `3a1088f` (2026-10-25) — see §10.** The lane-2 row is stale: the
> shipped snapshot declares lane 2 `current` at **#564** (§8.1's append), not #430,
> and lane 1 is #562. The #430/#428 rows describe `68acf89f`, before the repair.
> Lane 3 declares #450 (CLOSED, unmerged), not #526, and lane 4 declares #431.

**All four** lane instructions pointed a successor agent at a dead thread. Two of
them were *installed by open PRs* (#548 → `#526`, #555 → `#536`), each while its
lane was `deferred` — so each PR's own gate passed while making the drift worse.

An additional, independent fact: **all ten** PRs the committed snapshot listed
under `open_prs` had closed (three unmerged). The snapshot was hand-transcribed,
and hand-transcription is the mechanism by which it drifted.

---

## 2. The repair

### 2.1 Freshness decided by guarded-path movement

Staleness is now: **a lane doc the snapshot names changed after the snapshot was
last written.** The reference point is *derived* from git history
(`git rev-list base..main -- <lane-state.json>`, newest first), not recorded.

Why not a declared `refresh_commit` (the first design): the commit that writes the
snapshot necessarily appears in its own window, so the exemption would have to
name a SHA that does not exist until the commit is made. Any snapshot shipped
without it would re-redden `main` the instant it merged. Derivation has neither
problem and is topology-independent.

Measured on four constructed topologies (hermetic scratch repo):

| Topology | Expected | Measured |
|---|---|---|
| One commit touches doc **and** snapshot | fresh | fresh |
| Doc edited, no snapshot refresh | **stale** | stale |
| Refresh *after* a doc edit | fresh | fresh |
| Doc edit *after* a refresh | **stale** | stale |
| Unrelated file only | fresh | fresh |

Every inability to establish the window **fails closed** (a finding, not a pass):
unresolvable `main`, absent `base_main`, `base_main` not an ancestor of `main`
(rewritten history voids the recorded provenance), and any git failure.

### 2.2 Authoritative PR-state oracle

`--verify-live` reads each PR from the GitHub REST API (GET only, read-only; the
token is never printed) and classifies it **OPEN / MERGED / CLOSED_UNMERGED /
UNKNOWN**. `merged` is consulted before `state` because GitHub returns
`state == "closed"` for both merge outcomes; a record missing either field is
`UNKNOWN` rather than guessed. Any transport/auth/non-200 outcome becomes a
failure string, so the caller fails closed instead of reading an empty result as
"no PRs exist" — which would look identical to a pass.

Critically, liveness is judged on the **document**, for every lane, independently
of disposition. That is what closes the deferral hole.

### 2.3 The suppression that measurement killed

An intermediate design let a lane record a `pointer_handoff` naming an open PR
that would re-point its doc, suppressing the finding while that PR stayed open.
It was **removed, not shipped**: measurement showed both PRs that would have been
named (#548, #555) *install* a dead pointer rather than repair one. The
suppression would have been false — the same defect as the one being repaired,
one level up. Recorded here because the mechanism is plausible and a future pass
should not re-invent it without measuring the owner first.

### 2.4 Snapshot is derived, not transcribed

`scripts/lane_state_refresh.py` re-measures the snapshot from live PR state.
Lane assignment is by **exclusive path ownership** (`SHARED-CONTRACTS.md` §1), so
overlap is visible instead of resolved by guessing; a PR matching no lane is
recorded under `unassigned_open_prs` rather than attributed.

The first dry run caught an error in the refresher's own ownership table: blanket
`weaver/` and `lab/` prefixes swept the EAA/dispatch/acceptance PRs
(#499/#500/#502/#508/#535/#553) into lane 4, none of which touch a feature-local
console module — and the contract's lane-4 row explicitly says lane 4 *must not
edit* those surfaces. Narrowed to the console feature surface.

Schema is `arkadia.lane-state/1.2`: adds `closed_unmerged`, `unassigned_open_prs`,
`updated_at`/`head_sha` per PR, and a deterministic `active_pr` rule (most
recently updated open lane PR, ties broken on number).

### 2.5 Blocking scope vs reporting scope

Dead pointers **block** only for the lanes this guard owns (lane 1). Every lane is
still **reported** — a finding nobody prints is the hole being repaired. Blocking
on a doc the guard does not own would make the gate permanently red for work it
cannot do, which is how operators learn to ignore a gate.

`AGENT-03` and `AGENT-04` are owned by PRs #548 and #555; their dead pointers are
recorded here as a **measured handoff**, not edited from a lane that does not own
them.

### 2.6 CI wiring

`.github/workflows/lane-doc-currency.yml` previously ran only the offline check,
so the oracle — the check that actually finds a dead pointer — executed
**nowhere** ("a guard no workflow executes is decoration"). Added:

- the `--verify-live` step, with `GH_TOKEN: ${{ github.token }}` in scope;
- the wiring guard, run **inside** the gate so a rewrite of the workflow is judged
  by the workflow it rewrites;
- both new paths added to both `paths` filters.

The oracle fails closed on a GitHub outage, so a transient failure reddens the
step. That is the safe direction for a staleness check and is stated in the
workflow comment.

---

## 3. Verification

### 3.1 Contract and wiring suites

```
tests/test_lane_instruction_doc_currency.py   38 passed
tests/test_lane_currency_ci_wiring.py         12 passed
architecture suite                            11 passed
```

`api/main.py` untouched at **2505** lines (budget 2600). Both scripts
`py_compile` clean.

### 3.2 Negative controls — each detector disarmed, in turn

Every control mutated the **real** file, asserted the guard reddened, then
restored **byte-identically** (`diff -q` clean).

| Control | Mutation | Result |
|---|---|---|
| NC1 | `_declared_pointer_findings` returns `[]` | **4 failed**, 34 passed |
| NC2 | freshness staleness branch disabled | **1 failed**, 37 passed |
| NC3 | unresolvable `main` abstains instead of failing closed | **1 failed**, 37 passed |
| NC-A | live-oracle step removed from the real workflow | **2 failed**, 8 passed |
| NC-B | contract step mutated to `echo python -m pytest …` | **1 failed**, 9 passed |
| NC-C | refresh script dropped from a `paths` filter | **1 failed**, 9 passed |
| NC-D | wiring-guard step removed | **1 failed**, 11 passed |

**NC-B is the important one.** The first version of the wiring detector *did not
bite* on the `echo` form: it checked that `-m` preceded `pytest` but never that
the command word started there. It was fixed to require `pytest` or
`python -m pytest` as the command word, and re-measured to bite. A detector with
that hole would have let the executing step be replaced by an `echo` while the
wiring guard stayed green.

### 3.3 Regression measurement (same environment, both trees)

Environment: Python 3.13.15, pytest 9.1.1, `PYTHONPATH=archive/legacy_python`,
`-rEf --continue-on-collection-errors`. Both trees measured in the same session.

| Tree | Result |
|---|---|
| `main` `68acf89f` | 97 failed, 2966 passed, 31 skipped, 42 errors |
| branch `3a703e91` | 97 failed, 3006 passed, 31 skipped, 42 errors |

Failing/error **node set**: 140 nodes both sides, `sha256`
`db78e124b4ca58a93abef501281d7532b406c537da8fc89a0b82a47b6e75cb87` on **both**;
`comm -3` empty. **Zero regression.**

`+40 passed` attributed by `--collect-only` arithmetic, not inferred from the
total: lane-currency contract 23 → 38 (**+15**), lane-currency wiring 0 → 12
(**+12**), `test_knowledge_graph_traverse_boundary` 0 → 9 (**+9**),
`test_knowledge_search_boundary` 21 → 25 (**+4**). The `+13` outside
lane-currency is PR #548's own tests, carried by the composition.

**A superseded figure, reconciled rather than restated.** An earlier pass recorded
`+28` for this branch. Both numbers are correct *for their own commit*: `+28`
(= 15+9+4) was measured at `24d5134f`, and
`git cat-file -e 24d5134f:tests/test_lane_currency_ci_wiring.py` returns absent —
the wiring guard did not exist yet. The `+12` it adds is the difference. Quote
`+40` for head `3a703e91`, and say which commit a delta belongs to.

An earlier measurement of this same branch read `112 failed, 2277 passed, 111
errors` because `fastapi` was absent from the sandbox. It is superseded by the
measurement above; both trees were re-measured in the same session after
installing dependencies, and the node sets still matched.

### 3.4 Composition with PR #548

#548 owns `scripts/lane_state.py`, `lane-state.json`,
`tests/test_lane_instruction_doc_currency.py` — the same contended files. Its
head was **merged** into this branch (`git merge`, not a patch):

```
10 files changed, 790 insertions(+), 157 deletions(-)
```

Zero conflicted paths; both `_disposition_findings` (from #548) and the
guarded-path freshness rule (from this work) are present and exercised. No
competing patch was pushed over #548's work.

---

## 4. Exact-head reconciliation (2026-10-24T12:09Z)

Re-derived from live state rather than restated. Observation timestamp
`2026-10-24T12:09:12Z`.

| Property | Value |
|---|---|
| PR | #563, `OPEN`, `draft=true`, `MERGEABLE` / `CLEAN` |
| Reconciled head | `3a703e91396e037e813c32f40a09b679343f9a4b` (12/12 success, run `40088929871`) |
| Current head | `7a60c2b9cf9d43fa5c6f4dcf4ac45fd02acaabc6` (12/12 success, run `40093400494`) |
| Local `HEAD` | `7a60c2b9cf9d43fa5c6f4dcf4ac45fd02acaabc6` — **matches** |
| Branch base | `main` `68acf89f3045a01b0ba04038fabac4edfb5f937e` |
| Live `main` | `68acf89f3045a01b0ba04038fabac4edfb5f937e` — **unchanged**, 0 commits behind |
| Working tree | clean (agent memory is gitignored) |

**Reviewed diff == tested diff, by object identity.** Every one of the 16 changed
paths was compared between the local object store and GitHub's contents API at
that exact head; all 16 git blob SHAs are identical. This is stronger than
comparing a patch: it establishes the bytes, not just the diff.

**Checks bound to the exact head.** `commits/3a703e91…/check-runs` reports
`total_count: 12`, all `completed/success`, every `head_sha` equal to the full
head. The gate run is `40088929871` (`event=pull_request`,
`head_sha=3a703e91…`).

**Negative control on the SHA trap** (recorded in `AGENTS.md`): the abbreviated
SHA `3a703e91` passed to `?head_sha=` returns `total_count: 0` while the full
40-character SHA returns `9` — the same tree, the same token, the same instant.
A `0` from a short SHA is *unproven*, not *absent*. Re-measured here rather than
trusted from memory.

**This document's own commit moved the head it describes — stated, not hidden.**
Reconciling §4 required editing this file, which advanced the head from
`3a703e91` to `7a60c2b9`. That is a genuine circularity, so it was resolved by
measurement rather than by wording: `git diff --name-only 3a703e91..7a60c2b9`
shows **exactly one** path (this document), and every code artifact was compared
by blob SHA across the two heads — `scripts/lane_state.py`,
`scripts/lane_state_refresh.py`, both test files, the workflow, the snapshot and
the lane doc are all byte-identical. The reconciled head was therefore re-verified
rather than assumed: 12/12 checks success on `7a60c2b9` (run `40093400494`), with
the gate log independently reproducing `live PR state: 15 PR(s) read` and all
three NOTEs. **The reviewed code is the tested code; only the prose around it
changed.**

**Suites at the exact head.** contract 38 passed, wiring 12 passed, architecture
11 passed; `api/main.py` 2505 lines (budget 2600), untouched; both scripts and
`api/main.py` compile clean.

**A mid-session environment reset was detected and repaired.** The container lost
its site-packages between passes (`ModuleNotFoundError: No module named
'pytest'`), which would have read as a catastrophic regression had it been
attributed to the change. Reinstalled (`pytest` 9.1.1, `fastapi` 0.162.0) and
both trees re-measured in the same session. Recorded because the failure mode is
indistinguishable from a real one at the summary line.

**`gh` credential availability is intermittent, not absent.** One `gh pr view`
call failed with "please run `gh auth login`" while `gh auth status` reported a
valid session and an immediately-following identical call succeeded. Do not
conclude the credential is missing from a single failure; retry and re-read
`gh auth status` before recording a BLOCKED boundary.

---

## 5. Gate-2 boundary (unchanged)

No merge, no deployment, no production claim. `api/main.py` untouched. Human merge
and release authority not exercised.

---

## 6. Preserved handoff — remaining lane-document debt (NOT repaired here)

Recorded so the debt survives this workstream rather than being silently closed
with it. These are **outside this guard's ownership**; repairing them from a lane
that does not own the docs would be a scope violation, so they are reported (3
NOTEs in CI) and left standing.

| Lane | Doc | Declares | Live state | Owner |
|---|---|---|---|---|
| 2 | `AGENT-02-NOVANET-OPPORTUNITY.md` | #564 | OPEN | lane-2 owner — **re-pointed by this repair (§8.1)** |
| 3 | `AGENT-03-SOLARIUN-KNOWLEDGE.md` | #450 | CLOSED, unmerged | PR #548 |
| 4 | `AGENT-04-ARKANA-WEAVER-LAB.md` | #431 | MERGED | PR #555 |

> **Superseded at `3a1088f` (2026-10-25).** This table was derived at `68acf89f`
> and describes the pre-repair state; the rows above are the shipped ones. The
> "3 NOTEs" figure was measured before §8.1's lane-2 append, which *removed* one:
> the shipped gate reports **2 NOTEs** (lanes 3 and 4), which is what §10.2
> measures and what CI reproduces.

Lane 1 was re-pointed at live PR #562 as part of this repair, because this guard
owns it.

**Re-entry condition:** when #548 and #555 land or are superseded, re-point
`AGENT-03` and `AGENT-04` at live lane threads and run
`python scripts/lane_state.py --check --verify-live`. It should then be clean
with no NOTEs. Until that happens, a successor agent reading AGENT-02/03/04 is
sent to a dead thread — the oracle now says so out loud, which is the change that
matters: **the debt is visible, not repaired, and not concealed.**

The measured handoff was also posted to PR #548 (comment `6383546506`), which owns
lanes 3 and 4.

---

## 8. Snapshot refresh widens the gate's own blocking scope (measured 2026-10-24T16:2xZ)

Re-running this workstream's own refresher against live state surfaced a defect the
first pass could not see, because the pass that wrote the snapshot ran before the
condition existed.

`python scripts/lane_state_refresh.py --write` moved lane 2 from
`doc_guard: idle` to `doc_guard: current`: PR **#564**
(`feat/prism-l2-field-completeness-01`, opened 2026-10-24T12:55Z) is the first open
PR whose changed paths fall inside lane 2's exclusive ownership
(`web/arkadia_console/src/pages/NovaNetPage.tsx`). The snapshot is a *derived*
mirror, so recording that was correct.

The consequence was not anticipated by the first pass. The guard's **blocking**
scope is:

```
findings += check_lane_docs(state, lanes=current_lanes(state))
```

`current_lanes` reads the snapshot's `doc_guard` field -- a field the refresher
writes. So a refresh can widen the gate's teeth onto a lane whose doc it does not
repair. Measured immediately after the refresh, at `main` `68acf89f`:

```
$ python scripts/lane_state.py --check
  DRIFT lane 2 (AGENT-02-NOVANET-OPPORTUNITY.md): declares PR #430, which is not an
    open lane PR in the snapshot (open: [..., 562, 563, 564])
  exit 1

$ python -m pytest tests/test_lane_instruction_doc_currency.py -q
  1 failed, 49 passed
  test_live_guarded_docs_agree_with_the_snapshot
```

`AGENT-02` declares PR #430, which is **MERGED**. The finding was therefore
*correct*, and the refreshed tree could not be merged as it stood: the gate was red
on the workstream that owns the gate. This is the same class the first pass
recorded -- a lane instruction pointing a successor agent at a dead thread -- one
lane further along.

### 8.1 The repair, and why it is an append

`AGENT-02-NOVANET-OPPORTUNITY.md` gains one appended dated status block naming the
live lane-2 thread (#564 / `feat/prism-l2-field-completeness-01`). No code change, no
shared file, no mutation path, no new abstraction. Appending is the convention the
document already uses and the one `declared_branch`/`declared_pr` implement
(last declaration wins), so the stale pointers above it stay as provenance rather
than being destroyed.

`AGENT-03` and `AGENT-04` are deliberately **not** touched: they are `deferred` to
open PRs #548 and #555, which install their own pointers. That is §6's measured
handoff, and repairing them from here would be a scope violation.

### 8.2 The design tension is recorded, not resolved

The honest statement is that this workstream repaired a lane-2-owned document
because the guard it owns began blocking on it. The alternative -- leaving the
snapshot un-refreshed so lane 2 stayed `idle` -- would have passed CI while
recording a falsehood (an open lane PR omitted from the mirror), which is precisely
the hand-transcription drift this workstream exists to remove.

The underlying tension is real and is left for sovereign review: **a gate whose
blocking scope is derived from a field its own refresher writes can widen its own
teeth.** Resolving it means either fixing the blocking scope to a stated lane set or
making the refresher refuse to widen scope, and either is a design change to the
guard rather than a bounded repair. Recorded here so a successor pass does not
re-invent the question; do not "fix" it inside a pointer-repair slice.

### 8.3 Verification at this head

| Check | Result |
|---|---|
| `tests/test_lane_instruction_doc_currency.py` | **38 passed** |
| `tests/test_lane_currency_ci_wiring.py` | **12 passed** |
| `tests/architecture` | **11 passed** |
| `scripts/lane_state.py --check` | exit **0** |
| `scripts/lane_state.py --check --verify-live` | exit **0** (2 NOTEs, lanes 3 and 4) |

The two remaining NOTEs are the §6 handoff, unchanged and still reported rather than
hidden.

## 7. Next permitted action

Human exact-head review of `gate-hygiene/lane-currency-truth-01` at
`3a703e91`, then — separately authorized — merge. Merge, deployment, and
acceptance are three separate decisions; the 12/12 checks and `MERGEABLE/CLEAN`
status are evidence, not authorization.

Scope is deliberately bounded: this PR repairs the guard and makes the oracle
operational. It does **not** repair the four lane documents.

---

## 9. Isolation onto current main (2026-10-24T18:xxZ)

### 9.1 Why this branch exists

The prior branch head (`1a39c843`) reached `main` through a **merge of PR #548's head**
(`13ace844`, this workstream's own composition check). That measurement action left **seven of
#548's commits in the branch history**, so merging that head would have carried
`knowledge/graph.py`, `knowledge/search.py` and their tests into `main` alongside an unrelated
governance repair. Measured: `git diff --stat origin/main...1a39c843` = **17 files, 2717+/90-**.

Isolation is therefore not a rewrite of the repair. It is the same repair composed onto `main`
without the foreign commits.

### 9.2 Method

`main` `68acf89f` + this workstream's own changes only. The guard delta was taken as a diff
against #548's version and applied onto `main`'s `lane_state.py`; it applies **cleanly**
(`git apply --3way` exit 0), which is the evidence that the repair never depended on #548.

**#548's `idle` disposition vocabulary is deliberately not adopted.** Its commits are titled
"represent lane with no active PR honestly"; it widens the guard's accepted set to
`{current, deferred, idle}`. The isolated guard keeps `{current, deferred}`. Adopting it would
import another lane's design into this repair and would re-couple the two PRs.

One defect in the refresher is repaired here because isolation exposed it:
`_active_thread()` indexed `ranked[0]` unconditionally, so a lane with no open PR raised
`IndexError`. It now returns `(None, None)` — the honest representation. (This path was
unreachable while `idle` short-circuited it, so adopting `idle` would have *concealed* the bug.)

### 9.3 The isolated diff

9 files, 1667+/76-, and **zero** paths under `knowledge/` or `tests/test_knowledge_*`:

| Path | Δ |
|---|---|
| `scripts/lane_state.py` | +468 |
| `scripts/lane_state_refresh.py` | +394 (new) |
| `tests/test_lane_instruction_doc_currency.py` | +307 |
| `tests/test_lane_currency_ci_wiring.py` | +182 (new) |
| `docs/control-plane/parallel-ui/lane-state.json` | +274/- |
| `docs/control-plane/parallel-ui/AGENT-01-SHELL.md` | +41 |
| `docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md` | +46 |
| `.github/workflows/lane-doc-currency.yml` | +26 |
| `.gitignore` | +5 |

### 9.4 Acceptance criteria, each measured

Measured on a **separate clone** of the branch, so no probe could mutate the tree under test.

| # | Criterion | Method | Result |
|---|---|---|---|
| AC1 | Unrelated `main` advancement is not a freshness failure | commit outside guarded paths, advance `origin/main` | exit **0** — PASS |
| AC2 | A guarded-path change triggers re-measurement | commit touching `AGENT-04`, advance `origin/main` | exit **1**, `snapshot is stale: 1 commit(s)` — PASS |
| AC3 | Unresolvable `main` fails closed | delete the `main` refs | exit **1**, `freshness is UNKNOWN, not a pass` — PASS |
| AC4 | Closed-unmerged PRs cannot stay "open" | plant #507 (closed-unmerged) as an open lane PR, `--verify-live` | exit **1**, `recorded as open but is CLOSED without merging` — PASS |
| AC5 | Unknown GitHub state fails closed | plant #99999999 (404), and separately unset every token | exit **1**, `UNKNOWN, not a pass` (both) — PASS |

The pre-existing negative controls are intact: `test_snapshot_freshness_is_asserted_not_merely_printed`
still reddens a genuinely superseded snapshot (fed `"0"*40` it reports drift), so the assertion was
made *correct*, not removed.

### 9.5 Verification

| Check | Result |
|---|---|
| `tests/test_lane_instruction_doc_currency.py` | **37 passed** |
| `tests/test_lane_currency_ci_wiring.py` | **12 passed** |
| `tests/architecture` | **11 passed** |
| `scripts/lane_state.py --check` | exit **0** |
| CP10 `--judge` on all 9 paths | PASS |
| Full suite vs `main` `68acf89f`, same env | **identical node set**, 139 nodes, `sha256 5c17a6b7…` — zero regression |

Full suite: `main` 97 failed / 2966 passed / 42 errors; branch 97 failed / **2992** passed / 42 errors.
The `+26` is exactly 14 new contract tests + 12 wiring tests.

### 9.6 What this does not claim

The repair's scope is unchanged and still bounded: it repairs the guard and makes the oracle
operational. It does **not** repair the lane 3/4 documents (they are `deferred` to #548/#555,
which install their own pointers). It does not resolve §8's design tension. It does not merge,
deploy, or constitute acceptance.

The lane-2 re-point from `1a39c843` is retained (it is this guard's own blocking scope), but
#548's `idle` design is not — so #548 and this branch remain independently mergeable in either
order.

---

## 10. Shipped state, and the corrections §6/§7 needed (measured 2026-10-25)

### 10.1 What actually landed

PR #565, squash merge **`3a1088c5`**, onto `68acf89f`. Diff verified after the merge
by re-reading `origin/main`: 10 files, 2185+/76-, **0** paths under `knowledge/` or
`tests/test_knowledge_*`. Superseded PR #563 (head `1a39c843`, 17 files / 2717+,
carrying #548's seven commits) is **CLOSED**; nothing in it is needed.

**The original defect is repaired on `main`.** Before: `scripts/lane_state.py --check`
on `main` exited **1** — the gate was red against its own repository. After:
exit **0**, and it is green *while `main` has advanced one commit past the snapshot's
`base_main`* (`68acf89f` → `3a1088c5`). That is precisely the false failure the old
SHA-equality rule produced, so the fix is demonstrated by the shipped revision itself
rather than by a fixture.

Continuously enforced, not just at PR time: the `push` run on `3a1088c5`
(`Lane Doc Currency`, run `40164716935`) is `completed/success`, and its log shows the
**live oracle executing** — `python scripts/lane_state.py --check --verify-live`
followed by the two NOTEs and `lane instruction docs consistent with snapshot
(2 guarded lanes)`. A green conclusion alone would not have proved the step ran.

### 10.2 Corrections to §6 and §7 — both were measured at the wrong revision

§6's table and §7's table were derived at `68acf89f`, **before** §8.1's lane-2 append.
They were left standing after the append and after the merge, so they described a
state that no longer existed. Corrected in place with a dated supersession note rather
than rewritten, so the pre-repair measurement stays as provenance.

| Claim | §6/§7 said | Shipped state | Why it moved |
|---|---|---|---|
| lane 1 declares | #507 (CLOSED) | **#562** (open) | this repair re-pointed it |
| lane 2 declares | #430 (MERGED) | **#564** (open) | §8.1's append |
| lane 3 declares | #526 (CLOSED) | **#450** (CLOSED, unmerged) | #548 owns lane 3 |
| lane 4 declares | #428 (MERGED) | **#431** (MERGED) | #555 owns lane 4 |
| NOTEs in CI | "3 NOTEs" | **2 NOTEs** | the lane-2 append removed one |

The "3 NOTEs" figure was the sharper error: §7 asserted it in the same document whose
own §10.2 later measured 2, and CI reproduces 2. It was a stale count carried forward
from a pre-append run, not a disagreement about the state.

### 10.3 Verification of this documentation-only change

The change is prose in one evidence file — no code, no guard, no snapshot. It cannot
alter the gate's verdict, and it is verified as such: `git diff --name-only` is exactly
one path. Because it edits a tracked path it is nonetheless run through CP10's
`--judge` before pushing.

### 10.4 What is still open, and what is still not claimed

- **#548 and #555** remain open and own lanes 3/4. Measured composition of #548's head
  (`3da97fa5`) with this repair: the only conflict is `lane-state.json`, a **derived**
  file whose correct resolution is `lane_state_refresh.py --write`, not hand-editing.
  The code files auto-merge cleanly and both designs coexist (composed tree `a0671dfc`:
  guard exit 0, 50 contract/wiring passed, #548's 34 knowledge tests passed). #548 is
  currently `CONFLICTING` against `main` for unrelated reasons.
- **The §8.2 design tension remains open** — a gate whose blocking scope is derived
  from a field its own refresher writes can widen its own teeth. Recorded, not resolved;
  resolving it is a design change to the guard and belongs to the sovereign.
- Production acceptance remains **NOT CLAIMED**. This workstream does not deploy.
