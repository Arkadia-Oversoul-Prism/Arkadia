# SOLARIUN-X01 — EVIDENCE

## Baseline
- Verified origin/main: `8136727c68892bf7beedf7c6a1d5a1b067819ec1`

## Implementation
- Branch: `solariun/x01-canvas-foundation`
- Files: `solspire-canonical.css`, `SolSpireExperience.tsx`, evidence docs

## Architectural checks
| Check | Result |
|-------|--------|
| Single shell (console → Experience) | PASS |
| V2 is re-export only | PASS |
| No backend mutation | PASS |
| No K15/K3/WorkEvent/AEAS change | PASS |
| No fake objects/metrics/events | PASS |
| No parallel Solariun shell | PASS |

## Static verification
- See build log in this folder / CI after push

## Runtime (operator)
After deploy of this branch:
1. Sign in → `/solspire` loads canvas chrome
2. `/solspire/files` remains on canonical FilesWorkspace (not black page from dual shell)
3. Tab to reveal skip link; Enter focuses main field
4. Desktop / mobile: existing nav still present (GlobalDoors + bottom rail)

## Remaining unsupported (not X01)
Object cards, relationship layer, activity stream, semantic search UI expansion, Observatory polish
Build environment: npm install failed in agent sandbox (npm exit handler). Build verification deferred to Vercel/local.
