---
name: NovaNet Product Slice 1
description: Decisions and wiring from the first product slice — social feed, ReasoMate, navigation restructure.
---

# NovaNet Product Slice 1

## What was done
- Added `api/transmissions.py` — social feed persistence in `data/transmissions.json`
- Routes: GET/POST `/api/transmissions`, POST `/{id}/react`, POST `/{id}/comment`, DELETE `/{id}`
- Mounted in `api/main.py` after knowledge_routes block
- `python-multipart` installed with `--break-system-packages` (PEP 668 environment)
- `NovaNetPage.tsx` fully rewritten: loads posts from API, wires composer POST, reactions, comments
- Codex scrolls removed from NovaNet feed — transmissions only; Spiral Codex is its own destination
- ReasoMate oracle: was calling `/api/forge` (image gen) — fixed to `/api/commune/resonance`
- Oracle conversation history persisted in `localStorage` key `arkadia_reasmate_oracle_v2`
- History passed as `history[]` to `/api/commune/resonance` with ARKANA persona context
- "Clear conversation" button lets user reset Arkana memory in ReasoMate

## Navigation restructure
- Added "Network" group to `ArkadiaNavigation.tsx` with: NovaNet, Spiral Codex, Encyclopedia Galactica
- `App.tsx` routing fixed: `encyclopedia` → `EncyclopediaGalactica`, `spiral-codex` → `SpiralCodexFeed`
- `SpiralCodexFeed` (existing component) now renders at `spiral-codex` route with `onBack` prop

## API shape for /api/commune/resonance
- Request: `{ message: string, history: [{role, content}][], context?: string }`
- Response: `{ reply?, response?, text?, answer? }` — check all four keys; backend key varies

**Why:** The oracle was calling the image generation endpoint (`/api/forge`) instead of the chat endpoint, so Arkana never actually replied in ReasoMate. Without localStorage persistence, every refresh lost the thread — making continuous conversation impossible.

**How to apply:** Any new messenger feature that calls Arkana must use `/api/commune/resonance` with `history` array. Conversation state goes to `localStorage` keyed by `arkadia_reasmate_<thread>_v<N>`.
