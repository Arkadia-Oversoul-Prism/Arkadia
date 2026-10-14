# Prism UI — Lane 1 (shell/router): legacy hub sub-path alias resolution

**Branch:** `feat/prism-next9-01-nexus-alias`
**Base `main`:** `49809f45274f2f81b24e01fefdfb3009e8717495` (merge of PR #487, 2026-10-12)
**Ownership:** Lane 1 (shell / navigation / integration seam) — `src/lib/router.ts`,
`tests/test_console_shell_nav_contract.py`. No file owned by Lane 2/3/4 is touched.
**Authority:** inspection, implementation and test only. No merge, deployment, or acceptance.

**Evidence freshness:** The reproduction and test/build results below were measured on predecessor PR #489 at its old base/head. The relevant source/test files were byte-identical between that old base and current main at branch cut, so the patch was replayed. These numbers are retained as historical provenance only. Current-head CI is tracked on PR #497; until it completes, this file does not claim the tests passed on the fresh head.


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

## 5. Historical checks from predecessor PR #489 (not rerun on this head)

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

## 7. Pulse 2026-10-14 - alias depth idempotence repair (head `e4bfcfff`)

**Measured base.** Live `main` was `7580bd8f` (`Merge pull request #533`). The PR's
recorded base `49809f45` is an ancestor of `main`; the branch was re-composed onto
`7580bd8f` with `git merge --no-commit --no-ff` and merged **without conflict**
(`Auto-merging tests/test_console_shell_nav_contract.py`).

**Defect (measured, not inferred).** The alias branch carried the path remainder as
the section at *any* depth, so `/nexus/a/b` returned
`{surface: novanet, section: "a/b", path: "/novanet/a/b"}`. `SECTION_PATTERN` is
`/^\/([^/]+)\/([^/]+)$/`, so re-reading `/novanet/a/b` falls through to `home`, and
`useRouter`'s normalisation-on-load (`window.history.replaceState({}, "", canonical)`)
rewrites the address bar to `/`. A shared `/nexus/a/b` link is therefore discarded -
the same silent link loss the slice exists to prevent, restored through a second door.

Node trace, same tree, before and after:

| inbound | pre-repair canonical | re-read | post-repair canonical | re-read |
|---|---|---|---|---|
| `/nexus` | `/novanet` | `/novanet` | `/novanet` | `/novanet` |
| `/nexus/ims` | `/novanet/ims` | `/novanet/ims` | `/novanet/ims` | `/novanet/ims` |
| `/nexus/a/b` | `/novanet/a/b` | **`/`** | `/novanet` | `/novanet` |

**Repair.** `const section = segments.length === 2 ? segments[1] : undefined;` - carry
the remainder only at the one depth a declared surface accepts. Deeper paths resolve to
the aliased surface with no section, so the alias branch cannot emit a path the router
itself does not read back.

**Guard.** `_reread_canonical_paths(router_text)` resolves each inbound probe and then
re-resolves the canonical path it returned, reporting any `(inbound, canonical, reread)`
where the two disagree - the property is *idempotence of `resolvePath`*, which is what
makes the address-bar normalisation safe, rather than a restatement of the probe table.
`test_the_alias_branch_emits_only_paths_the_router_reads_back` asserts the offender list
is empty; `test_detector_flags_a_canonical_path_the_router_does_not_read_back` is its
negative control, reconstructing the pre-repair shape by substituting the any-depth join
and asserting `("/nexus/a/b", "/novanet/a/b", "/")` reappears. A guard that is silent on
both the defect and its absence is not a guard.

**Tests, same environment.**

| Check | Result |
|---|---|
| `python -m pytest tests/test_console_shell_nav_contract.py -q -rEf` | **34 passed** (was 32; +2 new guards) |
| `python -m pytest tests/test_console_shell_nav_contract.py tests/test_canonical_frontend_routing.py tests/test_console_endpoint_registry_contract.py tests/test_prism_console_ci_wiring.py -q -rEf` | **88 passed** |
| composed tree (`7580bd8f` + branch) `tests/test_console_shell_nav_contract.py` | **34 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `cp10_mutation_boundary_policy.py --judge` (all three changed paths) | **PASS** (exit 0) |
| `python -m py_compile api/main.py` | OK; `api/main.py` = **2505 lines** (budget 2600) |

Attribution is by node identity: the `+2` is exactly the two guards added, and the
composed-tree run reproduces the same result as the branch alone.

**Defect still live on `main`.** `main` `7580bd8f` carries the *older* shape,
`PATH_ALIASES[path]` matching the exact string only, so `/nexus/ims` resolves to `home` -
this slice's original subject is unrepaired on `main`, not merely its depth edge.

**Non-claims.** No merge, no deployment, no production acceptance; the PR stays draft.
No file owned by Lane 2, 3, or 4 was touched. No Vercel path used or treated as evidence
(ADR-016).

