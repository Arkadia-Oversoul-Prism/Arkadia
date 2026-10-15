# Slice A — the shared lens strip becomes a labelled navigation landmark

**Workstream:** Prism UI reconciliation (Lane 1 — shell / navigation / design system)
**Contract:** `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md`,
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`,
`docs/control-plane/parallel-ui/AGENT-01-*.md`
**Branch:** `feat/prism-l1-lens-strip-keyboard-01`
**Base main at selection:** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`
**Class:** bounded, user-visible, tested slice. Draft PR; no merge, no deploy.

## 1. The defect (measured, not assumed)

`web/arkadia_console/src/components/SurfaceLenses.tsx` is the one sub-view
switcher every lens-bearing surface renders (`NovaNetPage`, `SolariunPage`). It
rendered as an **anonymous `<div>` of buttons**:

```tsx
<div className="mb-4 flex flex-wrap gap-1" data-testid={`${surface}-lenses`}>
  {lenses.map((l) => (<button ... aria-current={...} data-testid={`surface-lens-${l.id}`}>...</button>))}
</div>
```

A screen-reader user reaching the strip hears a run of unlabelled controls with
no statement of which region they are in. The element carries **no landmark** and
**no accessible name** - `grep -rn "aria-label" SurfaceLenses.tsx` was empty.

This is a genuine reconciliation gap: the archived Prism rendered the same rail
as a labelled landmark. In
`archive/frontend/arkadia-prism/web/public_prism/src/components/PrismInteriorShell.tsx`
the equivalent strip is `<nav aria-label="NovaNet primary navigation">`. So the
accessible region is a **recovered capability**, not an invention.

The slice is not a re-litigation of the strip's already-repaired behaviour. The
navigability and "no decorative control" properties are pinned by
`tests/test_console_shell_nav_contract.py` (section 4 Slice A) and are unchanged
here. What was missing was the **landmark and its name**.

## 2. The change (minimal)

- `SurfaceLenses.tsx`: the container `<div>` becomes `<nav>` carrying
  ``aria-label={`${SURFACE_BY_ID[surface].name} views`}``.
- The name is **derived from the surface registry** (`SURFACE_BY_ID` in
  `src/lib/surfaces.ts`) rather than hardcoded. A hardcoded name would be a
  second surface-name list - the duplicate-model class directive 5.1 forbids.
  The registry stays the single source of that vocabulary.
- One import line added (`SURFACE_BY_ID`, `SurfaceId`); the `<button>` markup,
  `onClick` -> `onNavigate`, `aria-current`, testids and classes are **unchanged**.

`<nav>` is used (not `role="tablist"`) deliberately: the strip is a set of
navigation links to `/surface/<lens>` that already carry `aria-current="page"`,
which is exactly what a `nav` landmark is for. A tablist would assert a
composite widget with roving focus that the console does not implement, and would
have to drop `aria-current`. See section 5.

## 3. Regression guard

New file `tests/test_console_lens_landmark_contract.py` (7 tests). Each
load-bearing detector carries a **negative control** so a detector that always
passes is itself caught:

- `test_detector_flags_the_pre_repair_anonymous_div` - the exact pre-repair
  `<div>` shape must be reported.
- `test_detector_flags_a_nav_with_no_accessible_name` - a `<nav>` without a name
  must be reported.
- `test_detector_flags_a_hardcoded_surface_name` - a literal name must not count
  as registry-derived.
- `test_detector_reads_the_whole_tag_when_the_label_is_a_template` - the scanner
  reads past the `${...}` template and the `=>` handler, which a naive `<[^>]*>`
  match would truncate.

The file names the active console with the `"arkadia_console"` Path-segment
spelling, so it enters the **derived** console-contract domain
(`scripts/console_contract_domain.py`) automatically and is executed by the
`prism-console-contract` gate **without editing the workflow** - measured:
domain count 23 -> 24, new guard at position 4.

## 4. Proof (run in this environment)

| Command | Result |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` (`web/arkadia_console`) | PASS (3.2s) |
| `corepack pnpm run build` (`tsc --noEmit && vite build`) | **PASS** - 83 modules, `dist/assets/index-BeTUZgVp.js` 100.79 kB |
| `python -m pytest tests/test_console_lens_landmark_contract.py -q -rEf` | **7 passed** |
| `python -m pytest -q $(python scripts/console_contract_domain.py)` | **433 passed** (18.0s) |
| `python -m pytest tests/test_prism_console_ci_wiring.py -q` | **30 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| targeted: lens + shell + interior-shell + routing + acceptance suites | **72 passed** |

The `tsc --noEmit` half of the build is load-bearing: it proves the
`SURFACE_BY_ID` import and the `<nav>` markup type-check against the real
registry.

## 5. Deliberate non-goals (recorded, not silently dropped)

- **`role="tablist"` / arrow-key roving focus.** A tablist is a composite widget:
  it requires `role="tab"` children, roving `tabindex`, and Arrow/Home/End
  handling. Half of that is worse than none - a `role="tablist"` whose children
  stay ordinary buttons mis-announces the widget. Either the whole pattern is
  implemented (a separate, larger slice on the same primitive) or the plain
  navigation landmark is used. This slice takes the smaller, complete step and
  records the tablist as a candidate follow-on.
- **Shell / route registry.** Not touched. `App.tsx` is owned by open PRs
  (#510, #511, #514) and `Shell.tsx` by #516; `router.ts` by #505. No shared
  file is edited by this slice.

## 6. Baseline and regression boundary

- Full suite (`python -m pytest tests/ -q -rEf --continue-on-collection-errors`),
  one pass: `12 failed, 2986 passed, 22 skipped, 1 error` (202.4s).
- Failing/error node set (13 nodes, sorted, sha256
  `996380272f8b271e1c7d8d44a7e509ccdb81d4f05425c5049261a5bdeb5a40c3`):
  `test_autonomy.py` (collection error, CE-01 module-vs-package collision) +
  the four `test_agents_md_encoding_adjudication.py` oracle-revision nodes +
  `test_ais_w2_living_gate_grove_handoff`, two `test_engineering_lab_api` pins,
  `test_identity_spine_w1`, `test_m02_reasomate_truth`, two
  `test_solspire_r1_governance_convergence`, `test_solspire_r3_execution_runtime`.
- **None of the 13 nodes names a file this slice touches.** The four
  `test_agents_md_encoding_adjudication` nodes are the documented shallow-clone
  class (`git rev-parse --is-shallow-repository` -> `true`; the oracle revision is
  unreachable). The rest are pre-existing `main` drift recorded in `AGENTS.md`
  (unowned Landing/Lab pins; the CE-01 collision reserved to the sovereign).
- The branch adds **+7 passing nodes**, exactly the new file's `--collect-only`
  count (7). Attribute by node identity, not totals.

## 7. Authority boundary

Draft PR only. No merge, no deploy, no production claim, no acceptance. The
change is a repository-source claim; it is not a production-parity observation
and not a browser observation (no e2e harness in this sandbox - the build plus
the source-contract suite are the executable evidence).
