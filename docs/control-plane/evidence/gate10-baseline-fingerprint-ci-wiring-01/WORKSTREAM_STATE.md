# Workstream state — gate10/baseline-fingerprint-ci-wiring-01

**Gate:** GATE-10 (Governed Execution) — gate hygiene / CI wiring
**BASE_MAIN:** `24a00f856a0286cbb464a4b585117dd57a2646fa`
**Branch:** `gate10/baseline-fingerprint-ci-wiring-01`
**Status:** IMPLEMENTED — awaiting sovereign merge
**Owner:** Weaver pass (OpenHands execution); merge is human-only.

## Deterministic next-action block

```
CURRENT STATE
  A new workflow `.github/workflows/baseline-fingerprint.yml` executes
  `tests/test_baseline_fingerprint.py` (previously hand-run only), and
  `tests/test_baseline_fingerprint_ci_wiring.py` states the wiring invariant
  generically over every workflow that runs the guard.

EVIDENCE
  docs/control-plane/evidence/gate10-baseline-fingerprint-ci-wiring-01/EVIDENCE.md
  guard + wiring suite      : 33 passed (24 guard + 9 wiring), CI-shaped, no PYTHONPATH
  architecture fitness      : 11 passed
  full suite                : 16F / 1786P / 22S / 1E — node set identical to main
  cp10 --judge on change set: PASS
  negative controls         : 5, each restored after measurement

BLOCKERS
  None owned by this workstream. Seven pre-existing failures on main are recorded,
  not repaired (EVIDENCE.md §7): four owned elsewhere (PR #354 deploy/ allowlist;
  PR #355 n-atlas-developer-lab.yml trigger filter) and three unowned drift whose
  repair would touch an authority surface (api/lab_routes.py) and is sovereign-only.

CORRECTED THIS PASS
  The guard pins the FIXTURE to a published fingerprint; it does not measure live.
  Live main reports 17 failing/error nodes, the recorded set holds 10, and the guard
  passes on both. EVIDENCE.md §1, §3, §7 and the workflow header comment carried the
  opposite claim and were corrected. See EVIDENCE.md §7.3.

AUTHORIZED ACTION
  Sovereign review and merge of this PR. No further mutation is required.

FORBIDDEN ACTIONS
  Merge (human-only). Touching `scripts/cp10_mutation_boundary_policy.py`
  (PR #354 owns it). Repairing the seven pre-existing failures, in particular the two
  `tests/test_engineering_lab_api.py` pins — those need an authority-surface change.
  Widening the workflow's trigger filter beyond the guard's actual inputs.

COMPLETION CONDITION
  PR merged, `baseline-fingerprint.yml` present on `main`, and a
  `pull_request` run of the workflow observed as executed (not merely declared).
```

## Follow-on work identified, NOT executed

1. **`docs/phase1/CONTINUATION_LEDGER.md` is a guard input but nothing regenerates it.**
   If a future pass changes the canonical fingerprint, the guard reddens on that document
   and a human must edit it. A bounded follow-on could give the document a generator so
   the fingerprint is written rather than hand-copied. Not in scope here.
2. **The seven pre-existing failures.** Four owned by PR #354 / PR #355. The three unowned
   drift nodes (EVIDENCE.md §7.2) are a separate bounded workstream: two of them require an
   authority-surface change and are sovereign-only. Do not touch inside this pass.
3. **The guard does not measure live, so the recorded set can be stale undetected.**
   EVIDENCE.md §7.3. A bounded follow-on could add a live-measurement mode (or a separate
   non-CI assertion) that fails when the fixture and a live run disagree, or that reports
   the disagreement as an explicit advisory rather than silence. Not in scope here: it
   changes what the guard asserts, and the guard's current pins are the subject of the
   superseded-fingerprint work already recorded in `AGENTS.md`.
