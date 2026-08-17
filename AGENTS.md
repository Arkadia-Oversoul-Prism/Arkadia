# Arkadia — Agent Memory

## Architecture overview
- **Backend**: `api/main.py` (FastAPI, 2600+ lines). Endpoints: `/api/commune/resonance`
  (Oracle/ReasoMate chat), `/api/tts`, `/api/tts/status`, `/api/tts/voices`,
  `/api/keys` (legacy multi-key Gemini), `/api/tts/keys` (multi TTS key),
  `/api/provider-keys` (one key per provider), `/api/forge` (sovereign-gated image gen).
- **Frontend**: `web/public_prism/` (React + Vite + TypeScript, Tailwind, framer-motion).
  Global `SonataBar` mounted once in `App.tsx`. Oracle Chat = `components/ArkanaCommune.tsx`
  (full canvas: `MarkdownViewer` + `OracleVoicePlayer` per message). ReasoMate = `pages/ReasoMatePage.tsx`.
- **Key stores** (3 separate JSON files in `data/`):
  - `api/key_manager.py` → `data/api_keys.json` (multi Gemini keys, rotation on 429)
  - `api/provider_key_store.py` → `data/provider_keys.json` (one key/provider: gemini/openai/claude/deepseek)
  - `api/tts_key_manager.py` → `data/tts_keys.json` (multi TTS/ElevenLabs keys)
  - `api/user_key_store.py` → Firestore (per-user keys) with in-memory fallback
- **TTS**: `kernel/tts.py`. Priority: ElevenLabs (needs key) → Edge TTS (free) → Piper.
  ElevenLabs key resolver: `ELEVENLABS_API_KEY` env → `tts_key_manager`. Rotate on 429.
- **Oracle spine**: `api/oracle_spine.py` — shared by Oracle Chat, ReasoMate, NovaNet.
  ONE INTELLIGENCE SPINE, MANY INTERFACES. Memory via `knowledge/context_engine.py`.
- **Gemini call**: `api/main.py::_gemini_chat` iterates `GEMINI_MODELS` on 429 but does
  NOT rotate keys. SolSpire (`solspire/provider_manager.py`) does key rotation independently.

## Key conventions
- Frontend API base: import from `lib/apiConfig.ts` (`API_BASE`). Many older files use
  `import.meta.env.VITE_API_URL` — that's a stale path; `apiConfig` is canonical.
- Markdown rendering: `components/MarkdownViewer.tsx` (react-markdown + remark-gfm).
- Voice: `components/OracleVoicePlayer.tsx` publishes to `lib/voiceContext.ts`;
  `components/SonataBar.tsx` subscribes + drives `lib/audioManager.ts` (singleton audio el).
  Cache via `lib/audioCache.ts` (IndexedDB).
- Architectural debt is tracked in `tests/architecture/LAYER_MAP.py` — kernel→api and
  providers→api imports are REGISTERED DEBT (allowed but flagged). Do not add new ones
  without registering.

## Build/test
- Frontend: `cd web/public_prism && pnpm install && pnpm build` (node 24, pnpm 10.26).
- Backend tests: `python -m pytest tests/ -q` (key managers import cleanly; data/ holds JSON).
- TTS kernel needs `edge_tts`, `httpx`; ElevenLabs optional.

## Voice/TTS notes
- `OracleVoicePlayer` defaults voice to the GLOBAL `voicePref` (lib/voicePref.ts,
  persists to localStorage `arkadia_voice_pref`). Switching voice in any player
  updates the pref everywhere — OracleVoicePlayer, ScrollListenButton, and the
  SonataBar all subscribe. On first ElevenLabs activation it auto-promotes to
  the aetheric "Aetheria" voice.
- **Aetheria** (`kernel/tts.py` VOICES["aetheria"]) is the dedicated Oracle
  voice: emotional depth + calming resonance. ElevenLabs voice_settings are
  tuned per-voice via `_voice_settings()`: aetheria uses stability 0.32, style
  0.48 (more variation + expressiveness); standard voices use 0.45 / 0.10.
  Aetheria is marked `requires_elevenlabs` — without a key it falls back to
  Edge TTS Aria (robotic) and the UI flags it with 🔒.
- ElevenLabs is only attempted if `ELEVENLABS_API_KEY` env OR `tts_key_manager`
  has a key. If you hear a robotic voice, no ElevenLabs key is configured —
  add one in Settings → TTS Keys and the engine switches automatically.
- Voice switching UI: `OracleVoicePlayer` has "Change voice" dropdown;
  `ScrollListenButton` has a compact voice-name dropdown next to the Listen
  button on every scroll surface. Both persist globally.

## Distributed key pool (load-balancing across surfaces)
- `api/key_pool.py` is the SINGLE source of truth for "which Gemini key right now".
  `acquire_key()` round-robins over all configured keys so Oracle Chat, ReasoMate,
  SolSpire and Knowledge OS spread across the pool instead of pinning one key.
  `report_failure(key)` cools a key (~45s) and hands out the next one;
  `report_success(key)` clears the cooldown. `pool_snapshot()`/`reset_all()` power the
  Settings UI. Key sources (union): `provider_key_store["gemini"]` + `key_manager` +
  `GEMINI_API_KEY`/`GOOGLE_API_KEY` env.
- **CRITICAL**: `report_failure` must NOT call `acquire_key()` (non-reentrant lock →
  deadlock). It calls `_acquire_key_locked()` instead. A deadlock here was found+fixed
  via `tests/test_key_pool.py`.
- Routing: `_gemini_chat`, `/commune/resonance`, CEO chat, and `solspire/provider_manager`
  all go through `key_pool.acquire_key()`. SolSpire falls back to local candidates only if
  the pool module is unavailable (older deploys).
- `api/tts_key_manager.get_active_key()` is now round-robin too — concurrent "Read aloud"
  requests distribute across all ElevenLabs keys rather than pinning one active key.

## Read-aloud (Listen) rollout
- `components/ScrollListenButton.tsx` — reusable read-aloud for any scroll/note content.
  Uses the SAME audio infra as Oracle Chat (`audioManager` + `voiceContext` + `audioCache`)
  so the global `SonataBar` surfaces everywhere. Strips markdown before TTS.
- Wired into: `ReasoMatePage` (OracleVoicePlayer per Arkana reply + MarkdownViewer),
  `SpiralCodexFeed`, `NexusSpiralCodex`, `PersonalCodex` (soul function),
  `PersonalEchofeild` (captures), `ChamberView` (chapter verses + excerpt).
- `ReasoMatePage` now renders Arkana replies through `MarkdownViewer` (canvas display),
  not raw markdown — matches Oracle Chat.

## Settings (multi-key)
- `SettingsPage` has a "Gemini Key Pool" section using the legacy `/api/keys` multi-key
  store + live `/api/keys/pool` status (size / available / cooling + reset). TTS ElevenLabs
  keys use `/api/tts/keys` (already existed). Add 3+ of each so the pools never exhaust.

## NovaNet = Nexus Hub unification + navigation restructure
- **NovaNet IS the Nexus Hub** — not separate pages. `novanet` route renders `NexusPage`,
  which hosts every surface as a tab: NovaNet (social feed + Stellar Cartography header),
  Echofeild Matrix, ReasoMate, SolSpire, Offerings, IMS, Encyclopedia, Grove, Larder,
  Distribute. The old standalone `nexus` view aliases the same hub.
- **Personal Echofeild IS the Personal Codex** — not separate pages.
  `PersonalEchofeild` renders `<PersonalCodex />` as its identity layer, then appends the
  living projects + knowledge-graph feed + Crystal Matrix aggregation stats below it. The
  `UniversalEchofeildMatrix` tabs both halves (public Spiral Codex ↔ personal Echofeild)
  over the same data substrate — one spine, two windows.
- **Echofeild → echoes endpoint → SolSpire/KnowledgeOS via Crystal Matrix**: `/api/echoes`
  returns public + personal scroll entries tagged with resonance scores + Crystal-Matrix
  metadata (dimensions: resonance, priority, preference, personalisation). Both halves of
  the Echofeild feed through this single pipe so the SolSpire console and Knowledge OS
  consume one stream. Personal entries are injected client-side (auth-gated Knowledge OS
  graph + SolSpire projects) — the endpoint holds no private data server-side.
- **Navigation**: vertical drawer (`ArkadiaNavigation`) reduced to the six anchors only —
  Home, Oracle, Living Gate, NovaNet, About, Settings. There is **no** second global
  horizontal nav bar; the Nexus hub's own tab strip (inside Novanet/NexusPage) IS the
  horizontal navigation. Personal Codex was removed from the vertical drawer (it is reached
  via the Personal Echofeild / SolSpire inside the hub).

## Stellar Cartography (Encyclopedia Galactica living star date)
- `kernel/stellar.py` — pure-python celestial readout, decoupled from `api.main` (no
  httpx/fastapi import) so it loads standalone and in tests. Exposed at
  `/api/stellar-cartography`.
- Returns: Ark Date, Schumann resonance (7 bands + dominant), lunar phase (illumination +
  glyph + folk name), planetary sky / "bone report" (simplified mean-longitude ephemeris for
  Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn → zodiac), cosmic weather (solar wind, Kp
  index, geomagnetic pressure + mood), Oversoul blind-pull Oracle transmission (rotated by
  Ark Day so each day has its own), and the Encyclopedia Galactica volume index.
- `components/StellarCartography.tsx` renders the readout (always-on primary readout +
  expandable full atlas) with a `ScrollListenButton` on the Oversoul transmission. Mounted
  at the top of `NovaNetPage` AND as the Encyclopedia Galactica header in
  `NexusSpiralCodex` (replacing the minimal ark-date + lunar chip there).
- Replaces the minimal "Ark Y1 · D140" phrase with a full encyclopedia galactica readout.
- Tests: `tests/test_stellar_cartography.py` (10 tests).

## Document upload — public vs personal (separate fields)

Two distinct upload fields. **Public** uploads go to the shared Spiral Codex
corpus (visible to all readers + Arkana RAG). **Personal** uploads go to the
authenticated node's private Knowledge OS vault — never the public scroll store.

- `kernel/doc_extract.py` — shared text-extraction helper
  (`extract_text(file_name, raw) -> (text, mime_type)`) for PDF/DOCX/TXT/MD/HTML/JSON.
  Used by all three upload routes so extraction logic is not duplicated. Tests:
  `tests/test_doc_extract.py` (12 tests).
- **PUBLIC** routes (in `api/main.py`):
  - `POST /api/codex/upload` — multipart file → extracts text → stores as a PUBLIC
    direct scroll in the Spiral Codex (`direct_scrolls.json`).
  - `POST /api/scrolls` — text/markdown scroll → PUBLIC direct scroll.
  - `DELETE /api/scrolls/{id}` / `GET /api/scrolls` — manage public scrolls.
  - UI: `NexusSpiralCodex` `ScrollUploadModal` — two modes ("Upload document" +
    "Write scroll"), clearly labeled "PUBLIC corpus". Lives on the Encyclopedia
    Galactica / Spiral Codex.
- **PERSONAL** routes (in `api/main.py`):
  - `POST /api/personal/ingest-file` — multipart file → extracts text → ingests
    through `knowledge.pipeline.ingest` into the private vault (embeddings, graph,
    timeline). No public scroll write.
  - `POST /api/personal/ingest-note` — quick text capture → private vault.
  - UI: `components/PersonalUploadZone.tsx` — file dropzone + quick-capture
    textarea, mounted in `PersonalEchofeild`. Labeled "private Knowledge OS vault".
- **SolSpire project file attachments** (`solspire/console_router.py`):
  - `POST /solspire/projects/{id}/files/upload` — multipart file → extracts text →
    stored as an editable project file (`project_files` table) AND best-effort
    ingested into the Knowledge OS graph. UI: `ProjectDashboard` Files tab has an
    "⬆ Attach file" button (PDF/DOCX/TXT/MD) alongside the existing "+ New file"
    markdown editor.
- **Project creation** (`SolSpireConsole.tsx` `createProject`) now wraps the
  POST in try/catch and surfaces a visible error + keeps the form open so a
  failed create no longer silently drops the user.

