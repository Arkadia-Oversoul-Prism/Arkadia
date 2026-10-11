# Prism UI Reconciliation — Feature / Route Inventory (first pulse)

**Status:** Inventory artifact for the overnight workstream. Evidence, not an implementation.
**Prepared:** 2026-10-11
**Workstream:** `feat/prism-ui-reconciliation-overnight-01` (PR #418)
**Directive:** `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` §3 (inventory before redesign)
**Authority:** Human retains merge, production-deployment, and acceptance authority. No merge, deployment, or acceptance is claimed by this document.

This is the §3 "first pulse" deliverable: a checked-in feature/route reconciliation matrix produced **before** any redesign. Every row is derived from live source in this repository, not from memory. Where a fact could not be established from source, the cell reads `UNKNOWN`.

## 0. Revision binding

| Item | Value |
|---|---|
| `main` at inventory time | `d2670ce8b41c500df5cf475f7c6526016c7bd3aa` (Merge PR #417) |
| Branch base (directive) | `1fd96e767575ade56e953a02fcf8f1db46073336` (PR #415 merge) |
| Branch head at inventory time | `42ade73b75cf9…` (merge of `main` into the branch) |
| Reconciliation | `main` merged into the branch; composed tree **0 behind / 4 ahead**; no force-push |

## 1. Method and oracles

- **Archive (legacy Prism):** `archive/frontend/arkadia-prism/web/public_prism/src/` — 123 `.ts(x)` files, 22 top-level components, 51 page modules (incl. `pages/dashboard/`, `pages/knowledge/`).
- **Active console:** `web/arkadia_console/src/` — 24 `.ts(x)` files, 9 page modules (35–91 lines each).
- **Route oracle:** legacy route tables are read from `App.tsx` (`resolvePath`, `routeForView`, `compatibility`, `direct`, `SOLSPIRE_LENSES`). Console routes are read from `src/lib/surfaces.ts` + `src/lib/router.ts`.
- **Backend-contract oracle:** the **real FastAPI route table** via `app.openapi()` (288 paths at the bound revision). A literal `grep` of source is *not* used as the oracle — it under-reports prefix-composed routes (e.g. `/api/lab/*` is composed from `APIRouter(prefix="/api/lab")`). `archive/legacy_python/` on `PYTHONPATH` shadows the `weaver` package and suppresses the SolSpire router mount; it must be **off** `PYTHONPATH` when measuring the route table.

## 2. Route reconciliation matrix

Legacy routes are from `archive/.../src/App.tsx`. "Current surface" is the console surface in `web/arkadia_console/src/lib/surfaces.ts`. "Backend contract" is verified against `app.openapi()` unless noted.

| Legacy route | Legacy view / section | Legacy source | Current surface | Backend contract | Decision | Status |
|---|---|---|---|---|---|---|
| `/` `/home` | home | `App.tsx` direct | `home` → `/` | `/api/version`, `/health` | Reuse (shell) | IMPLEMENTED |
| `/living-gate` `/gate` | gate | `App.tsx` direct | — (auth is `login`) | `/api/me` (auth) | Adapt → sign-in | DEFERRED |
| `/oracle` `/commune` | commune | `ArkanaCommune.tsx` | `arkana` → `/arkana` | `/api/commune/resonance`, `/api/commune/threads` | Reuse (Slice C) | PARTIAL |
| `/nexus` | novanet | `NovaNetPage.tsx` | `novanet` → `/novanet` (legacy `/nexus` aliased) | `/api/transmissions`, `/api/echoes` | Adapt (Slice A) | IMPLEMENTED |
| `/nexus/ims` | ims | `IMSArchivePage.tsx` | — | `/api/ims/inquiries`, `/api/ims/inquiry` | Defer | MISSING |
| `/nexus/grove` | grove | `SpiralGrovePage.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/nexus/larder` | larder | `LivingLarderPage.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/nexus/distribution` | distribute | `DistributePage.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/encyclopedia` | encyclopedia | `NexusSpiralCodex.tsx` | — | `/api/codex`, `/api/scrolls` | Defer | MISSING |
| `/spiral-codex` | spiral-codex | `SpiralCodexFeed.tsx` | — | `/api/scrolls`, `/api/codex` | Defer | MISSING |
| `/offerings` | offerings | `OfferingsPage.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/future-skills` `/challenge` | challenge | `FutureSkillsChallenge.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/reset` | reset | `CoherenceReset.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/pulse` | pulse | `ArkadianPulse.tsx` | — | `/api/heartbeat` | Defer | MISSING |
| `/reasomate` | reasomate | `ReasoMatePage.tsx` | — | `/api/messages` | Adapt (Slice C) | MISSING |
| `/sci` | sci | `SpiralCommandInterface.tsx` | — | `UNKNOWN` | Defer | MISSING |
| `/solspire` | solspire | `SolSpireConsole.tsx` | `solspire` → `/enterprise` | `/solspire/projects` etc. | Adapt (Slice D) | PARTIAL |
| `/solspire/voice` | voice | `SolspireVoice.tsx` | — | `/api/tts` | Defer | MISSING |
| `/solariun` + 13 sections | solariun | `SolariunConsole.tsx` | `solariun` → `/solariun` | `/api/me/field`, `/api/me/codex` | Adapt (Slice B) | PARTIAL |
| `/codex` `/knowledge-os` | solariun/knowledge | `pages/knowledge/*` | `knowledge` → `/knowledge` | `/api/knowledge/*` | Adapt (Slice E) | PARTIAL |
| `/loops` | solariun/tasks | `OpenLoopsPage.tsx` | — | `/api/open-loops`, `/api/dashboard/loops` | Defer | MISSING |
| `/dashboard` | solariun/overview | `pages/dashboard/*` | — | `UNKNOWN` | Defer | MISSING |
| `/personal-echofeild` `/echofeild-matrix` | solariun/observatory | `PersonalEchofeild.tsx` | — | `/api/me/field`, `/api/echoes` | Adapt (Slice B) | MISSING |
| `/settings` `/account` | solariun/settings | `SettingsPage.tsx` | — | `/api/keys`, `/api/provider-keys` | Defer | MISSING |
| `/about` | about | `AboutArkadia.tsx` | `about` → `/about` | — (static) | Reuse | IMPLEMENTED |
| `/login` | login | `LoginPage.tsx` | `login` → `/login` | `/api/me` | Reuse | IMPLEMENTED |

Console surfaces with **no legacy counterpart** (new architecture): `engineering-lab` → `/engineering-lab`, `weaver` → `/weaver` (both `requiresAuth`).

### 2.1 Route and suffix conflicts to preserve

These are real collisions/aliases in the archive. They must be resolved deliberately (directive §5), not silently collapsed:

1. **`/solspire` is a reserved backend prefix.** `solspire/console_router.py` mounts `APIRouter(prefix="/solspire")`; the console correctly serves SolSpire on `/enterprise` (`surfaces.ts` comment + `tests/test_canonical_frontend_routing.py`). The legacy SPA occupied `/solspire` — a collision that is already repaired in the console and regression-guarded.
2. **`/nexus` is an alias of `novanet`** (`routeForView`: `novanet: '/nexus'`) and the hub's sub-views (`/nexus/ims`, `/nexus/grove`, `/nexus/larder`, `/nexus/distribution`) are nested paths, not separate top-level surfaces.
3. **`/solariun/*` sections reuse `SolSpireLens`** — 13 section ids shared between two different product boundaries (personal vs enterprise). Any reimplementation must not conflate them.
4. **Legacy compatibility aliases** (`/codex`, `/knowledge-os`, `/loops`, `/dashboard`, `/personal-echofeild`, `/echofeild-matrix`, `/settings`, `/account`) all redirect into `solariun/*` sections. Inbound-link compatibility must be checked before removing any.

## 3. Console → backend contract verification

All endpoints declared in `web/arkadia_console/src/lib/endpoints.ts` were resolved against `app.openapi()` (288 paths):

| Endpoint | Resolves |
|---|---|
| `/api/version`, `/health` | ✅ |
| `/api/me`, `/api/me/codex`, `/api/me/identity-spine`, `/api/me/field` | ✅ |
| `/api/commune/resonance`, `/api/commune/threads` | ✅ |
| `/api/knowledge/status`, `/graph`, `/timeline`, `/projects` | ✅ |
| `/api/lab/overview`, `/api/lab/engineering/{overview,sessions,agents,artifacts,gateway}` | ✅ |
| `/api/lab/engineering/n-atlas/catalog` | ✅ |
| `/solspire/projects` | ✅ |
| `/api/approvals` | ✅ |

**Result:** every declared console endpoint resolves to a real backend route at the bound revision. No phantom endpoint was found in `endpoints.ts`.

### 3.1 Environment caveat (measured, not a repo defect)

With `archive/legacy_python/` on `PYTHONPATH`, the boot log records
`[SOLSPIRE] Console router mount skipped: No module named 'weaver.agent'; 'weaver' is not a package`,
and `/solspire/*` + `/api/lab/*` are absent from the route table. This is **legacy-path shadowing**, not a repository defect: the legacy path contains a top-level `weaver.py` that shadows the tracked `weaver/` package. Route-table measurements must run with that path **off** `PYTHONPATH`. Recorded here so a future pulse does not mis-diagnose the mount skip as a regression.

## 4. Slice readiness (directive §4)

| Slice | Legacy depth | Console depth | Backend readiness | Next bounded move |
|---|---|---|---|---|
| A — shell / design system | `PrismInteriorShell`, `ArkadiaNavigation`, `ui.tsx` | `Shell.tsx`, `components/ui.tsx` | n/a (static) | Inventory nav/IA; pick one shell primitive to reconcile |
| B — Solariun / personal | `SolariunConsole`, `PersonalEchofeild`, `PersonalCodex`, `PersonalUploadZone` | `SolariunPage.tsx` (87 lines) | ✅ `/api/me/field`, `/api/me/codex` | Reconcile personal field entry points |
| C — Arkana / Oracle | `ArkanaCommune`, `OracleVoicePlayer`, `MarkdownViewer`, `ReasoMatePage` | `ArkanaPage.tsx` (88 lines) | ✅ `/api/commune/*` | Recover conversation canvas + voice controls |
| D — SolSpire / Radar | `SolSpireConsole`, `ProjectDashboard`, `OpportunityRadarPage` | `SolSpirePage.tsx` (35 lines) | ✅ `/solspire/projects` | Project navigation/detail workspace |
| E — Knowledge OS | `pages/knowledge/*` (7 modules) | `KnowledgePage.tsx` (46 lines) | ✅ `/api/knowledge/*` | Reconcile graph/timeline/search surfaces |
| F — Weaver / Lab | `SolSpireWorkspacePanels`, `EdenControlRoom` | `WeaverPage.tsx`, `EngineeringLabPage.tsx` | ✅ `/api/lab/*`, `/api/approvals` | Make run/authorization/evidence legible |

## 5. Baseline (measured at the bound revision)

| Check | Result |
|---|---|
| `tests/architecture` | **11 passed** (the contract's "9/10" does not reproduce; repo memory's 11/11 is correct) |
| Route/frontend guards (`test_frontend_arkadia_console_rebuild_01`, `test_canonical_frontend_routing`, `test_aeas05_canonical_frontend_acceptance`) | **29 passed** |
| Full suite (with project deps installed) | **19 failed / 2133 passed / 20 skipped / 1 error**; failing/error node set sha256 `1ef23f26b64e76ea182794aee2f975fbbf97ed8d1c8501e426f59979bf43a80a` (20 nodes) |
| `python -m py_compile api/main.py` | OK; `api/main.py` = **2499 lines** (budget 2600) |

The full-suite baseline was captured with dependencies installed. Without them the suite reports ~79 failed / 62 errors (missing `firebase-admin`, `grpcio` build failure); that figure is an environment artifact, not repository debt. **Compare failing/error nodes by identity, never by count.**

## 6. Next bounded move

Produce the **Slice A shell/navigation inventory** as the next pulse: enumerate the archived shell, navigation, and design-system primitives against the console's `Shell.tsx` + `components/ui.tsx`, and select **one** reconciliation primitive. No UI implementation is proposed in this document.

## 7. Explicit non-claims

- No merge, production deployment, or production acceptance was performed.
- No Vercel deployment was created, promoted, or treated as evidence. Canonical production remains `https://arkadia-qzu4.onrender.com` (ADR-016).
- UI implementation and browser/build evidence are **not** claimed. `web/arkadia_console` was not rebuilt in this pulse; the frontend build remains `NOT RUN`.
- Every row marked `MISSING` is a *known gap*, not a defect claim against `main`.

## 8. Pulse log (continuity — reconstruct from this, not from memory)

| Pulse | Branch head | Slice | Deliverable | Status |
|---|---|---|---|---|
| 1 | `42ade73b75cf9…` | — | this inventory (feature/route matrix) | IMPLEMENTED |
| 2 | `a5443d2a…` | A | `PRISM-UI-SLICE-A-SHELL-INVENTORY.md` + `test_console_shell_nav_contract.py` (11 tests) | IMPLEMENTED |
| 3 | `1a2a5561…` | A.1 | NovaNet hub surface (`/novanet`, `/nexus` alias) + evidence record | IMPLEMENTED |
| 4 | `75bbd859…` | A.2 | NovaNet lens strip reconciled to a navigable control (`SurfaceLenses.tsx`) + §4 guard | IMPLEMENTED |

### Pulse 3 — Slice A.1: NovaNet hub surface

`/nexus` row (§2) moved `MISSING` → `IMPLEMENTED`. Evidence:
`docs/control-plane/evidence/prism-ui-reconciliation-slice-a-novanet-01/EVIDENCE.md`.

- Surface added at canonical `path: "/novanet"`; legacy `/nexus` is an inbound
  **alias** via `PATH_ALIASES`, not a second surface (§5.1/§5.2).
- Both contracts re-verified against the live route table (`/api/transmissions`
  at `api/transmissions.py:103`, `/api/echoes` at `api/main.py:1660`); TS types
  written from the handler return shapes.
- The four hub sub-views (`/nexus/ims`, `/nexus/grove`, `/nexus/larder`,
  `/nexus/distribution`) remain `MISSING` and render an explicit `NotYetWired`
  state — no route invented for an un-reconciled contract.
- `api/main.py` **not** touched by this slice; `python -m py_compile api/main.py` OK.

### Baseline at pulse 3 (same-environment before/after)

| Check | Result |
|---|---|
| Full suite, before / after the slice | 35F / 2114P / 34S / 1E — both |
| Failing/error node **set** | identical; 36 nodes; sha256 `d7490390ece4a5d428c1b7b534d62d94d0c8419e1dd199fae202d3b1f7dfc08c` |
| `tests/architecture` | **11 passed** |
| Targeted frontend/route guards | **44 passed** (was 40; `+4` = new alias tests) |
| `tsc --noEmit && vite build` | exit 0 — 63 modules |
| CP10 mutation boundary | PASS |

The pulse-3 absolute counts differ from the §5 bound-revision baseline
(19F / 2133P / 20S, node-set sha256 `1ef23f26…`) by the installed dependency set
in that sandbox. The pulse-3 claim rests on **node-set identity measured in one
environment**, never on a count — per the repository rule that a count delta
alone is not attributable evidence.

### Next bounded move (proposed, not implemented)

Reconcile `/nexus/ims` (`IMSArchivePage.tsx`, `/api/ims/inquiries`) — the only
remaining hub row whose backend contract is already known. `grove`, `larder` and
`distribution` stay `UNKNOWN` and require contract discovery before any surface
is added. Do **not** invent routes for them.

### Pulse-3 explicit non-claims

- No merge, no deployment, no production acceptance. PR #418 remains a **draft**.
- No claim that `https://arkadia-qzu4.onrender.com` serves the NovaNet surface —
  the console has not been deployed with this change.
- No Vercel path used, promoted, or treated as evidence (directive §8).

### Pulse 4 — Slice A.2: the lens strip becomes a control

The `NovaNet primary rail + "More" lens strip` row (§2) moved `DEFERRED` →
`IMPLEMENTED`. Evidence:
`docs/control-plane/evidence/prism-ui-reconciliation-slice-a-novanet-01/EVIDENCE.md`
(pulse-4 section).

- **Defect measured, not assumed:** each lens rendered as
  `<span data-testid=…>` with no `onClick` — the directive §4 decorative-control
  class. The legacy `PrismInteriorShell.tsx` `SurfaceButton` it reconciles is a
  real `<button onClick aria-current>`.
- **Fix:** one shared `components/SurfaceLenses.tsx`; every lens is a real
  `<button onClick={() => onNavigate(surface, l.id)}>` navigating through the
  router `App.tsx` already owns. Lenses narrowed to the three the client can
  honestly serve (`field`/`echoes`/`hub`); the sovereign-key-gated IMS contract
  and the `UNKNOWN` grove/larder/distribution contracts are **not** rendered as
  controls and are stated in the `hub` lens's `NotYetWired` note.
- No new route, no local sub-view state, no second navigation model (§5.1/§5.4).
- **Guard:** `tests/test_console_shell_nav_contract.py` `+5` tests (15 → 20),
  carrying negative controls for the pre-repair shape, a removed `App.tsx`
  binding, and a handler containing `=>` (a naive `<[^>]*>` scan would miss the
  `onClick`).

### Baseline at pulse 4 (same-environment, same-location before/after)

| Check | Result |
|---|---|
| Full suite, before / after | 35F / 2118P → 35F / **2123P**, 34S / 1E both |
| Failing/error node **set** | identical; 36 nodes; ids-sha256 `71522b9450fed649c107a2701db3e30b22d706bc9e4bc5f99fb1eb23000cf0f4` |
| `tests/architecture` | **11 passed** |
| Targeted frontend/route guards | **49 passed** (was 44; `+5` = the new tests) |
| `tsc --noEmit && vite build` | exit 0 — 64 modules, 35.43 kB |
| CP10 mutation boundary | PASS (exit 0) |
| `python -m py_compile api/main.py` | OK; 2499 lines (< 2600 budget) |

The before side was measured by stashing the change **in place** (same working
directory), so the node-set identity is the load-bearing claim; the absolute
counts differ from CI's by the installed dependency set.

### Next bounded move (proposed, not implemented)

Reconcile `/nexus/ims` (`IMSArchivePage.tsx`) **only** as far as its real
contract allows: `/api/ims/inquiries` is sovereign-key gated and the console
`apiClient` sends a Bearer token only, so a working lens is not available without
an authorization decision. Record it as an honest blocked/not-wired state rather
than shipping a control that can only fail. `grove`, `larder` and `distribution`
remain `UNKNOWN` and require contract discovery before any surface is added.

### Pulse-4 explicit non-claims

- No merge, no deployment, no production acceptance. PR #418 remains a **draft**.
- No claim that `https://arkadia-qzu4.onrender.com` serves this change; the
  console has not been deployed with it.
- No Vercel path used, promoted, or treated as evidence (directive §8).
