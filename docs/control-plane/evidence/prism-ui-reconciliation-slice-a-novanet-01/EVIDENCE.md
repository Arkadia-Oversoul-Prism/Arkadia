# Slice A — NovaNet hub surface (Prism UI reconciliation)

Bounded objective: add the **NovaNet hub** surface to the canonical console
(`web/arkadia_console`), reconciling the archived Prism `/nexus` route as an
**alias** of one canonical surface rather than a second route. Directive:
`docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` §5.

Authority: human retains merge, production deployment, and acceptance. Nothing
in this record claims any of the three.

## Revision binding

- Work branch: `feat/prism-ui-reconciliation-overnight-01` (draft PR #418).
- `origin/main` at the start of the pass: `d2670ce8b41c500df5cf475f7c6526016c7bd3aa`
  (merge of #417). The branch is a descendant of `main` via `42ade73`.

## Inventory first (§3/§5.2)

`docs/control-plane/overnight/PRISM-UI-INVENTORY.md` recorded `/nexus` → legacy
view `novanet`, legacy source `NovaNetPage.tsx`, backend contracts
`/api/transmissions` + `/api/echoes`, decision **Adapt (Slice A)**, status
`MISSING`. That row is now `IMPLEMENTED`.

Both backend contracts were re-verified against the live FastAPI route table
(`app.openapi()`), not assumed from the inventory:

| Endpoint | Source | In `openapi()["paths"]` |
|---|---|---|
| `/api/transmissions` | `api/transmissions.py:103` | True |
| `/api/echoes` | `api/main.py:1660` | True |

Response shapes were read from the handlers and the TypeScript types were
written to match them, not inferred:

- `list_transmissions` returns `{"transmissions": [...], "total": int}`; each post
  carries `id`, `author` (`id`/`name`/`avatar`/`role`), `content`, `timestamp`.
- `echoes_feed` returns `{"source", "public": [...], "personal": [...], "matrix":
  {"geometry", "dimensions": [...], "aggregate"}}`; each entry carries
  `id`/`kind`/`scope`/`title`/`category`/`preview`/`source`/`resonance`/`priority`.

## Changes

| Path | Change |
|---|---|
| `web/arkadia_console/src/lib/surfaces.ts` | `"novanet"` added to `SurfaceId`; `SurfaceDef` entry with canonical `path: "/novanet"`, accent `text-azure` |
| `web/arkadia_console/src/lib/router.ts` | `PATH_ALIASES` map (`/nexus` → `novanet`) resolved before path parsing |
| `web/arkadia_console/src/App.tsx` | `NovaNetPage` imported; `case "novanet"` added to the surface switch |
| `web/arkadia_console/src/lib/endpoints.ts` | `transmissions`, `echoes` endpoint constants |
| `web/arkadia_console/src/lib/types.ts` | `Transmission*` and `Echo*` response types |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | new page: public field + echoes reads, honest `ContractState` / `NotYetWired` states |
| `tests/test_console_shell_nav_contract.py` | alias-family regression tests + 2 negative controls |
| `docs/control-plane/overnight/PRISM-UI-INVENTORY.md` | `/nexus` row status `MISSING` → `IMPLEMENTED` |

The four legacy hub sub-views (`/nexus/ims`, `/nexus/grove`, `/nexus/larder`,
`/nexus/distribution`) remain `MISSING` in the inventory and render an explicit
`NotYetWired` state inside the surface — they are **not** routed as separate
top-level surfaces, so no new routes were invented for un-reconciled contracts.

## Verification (measured in this environment)

| Check | Command | Result |
|---|---|---|
| Full suite, before | `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | 35 failed / 2114 passed / 34 skipped / 1 error |
| Full suite, after | same | 35 failed / 2114 passed / 34 skipped / 1 error |
| Failing/error node **set** | normalized + `comm -3` | **identical**, sha256 `d7490390ece4a5d428c1b7b534d62d94d0c8419e1dd199fae202d3b1f7dfc08c` (36 nodes) both sides |
| Architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| Targeted frontend guards | `test_frontend_arkadia_console_rebuild_01` + `test_canonical_frontend_routing` + `test_aeas05_canonical_frontend_acceptance` + `test_console_shell_nav_contract` | **44 passed** (was 40; +4 new alias tests) |
| Typecheck + build | `corepack pnpm exec tsc --noEmit && corepack pnpm exec vite build` | exit 0 — 63 modules, `dist/assets/index-DiDDeGDD.js` 34.96 kB |
| CP10 mutation boundary | `printf '<paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS (exit 0) |

Regression verdict: **zero node-set delta**. The `+4 passed` is exactly the new
alias tests (`--collect-only` on the file: 15 nodes, was 11).

Environment caveat (recorded, not a defect): the absolute counts here
(35F / 2114P / 34S) differ from the inventory's bound-revision baseline
(19F / 2133P / 20S, node-set sha256 `1ef23f26…`, 20 nodes) because the installed
dependency set differs in this sandbox. The before/after pair above was measured
in the **same** environment, so the regression claim is the *node-set identity*,
never the absolute count — consistent with the repository rule that a failure
count delta alone is not attributable evidence.

## Alias-family regression (§5.6)

`test_console_shell_nav_contract.py` now asserts, over the live tree:

1. every `PATH_ALIASES` entry targets a **declared** `SurfaceId`;
2. no alias key **collides** with a canonical surface path (no duplicate route, §5.1);
3. `/nexus` resolves to `novanet` and `/nexus` is **not** a declared surface path.

Two negative controls exercise the same detector the live assertion uses, so the
guard cannot be disarmed by editing the console source alone:

- an alias targeting an undeclared surface is reported;
- an alias key that shadows a canonical path is reported.

Both controls are proven non-vacuous (`assert mutated != original`).

## Route-shadowing (§5.3)

`/novanet` and `/nexus` match **only** the SPA catch-all in the real FastAPI route
table; neither is a backend handler nor a reserved API prefix. Positive controls
`/health` and `/api/echoes` resolve to real routes, so the detector is not
trivially true. Total route objects inspected: 61.

## Explicit non-claims

- **No merge, no deployment, no production acceptance.** PR #418 stays draft;
  the human decides.
- No claim about the canonical runtime `https://arkadia-qzu4.onrender.com`
  serving this surface — the console has not been deployed with this change.
- `web/arkadia_console/dist/` is untracked build output; not committed.
- The remaining `MISSING` inventory rows are known gaps, not defects in `main`.

---

# Pulse 4 — Slice A.2: the NovaNet lens strip is now a control, not decoration

Bounded objective: remove the decorative control the directive §4 forbids from
the NovaNet surface and make its lens strip a single, navigable, regression-
protected control. Authority: human retains merge, deployment, acceptance.

## Revision binding

| Item | Value |
|---|---|
| `main` (fetched) | `d2670ce8b41c500df5cf475f7c6526016c7bd3aa` |
| Branch head at pulse start | `75bbd85956a61d1ec8f4fae10d0d42b5f8e06227` |
| Ancestry | `main` is an ancestor of the branch (`0 behind / 2466 ahead`) |

## The defect (measured, not inferred)

`pages/NovaNetPage.tsx` rendered each lens as
`<span data-testid={`novanet-lens-${l.id}`}>` with **no `onClick`** — a control
that looks like navigation and does nothing (§4: "No decorative controls that
do nothing"). The legacy shell it reconciles, `PrismInteriorShell.tsx`
`SurfaceButton`, returns a real `<button type="button" onClick aria-current>`,
so the console was a regression against the very pattern it recovers.

Four of the six pills (`ims`, `grove`, `larder`, `distribution`) additionally
pointed at contracts that do not fit this client: `/api/ims/inquiries` is
sovereign-key gated (the `apiClient` sends a Bearer token only), so a working
lens for it could only ever fail.

## Change

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/SurfaceLenses.tsx` | **new** — the one lens strip: every lens is `<button onClick={() => onNavigate(surface, l.id)} aria-current>` navigating through the shared router |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | lens strip replaced by `<SurfaceLenses>`; lenses narrowed to `field`/`echoes`/`hub`; `onNavigate` prop added |
| `web/arkadia_console/src/App.tsx` | `case "novanet"` binds `onNavigate={navigate}` (the router's own navigate) |
| `tests/test_console_shell_nav_contract.py` | §4 guard: 5 new tests (2 live assertions + 3 negative/robustness controls) |

The un-reconciled hub sub-views are **not** rendered as controls — a lens that
cannot navigate is not a control. They are stated honestly in the `hub` lens's
`NotYetWired` note, and an unknown section still renders the surface's honest
state rather than a silent default. No new route, no local sub-view state, no
second navigation model (§5.1/§5.4).

## Verification (measured in this environment, same location both sides)

| Check | Baseline (`75bbd859`) | After | Verdict |
|---|---|---|---|
| Full suite | 35 failed / 2118 passed / 34 skipped / 1 error | 35 failed / 2123 passed / 34 skipped / 1 error | `+5 passed` |
| Failing/error **node set** | 36 nodes, ids-sha256 `71522b9450fed649c107a2701db3e30b22d706bc9e4bc5f99fb1eb23000cf0f4` | identical, same sha256 | **zero node-set delta** (`diff` empty) |
| Architecture fitness | — | `11 passed` | no regression |
| Targeted frontend guards (4 files) | — | `49 passed` (was 44) | `+5`, exactly the new tests |
| Guard test definitions | 15 | 20 | `+5` attributes the `+5 passed` |
| `tsc --noEmit && vite build` | — | exit 0, 64 modules, `assets/index-CRYx0n-6.js` 35.43 kB | build passes |
| `python -m py_compile api/main.py` | — | OK; `api/main.py` 2499 lines (< 2600) | boot code untouched |
| CP10 boundary judge | — | PASS (exit 0) | every changed path admitted |

The before/after pair was measured by stashing the change **in place**, so the
suite ran from the same working directory on both sides; the regression claim is
the node-set identity, never the absolute count (this sandbox's dependency set
differs from CI's).

## Negative controls — proven against the live tree

The §4 guard is not a source-level assertion only. It was proven by mutating the
**real** source and observing the failure:

1. `SurfaceLenses.tsx` rewritten to the exact pre-repair shape (a `<span>` with a
   per-lens testid) → `2 failed, 18 passed`; restored byte-identically
   (`sha256 55098818f6c7942f75b282af92075e74c6a6682ccff0142270e2480604a3cedb`).
2. `App.tsx` binding removed (`<NovaNetPage section={route.section} />`) →
   `1 failed, 19 passed`; restored byte-identically
   (`sha256 bf64817e308bac9fcdab0ff29cd6a470b0086aa69a958ca03637b211c2dedb90`).

`test_detector_reads_the_whole_tag_when_a_handler_contains_an_arrow` covers the
harder form: a naive `<[^>]*>` match stops at the `=>` in an inline handler and
cannot see the `onClick`, so the scanner tracks brace depth and quotes.

## Explicit non-claims

- **No merge, no deployment, no production acceptance.** PR #418 stays draft.
- No claim about the canonical runtime serving this change; the console has not
  been deployed with it.
- No Vercel deployment was created, promoted, or treated as evidence (§8).
- The `hub` lens's `NotYetWired` state is an honest gap statement, not a defect
  claim against `main`.

