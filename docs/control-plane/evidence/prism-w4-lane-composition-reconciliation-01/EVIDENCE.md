# Workstream 4 - lane-4 composition reconciliation - evidence

**Branch:** `feat/prism-next8-04-automation-grammar` (PR #493)
**Base:** `49809f45274f2f81b24e01fefdfb3009e8717495` (`main`, merge of #490)
**Mode:** inspection / composition / test only - no merge, deployment, or acceptance.

## 1. The hazard, re-measured (not inherited)

Two open lane-4 PRs branch from the same base `49809f45` and both edit the single
lane-4-owned file `web/arkadia_console/src/pages/EngineeringLabPage.tsx`:

| PR | branch | head | adds to the page |
|----|--------|------|------------------|
| #493 | `feat/prism-next8-04-automation-grammar` | `d3e978d1` | `import` + `<LabAutomationGrammar />` |
| #501 | `feat/prism-next9-04-canonical-loop-mount` | `31d66332` | `import` + `readLoopStages()` + `<ExecutionLoop .../>` |

Both page diffs apply against the same `index 6ff37a3..` pre-image. A merge/union that keeps
one side drops the other lane's user-visible surface. This is exactly the shape PR #504's guard
(`tests/test_prism_next_wave_composition_reconciliation_01.py`) reports, and PR #504's body
requested the union be carried on a Lane-4 branch - this pass does that.

## 2. Dependencies verified present on #493's tree

- `web/arkadia_console/src/components/lab/ExecutionLoop.tsx` exists (committed `74936640`,
  orphaned on `main`).
- `endpoints.labEngineeringOverview == "/api/lab/engineering/overview"` (`endpoints.ts:30`).
- `lab/engineering_lab/runtime.py::CANONICAL_LOOP` present; `overview()` returns
  `"loop": list(CANONICAL_LOOP)`.

## 3. Change

- `EngineeringLabPage.tsx`: carry BOTH lane-4 projections - `<LabAutomationGrammar />` (#493)
  and `<ExecutionLoop stages={readLoopStages(...)} />` (#501) - with #501's reader helper.
- Add `tests/test_prism_w4_canonical_loop_mount.py` (#501's owning contract, brought onto this
  branch so the composed mount is judged by the contract that owns it).
- Add `tests/test_prism_next_wave_composition_reconciliation_01.py` (PR #504's composition
  guard), so a future one-sided union of this file is caught rather than silently shipping.

## 4. Proof

Targeted, on the composed tree:

```
python -m pytest tests/test_prism_w4_automation_grammar.py \
  tests/test_lab_automation_grammar_contract.py \
  tests/test_prism_w4_canonical_loop_mount.py \
  tests/test_prism_next_wave_composition_reconciliation_01.py -q
-> 66 passed
```

Live negative controls (mutate the real page, not a fixture):

- remove `<ExecutionLoop .../>` -> `2 failed` (`test_prism_w4_canonical_loop_mount.py::
  test_lab_page_renders_the_canonical_loop_surface` and the composition guard), then restored.
- remove `<LabAutomationGrammar />` -> `1 failed` (`test_lab_automation_grammar_contract.py::
  test_surface_is_mounted_in_the_lab_page`), then restored.

Frontend build of the composed tree:

```
cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build
-> 84 modules transformed; built in 1.60s
```

## 5. Boundary

Repository source only. No merge, no deployment, no acceptance, no production-parity claim.
PRs #493 and #501 stay draft; the human sovereign selects merge order. Once either merges,
the other must be rebased onto the new `main` rather than merged unreconciled.
