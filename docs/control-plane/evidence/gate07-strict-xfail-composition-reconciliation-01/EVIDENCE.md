# EVIDENCE — gate07/strict-xfail-composition-reconciliation-01

Trajectory: `ARKADIA-CONSOLE-COMPLETION-01` (GATE-07 — router / attention composition)
Move class: bounded verification + decision record (no gate promotion, no authority change,
no mutation of any subject PR)
Branch: `gate07/strict-xfail-composition-reconciliation-01`
Base: `main` @ `74e8ea53a30213db8783e6733679d2f11903de0b`
Subject PRs: #329 (base `4587890`, head `9c7c57644f1b383ca644fc2cd99d3375e6133112`)
and #342 (base `74e8ea53`, head `55ad358cf9fc17f824cf1967f0cbe0afc21e100e`)

## Defect (composition, not isolation)

Two open GATE-07 PRs are each green alone and **cannot both be merged in either order**:

| Revision | Result |
|---|---|
| `#329` alone (`/tmp/wt329`) | 5 passed, 1 xfailed |
| `#342` alone | 11 passed / 11 (its own guard), suite takes `-1 failed` |
| **`#329` + `#342`'s `weaver/` patch** | **1 failed (strict XPASS), 5 passed** |

`#329` pins the worker→attention seam end-to-end and records the clean-stop defect as a
`@pytest.mark.xfail(strict=True)` (file sha256 `ebf81a50ccac635bda70a4c44be03724086415fb562f6d8ae14cac9c81dd05ef`).
Its own reason text says so: *"…a strict xfail flips to a failure when it lands."*
`#342` **is** the repair that lands it: `weaver/engineering_router.py` begins emitting
`CLEAN_STOP_BLOCKER` instead of the plain "no legal pending move" blocker, so
`test_clean_completion_stays_quiet_through_the_worker` (which asserts
`any("no legal pending move" in b for b in result["blockers"])`) no longer passes, and the
strict xfail turns into a **strict XPASS failure**.

Reproduction (measured this pass):

```
git worktree add --detach /tmp/wt329 pr329
git diff origin/main pr342 -- weaver/engineering_router.py weaver/attention_bus.py > /tmp/pr342_weaver.patch
cd /tmp/wt329 && git apply /tmp/pr342_weaver.patch        # APPLIED CLEAN
python -m pytest -q tests/test_worker_attention_composition.py
# -> 1 failed (XPASS(strict)), 5 passed
```

`#342`'s own PR comment asserts the suite moves `10 failed -> 9 failed` when applied to
`main`. That measurement is correct **for `main` alone** — it counts the xfail as an
*expected* failure that the repair resolves. It does **not** see `#329`, whose xfail is
strict and therefore fails precisely when the repair succeeds. The two measurements are
both true and describe different trees; the divergence is the defect.

## Decision (the reconciliation rule)

The two PRs are serializable **only** with a companion change to `#329`:

1. `#329`'s `strict=True` xfail must be **re-materialized** as a strict *positive* assertion
   that the clean stop stays quiet (the repair has now made that assertion true).
   The pre-repair literal is preserved verbatim as `PRE_REPAIR_GUARD_TEXT` in
   `tests/test_gate07_strict_xfail_composition_reconciliation.py` so the original node
   identity and the recorded defect remain reconstructable.
2. Merge order: **`#329` (with its companion change) then `#342`**, or a single composed
   PR. Merging `#342` first leaves `#329` non-mergeable until that companion change lands.

Neither PR may be mutated by this workstream. This pass is `main`-based, additive, and
touches no subject PR.

## Guard (executable, and wired)

`tests/test_gate07_strict_xfail_composition_reconciliation.py` encodes the invariant:

* `test_a_strict_xfail_and_its_repair_cannot_coexist` — the live repository revision must
  not hold `CLEAN_STOP_BLOCKER` in `weaver/engineering_router.py` **and** a strict xfail in
  `tests/test_worker_attention_composition.py` at the same time.
* `test_detector_flags_the_known_pre_repair_pair` — **negative control**: the detector
  reports the measured pre-repair combination (it cannot be disarmed by editing the
  detector to return `None` unconditionally).
* `test_detector_is_silent_when_the_repair_is_absent` — **positive control**.
* `test_recorded_xfail_reason_declares_the_flip` — the premise is #329's own reason text.
* `test_reconciliation_decision_is_recorded` — the rule must live in-repo.
* `test_embedded_pre_repair_literal_matches_the_recorded_guard` — self-check that the
  embedded literal byte-equals the guard `#329` actually wrote (extraction anchored on the
  strict-xfail marker; skips while `#329` is unmerged). Verified byte-equal against
  `git show pr329:…` this pass.

## CI liveness

`weaver/**` is a `pull_request` path filter for **both** `provider-routing.yml` (which runs
the whole suite with `-rEf --continue-on-collection-errors`) and `weaver-mvp2-validation.yml`
(whole suite). This guard imports no `weaver` module, so it does not affect
`test_engineering_lab`-style file guards, but its assertion is judged by any workflow
running the suite — and both are selected by the `weaver/**` filter once a companion change
touches `weaver/`, which is exactly when the reconciliation matters.

## Test results

`python -m pytest -q -rEf tests/test_gate07_strict_xfail_composition_reconciliation.py`
on this branch: **5 passed + 1 skipped** (the literal self-check skips on a bare `main`
clone where `#329` is unmerged; with `#329`'s file present it is 6 passed — both measured).
With the `#329` guard absent at this revision, 4 of 5 checks still execute, including both
controls.

Full suite, this branch (`python -m pytest tests/ -q -rEf --continue-on-collection-errors`):

```
10 failed, 1708 passed, 21 skipped, 1 error in 140.69s
fingerprint  f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48  (outcomes)
             92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413  (ids)
```

The failing/error node-set is **identical** to `main`'s recorded baseline
(`f3e73647…` / `92d344d0…`): zero node-set regression. The 10 failures are the documented
pre-existing debt (`tests/test_steward_filter.py` et al.); the 1 error is the pre-existing
CE-01 `weaver.autonomy` module-vs-package collision. Architecture fitness: **11 passed**.

Detector liveness proven both ways:

```
on this branch (repair absent, strict xfail absent)   -> 5 passed, 1 skipped
on the composed tree #329 + #342's weaver/ patch      -> 1 failed
   "weaver/engineering_router.py carries the clean-stop repair while … still
    records the clean-stop defect as a strict xfail; the guard will fail as a
    strict XPASS."
```

Regression boundary: additive files only. No `weaver/`, no `api/`, no workflow, no subject
PR is modified. The live full-suite failing node-set is therefore expected to be unchanged;
the guard adds one node.

## CI diagnosis — `Provider Routing Verification` is red on the baseline, not on a PR

Measured this pass (read-only, GitHub API):

* The only failing run on record is run `37539664677`, `head_sha`
  `17e626cd27f8ea1e31f711fb787e6c7e5027ec70` — the **merge of PR #333**, an ancestor of
  current `main` (`74e8ea53`). It was `event: workflow_dispatch`, `pull_requests: []`, so it
  is not judging any open PR's head.
* Steps 6 (`Targeted K2 and key-pool regressions`) and 7 (`Relevant architecture regression`)
  **succeed**. The failure is step 8, `Broader test suite`, which runs
  `python -m pytest tests/ -q -rEf --continue-on-collection-errors`.

That step is structurally red for **any** revision carrying the documented baseline debt: the
suite exits non-zero on 10 pre-existing failures + 1 collection error, and the step has no
`continue-on-error` and no tolerance. There is no commit whose suite is green, so a red
`Provider Routing Verification` on `main` is the baseline, not a regression. Confirming the
failing node-set locally reproduces `main`'s recorded fingerprint `f3e73647…` (see above),
so no open PR's head is implicated.

Consequence for the batch: a PR whose path filter selects this workflow (any `weaver/**`
change) cannot obtain a green `Provider Routing Verification` without either (a) repairing
the baseline debt — a separate bounded workstream, explicitly out of scope here — or
(b) making the workflow's `Broader test suite` step a **reported** diagnostic rather than a
hard gate, which is a CI-contract change and therefore sovereign-gated. Neither is executed
by this pass; this is a diagnosis, not a proposed patch.

## Remaining uncertainty

* The reconciliation rule is a **decision record**, not an implementation. Materializing
  the companion change to `#329` requires touching a subject PR, which is outside this
  workstream's authority — it is handed to the sovereign.
* The GATE-07 batch (`#329`, `#331`, `#332`, `#334`, `#335`, `#336`) composed by `#341`
  omits `#342`. If a batch merge is attempted, the strict-xfail constraint above applies.
