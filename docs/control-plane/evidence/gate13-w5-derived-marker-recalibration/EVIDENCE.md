# GATE-13 · Continuous Recalibration — W5 derived-graph marker

## Objective
Align stale test assertions with the canonical derivation-provenance marker so the
repository's own tests no longer contradict its source of truth.

## Bounded scope
Single file: `tests/test_weaver_w5.py` (two assertions). No production code touched.

## Finding
`solspire/project_knowledge.build_derived_graph()` is documented in-source as a
*"Compatibility wrapper for the bounded semantic graph projection"* and delegates to
`solspire.semantic_graph.build_bounded_semantic_graph()`, which returns
`"kind": "DERIVED_BOUNDED_SEMANTIC"`.

The W5 test still asserted the pre-migration literal `"DERIVED"`.

Evidence of canonicality:
- `solspire/semantic_graph.py:112` — `"kind": "DERIVED_BOUNDED_SEMANTIC"`
- `solspire/project_knowledge.py:98-101` — compatibility wrapper, delegates
- `tests/test_weaver_mvp2_05.py:24` — peer test asserts the long form
- No production consumer reads the short form. The unrelated `'DERIVED'` in
  `web/public_prism/src/lib/sciCommandRegistry.ts` is a `SciAuthorityClass` variant;
  the `"DERIVED"` in `lab/canon/loader.py:18` is a document-classification fallback.

The test assertion was stale; the code is correct. The fix is test-side only.

## Change set
- `tests/test_weaver_w5.py` — `test_derived_graph_provenance` and
  `test_project_knowledge_endpoints` (graph endpoint) now assert
  `DERIVED_BOUNDED_SEMANTIC`.

## Verification
| Check | Result |
|---|---|
| `pytest tests/test_weaver_w5.py tests/test_weaver_mvp2_05.py` | 9 passed |
| `pytest tests/architecture -q` | 11/11 passed |
| `python -m py_compile api/main.py` | clean (boot surface untouched) |
| `api/main.py` line budget | 2519 / 2600 (unchanged) |

## Baseline comparison
Fingerprint reproduced at the start of this pass and re-measured after the change,
same invocation (`--continue-on-collection-errors`, PYTHONPATH=archive/legacy_python).

| | failed | passed | skipped | collection errors |
|---|---|---|---|---|
| baseline (pre-change) | 49 | 903 | 12 | 2 |
| post-change | 47 | 905 | 12 | 2 |

Delta is exactly the two targeted tests. No new failure; no fingerprint change in any
other test. Remaining 47 failures and 2 collection errors are pre-existing baseline debt
(root `index.html` frontend fixture absent; stale `tests/test_prism_pass_c_surface_ownership.py`
and `tests/test_weaver_sci_*` nav assertions from before the NovaNet/Nexus navigation
restructure). Not addressed here per the rule against widening scope.

## Regression boundary
Test-only change. No runtime, authority, mutation, or boot surface modified.

## Remaining uncertainty
The 47 baseline failures are not attributable to this change. Their remediation is a
separate bounded workstream and was deliberately not entered.

## Status
VERIFIED — implementation exists, required tests pass, protected regression passes,
provenance inspectable. Awaiting sovereign review for merge.
