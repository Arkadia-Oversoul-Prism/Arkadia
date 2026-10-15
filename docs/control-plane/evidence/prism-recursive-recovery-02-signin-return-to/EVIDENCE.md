# EVIDENCE — PRR-02 · sign-in returns the user to the destination it interrupted

**Work item:** PRR-02 (prism-recursive-recovery-01 ledger)
**Target behavior:** Crossing into the sign-in surface records where the user
was; a *confirmed* sign-in returns them to that destination (surface + lens
section). A failed sign-in neither navigates nor spends the destination. A
return target that is external, invented, or loops back to `/login` degrades to
the router's own fallback or is refused — it can never navigate off-origin.
**Base SHA:** `dfbd2304db27746b22f0cda9b6961d1e37fda313` (main; this branch was
cut directly from it)
**Implementation commit:** `089b772a7008524b437cb87b6aeed1285c538b74`
(candidate head when every verification below was executed; the PR head also
carries this record — base SHA + PR head identify the exact candidate)
**Branch:** `feat/prism-rec-02-signin-return-to`

## 1. Problem (measured at base SHA)

- `AuthThreshold` (App.tsx) rendered for protected surfaces with
  `href="/login"`; nothing recorded the protected path the address bar still
  held.
- `Shell`'s `nav-sign-in` button navigated to `login` with no destination.
- `SignInPage.submit` awaited `signIn(...)` and stayed on `/login` — after a
  successful sign-in the user was left standing on the sign-in surface with no
  route back to the surface they had requested (the composition root only
  re-renders once auth state changes; the route never moved).

Reference: the archived Prism's own gate/login flow kept post-sign-in
continuity (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx`
navigation handling); the console's threshold is the reconciled seam. No
second auth system was introduced — Firebase identity, `require_auth`, and the
session contracts are untouched; this change only moves the *view*.

## 2. Changed paths

- `web/arkadia_console/src/lib/returnTo.ts` (new) — `rememberReturnTo` /
  `consumeReturnTo`. Session memory written on the way in, `?returnTo=` deep
  link as second source, resolved through the router's `resolvePath`, refused
  when it resolves back to the sign-in surface, cleared on read.
- `web/arkadia_console/src/App.tsx` — one shared `handleNavigate` wrapper:
  reaching `login` records `route.path` before navigating. The threshold, the
  shell, and the sign-in page all cross through it. No pathname parsing
  outside `lib/router.ts` (that guard is preserved — see §3).
- `web/arkadia_console/src/pages/SignInPage.tsx` — takes `onNavigate`; after
  `signIn` resolves, consumes the destination and navigates. The `catch` path
  does neither.
- `tests/test_console_return_to_contract.py` (new, 15 tests).

Reverted during implementation (before commit): an earlier draft read
`window.location.pathname` inside App/Shell, which was caught by
`test_router_module_owns_the_only_pathname_resolution`; the wrapper design
above removes the need for any pathname read outside the router. `Shell.tsx`
is byte-identical to base. No test was edited.

## 3. Verification (exact commands and results)

| Command | Baseline @ base SHA | After candidate |
|---|---|---|
| `cd web/arkadia_console && pnpm run build` (`tsc --noEmit && vite build`) | PASS (exit 0) | **PASS** (exit 0, `dist/assets/index-f9ZejzMj.js`) |
| `python3 -m pytest tests/test_console_return_to_contract.py -q` | n/a (new) | **PASS — 15 passed** |
| `python3 -m pytest tests/test_console_return_to_contract.py tests/test_canonical_frontend_routing.py tests/test_frontend_arkadia_console_rebuild_01.py tests/test_aeas05_canonical_frontend_acceptance.py tests/test_console_endpoint_registry_contract.py tests/test_console_authority_chain.py tests/test_console_shell_nav_contract.py tests/test_prism_pass_c_surface_ownership.py tests/test_solariun_experience_consolidation_01.py tests/test_m02a_ci_gate_integrity.py tests/architecture -q` | **181 passed** (measured in a detached worktree at `dfbd230`, same command minus the new file) | **196 passed** |

The new suite **executes** `surfaces.ts` + `router.ts` + `returnTo.ts` in Node
(module wiring stripped, `window.sessionStorage` stubbed) and asserts:
round-trip survives and is cleared; section preserved; `/login` never stored;
query deep link honoured when nothing was stored; stored memory wins over the
query; absolute-URL targets degrade to the router fallback and never contain
the external origin; a target resolving back to `/login` is refused; no
destination means `null`, not a guess. Source contracts (with negative
controls): the wrapper remembers before it navigates and is gated on `login`
(a reversed or ungated ordering is flagged); the destination is consumed only
after `signIn` resolves and never inside `catch` (a `catch` copy is flagged);
the pinned sign-in testids and exact `href="/login"` are preserved.

Guards that caught candidate defects (fixed in the candidate, tests untouched):
`test_router_module_owns_the_only_pathname_resolution` (twice — first the
pathname reads, then a comment containing the literal string), and the
suite's own ordering negative controls.

## 4. Review findings

- Scope: 2 source edits + 1 new module + 1 new test (+evidence). `Shell.tsx`,
  `AuthContext.tsx`, and all backend files unchanged.
- Every control real: the threshold anchor keeps `href="/login"` (works even
  without the handler), the click path stays in the SPA and records the
  destination; the sign-in button and form behave as before plus the return
  leg.
- No auth/authority change: no bypass, no token handling change, no new
  write path; identity states and the unconfigured-Firebase behavior are
  untouched (`test_aeas05_canonical_frontend_acceptance` passes unmodified).
- Honest states: nothing claims a destination that was not recorded; a failed
  sign-in keeps its error copy and its destination for the next attempt.

## 5. Limitations / risks (explicitly not claimed)

- **NOT TESTED (browser):** no browser harness in this sandbox. The return leg
  is proven by executed-module tests and source contracts, not by an observed
  session.
- The `?returnTo=` deep link is honoured on load, but the in-app entries use
  session memory; a full-page `<a href="/login">` fallback (handler skipped,
  e.g. new tab) starts without a destination — the user simply signs in and
  stays on `/login`, as before.
- `sessionStorage` is per-tab; a destination does not survive a new tab. By
  design.
- Overlap: this branch cuts from `main` @ `dfbd230` and touches `App.tsx`
  regions adjacent to (but disjoint from) draft PR #510 — both are independently
  mergeable; conflicts, if any, are one-line comment/case adjacency.

## 6. Next dependency / recommended action

Draft PR against `main`; human review + required checks. Merge order between
#510 and this PR is unconstrained semantically.
