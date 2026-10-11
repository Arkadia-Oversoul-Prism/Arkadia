# GATE-10 — ADR-016 static-corpus freshness + executable guard wiring

## Bounded objective

Repair the test-side frozen-literal pin that reddened `main`, and close the recurring
"guard no workflow executes" defect class for that guard.

## Evidence-backed defect

1. **Frozen snapshot contradicts a live glob.** `knowledge/static_ingestion.py`
   declares the ADR source with `"glob": "*.md"` over `docs/adr`. ADR-016
   (`docs/adr/ADR-016-single-canonical-deployment.md`, added `ba3c7b57`) is a valid
   record the glob already selects. `tests/test_static_ingestion_sources.py::test_adr_source_root_resolves_and_holds_the_records`
   asserted the corpus was **exactly** a six-name list, so it failed on a corpus the
   declared source legitimately holds. The literal was the defect; the source was not.

2. **The guard was executed by no gate.** `grep -rn test_static_ingestion
   .github/workflows/` returned **0**. It held only when a human ran the suite by hand —
   the defect class this repository already names ("a guard no workflow executes is
   decoration"), previously closed for `test_boot_syntax_boundary.py`,
   `test_baseline_fingerprint.py`, and `test_solspire_route_composition.py`.

## Scope / files changed

| Path | Change |
| --- | --- |
| `tests/test_static_ingestion_sources.py` | Assert the *property* (non-empty corpus of `ADR-\d{3}-*.md`, retaining the recorded history) instead of a frozen list. `import re`. |
| `.github/workflows/static-ingestion-corpus.yml` | New execution surface. Path-filtered to the guard's derived inputs; `workflow_dispatch` added so it runs at an exact revision. |
| `tests/test_static_ingestion_corpus_ci_wiring.py` | New guard. States the execute/dispatch/filter/`continue-on-error` invariant generically over every workflow that mentions the contract; derives its filter selectors from `knowledge.static_ingestion._SOURCES` by import rather than restating them. |
| `docs/control-plane/evidence/gate10-adr-016-static-corpus-freshness-01/EVIDENCE.md` | This record. |

**Non-goals (not touched):** `test_m02_reasomate_truth.py` (frozen
`archive/frontend/arkadia-prism/...` path, separate workstream);
`test_no_firebase_persistence_in_gate` (FINDING F-01 proxy-invalidation, sovereign
decision); `api/main.py`; the `/api/version` ADR-016 probe.

## Commands and measured results

- Detector bite (live negative control): mutate the **real** workflow's executing step to
  `echo pytest tests/test_static_ingestion_sources.py` → wiring guard `2 failed, 10 passed`;
  restore byte-identically (`sha256sum -c` → OK) → `12 passed`.
- Guard file: `python -m pytest tests/test_static_ingestion_sources.py tests/test_static_ingestion_corpus_ci_wiring.py -q` → **22 passed**.
- Whole-corpus scanning suites unaffected: `test_m02a_ci_gate_integrity.py`,
  `test_ci_gate_trigger_coverage.py`, `test_workflow_injection_boundary.py`,
  `test_ci_suite_collection_continuation.py`, `tests/architecture` → 1 failed
  (pre-existing `openapi-security-metadata.yml` push/pull_request filter asymmetry,
  owned by PR #454), 243 passed. The new workflow's two filters are byte-identical.
- `python -m py_compile api/main.py` → clean. `api/main.py` untouched.
- Full suite (`-q -rEf --continue-on-collection-errors`): `18 failed, 2631 passed,
  20 skipped, 1 error`.

## Regression boundary — node identity, not totals

| Tree | Failing/error nodes | sha256 |
| --- | --- | --- |
| `main` (`36df0ea8`) | 20 | `6cd8bea1f7a4387f716e766a22704954b8bafd363396e95b12a0b02b80fc5dac` |
| branch, repair only | 19 | `477873bca14ef274fb1af87f9aa175ec3e3f95dde53000956d585bb4df149eff` |
| branch, repair + wiring | 18 | `477873bca14ef274fb1af87f9aa175ec3e3f95dde53000956d585bb4df149eff` |

`comm -3` between the after-wiring node set and the repair-only node set is **empty** —
zero regression. The one removed node vs `main` is exactly
`test_static_ingestion_sources.py::test_adr_source_root_resolves_and_holds_the_records`.

The `+17 passed` is **attributed by `--collect-only`**, not inferred from the delta:
+12 new wiring-guard nodes, plus +5 parametrizations the generic workflow-scanner suites
gain by construction (trigger coverage 75→78, injection boundary 41→42, continuation
44→45) — a new workflow file enters three `glob(".github/workflows/*.yml")` domains.

## Remaining uncertainty / authorization boundary

- The repair and its wiring are repository-source claims. CI execution of
  `static-ingestion-corpus.yml` is **not observed in this pass**; it is proven after
  the PR pushes (the Pull Request event triggers it, since the filter names the guard).
- Merge, production deployment, and acceptance remain **sovereign-only**.
- The frozen-path failure in `test_m02_reasomate_truth.py` and FINDING F-01
  (`test_no_firebase_persistence_in_gate`) are **recorded, not repaired** — separate
  bounded workstreams.
