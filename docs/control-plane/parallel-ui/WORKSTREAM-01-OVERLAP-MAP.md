# Workstream 1 — Shell Overlap Map (first task)

**Status:** inventory + contract coverage. Evidence, not an implementation. No merge, deployment, or acceptance.
**Prepared:** 2026-10-11
**Branch:** `feat/prism-parallel-01-shell-implementation` (PR #423)
**Instructions:** `docs/control-plane/parallel-ui/AGENT-01-SHELL.md`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`

This is the §1 deliverable of `AGENT-01-SHELL.md`: reconstruct current `main`, PR #418,
the archived shell files and the route contracts, and record the exact SHAs and the
overlapping paths. Every cell is read from live source at the revisions below
(`git`, the GitHub REST API, `cat`/`grep`) — not from memory, prose, or a rendered screenshot.

## 0. Revision binding

| Item | Value | How measured |
|---|---|---|
| `main` | `a29a9b8f18ada55cb9457ea3cdab98414522a4e8` | `git rev-parse origin/main` |
| PR #423 head (this branch) | `1fd66fc5e20c63b354d780ca39cb5beece9d9afd` | `git rev-parse HEAD` |
| PR #423 base | `main` (`a29a9b8f`) | `GET /repos/.../pulls/423` |
| PR #418 head | `34c9a58b1da041e729385a7e8eb82a5c2c429f6c` | `GET /repos/.../pulls/418` |
| PR #418 base | `d2670ce8b41c500df5cf475f7c6526016c7bd3aa` (PR #417 merge) | `GET /repos/.../pulls/418` |
| PR #418 state | **open, draft, `mergeable: true`, `mergeable_state: unstable`**, 14 files, +1483/−0 | same |
| PR #418 checks at its head | 12 `completed/success`, 1 `in_progress` (`validate`) | `GET /commits/34c9a58b.../check-runs` |
| Composed tree | `git merge-base --is-ancestor` + `rev-list --left-right --count` (below) |

`main` moved from the base recorded in `SHARED-CONTRACTS.md` (`d2670ce8`) to `a29a9b8f`
(PR #419, the governance contract). #418 has **not** been rebased onto that merge.

Measured (`git merge-base --is-ancestor <sha> 34c9a58b`):

| SHA | ancestor of #418 head? |
|---|---|
| `d2670ce8` (PR #418's own base) | **yes** |
| `a29a9b8f` (current `main`) | **no** |

`git rev-list --left-right --count a29a9b8f...34c9a58b` → **1 / 12**: #418's head is 12
commits ahead of current `main` and **1 behind it**. So `SHARED-CONTRACTS.md`'s "`main`
fully contained in the branch" holds only against #418's *old* base, not against current
`main` — #418 is now a divergent branch, and it is still a draft. No human has chosen a
split or a migration strategy, so **its paths remain off-limits to this workstream**
(§3 below). Merging or rebasing it is not this workstream's call.

## 1. PR #418 measured patch map — overlap set

Measured from `GET /pulls/418/files` and a `git cat-file -e origin/main:<path>` per path
(`EXISTS` = the file is already tracked on `main`; `NEW` = #418 adds it).

| #418 path | on `main`? | +/- | Workstream-1 ownership |
|---|---|---|---|
| `web/arkadia_console/src/App.tsx` | EXISTS | +3 | **OVERLAP — do not edit** |
| `web/arkadia_console/src/lib/router.ts` | EXISTS | +14 | **OVERLAP — do not edit** |
| `web/arkadia_console/src/lib/surfaces.ts` | EXISTS | +12 | **OVERLAP — do not edit** |
| `web/arkadia_console/src/components/SurfaceLenses.tsx` | NEW | +47 | **OVERLAP — do not edit** |
| `web/arkadia_console/src/lib/endpoints.ts` | EXISTS | +3 | **OVERLAP — do not edit** |
| `web/arkadia_console/src/lib/types.ts` | EXISTS | +48 | **OVERLAP — do not edit** |
| `tests/test_console_shell_nav_contract.py` | NEW | +448 | **OVERLAP — do not edit** |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | NEW | +152 | Workstream 2's feature surface; do not duplicate |
| `AGENTS.md` | EXISTS | +25 | coordinator-owned |
| `docs/control-plane/evidence/console-complete-build/OVERNIGHT-BUILD.md` | EXISTS | +7 | coordinator-owned |
| `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` | NEW | +188 | coordinator-owned directive |
| `docs/control-plane/overnight/PRISM-UI-INVENTORY.md` | NEW | +247 | coordinator-owned inventory |
| `docs/control-plane/overnight/PRISM-UI-SLICE-A-SHELL-INVENTORY.md` | NEW | +88 | **#418's own shell inventory** — do not compete |
| `docs/control-plane/evidence/prism-ui-reconciliation-slice-a-novanet-01/EVIDENCE.md` | NEW | +201 | workstream 2 evidence |

The comment that opened this task names seven of these (`App.tsx`, `router.ts`,
`surfaces.ts`, `SurfaceLenses.tsx`, `endpoints.ts`, `types.ts`,
`test_console_shell_nav_contract.py`). The measurement adds two more that were **not**
named and would otherwise be easy to walk into:

- `web/arkadia_console/src/pages/NovaNetPage.tsx` — the NovaNet feature surface
  (workstream 2's boundary; `AGENT-01-SHELL.md` forbids implementing its internals).
- `docs/control-plane/overnight/PRISM-UI-SLICE-A-SHELL-INVENTORY.md` — #418 already
  carries a Slice-A shell inventory. This workstream must not open a competing shell
  inventory; it records its own map here instead.

## 2. What #418 actually changes (so this workstream does not duplicate it)

Read from the patch (`GET /pulls/418` with `Accept: application/vnd.github.v3.diff`):

| File | Substance of the change |
|---|---|
| `lib/surfaces.ts` | adds `"novanet"` to the `SurfaceId` union and one `SURFACES` entry at `path: "/novanet"`, `accent: "text-azure"` |
| `lib/router.ts` | adds `export const PATH_ALIASES = { "/nexus": "novanet" }` and one lookup at the top of `resolvePath` |
| `App.tsx` | adds `case "novanet": return <NovaNetPage section={route.section} onNavigate={navigate} />` |
| `components/SurfaceLenses.tsx` | new shared lens strip; each lens is a real `<button onClick={() => onNavigate(surface, l.id)}>` |
| `lib/endpoints.ts` | adds `transmissions: "/api/transmissions"`, `echoes: "/api/echoes"` |
| `lib/types.ts` | adds `Transmission*` / `EchoEntry` / `EchoesFeed` shapes |
| `tests/test_console_shell_nav_contract.py` | new 448-line source-level guard: one nav model, one shell mount, one router, surface→composition completeness, alias soundness, no hardcoded origin, no hex literals, no decorative lens controls |
| `pages/NovaNetPage.tsx` | new NovaNet surface over `/api/transmissions` + `/api/echoes` |

Verified live: both endpoint paths exist on the served app — `api/transmissions.py:103`
(`GET /api/transmissions`) and `api/main.py:1660` (`GET /api/echoes`). #418's endpoint
additions are backed by real handlers, not invented paths.

## 3. Archive shell sources and route contracts

**Archived Prism shell** (the reconciliation input; archived, not built or served):

| Archived file | Lines | Route/shell model it carries |
|---|---|---|
| `archive/frontend/arkadia-prism/web/public_prism/src/App.tsx` | 160 | a 33-member `View` union, a `routeForView` map, a `resolvePath` with a 9-entry `compatibility` alias table and a `direct` path→view table |
| `.../components/PrismInteriorShell.tsx` | 98 | `PRIMARY` (7 items) / `SECONDARY` (6 items) rails; each rail item is a real `<button onClick>` |
| `.../components/ArkadiaNavigation.tsx` | 65 | `NAV_GROUPS` (Field / Nexus / Workspaces / System), a top bar + 288px slide-in drawer, `UserSection` shortcuts |

**Active console shell** (canonical; what this workstream owns):

| Console file | Lines | Model |
|---|---|---|
| `web/arkadia_console/src/lib/surfaces.ts` | 122 | one `SurfaceId` union (9 ids), one `SURFACES` table (one `path` per surface) |
| `web/arkadia_console/src/lib/router.ts` | 53 | one `resolvePath`, one `routeForSurface`, one `useRouter` |
| `web/arkadia_console/src/App.tsx` | 90 | one `switch (route.surface)` composition root, one `<Shell>` mount |
| `web/arkadia_console/src/components/Shell.tsx` | 96 | `NAV_SURFACES = SURFACES.filter(s => s.nav !== false)` — nav derived from the surface table |

Route-contract constraints already guarded elsewhere (do not duplicate):

- `tests/test_canonical_frontend_routing.py` — reserved prefixes + backend-route shadowing
  (including the `/solspire` reserved-namespace collision that moved the SolSpire surface to
  `/enterprise`).
- `tests/test_aeas05_canonical_frontend_acceptance.py` — auth threshold + CP10 gate testids.
- `tests/test_frontend_arkadia_console_rebuild_01.py` — archive preservation + buildability.
- `tests/test_prism_interior_shell.py`, `tests/test_prism_pass_c_surface_ownership.py`,
  `tests/test_m03_novanet_public_field.py` — source-level contracts over the **archived**
  Prism tree (they read `archive/frontend/arkadia-prism/...`), not over the console.

## 4. Gap this workstream can close without touching a #418 path

The console's API surface is declared once, in `web/arkadia_console/src/lib/endpoints.ts`
(`SHARED-CONTRACTS.md` §3.3: "API evidence before UI claims … never invent an endpoint").
Measured at `a29a9b8f`: **no test in `tests/` or `scripts/` reads `endpoints.ts`**
(`grep -rln "endpoints.ts" tests/ scripts/` → 0 matches). The registry is therefore an
unpinned contract: a path could be added, renamed, or invented with nothing to catch it.

This is (a) squarely workstream 1's ("integration of shared endpoint/type registries"),
(b) a **new file**, and (c) not a duplicate of `test_console_shell_nav_contract.py`, which
pins navigation/shell/design invariants and asserts nothing about the endpoint registry or
the served backend. Added as `tests/test_console_endpoint_registry_contract.py`.

A related, **recorded-not-repaired** finding (evidence, not a claim against `main`): the
`NotYetWired` `contract="…"` strings are *advertised* contracts, not registry entries.
Advertised strings that are not served paths:

| Advertised string | Served? | Note |
|---|---|---|
| `/api/solspire/voice` | **not served** | the backend serves `/solspire/voice/events` (and `/api/lab/engineering/voice`); the advertised string appears nowhere |
| `/api/lab/engineering/sessions/{id}/execute` | **not served** | path-param spelling differs from every served shape |
| `/api/solspire/projects/{id}/runtime-context` | **not served as written** | the served shape is `/solspire/projects/{project_id}/runtime-context` (no `/api` prefix, `{project_id}`) |
| `/api/solspire/workloads`, `/api/solspire/proposals`, `/api/solspire/pulses` | served under a different prefix | real contracts are `/solspire/workloads`, `/solspire/proposals`, `/solspire/pulses` |

These are display copy inside page bodies owned by workstreams 2–4 and #418's
`NovaNetPage`. Repairing them is a feature-page edit, so it is **proposed, not executed**
here. The new guard records them as a bounded, non-failing finding so the drift is visible
rather than silently repeated.

## 5. Non-overlapping deliverables in this pass

1. `docs/control-plane/parallel-ui/WORKSTREAM-01-OVERLAP-MAP.md` (this file) — new.
2. `tests/test_console_endpoint_registry_contract.py` — new; registry↔served-OpenAPI
   contract with a negative control.

No `App.tsx` / `router.ts` / `surfaces.ts` / `SurfaceLenses.tsx` / `endpoints.ts` /
`types.ts` / `test_console_shell_nav_contract.py` / `NovaNetPage.tsx` edit was made.

## 6. Measurements (this pass, at the SHAs above)

| Check | Command | Result |
|---|---|---|
| New guard | `pytest tests/test_console_endpoint_registry_contract.py -q -rEf` | **8 passed** |
| Live negative control | add `ghostFeed: "/api/ghost-feed"` to `endpoints.ts`, rerun | **1 failed, 7 passed** (`test_every_declared_endpoint_is_served_by_the_canonical_app`); restored byte-identically (`git status --porcelain` empty) |
| Related frontend/route guards | `pytest tests/test_canonical_frontend_routing.py tests/test_aeas05_canonical_frontend_acceptance.py tests/test_frontend_arkadia_console_rebuild_01.py tests/test_frontend_script_assets_resolve.py tests/test_console_authority_chain.py tests/test_prism_interior_shell.py tests/test_prism_pass_c_surface_ownership.py tests/test_m03_novanet_public_field.py tests/test_documented_route_contract.py -q -rEf` | **71 passed** |
| Console typecheck + build | `corepack pnpm install --frozen-lockfile && corepack pnpm exec tsc --noEmit && corepack pnpm build` | **exit 0** — 62 modules transformed, assets emitted |
| CP10 admission | `printf '<path>\n' \| python scripts/cp10_mutation_boundary_policy.py --judge` for both new paths | **PASS (exit 0)** |
| Full suite — `main` `a29a9b8f` | `pytest tests/ -q -rEf --continue-on-collection-errors` | **18 failed, 2137 passed, 17 skipped, 1 error** |
| Full suite — this branch | same command | **18 failed, 2145 passed, 17 skipped, 1 error** |
| Baseline fingerprint | `python scripts/baseline_fingerprint.py <log> --json` | **identical on both trees** — outcomes `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b`, ids `716df34bc5a6ad51dd122ffb09175f1be7883f85a5f4bc07dc12831109b0a45e` (19 nodes) |
| Node-set delta | `comm`-equivalent over the `FAILED`/`ERROR` lines | **empty** (identical node sets) |

The `+8 passed` (2137 → 2145) is exactly this file's node count
(`pytest --collect-only -q` → 8 collected), not a change in any other test's outcome.

Pre-existing debt on both trees (recorded, not repaired, not this workstream's): 18
failures + 1 collection error, dominated by the known `knowledge.db` "Cannot operate on a
closed database" cross-test contamination, the `weaver.autonomy` module-vs-package
collision (`tests/test_autonomy.py`), the `tests/test_engineering_lab_api.py` pins
(sovereign-only — `api/lab_routes.py` is an authority surface), and the Landing/NodeEntry
copy pins. None is caused by, or repaired by, this pass.

## 7. Explicit non-claims

- No merge, no production deployment, no acceptance. Canonical production remains
  `https://arkadia-qzu4.onrender.com` (ADR-016).
- No Vercel deployment was created, promoted, or treated as evidence.
- #418 was not rebased, split, cherry-picked, closed, or rewritten.
- The route-collision finding is `tests/test_canonical_frontend_routing.py`'s, already
  measured; this pass re-derives the archive/console route *shape* only.
