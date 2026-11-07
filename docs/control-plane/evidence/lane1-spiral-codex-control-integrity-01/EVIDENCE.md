# Lane 1 — spiral-codex control integrity (vacuous negative controls, third guard)

**Lane:** 1 (shell / navigation / design system / integration seam)
**Branch:** `feat/prism-l1-spiral-codex-control-integrity-01`
**Base:** `main` `35e03fcb3055745cf1ffb1ba188d4fea25e452a9` (live this pulse)
**Date:** 2026-11-07
**Authority:** `11 — LANE NEW-PR AUTHORIZATION` (N1–N8)

## 1. Defect

`tests/test_console_spiral_codex_contract.py` carried two `test_negative_control_*` nodes that
**restated their detectors inline instead of calling them**. A negative control exists to fail
when the live detector it protects is disarmed; one that re-implements the predicate instead of
calling it cannot do that.

| Control | Restated inline | Live assertion it claimed to protect |
|---|---|---|
| `test_negative_control_detector_flags_a_panel_that_inlines_the_path` | `assert '"/api/codex"' in mutated` + `assert "endpoints.publicCodex" not in mutated` | `test_the_panel_reads_the_registry_not_a_literal` |
| `test_negative_control_detector_flags_a_reintroduced_categories_request` | `assert "/api/codex/categories" in mutated` | `test_the_categories_route_the_archive_used_is_not_served` |

Neither control called the live assertion's predicate. The first restated a two-clause
comparison; the second asserted only that its own string edit had landed and never ran a detector
at all. Both live detectors could therefore be edited to anything with no red test.

This is the same defect class already repaired in three Lane-1 guards: #631
(`test_console_surface_error_boundary.py`, `test_console_shell_nav_contract.py`), #634
(`test_console_unified_interface_contract.py`, six controls), and #636
(`test_console_posture_currency.py`).

## 2. Discriminating A/B on the real file

The pre-repair file, with **only the live test's own expression** neutered by its `ast` span (so
the control's inline copy is untouched):

```
$ python -m pytest -q -rEf tests/test_console_spiral_codex_contract.py
FAILED tests/test_console_spiral_codex_contract.py::test_the_categories_route_the_archive_used_is_not_served
1 failed, 20 passed
```

The live node reddened; **its control stayed green**. That is the vacuity, measured rather than
argued. (A naive whole-file `str.replace` moved both occurrences and reddened both — which is why
the mutation is scoped by `ast` span, not by string.)

The repaired file, with the **shared helpers** forced to always report:

```
$ python -m pytest -q -rEf tests/test_console_spiral_codex_contract.py
FAILED tests/test_console_spiral_codex_contract.py::test_the_panel_reads_the_registry_not_a_literal
FAILED tests/test_console_spiral_codex_contract.py::test_the_categories_route_the_archive_used_is_not_served
FAILED tests/test_console_spiral_codex_contract.py::test_negative_control_detector_flags_a_panel_that_inlines_the_path
FAILED tests/test_console_spiral_codex_contract.py::test_negative_control_detector_flags_a_reintroduced_categories_request
4 failed, 17 passed
```

Both live nodes **and** both controls redden together, so the control is bound to the detector
that decides the live assertion. The file was restored byte-identically afterwards
(`21 passed`).

## 3. Repair

Two module-level helpers now hold the predicates, and the live assertions and their controls both
call them:

- `_inlined_corpus_path(code) -> bool` — the registry-bypass predicate.
- `_categories_route_mentions(code) -> list[str]` — every occurrence of the unserved categories
  path. It matches the **whole literal** rather than one request form, so it is no weaker than the
  substring check it replaces (a bare string, a template literal, or any other spelling of the
  dead path is still reported). Comments are removed by `_code_only` before it runs, which is what
  keeps a doc comment that *names* the dead route from reading as a request.

Each control now asserts **both** polarities: the mutated input is reported *and* the repaired
input is not, so a detector that matches everything cannot pass either.

## 4. Measurements

| Check | Result |
|---|---|
| `pytest tests/test_console_spiral_codex_contract.py -q -rEf` | **21 passed** (was 21 passed) |
| `pytest --collect-only` on the file | **21 nodes** — unchanged (a strengthening, not an addition) |
| `pytest -q $(python scripts/console_contract_domain.py)` | **10 failed, 1123 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `scripts/lane_state.py --check` | exit 0 |
| `scripts/lane_state.py --check --verify-live` | exit 0 |

The 10 domain failures are all `tests/test_mission_lifecycle_adapter_contract.py`, the documented
missing-`node_modules` TypeScript-toolchain baseline (present on `main`, unrelated to this change
and not attributable to it). The full-suite baseline measured this pulse at `main` `35e03fcb` is
**20 failed / 3978 passed / 18 skipped / 1 error**; this change touches one test file and its node
count is unchanged.

## 5. Boundaries

- No console source, backend contract, registry entry, or other lane's file is touched.
- No protected authority, identity, K15/K3 governance, approval enforcement, or deployment
  configuration is altered.
- Merge, production deployment, and acceptance remain human-only.
