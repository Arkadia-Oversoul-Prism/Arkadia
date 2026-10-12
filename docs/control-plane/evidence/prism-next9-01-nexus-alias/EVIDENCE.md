# Prism UI — Lane 1 (shell/router): legacy hub sub-path alias resolution

**Branch:** `feat/prism-next9-01-nexus-alias`
**Base `main`:** `49809f45274f2f81b24e01fefdfb3009e8717495` (merge of PR #487, 2026-10-12)
**Ownership:** Lane 1 (shell / navigation / integration seam) — `src/lib/router.ts`,
`tests/test_console_shell_nav_contract.py`. No file owned by Lane 2/3/4 is touched.
**Authority:** inspection, implementation and test only. No merge, deployment, or acceptance.

---

## 1. The defect (reproduced before any change)

The recorded handoff is `docs/control-plane/evidence/prism-ui-reconciliation-pulse5-governance-conflict-01/EVIDENCE.md`
Finding 2. It is re-measured here, not inherited.

`PATH_ALIASES` maps the **exact string** `/nexus`, and alias resolution runs before
path parsing, so a legacy hub sub-path falls through to `home`:

```
before (verbatim router.ts + surfaces.ts evaluated under node v24.21.0):
  /nexus                   -> surface=novanet    section=-    path=/novanet
  /nexus/ims               -> surface=home       section=-    path=/
  /nexus/grove             -> surface=home       section=-    path=/
  /nexus/larder            -> surface=home       section=-    path=/
  /nexus/distribution      -> surface=home       section=-    path=/
  /novanet/ims             -> surface=novanet    section=ims  path=/novanet/ims
```

Legacy binding confirmed from the archive, not memory:
`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:71-72`:
`'/nexus': 'novanet', '/nexus/ims': 'ims', '/nexus/grove': 'grove', '/nexus/larder': 'larder', '/nexus/distribution': 'distribute'`.

This is a silent discard of a shared inbound link — the same class the exact-match
`/nexus`, `/oracle`, `/commune` aliases were added to repair, left half-done for the
alias *namespace*.

## 2. Repair

`src/lib/router.ts` — alias resolution now keys on the path's **first segment** and
carries the remainder as the section, exactly as a declared surface path does for
`/solariun/knowledge`:

```ts
const segments = path.split("/").filter(Boolean);
const alias = PATH_ALIASES[`/${segments[0] ?? ""}`];
if (alias) {
  const section = segments.length > 1 ? segments.slice(1).join("/") : undefined;
  const base = SURFACE_BY_ID[alias].path;
  return { surface: alias, section, path: section ? `${base}/${section}` : base };
}
```

The alias branch was inlined into `resolvePath` rather than extracted into a helper
with a `Route | null` return type: the module's dependency-free evaluation harness
(`_js_route_resolver`) strips a fixed set of type annotations, and a union return
type is not among them. Keeping the signature annotation-free is what lets the
property be *executed* instead of pattern-matched. No behaviour depends on the shape.

**What this does and does not claim.** It restores *resolution*: `/nexus/ims` now
reaches NovaNet with `section="ims"`, where `NovaNetPage` already renders its honest
`NotYetWired` state for a lens outside its declared set. It makes **no** claim that
the legacy sub-view's backend contract is serviceable — `/api/ims/inquiries` is
sovereign-key gated while `apiClient` sends a Bearer token only, and that separation
is preserved (the alias does not itself send anyone into that contract; the surface
states it is not wired).

## 3. After the repair

```
after:
  /nexus                   -> surface=novanet    section=-             path=/novanet
  /nexus/ims               -> surface=novanet    section=ims           path=/novanet/ims
  /nexus/grove             -> surface=novanet    section=grove         path=/novanet/grove
  /nexus/larder            -> surface=novanet    section=larder        path=/novanet/larder
  /nexus/distribution      -> surface=novanet    section=distribution  path=/novanet/distribution
  /nexus/a/b               -> surface=novanet    section=a/b           path=/novanet/a/b
  /novanet/ims             -> surface=novanet    section=ims           path=/novanet/ims
  /oracle                  -> surface=arkana     section=-             path=/arkana
  /commune                 -> surface=arkana     section=-             path=/arkana
```

Every resolved path is canonical for its surface (`<declared path>` or
`<declared path>/<section>`), so the on-load `history.replaceState` normalises the
legacy address bar to `/novanet/ims` instead of leaving a discarded path.

## 4. Guard

`tests/test_console_shell_nav_contract.py`:

- `test_alias_sub_paths_resolve_into_the_target_surface` — the four measured legacy
  sub-paths, a deeper `/nexus/a/b`, and `/novanet/ims` (proving the alias branch does
  not swallow a declared surface's own section).
- `test_detector_flags_a_router_that_matches_only_the_alias_root` — **negative
  control**: reverts the lookup to `PATH_ALIASES[path]` and asserts the measured
  pre-repair fall-through to `home` reappears. The guard cannot be disarmed by
  rewriting `router.ts`.
- `_js_route_resolver`'s probe list extended with the six sub-path probes so every
  existing assertion (`test_the_router_normalises_the_address_bar_to_a_declared_surface_path`)
  also judges the new paths.

## 5. Checks run (this environment)

| Check | Result |
|---|---|
| `python -m pytest tests/test_console_shell_nav_contract.py -q -rEf` | **32 passed** (was 30; +2 new guards) |
| `python -m pytest -q $(python scripts/console_contract_domain.py)` | **403 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `cp10_mutation_boundary_policy.py --judge` (both changed paths) | **PASS** (exit 0) |
| `python -m py_compile api/main.py` | OK; `api/main.py` = **2505 lines** (budget 2600) |
| `cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build` | **✓ built in 1.53s**; `dist/assets/index-BaV9cROs.js` 95.84 kB |
| Node router evaluation (before/after) | recorded above; defect reproduced then repaired |

`main` and branch were measured in the same environment; the only changed nodes are
the two added guards, and the pre-existing console-contract set is unchanged.

## 6. Explicit non-claims

- No merge, no deployment, no production acceptance. The PR starts and remains **draft**.
- No claim that `https://arkadia-qzu4.onrender.com` serves this change; the console has
  not been deployed with it.
- No Vercel path was used, promoted, or treated as evidence (ADR-016; directive §8).
- No file owned by Lane 2, 3, or 4 was edited.
- The IMS/Grove/Larder/Distribution backend contracts remain unwired; only inbound link
  *resolution* is restored.
