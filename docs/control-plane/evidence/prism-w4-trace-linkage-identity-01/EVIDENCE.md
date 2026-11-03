# Workstream 4 — render session-level linkage classifications by identity

**Lane:** 4 (Arkana / Weaver / Engineering Lab)
**Branch:** `feat/prism-w4-trace-linkage-identity-01`
**Base:** `main` `46d85e2d74df4f5016f54a4ee9c3d994a5bb0c03`
**Status:** IMPLEMENTED — targeted tests, console-contract domain and build pass; no merge, deployment or acceptance claimed.

## 1. Defect

`web/arkadia_console/src/components/lab/labRunTrace.ts` computes seven session-level
linkage classifications (lines 183-195):

```
unlinked_events            unlinked_evidence       unattributed_evidence
unlinked_artifacts         unattributed_artifacts
duplicate_evidence_ids     duplicate_artifact_ids
```

`LabRunTrace.tsx` rendered only their *count*, through `ledger.unresolved`. A reader
learned that a reference failed to resolve but never **which** reference. A duplicate id
is dropped from the traced set rather than merged (`evidenceDedup.duplicates`), so the
identity is the only way to find the record the surface left out.

The prior note said "six". Re-measured against the ledger's own interface at this base:
**seven**. The slice renders exactly those seven — none missed, none invented.

## 2. Change

`LabRunTrace.tsx` (+90): a `LinkageGroup` component and a `linkage` array built from the
seven ledger fields, filtered to non-empty groups and rendered as a `<ul data-testid="lab-trace-linkage">`.
Each group renders `data-testid={`lab-trace-linkage-${kind}`}` with its ids joined.

## 3. Verification

| Check | Command | Result |
|---|---|---|
| Own guard | `pytest tests/test_prism_w4_trace_linkage_identity.py -q` | **11 passed** |
| Lane-4 neighbours + wiring | `pytest tests/test_lab_run_trace_contract.py tests/test_prism_console_ci_wiring.py -q` | **63 passed** (with own guard) |
| Console contract / lane-1 | `pytest tests/test_console_endpoint_registry_contract.py tests/test_console_legacy_route_coverage.py tests/test_console_shell_nav_contract.py -q` | **83 passed** |
| Architecture | `pytest tests/architecture -q` | **11 passed** |
| Build + typecheck | `corepack pnpm build` (`tsc --noEmit && vite build`) | **clean**, 146 modules |
| CP10 boundary | `cp10_mutation_boundary_policy.py --judge` on the three new paths | **PASS** (exit 0) |

Served-artifact proof: the built bundle carries every `kind` as data —
`"unlinked-events"`, `"unlinked-evidence"`, `"unattributed-evidence"`,
`"unlinked-artifacts"`, `"unattributed-artifacts"`, `"duplicate-evidence"`,
`"duplicate-artifacts"` → 1 occurrence each; `lab-trace-linkage` → 2.

**Note on marker counting.** The per-kind testid is a *template literal*
(`` `lab-trace-linkage-${kind}` ``), so an expanded-literal grep for e.g.
`lab-trace-linkage-unlinked-evidence` reads **0** in the minified bundle. That is the
documented "expanded literal vs template" trap, not an absent feature — the template's
`kind` values are what survive, and they do (above).

### Negative control

Stripping the render block from the **real** file reddened the guard. The first detector
scored a *mention* of `ledger.<field>` as execution, so only 1 node failed; the detector
now scopes the check to the JSX body returned by `export function LabRunTrace`, and the
primary invariant bites. `LabRunTrace.tsx` was restored byte-identically
(md5 `5b40a6104eed5577c1b2baf58425f5a7`).

## 4. Domain participation

`tests/test_prism_w4_trace_linkage_identity.py` matches `DOMAIN_NEEDLES` via
`"arkadia_console"`, so once tracked it joins the derived console-contract domain
(`scripts/console_contract_domain.py`, 64 → 65) and is executed by
`prism-console-contract.yml` without editing the gate.

## 5. Not claimed

No merge, no production deployment, no acceptance. `main` carries **no branch
protection** (measured: `GET /branches/main/protection` → 404), so no required check
gates this; eligibility under M1-M13 remains a separate, revalidated decision.
