# SOLARIUN-X01-MAPPING — Canvas Foundation

**Move:** SOLARIUN-X01  
**Status:** MAPPED → IMPLEMENTING  
**Repository:** Arkadia-Oversoul-Prism/Arkadia  
**Branch base (authoritative at mapping):** `575014840c2ead75f460b38de06b04e99d6993f7`  

## 1. Baseline calibration

| Claimed protocol baseline | Actual origin/main |
|---|---|
| `8136727c68892bf7beedf7c6a1d5a1b067819ec1` (PR #58 / SolSpire P2) | `575014840c2ead75f460b38de06b04e99d6993f7` (PR #59 / experience consolidation) |

`8136727` is an **ancestor** of current main. Protocol §3 requires re-inspect and rebase — not assumed continuity.

Already present after consolidation-01 (not to re-invent):

- Shared experience grammar across NovaNet / Solariun / Spiral Command
- Canonical shell: `SolSpireExperience.tsx` (V2 is re-export stub only)
- `solspire-canonical.css` + `solspire.css` token layer
- Mobile object sheet / activity / governance visibility (P0–P1 evidence under `docs/control-plane/evidence/`)

## 2. Existing relevant routes

| Route | View / lens |
|---|---|
| `/solspire` | overview (Home / Solariun field entry) |
| `/solspire/{section}` | projects, commercial, knowledge, files, conversations, tasks, memory, weaver, observatory, engineering-lab, settings |
| Compatibility | `/dashboard`, `/codex`, `/knowledge-os`, `/loops`, `/settings` → mapped into SolSpire lenses |

Mounted via: `App.tsx` → `SolSpireConsole` → **canonical** `SolSpireExperience` (not a parallel shell).

## 3. Existing relevant components

| Component | Role |
|---|---|
| `SolSpireConsole.tsx` | Auth gate + token bind + section adapter |
| `SolSpireExperience.tsx` | Canonical workspace shell (header, sidebar, mobile nav, lenses, Arkana overlay, search) |
| `SolariunHomeCockpit.tsx` | Overview field composition over live endpoints |
| `WorkspaceActionSurfaces.tsx` | Files / Conversations / Tasks workspaces |
| `ProjectsWorkspace.tsx` | Project list |
| `ProjectDashboard.tsx` | Project interior |
| `solspire-canonical.css` / `solspire.css` | Visual language |
| `SolSpireExperienceV2.tsx` | **Re-export only** — must not become a second shell |

## 4–6. Data / API / auth (X01 does not mutate)

Auth chain remains: Firebase → `AuthContext` → `setApiAuthToken` → `apiClient` → SolSpire APIs.

X01 is **presentation foundation only**. No new endpoints, schemas, or persistence.

## 7. Event/activity sources

Existing project events, WorkEvent surfaces, pulse/synthesis — **out of X01 scope** (Activity Grammar is X06).

## 8. Existing visual tokens

`--ss-gutter`, `--ss-panel`, `--ss-line`, `--ss-soft`, focus rings, mobile safe-area, reduced-motion rules already in `solspire-canonical.css`.

## 9. Responsive behavior

Desktop: GlobalDoors + Header + Sidebar + main.  
Mobile: Header + main + bottom `MobileNav` + more menu.  
Project mode: `ProjectDashboard` interior with lens→tab continuity.

## 10. Existing tests

Experience consolidation tests and control-plane evidence folders under `docs/control-plane/evidence/`. X01 adds mapping/evidence docs; no backend test changes required.

## 11. Existing capability (X01-relevant)

- Single authenticated Solariun workspace shell
- Lenses over real SolSpire substrate
- Arkana overlay with context pack
- Search overlay
- Focus-visible and reduced-motion foundations

## 12. Missing substrate for full “Obsidian Canvas” metaphor

| Gap | Class |
|---|---|
| Named canvas field surface / zoom attributes | GAP-B (composition only) |
| Explicit ENVIRONMENT / OBJECT / METADATA type scale | GAP-B |
| Field vs focus vs deep as data attributes for later moves | GAP-B |
| Fake objects/metrics for empty field | **Forbidden** |

## 13. Proposed visual composition (X01 only)

Extend **in place**:

1. Root workspace marks itself as `solariun-canvas` with `data-solariun-zoom="field|focus|deep"`.
2. Canvas CSS tokens for depth, type scale, field surface — layered on existing `--ss-*`.
3. Landmark / accessibility labels on shell regions.
4. **No** new shell file, **no** V2/V3, **no** new navigation system, **no** fake objects.

## 14. Files to modify

- `web/public_prism/src/components/solspire/SolSpireExperience.tsx`
- `web/public_prism/src/components/solspire/solspire-canonical.css`
- `docs/control-plane/evidence/solariun-x01-canvas-foundation/*`

## 15. Files not to modify

- Backend routers / K15 / K3 / WorkEvent semantics
- `SolSpireExperienceV2.tsx` (leave as re-export)
- NovaNet / Spiral Command product logic beyond shared shell already merged
- Auth, apiClient, solariunApi contracts

## 16. Architectural risks

| Risk | Mitigation |
|---|---|
| Parallel shell regression (prior V2 failure) | Extend canonical file only |
| CSS specificity fighting legacy | Additive classes under `.solspire-workspace.solariun-canvas` |
| Implying capability that does not exist | No fake metrics/objects in X01 |

## 17. Verification plan

- Import path: Console → Experience (canonical)
- Typecheck/build frontend if tooling available
- Confirm no second shell import
- Confirm routes still resolve
- Document unsupported items explicitly

## 18. Explicit non-goals (X01)

Object grammar, field “what matters” composition, object sheets, relationships, activity stream, Arkana context expansion, Weaver state surface, semantic search, mobile spatial rewrite, observatory, motion polish (X02–X12).
