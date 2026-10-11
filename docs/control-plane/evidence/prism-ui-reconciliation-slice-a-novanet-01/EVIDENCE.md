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
