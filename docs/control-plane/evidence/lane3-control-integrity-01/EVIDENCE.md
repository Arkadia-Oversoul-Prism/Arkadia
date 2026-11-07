# Lane 3 — negative-control integrity in two lane-3 guards

**Base `main`:** `03220c958e4549a3e1ff6623035470e7b1ddbfbf` (2026-11-07)
**Lane:** 3 (Solariun + Knowledge OS) — SHARED-CONTRACTS.md §1
**Defect class:** vacuous negative controls (a `test_negative_control_*` node that restates its
detector inline and never calls it, so it cannot fail for any edit to the assertion it protects).

## 1. Defect, measured

Same class repaired in Lane 1 by #631, #634, #636 and #637. Those passes did not reach the two
lane-3 guards below.

### A — `tests/test_prism_solariun_memory_lens.py`

`test_negative_control_detects_confident_zeros_for_unavailable_sources` built a string
(`"value: count(data[key])"`) and asserted a literal was absent from it. It called no detector.
The live assertion `test_degraded_sources_are_shown_as_degraded_not_zero` called
`_renders_degraded_counts(PANEL)`, which the control never touched.

Pre-repair proof (AST-scoped mutation of the live predicate, real file):

```
force _renders_degraded_counts -> `return True`
  -> 7 passed
```

The detector was fully disarmed and the whole file stayed green, including the control that
claims to prove it.

### B — `tests/test_knowledge_graph_provenance_boundary.py`

`test_negative_control_panel_does_not_hardcode_an_origin` and
`test_negative_control_panel_never_hardcodes_an_author` each restated their regexes inline and
called no detector. They were also the **only** enforcement of the "no literal attribution"
invariant — the property was guarded by nodes labelled as controls rather than by a live
assertion.

Pre-repair proof (real blob at `03220c95`):

```
replace both control assertions with `assert True`
  -> 24 passed
```

## 2. Repair

Both files now hold a module-level detector that the live assertions **and** their controls call:

- `_degraded_reading_defects(panel) -> list[str]` (was `_renders_degraded_counts -> bool`).
  Returns the reasons a degraded source could read as a confident zero, so the control asserts
  the *specific* defect rather than a boolean.
- `_hardcoded_attribution_hits(source) -> list[str]` — the three literal-attribution patterns
  (`captured_by=`, `authored_by=`, `author=`).

The attribution invariant moved onto the live assertions
(`test_panel_renders_the_provenance_reading`, `test_panel_renders_the_authorship_reading`); the
controls now only prove the detector bites. Each control also asserts the repaired input is
**not** reported, so a detector that matches everything cannot pass either.

Node count unchanged in both files: **7** and **24**.

## 3. Post-repair proof (the discriminating control)

Force the shared helper to always report, then re-run:

```
A: _degraded_reading_defects -> `return ["forced"]`
   -> 2 failed, 5 passed
      FAILED test_degraded_sources_are_shown_as_degraded_not_zero
      FAILED test_negative_control_detects_confident_zeros_for_unavailable_sources

B: _hardcoded_attribution_hits -> `return ["forced"]`
   -> 4 failed, 20 passed
      FAILED test_panel_renders_the_provenance_reading
      FAILED test_negative_control_panel_does_not_hardcode_an_origin
      FAILED test_panel_renders_the_authorship_reading
      FAILED test_negative_control_panel_never_hardcodes_an_author
```

Both sides redden. On the pre-repair blobs the same mutation left every node green — the
controls were vacuous, and the invariant had no live owner.

Both files were restored byte-identically after each control (`git diff` empty for the mutation).

## 4. Verification

| Check | Result |
|---|---|
| `pytest tests/test_prism_solariun_memory_lens.py tests/test_knowledge_graph_provenance_boundary.py -q` | **31 passed** |
| `pytest $(python scripts/console_contract_domain.py) -q` | **1123 passed / 10 failed** |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | **67 passed** |
| `python scripts/lane_state.py --check` | exit **0** |
| `python scripts/lane_state.py --check --verify-live` | exit **0** |

The 10 domain failures are **entirely** `tests/test_mission_lifecycle_adapter_contract.py` and are
the documented missing-`node_modules` baseline (`node_modules/typescript/lib/typescript.js`
absent locally; CI runs 1133 passed). Identical to `main` — not attributable, not repaired.

`--collect-only` attributes the delta: 7 and 24 nodes before and after in the two touched files,
so the change adds no node and removes none.

## 5. Lane bookkeeping

`docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md` gains a status block declaring
**no active PR** (a lane PR cannot declare itself open at merge time — the merge closes it), and
`lane-state.json` is re-derived in the same commit via
`scripts/lane_state_refresh.py --write --base-main 03220c95…`. The two are one atomic change:
editing a guarded lane doc without the refresh reddens `lane-doc-currency` on `main` at merge.

## 6. Boundaries

Tests-only plus lane bookkeeping. No application source, no authority surface, no identity or
governance file, no deployment configuration. Lane 3 owns both guards (Solariun/Knowledge OS
feature-local tests) and the two console surfaces they guard are lane-3 feature modules.

Merge, deployment and acceptance remain human-only.
