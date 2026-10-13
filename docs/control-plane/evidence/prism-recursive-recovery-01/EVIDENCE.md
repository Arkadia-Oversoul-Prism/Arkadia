# EVIDENCE — PRR-01 · Solariun lens strip becomes real routed navigation

**Work item:** PRR-01 (prism-recursive-recovery-01 ledger)
**Target behavior:** The Solariun lens strip is real navigation through the
shared router (`/solariun/<lens>`), every lens has a truthful content state, and
an undeclared section renders an honest "not a lens" state instead of silently
showing the projects view.
**Base SHA:** `dfbd2304db27746b22f0cda9b6961d1e37fda313` (main, clean tree;
verified == `origin/main` after fetch)
**Candidate head SHA:** recorded in the draft PR for this branch (this file
cannot contain its own commit hash; base SHA + PR head identify the exact
candidate).

## 1. Relationship to the archived Prism reference

- Archived source: `archive/frontend/arkadia-prism/web/public_prism/src/pages/SolariunConsole.tsx`
  → `SolSpireExperience` lenses (`overview · projects · knowledge · memory ·
  weaver · observatory · …`), and `src/App.tsx` route table
  (`routeForView('solariun')` → `/solariun/<lens>`; legacy inbound aliases
  `/codex`, `/loops`, `/dashboard`, `/settings`, `/account`,
  `/personal-echofeild` → solariun sections).
- The canonical console (`web/arkadia_console`) reconciles that vocabulary to
  four lenses. Its `SurfaceLenses` component already documents the contract:
  "Each lens is a real navigation to `<surface-path>/<lens-id>` … A lens is
  never a decorative pill."
- **Measured source state before this change** (`web/arkadia_console/src/pages/SolariunPage.tsx`
  at base SHA): a page-local `<span>` strip rendered the four lens labels with
  active styling but no `onClick` and no navigation; content ignored `section`
  entirely; `/solariun/bogus` silently showed the projects view while the
  address bar claimed `/solariun/bogus`. `App.tsx` passed no `onNavigate` to
  `SolariunPage`.
- The archive is preserved untouched; this is a recovery of the interaction
  pattern, not a restoration of the archived runtime.

## 2. Changed paths

- `web/arkadia_console/src/pages/SolariunPage.tsx` — strip replaced with the
  shared `SurfaceLenses` (routed, `aria-current`, `data-testid`); per-lens
  content: `projects` keeps the real `/solspire/projects` read; `knowledge` and
  `weaver` name their canonical owning surface and navigate to it (no duplicate
  read); `memory` states that no verified read contract exists; an undeclared
  section renders the not-a-lens state listing the reconciled lenses. The
  `UNKNOWN` classification is a named constant, not an advertised route.
- `web/arkadia_console/src/App.tsx` — one line: the solariun case now binds
  `onNavigate={navigate}` (same as the novanet case).
- `tests/test_solariun_lens_contract.py` — new contract suite (12 tests).
- `docs/control-plane/evidence/prism-recursive-recovery-01/` — this record and
  the machine-readable `WORK_LEDGER.json`.

Out of scope and untouched: `lib/router.ts` (PR #505 owns legacy aliases),
backend handlers, all other surface pages owned by open PRs.

## 3. Verification (exact commands and results, base-SHA baseline first)

| Command | Baseline @ base SHA | After candidate |
|---|---|---|
| `cd web/arkadia_console && pnpm run build` (`tsc --noEmit && vite build`) | PASS (exit 0) | **PASS** (exit 0, `dist/assets/index-C7u-ubKz.js`) |
| `python3 -m pytest tests/test_solariun_lens_contract.py -q` | n/a (new) | **PASS — 12 passed** |
| `python3 -m pytest tests/test_solariun_lens_contract.py tests/test_canonical_frontend_routing.py tests/test_frontend_arkadia_console_rebuild_01.py tests/test_aeas05_canonical_frontend_acceptance.py tests/test_console_endpoint_registry_contract.py tests/test_console_authority_chain.py tests/test_console_shell_nav_contract.py -q` | 85 passed | **97 passed** |
| `python3 -m pytest tests/test_solariun_experience_consolidation_01.py tests/test_solariun_knowledge_slice_01.py tests/test_solariun_x01_x12_canonical_recovery.py tests/test_prism_pass_c_surface_ownership.py tests/test_baseline_fingerprint.py tests/test_prism_console_ci_wiring.py -q` | not run pre-edit | **PASS — 89 passed** |
| `python3 -m pytest tests/test_m02a_ci_gate_integrity.py -q` | not run pre-edit | **PASS — 68 passed** (CP10 path allowlist accepts the new files) |
| `python3 -m pytest tests/architecture -q` | not run pre-edit | **PASS — 11 passed** |

Environment notes: `pnpm install --frozen-lockfile` (pnpm 10.26.1) succeeded;
`pytest 9.1.1` + `requirements.txt` installed this session; Node v22.23.2
executes the router probes. The new suite executes the console's real
`resolvePath` in Node (not string-matching) for `/solariun/<lens>` and
`/solariun/bogus`, and carries negative controls for each load-bearing
detector.

During implementation, two pre-existing guards caught real mistakes in the
candidate and were repaired in the candidate (not weakened):
`test_no_lens_control_is_decorative` / `test_the_lens_strip_is_declared_once`
(the first draft reused the `-lens-` testid namespace for a non-control
element) and `test_advertised_contract_strings_are_recorded` (a literal
`contract="UNKNOWN"` read as an advertised route). No test was edited.

## 4. Review findings (diff reviewed against the work-item contract)

- Only the intended responsibilities changed; diff = 2 source files (+129/−36),
  1 new test, 1 evidence dir.
- Every visible control has real, authorized behavior: lenses navigate through
  the shared router; the two "Open …" buttons navigate to declared surfaces
  that exist in the composition root. No mutation of any kind was introduced
  (read-only surface; no writes, no new endpoints).
- States are truthful: the projects read is the same owner-scoped contract as
  before; `memory` and undeclared sections render explicit not-wired states;
  `knowledge`/`weaver` do not re-read another surface's contract.
- No security or authority check weakened: `requiresAuth` on Solariun, auth
  threshold, and server-side checks untouched.
- No duplicate UI or second source of truth: the strip is the shared
  component; authority is named, not forked.

## 5. Limitations / risks (explicitly not claimed)

- **NOT TESTED (browser):** no browser/e2e harness exists in this sandbox.
  Rendering, `aria-current` behavior, and click-through navigation are covered
  by the build and the executed-router + source-contract suite, not by an
  observed browser session. Production verification is likewise not claimed.
- The `/solspire/projects` read still fires on non-projects lenses (hooks must
  run unconditionally); request volume is unchanged from base.
- Legacy Prism inbound aliases into Solariun (`/codex`, `/loops`, `/dashboard`,
  `/settings`, `/account`, `/personal-echofeild`) are **not** reconciled here —
  `lib/router.ts` is owned by open PR #505; recorded as the next work item
  (PRR-02) to be coordinated, not started unilaterally.
- Merging and deployment are out of authority: this change is present in a
  branch only.

## 6. Next dependency / recommended action

Draft PR against `main` @ `dfbd230`; human review and required checks; then
PRR-02 (Solariun legacy alias families) coordinated with PR #505's alias work.
