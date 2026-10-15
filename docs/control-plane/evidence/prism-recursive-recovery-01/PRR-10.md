# PRR-10 — Home identity-aware primary entry action

Mission: `prism-recursive-recovery-01` — "Recover useful Prism UI capabilities,
interaction patterns, and visual coherence into the canonical Arkadia Console
application."

## Objective

Recover the archived Prism home's **identity-aware primary entry action** into the
canonical console Home surface (`web/arkadia_console/src/pages/HomePage.tsx`).

The archived Prism home rendered exactly one primary entry whose target depended on
the viewer's identity — `Enter Arkadia` for an anonymous visitor, `Open Solariun`
for a signed-in node — plus a secondary action, then a portal grid to the other
surfaces. The console HomePage kept the portal grid but had **no primary action**:
a returning, authenticated node landing on `/` had no single obvious way back into
its workspace.

## Evidence of the recovery gap

- Console pre-fix `HomePage.tsx` rendered `Page` → `Panel` → a flat
  `SURFACES.filter(s => s.id !== "home").map(Portal)` grid. No primary entry, no
  identity branching.
- Archived reference, `archive/frontend/arkadia-prism/web/public_prism/src/App.tsx`
  `function Home` (line 90), renders `data-testid="button-home-oracle"` with
  `onNavigate(isAuthenticated ? 'solariun' : 'gate')` and label
  `{isAuthenticated ? 'Open Solariun' : 'Enter Arkadia'}`, plus
  `data-testid="button-home-private"` secondary and the `PortalDoor` grid.

## Change

`web/arkadia_console/src/pages/HomePage.tsx`:

- adds a local `entryActions(isAuthenticated)` helper returning a `primary` and a
  `secondary` action, branching on identity;
- renders an **Entry** panel above the portal grid with two controls,
  `data-testid="home-entry-primary"` and `data-testid="home-entry-secondary"`, each
  wired to the shared `onNavigate`.

Targets (all **declared** canonical surfaces, none invented):

| viewer | primary | secondary |
|---|---|---|
| signed in | `solariun` (Open Solariun) | `solspire` (Open the team workspace) |
| anonymous | `login` (Enter Arkadia) | `about` (See the architecture) |

**Deviation from the archive, deliberate and evidence-backed.** The archived home
routed an anonymous visitor to a `gate` surface. The console declares no `gate`
surface (its `SurfaceId` union has `login`), and creating one would be a *second*
surface. The anonymous primary therefore targets the real sign-in surface `login`.
The archive's own landing page does the same thing for its login button
(`ArkadiaLandingPage.tsx:53`, `onNavigate(authenticated ? 'solspire' : 'login')`),
so `login` is the faithful console spelling of the archived intent.

## Files changed

- `web/arkadia_console/src/pages/HomePage.tsx` (source)
- `tests/test_prism_home_entry_contract.py` (new guard, 7 tests)
- `docs/control-plane/evidence/prism-recursive-recovery-01/PRR-10.md` (this record)

## Verification

| check | command | result |
|---|---|---|
| new guard | `python -m pytest tests/test_prism_home_entry_contract.py -q -rEf` | **7 passed** |
| derived console domain | `python -m pytest -q $(python scripts/console_contract_domain.py) -rEf` | **433 passed** |
| wiring judge | `python -m pytest tests/test_prism_console_ci_wiring.py -q -rEf` | **30 passed** |
| architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| frontend build | `corepack pnpm install --frozen-lockfile && corepack pnpm build` | **built in 1.57s** |

### Guard shape

`tests/test_prism_home_entry_contract.py` asserts, against the live source:

1. a primary **and** secondary entry control exist and are wired to `onNavigate`;
2. the entry is identity-aware (branches on `isAuthenticated`) and the primary
   target differs by identity (`solariun` vs `login`);
3. every entry target is a **declared** `SurfaceId`;
4. each target resolves, through the console's **executed** `resolvePath` (run in
   Node), to the surface it names — including that `/enterprise` → `solspire` and
   that `/solspire` (a reserved backend namespace) does **not** resolve to the
   SolSpire surface.

Negative controls are carried for the two load-bearing detectors — the
"entry vs portal-grid-only" detector and the "invented target" detector — so a
detector that always passes is itself caught.

The guard names the console with `Path` segments, so it enters the **derived**
console-contract domain (`scripts/console_contract_domain.py`) automatically: the
domain grew 23 → 24 and the wiring judge stayed green, with no workflow edit needed.

## Regression boundary

No change to `main`'s failing/error node set is claimed here — this pass did not run
the full suite twice. The change is confined to one console page, one new test
module, and one evidence file; it touches no shared shell file
(`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`, `types.ts`,
`SurfaceLenses.tsx`) and no backend surface. The frontend build is byte-clean.

## Authority boundary

- No merge, no deploy, no acceptance — a draft PR only.
- `docs/control-plane/evidence/prism-recursive-recovery-01/WORK_LEDGER.json` is
  **owned by open PR #521** and was deliberately **not** edited. The ledger entry
  for this item (a new `PRR-10`) is a follow-on to be made by whichever change owns
  the ledger at merge time; this file is the durable record until then.

## Remaining uncertainty

- The archived home also offered a `FieldPulse` element and a different subtitle
  voice; those are visual/typographic recoveries, out of this slice's scope.
- Whether the console should grow a real `gate` surface (separate from `login`) is a
  routing/navigation decision owned by LANE 1, not asserted here.
