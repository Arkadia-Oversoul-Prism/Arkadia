# Lane-Guard Authority Boundary — Bounded Design Investigation

**Companion to:** `INCIDENT.md` (same directory).
**Base revision:** `3a1088c54a354d76958a05511cb9d7bade9f3dc9`.
**Status:** **INVESTIGATION ONLY. No implementation. No merge authority.**

> This document establishes an invariant, the questions that must be answered before any
> implementation, the candidate designs identified, and an executable probe that judges a
> candidate. It does **not** change the guard, does not repair the red gate, and does not
> authorize either. Choosing among the candidates is a sovereign design decision.

---

## 1. The invariant

> **I1 — PR activity cannot alter the enforced set.**
> The set of lanes subject to governance checks must not be widened or reduced by the
> live PR activity being evaluated.

> **I2 — The enforced set cannot be emptied.**
> The effective blocking scope must remain non-empty under adversarial input.

I2 is required as a *separate* property because I1 admits a degenerate satisfaction.
Fixing the enforced set to a constant satisfies I1 trivially, while a snapshot that is
empty, truncated, or fully deferred can still leave nothing to judge — a guard that
examines nothing and reports success. I1 alone would call that conforming.

A third property is implied by the two and worth stating because it is the direction the
current defect moves in:

> **I3 — Fail closed.** Any inability to establish the enforced set is a finding, not a
> pass.

---

## 2. Why the current design violates I1

The enforced set is computed from the snapshot's `doc_guard` field, and `doc_guard` is
computed from live open PRs:

```
lane_state_refresh.build()
    lane["doc_guard"] = "deferred" if lane.get("deferred_to_pr") else "current"
        ^ deferred_to_pr is set when an OPEN PR touches
          (one of this lane's owned code paths) AND (this lane's doc)

lane_state.current_lanes(state)
    -> only lanes whose doc_guard == "current"
        ^ this is the enforced set

lane_state.check_lane_docs(..., lanes=current_lanes(state))
lane_state.main() -> _declared_pointer_findings(..., lanes=owned)
```

So: **an open PR touching a lane's code path and that lane's doc removes the lane from
judgement.** No approval, no review, no human step.

### 2.1 Measured, not inferred

`scripts/lane_scope_probe.py` (read-only) judges the shipped implementation:

| Check | Result on shipped design |
| --- | --- |
| One PR cannot exempt its own lane from judgement | **FAIL** — removes lanes `['1','2','3','4']` |
| One PR cannot empty the blocking scope | **FAIL** — `judged_after: []` of 4 |
| An empty or fully-deferred snapshot cannot pass vacuously | **FAIL** — `[]` in both cases |
| A lane with no ownership entry is still subject to judgement | PASS |

Three of four checks fail. The probe's own control (`--selftest`) passes all four against
a conforming resolver, so the failures are attributable to the implementation and not to
an unsatisfiable check.

### 2.2 The shipped commit is an instance of the defect

`3a1088c5` appends to `AGENT-02-NOVANET-OPPORTUNITY.md` — **lane 2's own doc** — moving
lane 2 from `idle` to `current`. The shipped evidence document states the reason (§8.2):
the guard *"began blocking on it."* That is the guard's own scope being resolved by the
workstream that authored the guard, and the document records the tension as unresolved:

> a gate whose blocking scope is derived from a field its own refresher writes can widen
> its own teeth

This investigation treats that statement as the defect to be designed away.

---

## 3. Questions that must be answered before implementation

| # | Question | Why it blocks implementation |
| --- | --- | --- |
| Q1 | **What is the canonical lane set and its ownership source?** `LANE_OWNERSHIP` currently lives in `lane_state_refresh.py` — the writer. Is the ownership map the authority, or is the lane directory? | A fixed set must derive from a source that is not itself a refresh output, or the defect reappears one level up |
| Q2 | **May `doc_guard` describe deferral without controlling judgement?** | This is the narrowest candidate change; it must be decided explicitly rather than left implicit in code |
| Q3 | **Can one PR remove its own lane from evaluation?** | Must be **no**. A lane mid-repair must still be judged, or the deferral must be advisory only |
| Q4 | **Can a PR empty the blocking scope?** | Must be **no** |
| Q5 | **Do stale snapshots and unknown live GitHub states still fail closed?** | AC3 and AC5 are the fail-closed directions; a scope repair must not regress them |
| Q6 | **Can a refresh authorize its own scope change?** | Must be **no**. If `lane_state_refresh.py --write` can alter the enforced set, the defect persists regardless of `doc_guard`'s meaning |

Q6 is the sharpest. It is why a fix confined to `lane_state.py` is likely insufficient:
the writer and the reader must agree on where the enforced set comes from, and the writer
must not be able to change it.

---

## 4. Candidate designs

Investigated, **not adopted**. Presented with their residual risk so the choice is
informed.

### (a) Fixed lane set from a constant; `doc_guard` becomes advisory

The enforced set is derived from `LANE_OWNERSHIP` (or the lane directory), not from the
snapshot. `doc_guard` remains as a *reported* disposition so an operator still sees which
lanes are mid-repair.

- Satisfies I1: PR activity cannot alter the set.
- Satisfies I2: the set is a constant, non-empty by construction.
- Residual risk: needs a canonical non-refresh source (Q1); a new lane must be added
  deliberately rather than appearing automatically. That is a feature, not a bug, for a
  governance gate — but it must be an explicit decision.
- **Narrowest version:** keep the entire existing vocabulary and diagnostics, and change
  only where the enforced set comes from. This is the smallest change that satisfies the
  invariant, and it is why (a) is the clearest initial candidate.

### (b) Refresher refuses to widen or narrow scope

`build()` may not change the enforced set, and asserts the set is unchanged and non-empty.

- Preserves the existing vocabulary entirely.
- Residual risk: the refusal must itself be enforced by a check that does not depend on
  the refresher's output. If the only thing preventing a scope change is the refresher's
  own assertion, then a change to the refresher is a change to the guard's teeth — the
  same self-reference, one level down. Needs an independent non-emptiness assertion.

### (c) Deferral suppresses only the snapshot-agreement finding (considered, not adopted)

Treat a deferral as suppressing only the *snapshot-agreement* finding, while all liveness
findings remain blocking. This is close to what `_declared_pointer_findings` already does
for non-owned lanes, and it has real precedent in the codebase.

- **Not adopted**, because it leaves the enforced set still derived from live PRs. It
  narrows the damage rather than removing the mechanism, and I1 would remain violated.

---

## 5. Acceptance test for any candidate

`scripts/lane_scope_probe.py` is the acceptance test. A candidate passes only when:

1. `python scripts/lane_scope_probe.py` exits **0** (all four checks pass), **and**
2. `python scripts/lane_scope_probe.py --selftest` exits **0** (the checks remain
   satisfiable — the control must not be broken by the repair).

Requirement 2 matters: it is not enough for the shipped checks to pass. If a repair makes
the checks pass by making them vacuous, the control detects it.

### 5.1 Additional tests required before implementation is accepted

The probe covers the invariant. A complete suite also needs:

- **Empty scope** — an empty or truncated `lanes` map must fail closed (probe check 3).
- **Missing ownership data** — a lane in the snapshot but absent from `LANE_OWNERSHIP`,
  and a lane whose doc file is missing (probe check 4; `check_lane_docs` already reports
  a missing doc, which must not become a skip).
- **Unknown provider state** — the AC5 direction: no token, non-200, PR absent from the
  response → `UNKNOWN, not a pass`.
- **AC1–AC5 regression** — the five criteria independently reproduced in `INCIDENT.md`
  §6.2 must still hold, particularly AC3 and AC5.
- **Negative controls** — each new check must be proven to bite on the current design and
  be silent on a conforming one. The probe already demonstrates both directions.

### 5.2 What must NOT be done to make the gate green

Recorded because it is the tempting wrong move. The gate on `main` is red (`INCIDENT.md`
§4.1) and none of the following repairs it:

- refreshing the snapshot to erase the stale #563 pointer without re-measuring the lane
  PRs — this hides the symptom while leaving the pointers dead;
- broadening deferral so more lanes are excluded — this *is* the defect;
- weakening or removing the check — this trades a red gate for a false one.

The correct repair is to re-measure the lane PRs and re-point the lanes, which is a
separate bounded change from this investigation and is not authorized here.

---

## 6. What this document does not do

- It does not change `scripts/lane_state.py` or `scripts/lane_state_refresh.py`.
- It does not change the snapshot, the lane docs, or the workflow.
- It does not repair the red gate, and it does not make anything green.
- It does not select a candidate design.
- It does not authorize implementation or merging.

Implementation is a separate reviewed scope. The probe exists so that scope can be judged
by measurement rather than by argument.
