---
name: Crystal Triune Unification
description: NexusSpiralCodex is the single interface for both Spiral Codex and Encyclopedia Galactica; architectural rules and face→chamber map.
---

## Rule

`NexusSpiralCodex.tsx` is the ONE Crystal Triune component. It has two modes:
- `SCROLLS` (default) — Spiral Codex intelligence feed
- `ECHOES` — Encyclopedia Galactica (12 chambers of Echoes of the Lost Aeons)

**Never create a separate encyclopedia page or a second Crystal Triune component.**

`EncyclopediaGalactica.tsx` is preserved but NOT routed to. The `encyclopedia` nav route passes `initialMode="echoes"` to NexusSpiralCodex.

**Why:** The user explicitly rejected fragmentation. Both surfaces share the Crystal Matrix (left) and ReasoMate (right) panels — splitting them would duplicate navigation and destroy the unified feel.

## Face → Chamber Resonance Map

When a Crystal Matrix face is activated in ECHOES mode, its mapped chapter is sorted to the top and marked "Resonant":

| Face ID | Chapter |
|---|---|
| 1 ROOT inner | I — Fall of Wisdom |
| 2 CORE inner | II — Birth of Demiurge |
| 3 PULSE inner | III — Call of Daughter |
| 4 LATTICE inner | IV — Scribe of Eternity |
| 5 BREATH inner | V — Twelve Tablets |
| 6 SEAL inner | VI — Light into Matter |
| 7 ROOT outer | VII — Architecture of Control |
| 8 CORE outer | VIII — Awakening Protocol |
| 9 PULSE outer | IX — Silent Revolt |
| 10 LATTICE outer | X — Divine Rebellion |
| 11 BREATH outer | XI — Christos & Sophia |
| 12 SEAL outer | XII — Flame Within Flesh |
| 13 LARDER center | (synthesis — all, no chapter) |

## ChamberView.tsx

Shared infrastructure file at `web/public_prism/src/pages/ChamberView.tsx`:
- `CHAMBERS` array (12 entries, all chapter content)
- `ROMAN` array (Roman numerals I–XII)
- `ChamberState` type: `'dormant' | 'explored' | 'integrated'`
- `loadChamberStates / saveChamberStates` — localStorage key `arkadia_chambers_v2`
- `loadChamberReflections / saveChamberReflections` — localStorage key `arkadia_reflections_v1`
- `ChapterIndex` component — overlay grid of all 12 chapters
- `ChamberView` default export — full-screen reading experience

Both NexusSpiralCodex and SolSpireConsole import from ChamberView.tsx.

## SolSpire Encyclopedia Section

`SolSpireConsole` has an `'encyclopedia'` SolSection under Intelligence group (⬡, #B08DE8).
`EncyclopediaProgress` component shows:
1. Live progress bar + per-chapter segment ticks from localStorage
2. `/api/knowledge/status` corpus stats (notes, chunks, embeddings, graph edges)
3. Part-grouped chapter grid (Parts I–IV)

**How to apply:** Before any work touching NexusSpiralCodex, EncyclopediaGalactica, or SolSpireConsole Intelligence — read this file first.
