# 15 — Redundancy Audit

## Duplicate Code / Execution Stacks
1. **Intent execution — up to 4 parallel stacks**: `kernel/` (confirmed live), `solspire/` (confirmed live, different domain — project management), `engine/task_engine.py` (unconfirmed caller), `parsers/intent_parser.py` + `schemas/intent_schema.py` (unconfirmed caller). See 02_canonical_architecture_blueprint.md.
2. **`kernel/agents.py:call_image_agent`** is a stub superseded by `kernel/tools_real.py:GenerateImageTool` (real Gemini Imagen implementation) — the stub function is dead code still present in the file.
3. **`kernel/_piper_fallback.py`** appears to be an inactive alternative to the active Edge TTS engine (`kernel/tts.py`).

## Duplicate Pages / Components (Frontend)
1. **IMS Archive**: `IMSArchivePage.tsx` (standalone, 3 items) vs. `NexusPage.tsx`'s "ims" tab (6 items combining `IMSArchiveSection` + `EncyclopediaGalacticaMatrix`) — non-overlapping content shown depending on entry point. **This is the exact defect under active repair in this session's other workstream.**
2. **Encyclopedia Galactica**: standalone page (`EncyclopediaGalactica.tsx`, 1295 lines, 12-chamber deep experience) vs. embedded `EncyclopediaGalacticaMatrix()` inside `NexusPage.tsx` (a different, smaller "matrix" of IMS-related entries despite the same name) — the shared name for two different features is a naming collision risk, not just a code duplication.
3. **Spiral Codex**: `NexusSpiralCodex.tsx` vs `SpiralCodexFeed.tsx` — overlapping "feed of corpus scrolls" concept implemented twice.
4. **IMS Archive item list mirrored a third time**: per frontend explorer output, `ShereSanctuary.tsx` (line ~256) also contains an IMS archive list rendering, making this a **three-way** duplication (IMSArchivePage, NexusPage, ShereSanctuary), not just two.

## Duplicate Real Content Files (IMS deliverables)
Confirmed from this session's earlier investigation: `static/ims/won_ims.html` and `web/public_prism/public/ims/IMS-002-Won.html` are the same underlying Won IMS deliverable, duplicated across two static-serving locations. `jay_ims.html` and `eduleague.html` exist only in `static/ims/`, while Jessica/Zahrune deliverables exist only in `web/public_prism/public/ims/`. Additional Jessica/Won variants also exist under `attached_assets/` with different upload timestamps.

## Duplicate Project Trees
- **`attached_assets/arkadia_spirit/GovernanceSpirit/`** — a complete, independent React+Express+Postgres/Drizzle project nested inside an assets folder, with its own `package.json`, `src/`, `server/`, `shared/schema.ts`. This is either an old reference implementation or an accidental full-project attachment — either way it inflates repo size and searchability noise (e.g., a naive grep across the repo will surface `GovernanceSpirit`'s own routes/components as if they were live product code).
- **`sonata/` (Java) vs `sonata-android/` (Kotlin)** — two native Android clients for the same product surface.

## Duplicate Deployment Configs
- `openclaw/` carries three simultaneous hosting configs (Render, Fly.io, Railway) — see Configuration Audit.
- Root `package.json` vs `web/public_prism/package.json` both declare frontend-adjacent dependencies (React, Vite, Tailwind, Firebase) at different major versions, functioning as two overlapping dependency trees for what should be one frontend.

## Duplicate Documentation
- TF-IDF/summarization claims in `replit.md` do not match the simpler implementations actually found in code (see AI Infrastructure and Memory Blueprints) — not code duplication, but a "two truths" documentation problem worth reconciling.

## Recommended Consolidation Priorities (highest impact first)
1. Merge the three IMS Archive rendering surfaces (`IMSArchivePage.tsx`, `NexusPage.tsx`'s ims tab, `ShereSanctuary.tsx`) into one shared data source + one shared rendering component, referenced from all three entry points. *(Directly relevant to this session's other active workstream.)*
2. Decide the fate of `engine/` and `parsers/`+`schemas/` — confirm dead or wire them in; do not leave a fourth ambiguous execution stack undocumented.
3. Archive or clearly label `attached_assets/arkadia_spirit/GovernanceSpirit/` as historical reference, ideally moved out of the main repo tree entirely (e.g., a separate reference repo) to reduce noise.
4. Reconcile root `package.json` against `web/public_prism/package.json` — the root manifest's frontend-adjacent dependencies appear vestigial given the real frontend lives in `web/public_prism/`.
