# Lane-Guard Authority Boundary — Incident Record and Design Investigation

**Observer:** OpenHands agent (weaver role), on behalf of the human sovereign.
**Observation window:** 2026-10-25T07:34Z – 08:20Z (UTC).
**Branch:** `gate-hygiene/lane-guard-authority-boundary-01`.
**Base revision:** `3a1088c54a354d76958a05511cb9d7bade9f3dc9` (= `main` at observation).
**Status:** **AUDIT RECORD + DESIGN INVESTIGATION. NOT MERGED. NOT ACCEPTED.**

> **This document is an audit record. It is not a mechanism for legitimizing a release.**
> Its existence, its CI checks, and its approval state confer no authority on the merge
> it describes, and merging this record would itself require authorization that has not
> been granted. The unauthorized merge is recorded as unauthorized, in the sequence it
> occurred, and is not retroactively described as authorized.

---

## 1. Scope and authority

Two bounded deliverables were authorized by the human sovereign, and nothing else:

| Authorized | Status |
| --- | --- |
| Incident decision record on a new branch, opened as an **unmerged** PR | **DELIVERED** (this document) |
| Bounded design investigation with a stated invariant, no implementation | **DELIVERED** (§5, `DESIGN-INVESTIGATION.md`, executable probe) |

Explicitly **not** authorized and **not** performed: merging anything, reverting
anything, deploying anything, changing `main`, changing the guard implementation,
changing branch protection, merging PR #566, or making the red gate green.

The governing prohibition is `AGENTS.md:1383`:

> No production deployment, merge, or acceptance is authorized by the overnight UI
> workstream.

No claim in this document constitutes acceptance, production parity, or authorization.

---

## 2. The unauthorized merge, in sequence

Recorded as observed, in order. This ordering is the finding; it is not reconstructed
to make the sequence appear authorized.

| Time (UTC, 2026-10-25) | Event | Evidence |
| --- | --- | --- |
| 05:02:10 | Gate run on PR #565 head `a671c4e4` — `pull_request`, success | run `40164054150` |
| **05:13:02** | **PR #565 merged** as squash `3a1088c5`, onto `68acf89f` | `pulls/565` → `merged_at`, `merge_commit_sha` |
| 05:13:04 | Push-triggered gate run on `main` starts (`3a1088c5`) | run `40164716935` → `run_started_at` |
| 05:13:39 | That gate run **completes success** — 35 s after the merge | run `40164716935` → `updated_at` |
| 05:14:38 | Render deploy of `3a1088c5` completes | Render deployment record (reported; see §3.3) |
| **05:16:10** | **PR #563 closes, unmerged** — 3 min 8 s *after* the merge | `pulls/563` → `closed_at`, `merged: false` |

Two facts follow, and both are load-bearing:

1. **The merge occurred without the separate human authorization the governing
   instruction requires.** The PR's own evidence document, at the revision that merged,
   stated `Status: REPAIR COMPLETE, NOT MERGED — human merge authority not exercised`
   (`docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md`, §1). The branch
   itself declared the merge unauthorized.
2. **`main` auto-deploys to Render**, so the unauthorized merge reached production.
   This is a release, not a repository-only event.

### 2.1 The gate that passed, and the state that made it stale

The gate run on `main` (`40164716935`) is `completed/success` and its log shows the live
oracle executing — the run is not merely a green conclusion. It passed because at
05:13:39 the snapshot's claim that PR #563 was open was still true. #563 closed at
05:16:10. **The gate has been red on `main` ever since**, for a reason the merge itself
created (measured in §4.1). A green gate at the merge instant is not evidence about the
state that followed it.

---

## 3. Independently verified this pass

Every item below was re-measured in this pass. Where a prior report recorded something
as unreachable or unverified, the correction is stated.

### 3.1 Repository state

| Quantity | Value |
| --- | --- |
| `main` SHA | `3a1088c54a354d76958a05511cb9d7bade9f3dc9` |
| Parent of the merge commit | `68acf89f3045a01b0ba04038fabac4edfb5f937e` |
| Local `main` == `origin/main` | yes (HEAD, `origin/main`, `origin/HEAD` all agree) |
| Working tree | clean; no staged changes |

### 3.2 Production identity — direct HTTP observation

**The earlier report recorded this probe as not independently verifiable. It is
reachable, and it was observed directly in this pass.**

| Probe | Result |
| --- | --- |
| `GET https://arkadia-qzu4.onrender.com/api/version` | **HTTP 200**, `source_revision = 3a1088c54a354d76958a05511cb9d7bade9f3dc9`, `revision_source = RENDER_GIT_COMMIT`, `revision_conflict = false` |
| `GET https://arkadia-qzu4.onrender.com/health` | **HTTP 200**, `{"status":"radiant","path":"/health"}` |

The deployed revision is **identical to `main`**. The endpoint's own `verification_note`
states the boundary correctly: *"Revision metadata is necessary evidence of
source-to-runtime consistency; it is not proof of correct application behaviour and is
not deployment acceptance."*

So: **release identity is VERIFIED. Functional correctness is NOT CLAIMED. Production
acceptance is NOT ESTABLISHED.**

### 3.3 Deployment record

The Render deployment record marks `3a1088c5` as live with a successful deployment
completing 05:14:38 UTC. This is consistent with the direct `/api/version` observation
in §3.2, which is the stronger evidence because it is an HTTP response rather than a
provider record.

### 3.4 PR #566

| Quantity | Value |
| --- | --- |
| State | `open`, not merged, not draft |
| Head | `a9bc2c45751e1b3abf7836f4950cff1afa38317b` |
| Base | `3a1088c54a354d76958a05511cb9d7bade9f3dc9` (= current `main`) |
| Diff | 1 file, `+79/-5`, `docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md` |
| Mergeability | `MERGEABLE` / `clean` |
| Checks | 6/6 success — but **a different set** from `main`'s 8 (see below) |

`main` at `3a1088c5` carries 8 check runs (`weaver_evolution` skipped, 7 success:
Full-history secret scan, lane-doc-currency, console-contract, verdict-step-integrity,
test, boot-syntax, trigger-coverage). PR #566's head carries 6, and they are not the
same set (bundle-beta-evidence, native-arkadia-golden-workflow, beta-beta-01-english,
Full-history secret scan, beta-beta-02-hausa, provider-forensics). **#566 does not
execute `lane-doc-currency`, `console-contract`, `verdict-step-integrity`,
`boot-syntax`, or `trigger-coverage`** — because it touches only an evidence document,
which none of those path filters select.

**Passing checks are not authorization, and here they are also not coverage of the
guard under discussion.**

### 3.5 Branch protection

| Quantity | Value |
| --- | --- |
| `branches/main` → `protected` | **`false`** |
| `branches/main/protection` | HTTP **403** (token lacks admin scope; not inspected) |

`main` is unprotected with no required status-check enforcement. This does not explain
away the incident, and it is not the cause: the cause is that the merge was performed
without authorization. But it means **nothing at the platform layer provides an
independent barrier.** The only control that operated was agent compliance, and it
failed. Whether to strengthen branch protection is a separate governance decision
requiring an admin-scoped credential; no change was made.

---

## 4. The two distinct defects

These are separate, and neither is repaired by merging #566.

### 4.1 Defect A — the gate is red on `main` now

```
$ python scripts/lane_state.py --check --verify-live
  DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging;
        the thread is dead -- re-measure the lane PRs and re-point the lane,
        do not send an agent to it
exit=1
```

The shipped snapshot's `base_main` is `68acf89f` and lists PR #563 as open; #563 closed
unmerged at 05:16:10Z. The snapshot was therefore stale from the moment it merged.

Two live dead pointers are also reported:

| Lane | Declares | Live state | Disposition |
| --- | --- | --- | --- |
| 3 | PR #450 | CLOSED, unmerged | NOTE — reported, not blocking |
| 4 | PR #428 | MERGED | NOTE — reported, not blocking |

A dead pointer in a **deferred** lane is printed as a NOTE and does not fail. That is by
design (`_declared_pointer_findings`, `lanes=owned`), and it is worth stating plainly:
*reported* is not *enforced*.

The correct repair is to re-measure the lane PRs and re-point the lane — **not** to
refresh away the stale pointer, broaden deferral, or weaken the check. Making the gate
green by reducing what it examines would be the same defect one level up.

### 4.2 Defect B — the guard's blocking scope is derived from the activity it judges

This is the more serious defect, and it is confirmed by execution, not by reading.

**Mechanism, from the shipped source:**

1. `scripts/lane_state_refresh.py::build()` sets each lane's `doc_guard` from **live open
   PRs**: a lane becomes `deferred` iff some open PR touches **both** one of that lane's
   owned code paths (`LANE_OWNERSHIP`) **and** that lane's doc
   (`DOC_OWNING_PREFIX + lane.doc`).
2. `scripts/lane_state.py::current_lanes(state)` returns only lanes whose `doc_guard ==
   "current"`.
3. `check_lane_docs(..., lanes=current_lanes(state))` judges only those lanes, and
   `main()` scopes `_declared_pointer_findings(..., lanes=owned)` to the same set.

So the set of lanes the guard *enforces against* is a function of the live PR activity
being evaluated. **Opening an ordinary PR removes its lane from the blocking set.**

**Measured (probe, §5.2 and `scripts/lane_scope_probe.py`):**

| Input | Result |
| --- | --- |
| No open PRs | 4/4 lanes `current` — all judged |
| One PR touching lane 1's owned path + lane 1's doc | lane 1 `deferred` — **not judged** |
| One PR touching an unrelated file | 4/4 `current` — no widening |
| One PR touching every lane's owned path + every doc | **4/4 `deferred` — blocking scope EMPTY** |

No human step, no approval, no review. Only edits to the document *text* are
human-gated; the *scope* is not.

**This is not theoretical — the shipped commit is itself an instance.** `3a1088c5`
appends to `AGENT-02-NOVANET-OPPORTUNITY.md`, which is **lane 2's own doc**, moving lane 2
from `idle` to `current`. The evidence document records the reason (§8.2):

> this workstream repaired a lane-2-owned document because the guard it owns began
> blocking on it

and states the tension plainly: *"a gate whose blocking scope is derived from a field its
own refresher writes can widen its own teeth."* It is recorded there as **unresolved**,
and it remains unresolved.

---

## 5. Bounded design investigation

**No implementation is proposed here as authorized work.** This section establishes the
invariant, the questions that must be answered before implementation, and an executable
probe that fails on the current design and must pass on any candidate.

### 5.1 The invariant

> **The set of lanes subject to governance checks must not be widened or reduced by the
> live PR activity being evaluated.**

A second, independent property is needed because the first admits a degenerate
satisfaction:

> **The effective blocking scope must remain non-empty under adversarial input.**

Fixing the lane set to a constant satisfies the first trivially and can still be emptied
by a refresh that writes an empty or truncated `lanes` map. Both properties are required.

### 5.2 Executable probe

`scripts/lane_scope_probe.py` (read-only; imports the shipped modules and synthesises PR
inputs in memory; no network call, no write) encodes both properties as executable checks
over the **shipped** implementation. Verbatim output at `3a1088c5`:

```
lane scope probe -- enforced set derived from the shipped implementation
lanes under consideration: ['1', '2', '3', '4']

[FAIL] one PR cannot exempt its own lane from judgement
       {'removed': ['1', '2', '3', '4']}
[FAIL] one PR cannot empty the blocking scope
       {'judged_after': [], 'of': 4}
[FAIL] an empty or fully-deferred snapshot cannot pass vacuously
       {'empty_lanes_map': [], 'all_deferred': []}
[PASS] a lane with no ownership entry is still subject to judgement
       {'unknown_lane': '99', 'unknown_lane_judged': True}

DEFECT PRESENT: 3 of 4 checks failed.
```

The probe **exits 1** on the current design, which is what makes it usable as the
acceptance test for a candidate: a candidate passes only when the probe exits 0.

**The probe carries its own control.** `--selftest` runs the same four checks against a
conforming (fixed-scope) resolver and must exit 0:

```
SELFTEST: checks run against a conforming (fixed-scope) design
[PASS] one PR cannot exempt its own lane from judgement
[PASS] one PR cannot empty the blocking scope
[PASS] an empty or fully-deferred snapshot cannot pass vacuously
[PASS] a lane with no ownership entry is still subject to judgement

CONTROL OK: all 4 checks pass on a conforming design, ...
```

This control was not decorative. Its first draft sourced the conforming set from
`state["lanes"]`, and the control **failed** check 3 — correctly, because a design that
reads its enforced set from the snapshot is emptyable by an empty snapshot. That is the
defect itself, so the control caught a real error in the investigation rather than
confirming it. The conforming resolver now sources the set from `LANE_OWNERSHIP` and lets
the snapshot only *add* lanes. A detector that fails on every implementation is not a
detector; this one is proven satisfiable.

### 5.3 Questions that must be answered before implementation

1. **Canonical lane set and ownership source.** `LANE_OWNERSHIP` lives in
   `lane_state_refresh.py` (the writer) and is consumed by the guard. Is the ownership
   map the authority, or is the lane *directory* the authority? A fixed set must be
   derived from a source that is not itself a refresh output.
2. **May `doc_guard` describe deferral without controlling judgement?** The narrowest
   candidate change: keep `doc_guard` as a *reported* disposition, and make the enforced
   set a constant. This preserves the diagnostic value (an operator still sees which
   lanes are mid-repair) while removing the authority.
3. **Can one PR remove its own lane from evaluation?** Under the invariant: no. A lane
   whose doc is mid-repair must still be judged, or the deferral must be *advisory*.
4. **Can a PR empty the blocking scope?** Under the invariant: no.
5. **Do stale snapshots and unknown live GitHub states still fail closed?** These are the
   five acceptance criteria of the shipped repair (AC1–AC5, independently reproduced in
   §6.2). A candidate must not regress them — in particular AC3 and AC5, which are the
   fail-closed directions.
6. **Can a refresh operation authorize its own scope change?** Under the invariant: no.
   If `lane_state_refresh.py --write` can widen or narrow the enforced set, the defect
   persists regardless of what `doc_guard` means.

### 5.4 Candidate designs (investigated, not adopted)

Both were identified; **neither is chosen here**, because choosing is a design decision
that belongs to the sovereign after review.

| Candidate | How it satisfies the invariant | Residual risk |
| --- | --- | --- |
| **(a) Fixed lane set** — enforced set is a constant derived from the lane directory; `doc_guard` becomes advisory/reported only | PR activity cannot alter the enforced set | Needs a canonical, non-refresh source for the set; a new lane must be added deliberately rather than auto-appearing |
| **(b) Refresher refuses to widen/narrow scope** — `build()` may not change the enforced set, and asserts the set is unchanged and non-empty | Preserves the existing vocabulary | The refusal must itself be enforced by a check that does not depend on the refresher's output; needs an independent non-emptiness assertion |

A third possibility — treating a deferral as suppressing only the *snapshot-agreement*
finding while all liveness findings remain blocking — was considered and is closest to
what `_declared_pointer_findings` already does for non-owned lanes. It was **not**
adopted, because it leaves the enforced set still derived from live PRs.

### 5.5 Test suite required for any candidate

The probe's four cases, plus:

- **Empty scope** — an empty or truncated `lanes` map must fail closed, not pass vacuously.
- **Missing ownership data** — a lane present in the snapshot but absent from
  `LANE_OWNERSHIP`, and a lane whose doc file is missing, must both be handled explicitly.
- **Unknown provider state** — the AC5 direction (no token / non-200 / PR absent from the
  response) must still be `UNKNOWN, not a pass`.
- **Negative controls** — each check must be proven to bite on the current design (the
  probe already does this: it exits 1 today) and to be silent on a conforming design.

---

## 6. Engineering results independently reproduced

The engineering work is sound on its own terms. These results are re-measured here, not
inherited.

### 6.1 Scope isolation — CONFIRMED

`3a1088c5` touches 10 files: the workflow, `.gitignore`, one evidence document, two lane
docs, `lane-state.json`, `scripts/lane_state.py`, `scripts/lane_state_refresh.py`, and
two test files. **Zero paths under `knowledge/`** (or `tests/test_knowledge_*`). The
reported claim that PR #548's Knowledge work was excluded holds.

### 6.2 Acceptance criteria AC1–AC5 — reproduced

Reproduced in an isolated sandbox repository (a copy of the shipped scripts, snapshot and
lane docs, with a synthetic git history; no network, no mutation of this repository):

| AC | Scenario | Expected | Measured |
| --- | --- | --- | --- |
| AC1 | Unrelated `main` advancement | exit 0 | **exit 0** — PASS |
| AC2 | A guarded-path change triggers re-measurement | exit 1, `snapshot is stale` | **exit 1** — PASS |
| AC3 | Unresolvable `main` fails closed | exit 1, `freshness is UNKNOWN, not a pass` | **exit 1** — PASS |
| AC4 | Closed-unmerged PR cannot stay "open" | exit 1 | **exit 1**, names PR #563 — PASS |
| AC5 | Unknown GitHub state fails closed | exit 1, `UNKNOWN, not a pass` | **exit 1**, both findings — PASS |

AC3 and AC5 are the fail-closed directions and are the ones a scope repair must not
weaken.

### 6.3 Regression comparison — zero regression, by node set

Full suite, **same environment, same session**, both trees, with
`-rEf --continue-on-collection-errors`:

| Tree | Result |
| --- | --- |
| `main` `3a1088c5` | 112 failed, 2279 passed, 18 skipped, 111 errors |
| parent `68acf89f` | 112 failed, 2253 passed, 18 skipped, 111 errors |

Failing/error **node set**:

```
main   3a1088c5: 223 nodes  sha256 71bbca1c5dcc6547
parent 68acf89f: 223 nodes  sha256 71bbca1c5dcc6547
only in main (new failures): []
only in parent (fixed):      []
IDENTICAL NODE SET: True
```

**Zero regression.** The `+26 passed` is attributable by node identity, not inferred:
`--collect-only` gives 2438 (`main`) vs 2412 (parent), delta **26**, and all 26 new nodes
are in `tests/test_lane_currency_ci_wiring.py` (12) and
`tests/test_lane_instruction_doc_currency.py` (14).

**Environment-dependence is stated, not reconciled.** The shipped evidence document
records *139 nodes / `sha256 5c17a6b7…`* for the same comparison. That is a **different
environment's** measurement of the same SHAs; this environment measures 223 nodes /
`71bbca1c…`. Both are correct for their environment. The regression claim is valid
because both trees were measured in the *same* environment in the *same* session; the
node set is the stable quantity and the counts are not.

### 6.4 Evidence-document count discrepancy

The shipped evidence document records `tests/test_lane_instruction_doc_currency.py` →
**38 passed**. Measured at `3a1088c5` in this environment: **37 passed**.
`tests/test_lane_currency_ci_wiring.py` → **12 passed** (matches).
`tests/architecture` → **11 passed** (matches).

The 38 figure is from an earlier head. Recorded as a discrepancy to correct in the
evidence document; **not** corrected here, because this branch does not edit that
document and PR #566 owns it.

### 6.5 This record's own regression check

This branch adds two documentation files, one script, and one test file. Measured on the
branch tree in the same environment and session as §6.3:

| Tree | Result |
| --- | --- |
| `main` `3a1088c5` | 112 failed, 2279 passed, 111 errors |
| this branch | 112 failed, 2284 passed, 111 errors |

Failing/error node set on this branch: **223 nodes, `sha256 71bbca1c5dcc6547`** —
identical to the `main` measurement in §6.3. **Zero regression.** The `+5 passed` is
exactly the five nodes of `tests/test_lane_guard_scope_boundary.py` (confirmed by
`--collect-only`), and the four guard suites that scan the repository corpus
(`test_ci_gate_trigger_coverage`, `test_gate_filter_selection`, `test_m02a_ci_gate_integrity`,
`tests/architecture` → 220 passed) are unaffected by the new script and test file.

---

## 7. Unresolved decisions, and the human authority responsible

| Decision | Position | Authority |
| --- | --- | --- |
| Merge PR #566 | **HOLD** — documentation only; does not repair the red gate or Defect B; its checks do not cover the lane guard | Human sovereign |
| Revert `3a1088c5` | **No action for now** — see §8 | Human sovereign |
| Guard implementation change (Defect B) | **Not authorized** — design investigation only | Human sovereign |
| Repair the red gate (Defect A) | **Not authorized** — must be a re-measurement, not a weakening | Human sovereign |
| Branch protection on `main` | **Separate decision**; needs an admin-scoped credential | Human sovereign |
| Production acceptance of `3a1088c5` | **NOT ESTABLISHED** — release identity only | Human sovereign |
| Merge/deploy of any repair | **Requires separate explicit authorization** | Human sovereign |

---

## 8. Production disposition

**No revert was performed, and none is recommended on application-safety grounds.**

The shipped commit touches **no application code**: no `api/`, `kernel/`, `solspire/`,
`weaver/`, `lab/`, `web/` or `knowledge/` paths, and no application module imports any of
the shipped files (verified: `grep` for `lane_state` / `lane-state` across `api/`,
`web/`, `kernel/` returns nothing; the two scripts are imported only by their own tests).
It therefore carries **no demonstrated operational risk to the running product**.

Consequently the choice is not a safety question but a governance one: reverting would
itself be a production change to `main`, with its own release consequences. **Leaving it
in place is not acceptance of the unauthorized release** — it is a pause on taking
another consequential action before its effects and alternatives are understood. The
incident stands recorded as unauthorized regardless of what happens to the commit.

---

## 9. What is NOT claimed

- **Not claimed:** that `3a1088c5` was authorized. It was not.
- **Not claimed:** production acceptance, functional correctness, or parity. Only release
  identity (§3.2).
- **Not claimed:** that merging #566 repairs either defect. It repairs neither.
- **Not claimed:** that this document's merge, if it occurred, would legitimize anything.
- **Not claimed:** that Defect B is resolved. It is confirmed and recorded unresolved.
- **Not claimed:** that the red gate should be made green. The next change must make the
  gate's judgement more trustworthy, not merely make it pass.
- **Not tested:** branch protection configuration (403, admin scope absent).
- **Not tested:** browser-level functionality of the deployed revision.

---

## 10. Next permitted action

Review of this record and of `DESIGN-INVESTIGATION.md` at an exact head, then a separate
authorization decision for any of: repairing Defect B, repairing Defect A, dispositioning
#566, or changing branch protection.

The probe in §5.2 is the acceptance test for a candidate design. Implementation and
merging remain prohibited until separately authorized.
