# Lane 1 — section-routing coverage for lens-declaring surfaces (2026-11-09)

**Lane:** 1 (Shell / navigation / design system / integration seam)
**Branch:** `feat/prism-l1-section-routing-coverage-01`
**Base main:** `327187d23c7e4ad32efc61aed91f912de084e07d`
**Scope:** `tests/test_console_shell_nav_contract.py` (one file, test-side only)

## Defect

`_lens_alias_defects` decides that a declared lens alias *resolves* to the right
section. Nothing decided that the resolved section *arrives* at the page.

`lib/router.ts` hands a second path segment to the surface through the `section`
prop, and each lens-declaring page reads it (`SolariunPage`, `SolSpirePage`,
`NovaNetPage`). A surface composed without that prop discards every section of
it: `/solariun/weaver` renders `projects`, and the user sees a plausible screen
with no error.

**TypeScript cannot see this.** `section` is optional on every page
(`SolariunPage({ section = "projects", ... })`), so removing
`section={route.section}` from `App.tsx` compiles cleanly.

## Measured vacuity at base `327187d2`

Dropping the prop from the real `App.tsx`:

```
tests/test_console_shell_nav_contract.py                    47 passed   <- vacuity
derived console-contract domain  (10 failed / 1139 passed)  <- unchanged
```

The 10 are the documented missing-`node_modules` baseline
(`test_mission_lifecycle_adapter_contract.py`), present on `main` identically.

Reproduced independently for all three lens-declaring surfaces
(`solariun`, `solspire`, `novanet`): each mutation is silent before the repair.

## Repair

One module-level detector, `_section_routing_defects(app_text)`, holds the
predicate; the live assertion and both controls call it.

Its domain is **derived**, not restated: it iterates `_surface_page_modules`
(the composition root's own `switch`) and keeps the surfaces whose page declares
a `LENSES` array via `_declared_lenses`. A surface nobody enumerated is judged by
the same rule, and a surface whose page declares no lens strip stays outside the
domain (the resolver already discards its sections, so there is nothing to
forward).

| Node | Role |
|---|---|
| `test_every_surface_that_declares_lenses_receives_the_route_section` | live assertion + domain pin |
| `test_detector_flags_a_lens_surface_composed_without_the_section` | negative control (the exact pre-repair shape) |
| `test_the_section_routing_check_is_not_a_restated_surface_list` | control: a *new* lens surface is reported without an edit |

Node count 47 → 50 (`--collect-only` → 50).

## Verification (at this head)

- `python -m pytest tests/test_console_shell_nav_contract.py -q -rEf` → **50 passed**
- **Live negative control on the real `App.tsx`** (not a synthetic fixture):
  removing `section={route.section}` from the `solariun` case yields
  `2 failed, 48 passed` — the live node **and** its control — then the file was
  restored byte-identically (`git diff --stat web/arkadia_console/src/App.tsx`
  empty).
- `python -m pytest tests/architecture -q` → **11 passed**
- `python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` → see the run record
- Derived console-contract domain (`python -m pytest -q $(python scripts/console_contract_domain.py)`)
  → unchanged failing set vs `main` (the 10 missing-`node_modules` nodes)
- `python scripts/lane_state.py --check` → exit 0
- `python -m py_compile api/main.py` → OK (untouched)

## Scope / ownership

Lane 1 bounded slice under `SHARED-CONTRACTS.md` §11 (N1–N8). Changed paths:
`tests/test_console_shell_nav_contract.py`, the lane-1 instruction doc, the
re-derived `lane-state.json`, and this evidence record. No console source,
backend contract, registry, authority surface or other lane's file is touched.
The guard is executed by the derived console-contract domain, so no workflow edit
is needed.

The snapshot was re-derived **before** this PR was opened
(`scripts/lane_state_refresh.py --write --base-main 327187d2`), so it records no
PR that its own merge will close; PR #650 is recorded under
`unassigned_open_prs`, which is what the derivation produces.

## Status

Draft. Merge, deployment and acceptance remain human-only.
