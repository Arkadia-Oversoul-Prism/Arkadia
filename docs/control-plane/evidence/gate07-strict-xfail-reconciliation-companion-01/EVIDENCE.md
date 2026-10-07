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

## 4. What this branch is — and is not

This branch is the **reconciled composition** of #329 + #342 + #343. It is a companion
artifact, not a replacement for the three PRs: it exists so the reconciliation is a single
reviewable, green unit. The three PRs remain open and unmerged.

**Merge instruction (Architect):** merge this PR **instead of** #329, #342, #343 — merging
all four would double-apply the same files. #343's guard is satisfied by this tree, so it
is not dropped: it lands here, passing.

Not included: #341's batch of the other six GATE-07 PRs (#330–#336). Those are orthogonal
to this seam and carry their own composition review.

## 5. Provenance

* `main` base: `74e8ea53a30213db8783e6733679d2f11903de0b`
* #329 head / #342 head / #343 head: composed verbatim; the only edit to any of them is
  the xfail removal described in §2.
* Confirmed `main` carries neither `CLEAN_STOP_BLOCKER` nor any of the three guard files,
  so this branch does not depend on an unapplied change.
