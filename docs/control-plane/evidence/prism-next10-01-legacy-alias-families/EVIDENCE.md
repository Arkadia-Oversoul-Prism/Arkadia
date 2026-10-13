# Prism UI reconciliation — Lane 1, next-10: legacy inbound alias families (`/home`, `/knowledge-os`)

**Status:** Implementation + targeted proof. Draft PR — human merge/acceptance authority.
**Workstream:** Prism next-wave parallel UI reconciliation, **Lane 1** (Shell / Navigation / Design System / Integration seam).
**Branch:** `feat/prism-next10-01-legacy-alias-families`
**Base (`main`):** `49809f45274f2f81b24e01fefdfb3009e8717495` — re-fetched and confirmed unchanged at implementation time.
**Predecessor:** PR #497 (`feat/prism-next9-01-nexus-alias`, head `cc1e8f7`) reconciled legacy *namespace* aliases (root + sub-paths) for `/nexus`. This pass continues the same class in the same file.
**Authority:** No merge, deployment, or acceptance is claimed. Canonical production remains `https://arkadia-qzu4.onrender.com` (ADR-016).

## 1. Objective (bounded)

Reconcile **two more archived inbound paths** that each name a surface the console **already declares**, so a shared deep link lands on that surface instead of silently falling through to Home. Ownership: `web/arkadia_console/src/lib/router.ts` + the shared shell/route guard `tests/test_console_shell_nav_contract.py` — both Lane 1 (§1 of `SHARED-CONTRACTS.md`).

This is **not** a new surface and **not** a redesign. The alias table reconciles a legacy inbound path to the one canonical surface; the router already normalises the address bar to the canonical path on load, so the reconciliation is permanent for a copied link.

## 2. Capability matrix (archived source → console contract)

| Archived inbound path | Archived source | Archived destination | Console disposition | Backend collision |
|---|---|---|---|---|
| `/home` | `archive/frontend/arkadia-prism/web/public_prism/src/App.tsx` `direct: { '': 'home', '/home': 'home' }` | home (`/`) | **Adapt** → alias to the declared `home` surface (`/`) | none (`/home` not in `app.openapi()["paths"]`) |
| `/knowledge-os` | same file, `compatibility: { '/knowledge-os': {view:'solariun',section:'knowledge'} }` | a knowledge view | **Adapt** → alias to the declared `knowledge` surface (`/knowledge`), whose registry name is literally "Knowledge OS" | none (`/knowledge-os` not a served route) |
| `/codex` | same file, `compatibility: { '/codex': {view:'solariun',section:'knowledge'} }` | Solariun `knowledge` lens | **Defer** — see §5 | — |
| `/gate`, `/living-gate` | `direct`/`compatibility` | legacy `gate` view | **Defer** — no console surface | — |
| `/dashboard`, `/loops`, `/settings`, `/account`, `/personal-echofeild`, `/echofeild-matrix` | `compatibility` | Solariun lens (`overview`/`tasks`/`settings`/`observatory`) | **Defer** — target lens not declared by the console | — |

## 3. Method / evidence

- **Route/OpenAPI verification (done first).** `api.main:app.openapi()["paths"]` was enumerated in this environment and each candidate path probed for a collision (exact, prefix, or parameterised). `/home` and `/knowledge-os` are **clear** — no served route claims them, so neither may be a backend-owned namespace and both are safe UI aliases.
- **Router evaluated, not pattern-matched.** `tests/test_console_shell_nav_contract.py::_js_route_resolver` executes the real `resolvePath` in Node, so the assertion observes *what path a given inbound pathname resolves to*, not a restatement of the implementation.
- **Alias soundness reuses the existing detector** (`_path_aliases` / `_alias_defects`): every alias must target a declared surface and must never collide with a canonical surface path. No second detector was added.

### Targeted proof

```
python -m pytest tests/test_console_shell_nav_contract.py -q -rEf   -> 32 passed in 0.70s
python -m pytest tests/architecture \
  tests/test_console_shell_nav_contract.py \
  tests/test_console_endpoint_registry_contract.py \
  tests/test_canonical_frontend_routing.py -q -rEf                -> 67 passed in 3.48s
python -m pytest tests/test_prism_pass_c_surface_ownership.py \
  tests/test_weaver_mvp2_08.py tests/test_weaver_sci_discovery_01.py \
  tests/test_weaver_sci_boundary_01.py -q -rEf                    -> 45 passed
python -m pytest tests/architecture -q                            -> 11 passed (expected)
```

- **`+2` attributed by node identity, not count.** `--collect-only` on the guard: `main` **30**, branch **32**; the two additions are exactly the new test and its negative control.
- **Live negative control (real file, not a synthetic fixture).** Mutating the real `router.ts` so `/knowledge-os` → `home` (the pre-repair shape) reddens `2 failed, 30 passed`; restoring byte-identically returns `32 passed`. Both directions proven against the same file the guard reads.
- **TypeScript + build.** `npx tsc --noEmit` → exit 0; `corepack pnpm build` → exit 0, `81 modules transformed`, assets emitted. `dist/` is git-ignored and untracked.

## 4. Files changed

| Path | Change |
|---|---|
| `web/arkadia_console/src/lib/router.ts` | `PATH_ALIASES` gains `"/home": "home"` and `"/knowledge-os": "knowledge"`; comment records the archived source and the deferred cases. |
| `tests/test_console_shell_nav_contract.py` | New positive test `test_home_and_knowledge_os_reconcile_to_declared_surfaces` + negative control `test_detector_flags_an_unaliased_knowledge_os_that_falls_through_to_home`; the resolver probe list gains `/home` and `/knowledge-os`. |

`App.tsx` is **not** touched (no new surface), so no lane-1 shared-file request is owed to any feature lane.

## 5. Explicit non-claims / deferred (recorded, not repaired)

- `/codex` is **not** aliased. The archive routed it to Solariun's `knowledge` *lens*, but the console now declares **both** a `solariun` `knowledge` lens **and** a distinct `knowledge` surface. Choosing between them is a **capability/product decision**, not a routing one; aliasing would collapse that decision into this table. Proposed work, not executed (directive §3/§4 — a legacy path with no unambiguous declared target must not be force-resolved).
- `/gate` + `/living-gate` and the Solariun-lens aliases (`/dashboard`, `/loops`, `/settings`, `/account`, `/personal-echofeild`, `/echofeild-matrix`) remain deferred: their targets are not declared surfaces/lenses in the console. Recorded here so a later pass does not re-derive them.
- No merge, production deployment, or production acceptance. No Vercel deployment was created, promoted, or treated as evidence.

## 6. Baseline / regression boundary

Baseline failures are **not** attributed to this work; the change is additive (one map in `router.ts`, one guard test in a Lane-1-owned test file). The failing/error **node set** is unchanged by construction: the only new nodes are the two guard tests (proven by `--collect-only` 30 → 32), and no test file outside Lane 1 is touched. Full-suite node-set comparison is deferred to CI at the PR head (single full-suite pass per pulse budget).

## 7. One next bounded task

Reconcile `/codex` **after** a capability decision records whether the console's archive-link contract should resolve it to the `solariun` `knowledge` lens or the `knowledge` surface — a decision this routing lane cannot make unilaterally. Until then, continue with the next Lane-1 gap that names an existing declared target.
