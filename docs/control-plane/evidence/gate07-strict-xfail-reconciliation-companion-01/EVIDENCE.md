# GATE-07 — strict-xfail reconciliation companion

**Workstream:** `gate07/strict-xfail-reconciliation-companion-01`
**Base:** `main` @ `74e8ea53a30213db8783e6733679d2f11903de0b`
**Class:** IMPLEMENTED — composition artifact; not mergeable as a partial.
**Authority:** Architect owns authority; Weaver selected the move; human reviews and merges.

## 1. The conflict, measured

Three open GATE-07 PRs each pass in isolation and cannot compose:

| PR | Change | In isolation |
|----|--------|--------------|
| #329 | adds `tests/test_worker_attention_composition.py`, which records the clean-stop defect as a `strict=True` xfail, and wires the guard into `weaver-mvp2-validation.yml` | 5 passed, 1 xfailed |
| #342 | repairs the clean-stop defect in `weaver/engineering_router.py` (introduces `CLEAN_STOP_BLOCKER`, imported by `weaver/attention_bus.py`) and adds `tests/test_router_clean_stop_contract.py` | green |
| #343 | adds `tests/test_gate07_strict_xfail_composition_reconciliation.py`, which asserts the xfail and its repair cannot coexist | green |

`strict=True` declares that the node *must* fail. #342 lands exactly the event the
declaration says will turn the node green, so the node becomes an `XPASS(strict)` — a
failure. #343 then fails on top, because it asserts the conflict is resolved.

Measured on a faithful composed tree (`#329` + `#342` + `#343`, including #329's workflow
edits and #343's evidence file):

```
FAILED tests/test_worker_attention_composition.py::test_clean_completion_stays_quiet_through_the_worker
FAILED tests/test_gate07_strict_xfail_composition_reconciliation.py::test_a_strict_xfail_and_its_repair_cannot_coexist
2 failed, 21 passed
```

The composition is red in every order. Merging any subset leaves `main` red or leaves the
reconciliation unstated.

## 2. Reconciliation, per #343's own guard

#343 states the two legal repairs: *re-materialize the node as a strict quiet-stop
assertion, or drop the repair*. The repair (#342) is the wanted behaviour, so the node is
re-materialized:

* the `@pytest.mark.xfail(strict=True, ...)` decorator is removed from
  `test_clean_completion_stays_quiet_through_the_worker`;
* the docstring records why (the sentinel now carries the clean stop), replacing the
  "recorded defect" rationale.

The assertion body is **unchanged**. The node asserted the correct behaviour all along —
it was pinned as a known failure only because the repair had not landed.

## 3. Verification on this tree

| Check | Result |
|-------|--------|
| GATE-07 guard set (`status_truthfulness`, `attention_truthfulness`, `worker_attention_composition`, `router_clean_stop_contract`, `strict_xfail_composition_reconciliation`, `engineering_scheduler_bootstrap`, `scheduler_trajectory_conformance`) | **69 passed, 1 skipped** |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | OK (2434 lines, budget 2600) |
| Full suite `-q -rEf --continue-on-collection-errors` | **10 failed, 1725 passed, 21 skipped, 1 error** |

Baseline `main` @ `74e8ea5`, same command: **10 failed, 1703 passed, 20 skipped, 1 error**.
The failing/error node set is **identical** (10 names + `ERROR tests/test_autonomy.py`, the
pre-existing CE-01 collection error). Delta is `+22 passed / +1 skipped` — exactly the 22
new guard nodes this tree adds (1 skipped). **Zero regression.**

## 3b. CI on the PR head `30bccef` — Provider Routing is pre-existing red

| Workflow | Result |
|----------|--------|
| Weaver MVP2 validation | **success** |
| Arkadia Engineering Scheduler | success |
| Full-history secret scan | success |
| Vercel Preview Comments | success |
| Provider Routing Verification | **failure** |

`provider-routing.yml` is path-filtered to `weaver/**`, so this branch triggers it. Its
`Broader test suite` step fails on a **14-node set that is byte-identical to the same
workflow's failure on `main`** (`17e626cd`, run `37539664677`, 2026-10-06):

```
test_agents_md_encoding_adjudication.py  (4 nodes)   test_solspire_r1_governance_convergence.py (2)
test_ais_capability_profile_onboarding.py (1)        test_solspire_r3_execution_runtime.py      (1)
test_ais_w2_living_gate_grove_handoff.py  (1)        test_steward_filter.py                     (3)
test_identity_spine_w1.py                 (1)        ERROR tests/test_autonomy.py (CE-01 collection)
test_m02_reasomate_truth.py               (1)
```

Zero node delta. This is baseline debt the contract says to **record, not fix** inside an
unrelated gate. It is not attributable to this branch.

**Re-confirmed on the pass-3 head `e4458ee`.** `provider-routing` failed on `Broader test
suite` again (run `37657222572`, job `112915289014`): `14 failed, 1721 passed, 21 skipped,
1 error`. Its failing/error node set is **byte-identical** to the same workflow's failure on
`main` (`17e626cd`, run `37539664677`): sha256 `093938e8aa68086d838772a048564f44239643da7122401f697aa201573c4ce8`
on both sides, 15 nodes. The four `test_agents_md_encoding_adjudication` nodes in that set
are **clone-depth dependent** — they do not fail on a full local clone (absent from both the
`main` and composed-tree full-suite logs here), so the AGENTS.md lesson in §6 does not
introduce them. All other checks on `e4458ee` are green (mvp2-validation, engineering-scheduler,
Full-history secret scan, Vercel Preview Comments).

## 4. What this branch is — and is not

This branch is the **reconciled composition** of #329 + #342 + #343. It is a companion
artifact, not a replacement for the three PRs: it exists so the reconciliation is a single
reviewable, green unit. The three PRs remain open and unmerged.

**Merge instruction (Architect):** merge this PR **instead of** #329, #342, #343 — merging
all four would double-apply the same files. #343's guard is satisfied by this tree, so it
is not dropped: it lands here, passing.

**Correction (pass 3):** #330 is the *verification record for #329* — it is part of this
seam, not orthogonal to it, and an earlier revision of this section grouped it with the
unrelated batch. It is now folded in here (its two evidence files are added verbatim), so
this branch is the composition of #329 + #330 + #342 + #343. Not included: #341's batch of
the remaining GATE-07 PRs (#331–#336), which are orthogonal to this seam and carry their
own composition review.

## 5. Provenance

* `main` base: `74e8ea53a30213db8783e6733679d2f11903de0b`
* #329 head / #342 head / #343 head: composed verbatim; the only edit to any of them is
  the xfail removal described in §2.
* Confirmed `main` carries neither `CLEAN_STOP_BLOCKER` nor any of the three guard files,
  so this branch does not depend on an unapplied change.

## 6. Pass 3 — #330 folded in, #343 lesson landed, re-measured

Two gaps in the pass-2 artifact are closed here.

**(a) #330 was omitted.** #330 is the independent *verification record* for the #329 seam
(its authority is verification + evidence only — no code change, no merge, no push). It is
part of this seam, so its two evidence files are added verbatim. #344 §4 previously listed
it with the orthogonal #331–#336 batch; that grouping was wrong and is corrected above.

**(b) #343's `AGENTS.md` lesson had not landed on this branch.** #343's substance is the
durable lesson in `AGENTS.md`, not only its guard test (which §2 already satisfies). The
lesson is now applied. It is a pure insertion — the encoding audit reports
`alterations=0`, `reproduced=True`, Cyrillic `0 -> 0` — so it does not violate the
standing insertion-only constraint on the live `AGENTS.md`.

Re-measured on this tree (`main` @ `74e8ea5` + #329 + #330 + #342 + #343 + #344):

| Check | Result |
|-------|--------|
| `pytest tests/architecture -q` | **11 passed** |
| GATE-07 guard set (7 files) | **53 passed, 1 skipped** |
| `python -m py_compile api/main.py` | OK (2434 lines, budget 2600) |
| `AGENTS.md` encoding audit | Cyrillic `0 -> 0`, insertions-only, `alterations=0` |
| Full suite vs `main` @ `74e8ea5` | failing/error node set **identical** (`f3e73647…`, 11 nodes); delta `+22 passed / +1 skipped` |

The full-suite node-set identity is the load-bearing claim: the composed tree introduces
no failing node that `main` does not already carry, and the `+22 passed` is exactly the new
guard nodes.

## 7. Merge disposition (Architect authority — recommendation only)

Merge **#344** and close **#329, #330, #342, #343** as superseded. Merging #344 *and* any of
those four would double-apply the same files. #330 is verification-only, so closing it
loses no code — its record is preserved verbatim inside #344.
