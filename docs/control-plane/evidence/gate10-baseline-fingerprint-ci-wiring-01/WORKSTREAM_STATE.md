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
  None owned by this workstream. Four pre-existing failures on main are owned
  elsewhere (PR #354 deploy/ allowlist; PR #355 n-atlas-developer-lab.yml
  trigger filter) and are recorded, not repaired, in EVIDENCE.md §7.

AUTHORIZED ACTION
  Sovereign review and merge of this PR. No further mutation is required.

FORBIDDEN ACTIONS
  Merge (human-only). Touching `scripts/cp10_mutation_boundary_policy.py`
  (PR #354 owns it). Repairing the four pre-existing failures. Widening the
  workflow's trigger filter beyond the guard's actual inputs.

COMPLETION CONDITION
  PR merged, `baseline-fingerprint.yml` present on `main`, and a
  `pull_request` run of the workflow observed as executed (not merely declared).
```

## Follow-on work identified, NOT executed

1. **`docs/phase1/CONTINUATION_LEDGER.md` is a guard input but nothing regenerates it.**
   If a future pass changes the canonical fingerprint, the guard reddens on that document
   and a human must edit it. A bounded follow-on could give the document a generator so
   the fingerprint is written rather than hand-copied. Not in scope here.
2. **The four pre-existing failures.** Owned by PR #354 / PR #355. Do not touch.
