# Prism UI Reconciliation — Slice A: Shell / Navigation / Design-System Inventory

**Status:** Inventory artifact for the overnight workstream. Evidence, not an implementation.
**Prepared:** 2026-10-11
**Workstream:** `feat/prism-ui-reconciliation-overnight-01` (PR #418)
**Directive:** `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` §3 (inventory before redesign), §4 Slice A
**Predecessor:** `docs/control-plane/overnight/PRISM-UI-INVENTORY.md` (first pulse; §6 named this document as the next bounded move)
**Authority:** Human retains merge, production-deployment, and acceptance authority. No merge, deployment, or acceptance is claimed here.

This is the §3 deliverable for **Slice A** (product shell and design-system reconciliation). Every cell is derived from live source at the revision below, read with `cat`/`grep` — not from memory or from a rendered screenshot. Where a fact could not be established from source it reads `UNKNOWN`.

## 0. Revision binding

| Item | Value |
|---|---|
| Branch head at inventory time | `a5443d2a680e28fd9d1881b2c5f8326912c45087` (first-pulse inventory) |
| `main` at inventory time | `d2670ce8b41c500df5cf475f7c6526016c7bd3aa` (Merge PR #417) |
| Reconciliation | `main` fully contained in the branch; composed tree **0 behind / 5 ahead** |
| Route/surface oracle | `web/arkadia_console/src/lib/surfaces.ts` + `src/lib/router.ts`; legacy `archive/frontend/arkadia-prism/web/public_prism/src/App.tsx` |
| Guard added this pulse | `tests/test_console_shell_nav_contract.py` (11 tests) |

## 1. Method

- **Legacy shell sources (Slice A):** `PrismInteriorShell.tsx` (98 lines), `ArkadiaNavigation.tsx` (65 lines), and the design tokens in `styles/arkadia-core.css`. Note the archive has **no `components/ui.tsx`** — legacy primitives are inline, per-page.
- **Console sources:** `components/Shell.tsx`, `components/ui.tsx`, `lib/surfaces.ts`, `lib/router.ts`, `lib/apiConfig.ts`, `index.css`, `tailwind.config.js`.
- **Detectors:** the shell/nav invariants in §4 are asserted by `tests/test_console_shell_nav_contract.py`, which carries a negative control per detector. The detectors were additionally proven against the **live tree** this pulse: appending a hardcoded origin to `apiConfig.ts` and deleting one composition case from `App.tsx` produced exactly `2 failed, 9 passed`; restoring both byte-identically returned `11 passed` (`git diff -- web/arkadia_console/src/` empty).

## 2. Shell and navigation matrix

| Legacy capability | Legacy route / suffix | Legacy source | Current surface | Backend contract | State / persistence | Decision | Test | Status |
|---|---|---|---|---|---|---|---|---|
| Interior shell for authenticated views | every interior view | `PrismInteriorShell.tsx` | `Shell.tsx` (single, always-mounted) | n/a (static) | Client-side; nav state is a single `useRouter()` | **Adapt** — console shell is the reconciled form | `test_shell_is_mounted_exactly_once` | IMPLEMENTED |
| Global top bar + slide-in drawer | all | `ArkadiaNavigation.tsx` (top bar + 288px drawer) | `Shell.tsx` (persistent left rail `md:`, horizontal strip below `md:`) | n/a | Client-side | **Adapt** — drawer replaced by a responsive rail; one nav model both breakpoints | `test_navigation_model_is_declared_exactly_once` | IMPLEMENTED |
| Grouped nav model (`Field` / `Nexus` / `Workspaces` / `System`) | all | `NAV_GROUPS` in `ArkadiaNavigation.tsx` | `NAV_SURFACES = SURFACES.filter(s => s.nav !== false)` in `Shell.tsx` | n/a | Derived from the surface table, not a second list | **Replace** — the console keeps one model | `test_navigation_model_is_declared_exactly_once` | IMPLEMENTED |
| NovaNet primary rail + "More" lens strip | interior | `PrismInteriorShell.tsx` (`PRIMARY` / `SECONDARY`) | `components/SurfaceLenses.tsx`, mounted by `pages/NovaNetPage.tsx` | `/api/transmissions`, `/api/echoes` (public) | Real navigation through the shared router; un-reconciled hub sub-views render `NotYetWired` | **Adapt** — legacy rail items were real `<button onClick>` navigations; the console strip is now a real navigation too (pulse 4, `75bbd859`+) | `test_no_lens_control_is_decorative`, `test_the_lens_strip_is_declared_once` | IMPLEMENTED |
| Identity persistence bar ("PRISM · AUTHENTICATED") | interior | `PrismInteriorShell.tsx` (`IdentityPersistence`) | `Shell.tsx` identity block (`display_name`, `identity · {state}`, sign in/out) | `/api/me`, `/api/me/identity-spine` | Read from `AuthContext`; honest `identityState` | **Adapt** | `test_shell_is_mounted_exactly_once` | PARTIAL |
| Per-user drawer shortcuts (Profile, Solariun, SolSpire, ReasoMate, Echo Field, Encyclopedia, Offerings) | all | `UserSection` in `ArkadiaNavigation.tsx` | `MISSING` | mixed | — | **Defer** — several targets are not yet surfaces | — | DEFERRED |
| Duplicate/aliased routes (`/nexus`→`novanet`, `/codex`, `/knowledge-os`, `/loops`, `/dashboard`, `/personal-echofeild`, `/echofeild-matrix`, `/settings`, `/account`) | 9 alias families | `App.tsx` (`compatibility`, `direct`, `routeForView`) | one canonical path per surface in `surfaces.ts` | — | — | **Replace** — one route per surface (directive §5.1) | `test_every_surface_id_has_a_path_and_the_union_matches_the_table` | IMPLEMENTED |
| Reserved-prefix collision: legacy SPA on `/solspire` | `/solspire` | `SolSpireConsole.tsx` | `solspire` → `/enterprise` | `/solspire/*` (backend-owned) | — | **Replace** — already repaired + guarded | `tests/test_canonical_frontend_routing.py` | IMPLEMENTED |

## 3. Design-system matrix

| Legacy token / primitive | Legacy source | Current token / primitive | Decision | Status |
|---|---|---|---|---|
| `--deep-azure #001F3F`, `--emerald-gold #D4AF37`, `--sky-blue #7FDBFF` | `styles/arkadia-core.css` | `tailwind.config.js` palette: `ink #080A11`, `panel #0E1120`, `line #1B2033`, `gold #C9A84C`, `emerald #00D4AA`, `azure #6A9FD8`, `violet #B08DE8` | **Adapt** — the console palette is the reconciled set; legacy triple retired | IMPLEMENTED |
| `.bioluminescent-ring`, `.shimmer-text` | `styles/arkadia-core.css` | `MISSING` | **Defer** — decorative only; no contract | DEFERRED |
| Per-page inline hex (e.g. `#6A9FD8`, `#B08DE8`, `#C9A84C` hardcoded across `PrismInteriorShell.tsx`) | `PrismInteriorShell.tsx` | none — console TSX carries **zero** hex literals | **Replace** — tokens only | IMPLEMENTED |
| Shared background field | inline gradients per legacy page | `.aurora-bg` (one layer, `index.css`) | **Adapt** | IMPLEMENTED |
| Content column | ad-hoc `maxWidth` per legacy page | `.page-column` (`max-width: 960px`) | **Adapt** | IMPLEMENTED |
| Type stack (Inter / Cinzel / IBM Plex Mono) | inline `fontFamily` strings | `fontFamily` in `tailwind.config.js` | **Adapt** | IMPLEMENTED |
| Shared UI primitives (loading / empty / error / auth / not-wired) | none in archive (inline per page) | `components/ui.tsx`: `Page`, `Panel`, `Facts`, `Loading`, `ContractState`, `NotYetWired` | **New** — console-native, matches directive §4 Slice A | IMPLEMENTED |

## 4. Invariants now regression-protected (Slice A)

`tests/test_console_shell_nav_contract.py` asserts, each with a negative control:

1. **One navigation model** — `NAV_SURFACES` is declared only in `Shell.tsx` and derives from `SURFACES`.
2. **One shell mount** — `<Shell>` appears only in `App.tsx`.
3. **One router** — `window.location.pathname` is read only in `lib/router.ts`.
4. **Surfaces are complete** — every `SurfaceId` has a path, paths are unique, and every declared surface has a composition case in `App.tsx` (a declared-but-unhandled surface silently renders the default page).
5. **No hardcoded deployment origin** — no `http(s)://` literal in console TS/TSX; `apiConfig.ts` resolves the base at runtime (directive §5.5).
6. **No page-local colour literals** — no hex in console TS/TSX; the palette lives in `tailwind.config.js` + `index.css`.
7. **No decorative controls** — every per-lens testid is a `<button>` carrying an `onClick` (directive §4), the lens strip is declared once, and the strip navigates through the shared router. Added in pulse 4 (`75bbd859`+).

This is deliberately disjoint from `test_canonical_frontend_routing.py` (reserved prefixes + backend-route shadowing), `test_aeas05_canonical_frontend_acceptance.py` (auth threshold + CP10 gate testids) and `test_frontend_arkadia_console_rebuild_01.py` (archive preservation). No guard was duplicated.

## 5. Selected primitive and next bounded move

**Selected primitive:** the **single navigation model** — `Shell.tsx` deriving `NAV_SURFACES` from `surfaces.ts`. It is the highest-value Slice A element because every other slice (B–F) adds a surface to that one table, so a second nav list or an unhandled surface would silently break all of them. It is already reconciled in the console; this pulse makes the reconciliation **regression-protected** rather than merely present.

**Next bounded move (Slice A continuation):** the NovaNet hub surface named here as the next move landed in pulses 2–3 (`1a2a5561`). Pulse 4 (`75bbd859`+) reconciled its lens strip into a shared, navigable control (row 4 above, now `IMPLEMENTED`) and protected it. The next bounded move is to reconcile the **remaining `MISSING`/`DEFERRED` Slice A rows** — the per-user drawer shortcuts — only for targets that are already surfaces; every other target stays deferred with its evidence, not invented. This is proposed, not implemented here.

## 6. Baseline (measured this pulse, at `a5443d2a`)

| Check | Result |
|---|---|
| `tests/test_console_shell_nav_contract.py` (new) | **11 passed** |
| Targeted frontend/route guards (rebuild + routing + AEAS-05 + shell/nav) | **40 passed** |
| `tests/architecture` | **11 passed** (the contract's "9/10" does not reproduce; first-pulse inventory's 11 is confirmed) |
| `cd web/arkadia_console && tsc --noEmit && vite build` | **exit 0** — 62 modules transformed, assets emitted |
| Live negative control | mutated tree `2 failed, 9 passed`; restored byte-identically to `11 passed` |

## 7. Explicit non-claims

- No merge, production deployment, or production acceptance was performed. Canonical production remains `https://arkadia-qzu4.onrender.com` (ADR-016).
- No Vercel deployment was created, promoted, or treated as evidence (directive §8).
- No UI source was changed this pulse: Slice A is **inventory + regression protection**, not a redesign. Every row marked `MISSING`/`DEFERRED` is a known gap, not a defect claim against `main`.
- The build result is a local build of the branch, not production acceptance.
