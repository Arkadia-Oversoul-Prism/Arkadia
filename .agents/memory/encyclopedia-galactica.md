---
name: Encyclopedia Galactica Crystal Gateway
description: Architecture decisions for the EG crystal gateway page — dodecahedron as nav, full-screen chambers, state persistence.
---

## Rule
The Gateway page (`/nexus` route, `view=nexus` in App.tsx state machine) renders ONLY the crystal SVG — no tabs, no cards, no lists. All Spiral Codex / IMS content is woven into chambers as filtered feeds.

**Why:** User explicitly rejected tab-based layouts twice. Crystal must be the sole navigation surface.

## How to apply
- `EncyclopediaGalactica.tsx` is the single file for this entire subsystem (gateway + chamber views).
- Chamber state persisted in `localStorage` keys: `arkadia_chambers_v2` (states) and `arkadia_reflections_v2` (reflections).
- Codex filtering uses `api.codex` from `dashboardApi.ts` — filter scrolls by `chapter.keywords` array, render max 5 related scrolls inside each chamber view.
- The 12 chapter→chamber mapping is in the `CHAMBERS` array inside that file. All opening verses and excerpts are sourced from `attached_assets/ECHOES_OF_THE_LOST_AEONS__1780472195013.docx`.
- SVG geometry: center (200,200), ring radius 148, nodes at 30° clockwise from top. Inner geometry: ring perimeter lines + 4 equilateral triangles (groups 0,4,8 / 1,5,9 / 2,6,10 / 3,7,11) + radial spokes.
- Chamber states: `dormant` → `explored` (auto on first visit) → `integrated` (user-triggered, requires saved reflection).
- App routing is React state machine (`view` state in `App.tsx`) — URL params don't affect view, must click nav.
