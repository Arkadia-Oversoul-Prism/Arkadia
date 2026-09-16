# SOLARIUN-X01 — EVIDENCE

## Baseline

| Item | Value |
|---|---|
| Protocol claimed baseline | `8136727` |
| Actual mapping base | `5750148` (ancestor relationship verified) |
| Implementation mode | Extend canonical shell |

## Static checks

| Check | Result |
|---|---|
| Console imports canonical Experience | PASS |
| V2 is re-export only | PASS |
| No new shell file created | PASS |
| Canvas classes present on field + project roots | PASS |
| CSS additive under `.solariun-canvas` | PASS |

## Architectural verification

| Constraint | Status |
|---|---|
| No new database | PASS |
| No unauthorized endpoint | PASS |
| No auth bypass | PASS |
| No K15 / K3 change | PASS |
| No WorkEvent / provenance semantic change | PASS |
| No AEAS activation | PASS |
| No second memory / knowledge / project system | PASS |
| No parallel Solariun shell | PASS |

## Runtime / build

Frontend production build should be run in CI or local `pnpm build` when Node/pnpm available. X01 is CSS + markup attributes only; lens routes unchanged.

## Unsupported (honest)

- Full “Obsidian spatial editor” object constellation (requires X02+)
- Deterministic zoom transitions beyond data attributes
- Proof that every viewport was screenshot-verified in this agent environment

## Verdict readiness

Ready for human visual verification on `/solspire` after merge/deploy.  
Do **not** treat implementation as production verification without human walkthrough.
