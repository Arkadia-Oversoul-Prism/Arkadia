# EVIDENCE — PRR-06 · surface render-failure error boundary

**Work item:** PRR-06 (prism-recursive-recovery-01 ledger)
**Target behavior:** A render exception inside a surface replaces only that
surface with an honest failure state (real caught error, real recovery
actions) while the shell stays usable; the failure state cannot outlive the
surface that produced it.
**Base SHA:** `dfbd2304db27746b22f0cda9b6961d1e37fda313` (main; cut directly
from main)
**Implementation commit:** recorded in the PR head (base SHA + PR head identify
the exact candidate)

## 1. Problem (measured)

No React error boundary exists anywhere in `web/arkadia_console` (grep:
`ErrorBoundary|componentDidCatch` → 0 hits) nor in the archived Prism
(`archive/frontend/arkadia-prism/web/public_prism/src` → 0 hits). A render
exception in any surface therefore tears down the entire tree: a blank canonical
application with no recovery control. Lane A of the recovery matrix lists
"loading and error boundaries" as shared-shell scope.

This is a resilience seam of the canonical shell — not a parallel runtime: no
data path, auth path, or backend contract changes.

## 2. Changed paths

- `web/arkadia_console/src/components/ErrorBoundary.tsx` (new) — class
  boundary with both React lifecycle methods; failure copy states that a
  render failure changes nothing on the backend and that anything shown before
  it may be incomplete; shows the **real** `error.message`; two real recovery
  actions (full reload; navigation home through the shared router); the error
  is recorded with `console.error` only — nothing is transmitted or persisted.
- `web/arkadia_console/src/App.tsx` — mounted exactly once, inside the shell,
  wrapping the surface body, `key={route.surface}` (crossing surfaces remounts
  the boundary and clears the failure), `onHome` bound to the router's
  `navigate("home")`.
- `tests/test_console_surface_error_boundary.py` (new, 10 tests).

## 3. Verification (exact commands and results)

| Command | Baseline @ `dfbd230` (measured in a detached worktree) | After candidate |
|---|---|---|
| `cd web/arkadia_console && pnpm run build` (`tsc --noEmit && vite build`) | PASS | **PASS** (exit 0) |
| shared set (canonical routing, rebuild-01, aeas05 acceptance, endpoint registry, authority chain, shell nav, pass-C ownership, CP10 gate integrity, `tests/architecture`) | **173 passed** | **173 passed** (unchanged) |
| same set + `tests/test_console_surface_error_boundary.py` | — | **183 passed** |

New suite contracts: mounted exactly once in the composition root (JSX-mount
detector distinguishes `Component<ErrorBoundaryProps` type arguments from
mounts); keyed by surface; wraps `{body}` inside `<Shell>`; both lifecycle
methods present; fallback shows `{error.message}`, a real
`window.location.reload()`, and an `onHome` bound to `navigate("home")`;
failure copy claims nothing about backend work (forbidden words asserted);
negative controls for each detector (foreign mount, missing lifecycle,
unkeyed mount).

Guards that caught candidate defects (fixed in the candidate, tests untouched):
the mount detector initially counted the component's own type argument, and the
recovery-action assertion initially looked for an attribute the component never
used — both repaired in the test's detectors or component per what was true.

## 4. Review findings

- Scope: 1 new component, one mount in `App.tsx`, one test (+evidence).
  No other surface file touched; no open PR adds a boundary (verified by
  scanning all open PR file lists for `ErrorBoundary`).
- Every control real: reload reloads; home navigates through the shared
  router. No decorative controls.
- Honest states: real error message; copy explicitly separates render failure
  from backend state; no implied save/send/restore outcomes (asserted).
- No authority change: auth threshold, routing, and API contracts untouched;
  `test_aeas05_canonical_frontend_acceptance` passes unmodified.

## 5. Limitations / risks (explicitly not claimed)

- **NOT TESTED (browser)** — no browser harness in this sandbox. The catch
  behavior itself (React invoking the boundary at runtime) is not executed by
  these tests; they pin the wiring, lifecycle methods, and copy. A unit test
  rendering a throwing child would require a React test renderer the repo does
  not carry — adding a dependency for it was judged out of scope (no new
  dependency without demonstrated need).
- `componentDidCatch` records to `console.error` only; there is no crash
  reporting service, by design (nothing is transmitted).
- Adjacent-but-disjoint `App.tsx` hunks vs draft PRs #510, #511, #513; merge
  order semantically unconstrained, import-block conflicts (if any) trivial.

## 6. Next dependency / recommended action

Draft PR against `main`; human review + required checks.
