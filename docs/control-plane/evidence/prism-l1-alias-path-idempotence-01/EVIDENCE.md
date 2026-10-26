# Prism L1 — alias branch must emit only addressable paths (protocol-relative `//x` repair)

Lane: 1 (shell / navigation / router).
Base: `main` `36f53be22d753ffe269f05cbf3fb39212f744207`.
Branch: `gate10/prism-l1-alias-path-idempotence-01`.
Authority: sovereign merge. No deployment, no acceptance claimed.

## 1. Defect

`web/arkadia_console/src/lib/router.ts` resolves an inbound pathname and writes the
canonical path back to the address bar on load. The alias branch joined a section to
the aliased surface's declared path with a template literal:

```ts
const base = SURFACE_BY_ID[alias].path;
return { surface: alias, section, path: section ? `${base}/${section}` : base };
```

`home` is declared at `/`. For a legacy lens sub-path under a root-surface alias, the
join therefore produced `//x`:

```
/home/x  ->  //x
```

`//x` is **not a path**. A browser reads a leading `//` as the start of an authority,
so `//x` resolves to host `x` with the current scheme — a protocol-relative URL. The
router then `replaceState`d it, so a shared `/home/x` link became an off-origin
navigation (open-redirect class), not a normalisation.

Measured on the pre-repair tree, with `same-origin` resolved by the URL parser:

| inbound | canonical (BEFORE) | readback | note |
|---|---|---|---|
| `/home/x` | `//x` | `/` | **non-idempotent + protocol-relative** |
| `/home/x/y` | `/` | `/` | depth-bounded |
| `/home` | `/` | `/` | ok |
| `/nexus/ims` | `/novanet/ims` | `/novanet/ims` | ok |
| `/oracle/x` | `/arkana/x` | `/arkana/x` | ok |
| `/knowledge-os/x` | `/knowledge/x` | `/knowledge/x` | ok |

Every non-root alias was already correct. The defect is specific to an alias whose
target surface is declared at `/`.

## 2. Why the existing guard passed

`tests/test_console_shell_nav_contract.py::test_the_alias_branch_emits_only_paths_the_router_reads_back`
re-resolves each canonical path and reports any that does not read back unchanged. It
probed `/nexus`, `/nexus/ims`, `/nexus/a/b`, `/nexus/a/b/c`, `/oracle/x`,
`/commune/x/y` — all **non-root** aliases. `/home/x` was not probed, so the detector
stayed green (38 passed) on a live defect.

This is the recorded class: a hand-maintained probe list is an inventory, and an
inventory is not an oracle. The alias set had grown (including `/home`) while the
probe list had not.

## 3. Repair

Source (`router.ts`): delegate both the section decision and the path join to
`routeForSurface`, so the alias branch cannot disagree with the navigation wrapper
about which paths are addressable:

```ts
const base = SURFACE_BY_ID[alias].path;
const section = segments.length === 2 && base !== "/" ? segments[1] : undefined;
return { surface: alias, section, path: routeForSurface(alias, section) };
```

Guard (`test_console_shell_nav_contract.py`): the alias probes are **derived** from
`PATH_ALIASES` (`alias`, `alias/x`, `alias/x/y` for every declared alias) instead of
hand-listed, so a newly declared alias is judged by the same rule. `/nexus/a/b` is
retained for the pre-existing depth control.

After the repair:

| inbound | canonical (AFTER) | readback |
|---|---|---|
| `/home/x` | `/` | `/` |
| `/home/x/y` | `/` | `/` |
| `/nexus/ims` | `/novanet/ims` | `/novanet/ims` |
| `/oracle/x` | `/arkana/x` | `/arkana/x` |

No canonical path is protocol-relative; every one reads back unchanged.

## 4. Proof

Targeted:

```
python -m pytest tests/test_console_shell_nav_contract.py tests/test_console_legacy_route_coverage.py -q -rEf
47 passed
```

`test_console_shell_nav_contract.py` collects **39** nodes (was 38; +1 is the new
control below).

Negative controls, both in the same file:

- `test_detector_flags_a_canonical_path_the_router_does_not_read_back` — unbounded
  remainder join; asserts `/nexus/a/b` is reported.
- `test_detector_flags_a_protocol_relative_path_from_the_alias_branch` — the exact
  pre-repair template join and root-surface section decision; asserts
  `("/home/x", "//x", "/")` is reported.

**Live negative control** (not synthetic): reverting `router.ts` in the working tree to
the pre-repair shape reddens
`test_the_alias_branch_emits_only_paths_the_router_reads_back`
(`1 failed`), and restoring the file returns it to `1 passed`. The guard bites on the
real defect, not only on its own fixture.

Protected surfaces:

```
python -m pytest tests/architecture -q     -> 11 passed
cd web/arkadia_console && corepack pnpm build -> exit 0, built in 1.66s
printf '...' | python scripts/cp10_mutation_boundary_policy.py --judge -> PASS
```

Full suite, once, at the branch head:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
8 failed, 3455 passed, 20 skipped, 1 error in 237.67s
```

Failing/error node set (9 nodes, sha256 `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`):

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**Attribution.** The same 9 nodes were re-run on a stashed (clean `main`) tree:
`8 failed, 1 error` — identical. Zero nodes are attributable to this change; the
`+1 passed` is the new control. No failing node names `router.ts` or the nav contract
(the one `router` match is the backend Engineering Lab router, unrelated). `main`'s
pre-existing debt was recorded, not repaired.

## 5. Scope and limits

- Files changed: `web/arkadia_console/src/lib/router.ts`,
  `tests/test_console_shell_nav_contract.py`, this record.
- No shared-file change owned by another lane (`App.tsx`, `surfaces.ts`,
  `endpoints.ts`, `types.ts`, `SurfaceLenses.tsx` untouched).
- `tests/test_console_shell_nav_contract.py` is in the derived console-contract domain
  (`scripts/console_contract_domain.py`, entry 12) and is executed by
  `.github/workflows/prism-console-contract.yml`, whose `paths` filter selects
  `tests/**` and `web/arkadia_console/**` — so this change triggers its own gate.
- CI result at this head is **NOT CLAIMED** here; the local measurements above are
  what is evidenced.
- Not claimed: production parity, deployment identity, or acceptance. The router is
  frontend source; no runtime observation of a deployment is made.
- Related but distinct: PR #562 (`feat/prism-l1-legacy-lens-route-recovery-01`) adds
  legacy lens aliases and its own read-back guard. This change is independent of it and
  does not adopt or supersede it. If both merge, the derived probe list makes the two
  agree without a further edit.
