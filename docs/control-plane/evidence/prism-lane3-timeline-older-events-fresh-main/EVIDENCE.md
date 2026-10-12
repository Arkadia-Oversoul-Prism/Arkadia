# Evidence — Prism Lane 3 (Solariun / Knowledge OS): timeline "older events" paging

- **Workstream**: Prism UI reconciliation — Lane 3 (Solariun / Knowledge OS)
- **Branch**: `feat/prism-next9-03-knowledge-timeline-paging`
- **Base**: `main` @ `49809f45274f2f81b24e01fefdfb3009e8717495` (2026-10-12)
- **Authority**: draft PR only. No merge, no deploy, no acceptance. Human sovereign retains merge.

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

## Verification performed (measured, this pulse)

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
