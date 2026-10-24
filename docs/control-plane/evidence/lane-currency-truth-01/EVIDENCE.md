# Lane instruction-doc currency truth repair (EVIDENCE)

**Workstream:** gate-hygiene / lane-currency-truth-01
**Branch:** `gate-hygiene/lane-currency-truth-01`
**Base main:** `68acf89f3045a01b0ba04038fabac4edfb5f937e`
**Observed:** 2026-10-24
**Status:** REPAIR COMPLETE, NOT MERGED — human merge authority not exercised.
Production acceptance NOT CLAIMED (this workstream does not deploy).

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

Environment: Python 3.13.15, `PYTHONPATH=archive/legacy_python`, `-rEf
--continue-on-collection-errors`.

| Tree | Result |
|---|---|
| `main` `68acf89f` | 97 failed, 2966 passed, 31 skipped, 42 errors |
| branch `24d5134f` | 97 failed, 2994 passed, 31 skipped, 42 errors |

Failing/error **node set**: 140 nodes both sides, `sha256`
`db78e124b4ca58a93abef501281d7532b406c537da8fc89a0b82a47b6e75cb87` on **both**;
`comm -3` empty. **Zero regression.**

`+28 passed` attributed by `--collect-only` arithmetic, not inferred from the
total: lane-currency 23 → 38 (**+15**), `test_knowledge_graph_traverse_boundary`
0 → 9 (**+9**), `test_knowledge_search_boundary` 21 → 25 (**+4**). The `+13`
outside lane-currency is PR #548's own tests, carried by the composition.

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

## 4. Gate-2 boundary (unchanged)

No merge, no deployment, no production claim. `api/main.py` untouched. Human merge
and release authority not exercised.

---

## 5. Next permitted action

Human review of `gate-hygiene/lane-currency-truth-01`, then (separately
authorized) merge. After `#548`/`#555` land or are superseded, re-point
`AGENT-03` and `AGENT-04` at live lane threads and re-run
`python scripts/lane_state.py --check --verify-live`; it should then be clean
with no NOTES.
