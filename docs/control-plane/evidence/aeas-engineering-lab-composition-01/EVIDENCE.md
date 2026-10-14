# AEAS Engineering Lab composition gate — candidate evidence

Machine-readable companion: [`RECONCILIATION.json`](./RECONCILIATION.json).

- **Baseline:** `main` @ `2a1bca755bd6e93413ccbe78790e65d3aec1c2b1`
- **Candidate:** `aeas/engineering-lab-composition-01` from that exact SHA
- **Authority:** no merge, no deployment, no EAA/dispatch advancement, no unrelated PR disposition change.

## Source reconciliation

| PR | Head SHA | Disposition | Evidence |
|---|---|---|---|
| #512 | `f8da5158` | included | `LabOperationalSurfaces.tsx`, `labOperational.ts`, projection test, shell-nav comment fix; page mounts the surface and uses `scalarOverview()`. |
| #530 | `f54d463c` | included | `test_prism_w4_lane4_render_integrity.py` verbatim; its sole-consumer control decided the mount question. |
| #524 | `aad8a986` | included | `LabAuthorityReadings.tsx`, `labGovernance.ts`, governance test; page mounts the reading. |
| #493 | `255d665f` | partially included | Grammar component/projection/tests and the `<LabAutomationGrammar />` mount included; its 5-node hand-table copy of the composition guard superseded by #504's derived 11-node guard. |
| #501 | `31d66332` | superseded | Whole change contained in #493's head (`test_prism_w4_canonical_loop_mount.py` byte-identical; #493 also renders the grammar). |
| #525 | `daef33c4` | superseded | Weaver mount reverted — a second mount of the same canonical loop, fed by a second hydration of the same endpoint. |
| #504 | `a9cefd21` | partially included | Derived composition guard + guard-integrity test + evidence included; `AGENTS.md` append excluded (live file is under a standing insertion-only/oracle constraint). |

## The composition conflict, and why the mount is on the Lab page

Five of the seven sources edit `EngineeringLabPage.tsx`. Three of them (#493, #501, #530) add the
same `ExecutionLoop` mount; #512 and #524 add sibling projections.

`tests/test_prism_w4_lane4_render_integrity.py::test_control_the_real_pre_mount_page_reports_the_canonical_loop`
encodes the premise that the Lab page is `ExecutionLoop`'s **sole** consumer: it strips every
`ExecutionLoop` line from the page and requires the orphan detector to report the component.
Measured on the tree that also carried #525:

```
1 failed, 139 passed   # the control fails: LabWorkLoop is now a second consumer
```

`LabWorkLoop.tsx` (from #525) imports and renders `ExecutionLoop` on the Weaver page and hydrates
`endpoints.labEngineeringOverview` a second time. That is both a second mount of the canonical loop
and a second, competing reader of the same contract — against the directive's
"exactly one canonical Engineering Lab work-loop mount".

Decision: the canonical mount is the Lab page's `<ExecutionLoop>`, fed by the overview the page
already hydrates. Reverting #525 restores the control's premise **without touching any assertion**
— no guard was weakened, removed, or modified. Measured after the revert: `132 passed`.

## Verification (candidate tree)

| Check | Command | Result |
|---|---|---|
| Focused Lab composition | `pytest -q -rEf` over the 9 Lab/composition files | **132 passed** |
| Derived console-contract gate | `pytest -q -rEf $(python scripts/console_contract_domain.py)` | **546 passed** |
| Weaver + surface contracts | approval ledger, endpoint registry, shell nav, console CI wiring | **91 passed** |
| Architecture | `pytest tests/architecture -q` | **11 passed** |
| Boot syntax | `python -m py_compile api/main.py` | OK (2505 lines) |
| CP10 boundary | changed paths → `cp10_mutation_boundary_policy.py --judge` | PASS (exit 0) |
| Frontend build | `corepack pnpm install --frozen-lockfile && corepack pnpm build` | built, 92 modules, 0 type errors |
| Full suite (candidate) | `pytest tests/ -q -rEf --continue-on-collection-errors` | 8F / 3108P / 17S / 1E |
| Full suite (baseline) | same, detached worktree at `2a1bca75` | 8F / 3006P / 17S / 1E |

**Regression delta: none.** Failing/error node set is identical on both trees —
outcomes `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`,
ids `215e4308371a01f5b0b73f1e2b5dca5bba30f6578f65bb7c8af6eca67bc8b741` (9 nodes each).
The `+102 passed` is fully attributed by `--collect-only` to the eight imported test files
(11+3+7+12+22+27+8+12 = 102).

### Live negative control

Dropping `<LabOperationalSurfaces ... />` from the **real** composed page reddens
`test_a_mounted_lane4_projection_requires_all_of_them` and
`test_every_imported_lane4_component_is_rendered` (`2 failed, 21 passed`); restoring the file
byte-identically returns `23 passed`. The composition guard reads the file it judges.

## Exactly one canonical mount

```
import { ExecutionLoop }   → EngineeringLabPage.tsx:11   (1 hit)
<ExecutionLoop             → EngineeringLabPage.tsx:47   (1 hit)
LabWorkLoop                → no references
```

## Not claimed

Merge, production deployment, production parity/acceptance, and EAA/dispatch advancement are
explicitly **not** claimed. Pre-existing failures on `main` (Lab API authority pins, identity
spine, ReasoMate session key, solspire r1/r3) were recorded, not repaired.
