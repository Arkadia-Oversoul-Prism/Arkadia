---
name: Frontend Hub Architecture
description: Arkadia frontend is hub-based; Nexus + SolSpire are the consolidation points. Never fragment into standalone nav items.
---

## The Rule
Arkadia's frontend is intentionally **hub-based**, not item-based. The user explicitly wants consolidation, not fragmentation.

**Why:** Commit `6d7138f` (Jul 15 2026) was titled "Consolidate Arkadia frontend: Nexus and SolSpire unified hubs" and reduced nav from 18 items to 10. The user confirmed this direction by calling later fragmentation "worse."

**How to apply:** Before any frontend structural work, check — am I adding a standalone nav item or splitting something out of a hub? If yes, that is the wrong direction unless the user explicitly requests it.

## Hub Map (canonical as of ddf4069)

### Nexus Hub (`view === 'nexus'` → NexusPage.tsx)
Tabs: NovaNet · IMS Archive · Encyclopedia (→ NexusSpiralCodex) · Spiral Grove · Living Larder · Distribute

### SolSpire Console (`view === 'solspire'` → SolSpireConsole.tsx)
Tabs: Projects · Knowledge · Operations · Codex

## Key Component Assignments
- **Crystal Matrix dodecahedron navigator** lives in `NexusSpiralCodex.tsx` (1062-line version). It is the Encyclopedia tab inside Nexus Hub. Do NOT gut it.
- **ReasoMate** lives as a floating panel inside `NovaNetPage.tsx`. It is NOT a standalone page/nav item.
- **NexusSpiralCodex.tsx** renders as the `encyclopedia` tab of NexusPage, not as the `spiral-codex` standalone view. The `spiral-codex` view routes to `SpiralCodexFeed.tsx`.

## Navigation Structure (coherent state)
```
Core:        Home · Oracle · Living Gate
Network:     NovaNet · Spiral Codex · Encyclopedia Galactica
Intelligence: Nexus Hub · SolSpire Console
Modules:     Offerings
System:      Settings · About
```

## What Breaks Coherence
- Creating a standalone ReasoMatePage nav item (ReasoMate belongs inside NovaNet)
- Removing NovaNet or Encyclopedia tabs from NexusPage (they belong there)
- Gutting NexusSpiralCodex (the Crystal Matrix is a core UI artifact)
- Moving Encyclopedia Galactica out of NexusPage into a top-level standalone view
