# Evidence — Prism Lane 3 (Solariun / Knowledge OS): timeline "older events" paging

- **Workstream**: Prism UI reconciliation — Lane 3 (Solariun / Knowledge OS)
- **Branch**: `feat/prism-next9-03-knowledge-timeline-paging`
- **Base**: `main` @ `49809f45274f2f81b24e01fefdfb3009e8717495` (2026-10-12)
- **Authority**: draft PR only. No merge, no deploy, no acceptance. Human sovereign retains merge.

**Evidence freshness:** The handler behavior and test/build results below were measured on predecessor PR #491 at its old base/head. The relevant source files were byte-identical between that old base and current main at branch cut, so the patch was replayed. These numbers are retained as historical provenance only. Current-head CI is tracked on PR #498; until it completes, this file does not claim the tests passed on the fresh head.


## Objective

The timeline reader showed a single newest window and stated in prose that "older
events require an explicit offset query", but offered no control that performed one.
The measured backend contract (`test_knowledge_timeline_window.py`) already pages
*backwards from the newest event*: `offset = shown` returns the next page strictly
older than everything displayed. This slice lets the reader use that contract with a
bounded, honest, user-visible control.

## Scope (files changed)

Positively Lane-3-owned; **no shared file touched** (no `App.tsx`, `router.ts`,
`surfaces.ts`, `endpoints.ts`, `types.ts`, `SurfaceLenses.tsx`).

- `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` — adds `OlderPage`,
  `classifyOlderPage`, `mergeOlderEvents`, `olderOffset`, `olderEventsNotice`.
- `web/arkadia_console/src/components/knowledge/KnowledgeTimelinePanel.tsx` — a "Load
  older events" control; older pages accumulate beneath the newest window; distinct
  more/start/error states; disabled once the start is reached.
- `tests/test_knowledge_timeline_paging.py` — new console-contract guard (14 tests).
- This evidence document.

## What is asserted

1. **The backend supports a multi-page walk to the start.** 130 events, 100-window:
   page 1 = newest 100, page 2 = the older 30 (short of the limit — the backend's own
   stop signal), page 3 past the start returns `[]`. Measured against the live handler
   over ASGI; no mocks.
2. **The owner boundary holds on every page**, not only the first; anonymous stays
   empty on every page; the event-type filter applies before the window.
3. **The reader derives its paging state from the response** (`classifyOlderPage`),
   merges older pages beneath the newest window without duplicating rows
   (`mergeOlderEvents`), and states two outcomes that never share wording.

Each source detector carries a negative control (pre-repair shape fails it; an
import-without-a-call fails it), following the sibling console guards' convention.

## Historical verification from predecessor PR #491 (not rerun on this head)

| Command | Result |
|---|---|
| `python -m pytest tests/test_knowledge_timeline_paging.py -q -rEf` | **14 passed** |
| `python -m pytest tests/test_knowledge_timeline_window.py tests/test_knowledge_timeline_paging.py tests/test_knowledge_timeline_boundary.py -q` | **52 passed** |
| Sibling console/knowledge contracts (`boundary`/`projects`/`search`/`solariun slice`/`shell nav`/`endpoint registry`) | **136 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m pytest tests/test_prism_console_ci_wiring.py -q` | **30 passed** |
| `python scripts/console_contract_domain.py` | 22 guards (was 21); new guard present |
| `cd web/arkadia_console && corepack pnpm install && corepack pnpm build` | **built** (`tsc --noEmit` + vite; `dist/assets/index-BAigP8yp.js`, 97.38 kB) |
| CP10 `scripts/cp10_mutation_boundary_policy.py --judge` on the three new paths | **PASS** |

### Regression boundary

The one pre-existing pin that the first cut broke —
`tests/test_knowledge_timeline_window.py::test_latest_is_still_rendered_from_the_last_row`,
which requires the literal `events[events.length - 1]` — was **preserved, not
weakened**: the merged list keeps the identifier `events`, so the pinned property
holds and the sibling test passes. No test was relaxed.

### CI execution of the new guard

`tests/test_prism_console_ci_wiring.py` derives the console-contract domain from
`scripts/console_contract_domain.py`, and `.github/workflows/prism-console-contract.yml`
executes `python -m pytest -q $(python scripts/console_contract_domain.py)` with a
`tests/**` paths filter. The new guard names the console, so it **joins the derived
domain and is executed without a gate edit** (verified: `derive_domain` → 22, guard
present; wiring guard green).

## Remaining uncertainty / non-claims

- This is a repository-source claim. No production deployment, no browser observation,
  and no acceptance is claimed (draft-only authority).
- The pnpm build succeeded in this sandbox; the emitted `dist/` is untracked and not
  committed.
- No `main` full-suite run was performed this pulse (time budget); attribution is by
  targeted suites, the derived-domain count, and the failing/error node set of the
  touched suites, not a second full run.

## Fresh-head verification (measured on this head, 2026-10-13)

Residual slice: the timeline reader conflated an **unresolved session** with a
**settled sign-out**. `useAuth()` exposes `isAuthenticated`, `identityState`, and
`user`; an anonymous-looking read could be either a real anonymous viewer or an auth
provider that had not finished resolving. The reader previously had one anonymous
state, so it stated "no identity is present" for both — a false provider claim during
the loading window.

This slice adds a third scope, `pending`, derived from `identityState === "loading"`,
and gives it its own notice. It is a presentation-state distinction only: the backend
predicate is unchanged and no new request path is introduced.

### Files changed this pulse

- `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` — `TimelineScope`
  gains `"pending"`; `TimelineViewer` gains `"pending"`; `classifyTimelineScope`
  resolves it; `emptyTimelineNotice` branches to a distinct third string.
- `web/arkadia_console/src/components/knowledge/KnowledgeTimelinePanel.tsx` — derives
  `viewer` from `isAuthenticated` **and** `identityState`, so a loading session reads
  `pending`, not `unscoped`.
- `tests/test_knowledge_timeline_paging.py` — 5 new pending-state guards (14 → 19).
- `tests/test_knowledge_timeline_boundary.py` — the `emptyTimelineNotice` pin was
  re-pointed from the old two-arm ternary to the three-arm form (intent preserved,
  not weakened: three distinct notices, no shared wording).
- This evidence document.

### Measured results

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_knowledge_timeline_paging.py -q -rEf` | **19 passed** (was 14) |
| `python -m pytest tests/test_knowledge_timeline_boundary.py tests/test_knowledge_timeline_paging.py tests/test_knowledge_timeline_window.py -q -rEf` | **57 passed** |
| `python -m pytest tests/test_knowledge_timeline_paging.py tests/test_knowledge_timeline_boundary.py tests/test_knowledge_timeline_window.py tests/test_knowledge_os_boundary.py tests/test_knowledge_projects_boundary.py tests/test_knowledge_search_boundary.py tests/test_solariun_knowledge_slice_01.py tests/test_prism_console_ci_wiring.py -q -rEf` | **149 passed** |
| `python -m pytest tests/test_prism_console_ci_wiring.py tests/test_console_shell_nav_contract.py tests/test_console_endpoint_registry_contract.py -q -rEf` | **78 passed** |
| `cd web/arkadia_console && corepack pnpm install && corepack pnpm build` | **built** (`tsc --noEmit` + vite; `dist/assets/index-BwiaOTo5.js`, 97.62 kB) |
| `python scripts/console_contract_domain.py` | 22 guards; `test_knowledge_timeline_paging.py` in the derived domain |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on the four changed paths | **PASS** |

### Negative controls (the new guards bite)

- Reverting **both** source files to their pre-slice shape reddens exactly the 4 new
  source-level nodes (`test_scope_vocabulary_carries_the_pending_state`,
  `test_classify_timeline_scope_resolves_pending_distinctly`,
  `test_empty_copy_gives_pending_its_own_wording`,
  `test_panel_derives_pending_from_the_auth_identity_state`) → `4 failed, 15 passed`.
  Restoring both returns `19 passed`.
- Collapsing `emptyTimelineNotice` to a single shared string reddens
  `test_knowledge_timeline_boundary.py::test_empty_and_unreadable_are_distinguishable`
  (the tightened three-notice pin). Restoring returns it to green.
- The boundary pin first failed *naturally* on the source change (pre-existing
  two-arm regex), which independently proves these detectors read the real file.

### Regression boundary

No test was weakened. The one pre-existing pin that the source change broke —
`test_empty_and_unreadable_are_distinguishable` — was **updated in intent**: it now
requires all three scopes to carry distinct wording, which is strictly stronger than
the old "owner differs from the second arm" check. The `events[...]` literal pin in
`test_knowledge_timeline_window.py` is untouched and green.

## Remaining uncertainty / non-claims (this head)

- Repository-source claim only. No merge, no deploy, no production observation, no
  acceptance claimed (draft-only authority).
- The emitted `dist/` is untracked and not committed.
- No `main` full-suite run was performed this pulse (time budget); attribution is by
  the targeted suites above, the derived-domain membership, and the negative controls,
  not a second full run.
