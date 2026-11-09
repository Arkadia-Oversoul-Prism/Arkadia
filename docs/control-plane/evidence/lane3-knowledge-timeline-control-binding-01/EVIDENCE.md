# Lane 3 — bind the timeline paging control to its detectors (EVIDENCE)

**Branch:** `feat/prism-l3-knowledge-control-binding-02`
**Base `main`:** `24f0c9e1a295b1578720879cdaf0812193543709` (PR #648 merge, 2026-11-09T00:11:09+01:00)
**Bounded scope:** `tests/test_knowledge_timeline_paging.py` only — Lane 3 owned (Solariun /
Knowledge OS). No console source, backend contract, registry, authority surface or other
lane's file is touched.
**Node count:** unchanged at 19 (a strengthening, not an addition).

## 1. The defect

`tests/test_knowledge_timeline_paging.py` carries three source-level assertions about the
unresolved-identity (`pending`) state and one `test_detector_flags_the_pre_repair_two_state_viewer`
control that claims to prove them. The control **restated the live assertions' regexes
inline and ran no detector**: it asserted facts about strings it had just written
(`"identityState" not in pre_repair_panel`, `not _PENDING_LITERAL.search(pre_repair_contracts)`),
so it could not fail for any edit to the predicates it names. The live assertions were the only
enforcement of the property, and nothing exercised them but themselves.

Measured at `main` `24f0c9e1` by AST-scoped mutation of the **live** detector's own expression:

```
baseline:                                            2 passed
live detector neutered (regex -> r'.*', always match) -> 2 passed
restored:                                            2 passed
```

The live node and its control both stayed green while the detector that keeps a pending session
from being reported as a settled sign-out was disarmed.

This is the same defect class Lane 1 repaired in #631/#634/#636/#637, Lane 2 in #635/#640,
Lane 3 in #638 and Lane 4 in #639/#641/#642/#643/#645/#646/#647; those passes did not reach this
guard. Found by a transitive call-reachability sweep of every `tests/**/test_*.py` carrying
`test_negative_control_*` / `test_control_*` / `test_detector_flags_*` nodes, treating pytest
fixtures as roots as well as live tests.

## 2. The repair

Three module-level detectors now hold the predicates, and the live assertions **and** their
control both call them:

| Detector | Predicate | Live assertion |
|---|---|---|
| `_pending_scope_defects(contracts)` | `TimelineScope` / `TimelineViewer` name `pending` | `test_scope_vocabulary_carries_the_pending_state` |
| `_pending_classifier_defects(contracts)` | `classifyTimelineScope` branches on the pending viewer | `test_classify_timeline_scope_resolves_pending_distinctly` |
| `_pending_viewer_defects(panel)` | the panel's viewer consults the auth `identityState` | `test_panel_derives_pending_from_the_auth_identity_state` |

The control feeds each detector the pre-repair shape and asserts it is reported, **and** feeds it
the live input and asserts it is *not* reported — so a detector that reports unconditionally
cannot pass either. The now-redundant `_PENDING_LITERAL` was removed; its property is carried by
`_pending_scope_defects`.

## 3. Proof — discriminating A/B on the real file

Every degenerate detector body was exercised against the live node **and** the control
(AST-scoped, file restored byte-identically after each mutation — asserted in the harness):

```
baseline:                                            4 passed
scope detector always-report                         -> 2 failed
classifier detector never-report (return [])         -> 1 failed, 1 passed
viewer detector always-report                        -> 2 failed
restored:                                            4 passed
```

The `1 failed, 1 passed` row is the binding for the classifier: the live node reddens
(`assert defects == []` is satisfied by `return []`, so the control's own positive half is what
catches it) while the control passes, which is exactly the direction the pre-repair file could
not produce.

**Pre-repair control for the same shape.** Before the repair, the same `return []` mutation left
the live classifier node green (nothing called the predicate but the live assertion itself), which
is the vacuity.

## 4. Verification

- `python -m pytest tests/test_knowledge_timeline_paging.py -q -rEf` → **19 passed**
  (node count unchanged; `--collect-only` → 19).
- Sibling Lane-3 / console-domain guards: `tests/test_knowledge_status_read_boundary.py`,
  `tests/test_prism_solspire_control_plane.py`, `tests/test_operator_surface_convergence.py`,
  `tests/test_console_facts_value_overflow_contract.py` → **74 passed** with the target file.
- `python -m pytest tests/architecture -q` → **11 passed**.
- `python scripts/lane_state.py --check` and `--check --verify-live` → **exit 0**.
- `python scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths → admitted.

The guard is executed by the derived console-contract domain
(`scripts/console_contract_domain.py` lists `tests/test_knowledge_timeline_paging.py`), so
`.github/workflows/prism-console-contract.yml` runs it; no workflow edit is needed.

## 5. Recorded, not repaired

- `tests/test_knowledge_status_read_boundary.py::test_negative_control_the_status_surface_routes_through_the_shared_reader`
  asserts the page's `readStatus` seam by reading `KnowledgePage.tsx` directly rather than calling
  a module-level detector. It is bound to the property it names (the page body must call
  `requireKnowledgeStatusReading(`), so it is not vacuous; a future pass may still hoist it to a
  shared detector for symmetry. Out of this slice's scope.
- `tests/test_console_facts_value_overflow_contract.py::test_negative_controls_anchor_on_the_live_source`
  is an anchor guard, not a detector control; it is sound as written (its own docstring states why).

## 6. Authority

Lane 3 bounded slice under `SHARED-CONTRACTS.md` §11 (N1–N8). Reconciliation was exhausted first
(measured live at `24f0c9e1`: **0** open PRs repo-wide, all four lanes `doc_guard: idle`). No
merge, deployment, production change or acceptance is performed or claimed. The PR opens as a
draft; merge remains human-only (OpenHands does not hold Weaver's GOV-01 authority).
