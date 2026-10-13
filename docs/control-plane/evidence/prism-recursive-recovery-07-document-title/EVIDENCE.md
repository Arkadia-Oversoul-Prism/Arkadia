# EVIDENCE — PRR-07 · per-surface document title

**Work item:** PRR-07 (prism-recursive-recovery-01 ledger)
**Target behavior:** Navigating between surfaces re-announces the destination
through the document title (WCAG 2.4.2), derived from the one surface table.
**Base SHA:** `dfbd2304db27746b22f0cda9b6961d1e37fda313` (main; cut directly
from main)
**Branch:** `feat/prism-rec-07-document-title`

## 1. Problem (measured)

`web/arkadia_console/index.html` carries a single static `<title>ARKADIA</title>`
and no module in `src/` writes `document.title` (grep → 0 hits at base). Every
route shares one title, so a screen-reader user navigating surfaces hears no
announcement of where they arrived. The archived Prism also used a static
title, so this is **not** a recovery of a lost Prism behavior — it is a
cross-surface quality item (Lane F, rank: shared accessibility), recorded as
such rather than presented as restoration.

## 2. Changed paths

- `web/arkadia_console/src/components/Shell.tsx` — one effect keyed on
  `current` sets
  ``document.title = `${SURFACE_BY_ID[current].name} · ARKADIA` ``. The shell
  already owns "which surface is current" (it renders the navigation from the
  surface table), so the title derives from that same table — no second list.
  Verified: no open PR touches `Shell.tsx` (all open PR file lists scanned).
- `tests/test_console_document_title_contract.py` (new, 6 tests).

## 3. Verification

| Command | Baseline @ `dfbd230` (measured earlier in a detached worktree for this exact set) | After candidate |
|---|---|---|
| `cd web/arkadia_console && pnpm run build` (`tsc --noEmit && vite build`) | PASS | **PASS** (exit 0) |
| shared set (canonical routing, rebuild-01, aeas05 acceptance, endpoint registry, authority chain, shell nav, pass-C ownership, CP10 gate integrity, `tests/architecture`) | **173 passed** | **173 passed** (unchanged) |
| same set + `tests/test_console_document_title_contract.py` | — | **179 passed** |

Contracts: exactly one module writes `document.title` (the shell); the write is
in an effect keyed on `[current]` (navigation re-announces); the value derives
from `SURFACE_BY_ID` with a fixed product suffix; the shell's navigation still
derives only from `SURFACES`. Negative controls: a page-local title map is
flagged; an unkeyed effect is flagged.

## 4. Review findings

- Scope: one effect in one file, one test (+evidence). No route, auth, or
  backend change; announcement metadata only.
- No second source of truth: the surface table remains the only surface list.
- No control added (no UI element at all).

## 5. Limitations / risks (explicitly not claimed)

- **NOT TESTED (browser / screen reader):** no browser harness in this
  sandbox; no assistive-technology session was run. The change is pinned by
  source contracts and the build, not by an observed announcement.
- The title does not include the lens/section (e.g. `/solariun/knowledge`
  announces "Solariun · ARKADIA"); sections are surfaced only through the
  in-page `aria-current` strip. Recorded as a possible refinement, not done.
- `index.html`'s static title remains the pre-hydration default (correct
  before React mounts).
- Adjacent-but-disjoint `Shell.tsx` is untouched by every other open PR;
  `App.tsx` is not modified by this work item.

## 6. Next dependency / recommended action

Draft PR against `main`; human review + required checks.
