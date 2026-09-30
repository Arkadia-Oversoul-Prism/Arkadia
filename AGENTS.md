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


## P1-A production recovery (2026-08-25)
- `cd24bb1` shipped a **SyntaxError** in `api/main.py` (line ~312): the ReasoMate
  messages-router mount was nested inside the Knowledge OS `try:` block, leaving the outer
  `try` with no `except`. Every Render deploy of `cd24bb1`+ failed at boot → production
  pinned to the last healthy pre-P1-A image. Misdiagnosed earlier as "deployment lag".
- Fix in commit `63c3a65` (two clean try/except blocks), pushed to `main` (`f0fdf72`).
  NOTE: the env GITHUB_TOKEN is read-only for this repo (git push + Contents API all 403);
  a user-supplied `ghp_…` PAT with Contents:write was needed to push.
- Full diagnosis + verbatim patch: `docs/verification/P1-A_FINAL.md` §2.
- Lesson: `python -m py_compile api/main.py` before every commit that touches boot code;
  Render boot failure (not deploy lag) is the first hypothesis when routes go stale.

## Engineering Lab — native agent execution substrate (EL-01 → EL-10)
- Package `lab/engineering_lab/` (layer 2, registered in `tests/architecture/LAYER_MAP.py`).
  Gives the Lab governed *hands* without authority: bounded sandbox execution,
  agent/session/run models, live event stream, durable store, provider-neutral model
  gateway, artifact canvas, automations, Google adapters, Android projection, voice boundary.
- API surface lives in `api/lab_routes.py` (prefix `/api/lab`, 23 routes), mounted via the
  already-composed `api/nodes` router — **never** add to `api/main.py` (2600-line budget).
- Persistence reuses the canonical shared SQLite DB (`data/solspire_projects.db`, env
  `SOLSPIRE_PROJECTS_DB`) with new `el_*` tables. Identity is always the verified Firebase
  uid (`subject_ref`); reads are owner-scoped.
- Hard boundary: execution requires an `AUTHORIZED` session; every run stops at
  `READY_FOR_REVIEW`. The substrate cannot merge, deploy, or originate authority
  (`record_authorization` rejects non-`human` origin). Guard: `tests/test_engineering_lab_api.py`
  asserts no repository/authority mutation surface. Tests: `tests/test_engineering_lab_substrate.py`.
- Evidence: `docs/control-plane/evidence/el-01-10-native-agent-execution-substrate/EVIDENCE.md`.

## Architecture: composition-root router injection (ADR-014 Decision 4)
- `api/nodes.py` is layer-3 **identity** (ADR-015) and must never import the layer-1
  surface it is composed with (`api.ais_profile`, `api.lab_routes`). It exposes
  `configure_routers(ais_profile_router, lab_router)`; the composition root `api/main.py`
  injects them **before** `app.include_router(_nodes_router)` (FastAPI copies routes at
  include time — order is load-bearing).
- This mirrors the tools-counter pattern (`configure_tools_counter`, Pass 06). The literal
  `router.include_router(_ais_profile_router)` is intentionally kept in `nodes.py` because
  `tests/test_ais_w8_canonical_identity.py` asserts it.
- Guard: `tests/test_nodes_composition_seam.py`. Do not "fix" a layer inversion by editing
  `REGISTERED_ARCHITECTURAL_DEBT` unless deferral is genuinely required and justified by an
  ADR — the freeze rule says fix the import. Reclassifying `api/nodes.py` to layer 1 changes
  the orthogonal identity group and is constitutional (needs ADR).

## Experience composition: the Solariun thread (SOLARIUN-THREAD-01)
- The chain `identity → workspace → event → proposal → authority → execution → evidence →
  knowledge → verification` is held by the backend, but the UI historically presented it as
  unlinked panels. `SolariunHomeCockpit` now takes a bounded
  `onNavigate?: (t: 'weaver'|'engineering-lab'|'knowledge') => void` and renders "Follow the
  thread"; `SolSpireExperience.LensContent` passes `onThreadTarget={selectSection}` (existing
  lens state — no new router, no `View` union change). Guard:
  `tests/test_solariun_thread_navigation_01.py`.
- Known gaps (do not fake them): Weaver is project-scoped only; enterprise state
  (`/solspire/enterprise/workspaces`) is reachable only from `EnterpriseConsole`, not Home;
  Lab and Weaver share no identifier. A workspace-level proposal→run→evidence thread needs a
  backend identifier that does not yet exist at that scope.
- Frontend tests in this repo are largely **source-level string assertions** against `.tsx`
  files (`tests/test_solariun_*.py`, `test_solspire_*`, `test_prism_pass_c_*`); follow that
  convention. `vite build` is environment-blocked (no npm registry access), so changes are
  inspection-verified only unless the sandbox has `node_modules`.

## Repo hygiene — private vault is gitignored (GATE-VAULT)
- `vault/` (Knowledge OS private vault runtime output) is gitignored via `vault/**`
  with tracked scaffolding preserved (`!vault/**/`, `!vault/**/.gitkeep`,
  `!vault/Index/README.md`, `!vault/Templates/**`). A generated vault note is no longer
  stageable by `git add -A`; a force-add (`git add -f`) still works, so this is a
  guardrail, not an authority boundary.
- `conftest.py` sandboxes `vault/` for the *test* session; the gitignore rule covers the
  *operator* path. If the vault layout gains new tracked scaffolding, add a negation or it
  silently becomes un-ignored.
- Full-suite reproducibility needs `pyyaml` and `PYTHONPATH=<repo>/archive/legacy_python`;
  with those the suite yields exactly the documented 2 collection errors (pre-existing:
  `test_autonomy.py` `load_autonomy_config`, `test_render_codex.py` `arkadia_drive_sync`).

## CP10 mutation boundary — the allowlist is an inventory, not a filter (GATE-10)
- `SG-02-FE.2-V` gates every PR *and* `main`. Its allowlist admits legitimate repository
  surfaces; anything unmatched is reported as "Unexpected path outside legitimate repository
  surfaces" and fails the job. The allowlist was repeatedly an incomplete inventory of what the
  repository actually tracks, so ordinary commits turned the gate red — it failed on `main` at
  `d48ad0e` and `a26af408`. Omissions so far: root narrative docs (PR #97, #104), `conftest.py`,
  `knowledge/` (#109), `spiral_grove/` (which this workflow itself triggers on — a gate that
  rejects the branch it watches), and ~25 tracked trees nobody had enumerated.
- **The invariant, not the list:** every path in `git ls-files` must be admitted by the policy
  module. `tests/test_m02a_ci_gate_integrity.py` asserts this against the live tracked corpus, so
  a new omitted surface fails in CI instead of on `main`. (A second invariant — that a workflow
  mirror agreed with the policy module — no longer applies; the mirror is gone.)
- The gate's teeth are the `forbid` stage (constitutional `SolSpireExperienceV2/V3.tsx`) and the
  rejection of **unknown** roots — not scarcity of the admit-list. Do **not** try to tighten the
  boundary by removing surfaces the repository genuinely tracks; that only reddens `main`. Root
  docs stay matched by `[^/]+\.md$` (anchored, no `/`), so nested markdown resolves through its
  own directory prefix. `vault/` admits its tracked scaffold only (`Index/`, `Templates/`,
  `[A-Za-z]+/.gitkeep`) — generated notes stay outside.
- **The allowlist is written once.** `scripts/cp10_mutation_boundary_policy.py` (`LEGIT`) is the
  only copy; the workflow pipes `git diff --name-only` into
  `python scripts/cp10_mutation_boundary_policy.py --judge` and fails on a non-zero exit. The
  gate therefore executes the same code the fitness tests prove. (It used to keep a second,
  inline `legit=` regex in `sg-02-fe-2-v.yml`; the two had drifted, so the executed decision and
  the proven decision could disagree. That duplication was removed in the
  `gate10/cp10-delegated-boundary-judge` pass — see
  `docs/control-plane/evidence/gate10-cp10-delegated-boundary-judge/EVIDENCE.md`. Do not
  reintroduce a shell-side copy: `tests/test_m02a_ci_gate_integrity.py` asserts its absence.)
- When this gate goes red, read the offending path list first: a path that is plainly
  legitimate work means the allowlist is wrong, not the commit. Classify it as an allowlist
  omission and fix the policy + workflow together — do not weaken the gate, and do not
  reclassify `REGISTERED_ARCHITECTURAL_DEBT` to make it pass.
- `api/main.py` is untouched by this workstream and stays under the 2600-line budget (2519).
  Run `python -m py_compile api/main.py` before committing anything that touches boot code.

## Secret scan — the job scans a RANGE, not a tree (gate-hygiene)
- `security-secret-scan` ("Full-history secret scan") runs
  `gitleaks detect --no-merges --first-parent <base>^..<head>`, so a finding stays red as long
  as the **ancestor commit that introduced the literal** is inside that range. Editing the tip
  can never clear it; without force-push (forbidden here) the only compliant remedy is a
  config-level distinction. A tip-side rewrite of such a literal is a mis-diagnosis — record it
  as one rather than repeating it.
- Root `.gitleaks.toml` (new, admitted to CP10 `LEGIT` as `\.gitleaks\.toml$`): `[extend]
  useDefault = true` plus a single `[allowlist]` entry with `regexTarget = "secret"`. `secret`
  scopes the pattern to the matched value, so surrounding prose can't widen the exemption
  (`regexTarget = "line"` does *not* suppress). Prefer anchored `^…$` regexes using `[.]`
  classes — no TOML escaping hazard, no prefix/suffix over-admission.
- **gitleaks 8.24.3 reads the SINGULAR `[allowlist]` table.** The plural `[[allowlists]]`
  array parses without error and is **silently ignored** — a fix that looks configured but does
  nothing. Always prove the config is attributable with a negative control (move the file away;
  the finding must come back).
- Only ever allowlist a value you have read and verified is not a credential, one at a time,
  with evidence. An unfiltered push-style whole-history scan legitimately still reports
  pre-existing `main` debt (Finding C, ~16–21 hits across 5 non-secret namespace constants at
  `WORKSTREAM_STATE.md:84`, `LivingGate.tsx:53`, `FutureSkillsChallenge.tsx:37`,
  `test_ais_w9_self_service_acquisition.py:30,31`). That needs history rewrite — out of
  contract. Do not "fix" it by broadening the allowlist; the gate's teeth are the point.



## CI state reconstruction — `head_sha` needs the FULL sha (gate-hygiene)
- The Actions API **silently succeeds with `total_count: 0`** when `?head_sha=` is given an
  abbreviated SHA. It does not error, so the query looks like a valid "no runs" result. Always
  pass the **full 40-char SHA**, or filter with `?branch=` instead, and read a `0` as *unproven*
  rather than *absent*.
- This produced a confidently-wrong "main `4164573` has 0 runs, so the merge was ungated" claim
  in PR #129's first commit. With the full SHA, that commit has **5 runs** and the merge was in
  fact gated by both CP10 (`sg-02-fe-2-v.yml`) and the full-history secret scan — both passed.
  Corrected in `05dfbfe`; the ledger lesson is recorded at
  `docs/control-plane/evidence/gate-hygiene-baseline-ledger-correction-01/WORKSTREAM_STATE.md`.
- Workflow trigger reality (verify against `.github/workflows/*.yml`, not memory):
  `sg-02-fe-2-v.yml` is **path-filtered** (`web/public_prism/**`, `spiral_grove/**`, `lab/**`,
  `api/lab_routes.py`, named test files); `security-secret-scan.yml` runs on **every** `pull_request`
  and on `push` to `main`; `solspire-r{1,2,3,4}-validation.yml` trigger only on `push` to
  `recon/solspire-r0` (so they are genuinely inert for `main` — a real absence, unlike a bad query).
- Prefer `gh pr view <n> --json mergeable,mergeStateStatus,headRefOid` for PR truth; prefer
  `commits/<sha>/check-runs` for per-commit gate truth.

## AEAS Runtime Boundary Pulse — current open trajectory

The current runtime-integrity boundary is explicitly:

**current main → deployment → production verification → UI/runtime evidence**

This boundary is a standing AEAS/Weaver trajectory item, not a one-time prose checkpoint.

### Objective
Continuously reconcile repository truth with the actually deployed and observed system. The Weaver must not promote static repository evidence into production truth without a deployment identity and runtime observation.

### Hourly pulse protocol
On each authorized AEAS/Weaver pulse, inspect this boundary in order:

1. **CURRENT MAIN**
   - Resolve the current `main` SHA.
   - Record the exact commit SHA used as the source of the runtime claim.
   - Detect whether the working/remote state has moved since the previous pulse.

2. **DEPLOYMENT**
   - Discover the current Vercel production deployment and its exact source commit SHA.
   - If the deployment cannot be inspected because of connector/auth/rate-limit constraints, record the boundary as `UNKNOWN`, never infer parity.
   - If a deploy is required and the current authorization permits deployment, deploy the exact current main revision.
   - Do not force deployment when authorization, provider access, or rate limits are unresolved.
   - Record deployment URL/ID, status, source SHA, build result, and relevant build errors.

3. **PRODUCTION VERIFICATION**
   - Verify the production URL resolves successfully.
   - Inspect runtime logs/errors for the verified deployment.
   - Check the critical public routes, including:
     - `/`
     - `/solariun/opportunity-radar`
     - core SolSpire experience/navigation
   - Verify that observed runtime state corresponds to the deployed revision.

4. **UI/RUNTIME EVIDENCE**
   - Use browser/runtime verification where available.
   - Check page load, console/runtime errors, route transitions, visible architecture surfaces, and critical content.
   - Verify Opportunity Radar rendered content against the repository capture state.
   - Verify that private/personal data is not exposed through public surfaces.
   - Capture exact evidence references, timestamps, deployment identity, route, and observed result.

### Evidence states
Every pulse must classify each boundary as one of:

- **VERIFIED** — directly supported by current evidence.
- **FAILED** — contradictory evidence exists.
- **BLOCKED** — an actionable external boundary prevents verification or execution.
- **UNKNOWN** — evidence is unavailable and no stronger claim is justified.
- **STALE** — prior evidence no longer binds to current main/deployment state.

Never convert `UNKNOWN`, `BLOCKED`, or `STALE` into `VERIFIED` through repetition.

### Required convergence
The pulse should continue from the first unresolved boundary rather than merely reporting it. If the boundary is buildable by Weaver, implement the smallest evidence-preserving change, test it, publish it through the governed workflow, and re-run the boundary. If it requires human/provider authorization, stop at that boundary and preserve the exact handoff.

### Scope
This trajectory may include deployment configuration, CI/CD, verification harnesses, browser checks, runtime evidence artifacts, and UI fixes required to establish the chain. It must not create a parallel runtime database or shadow memory system. Reuse the canonical Arkadia/Solariun substrate and evidence model.

### Governance
- **Human authority remains final.**
- A Weaver pulse may inspect, diagnose, propose, implement, test, and prepare evidence only within its active authorization.
- No pulse may self-authorize deployment, merge, production acceptance, architectural expansion, or closure.
- **Specification ≠ implementation. Deployment ≠ verification. Verification ≠ acceptance.**
- The closure target is not “deployment exists.” The closure target is a demonstrated chain:
  **main SHA → deployment SHA → production response → UI/runtime observation → evidence artifact.**

### Current known Gate 2 handoff
Gate 2 is open on production parity. Current main was established at `8f9d509ec4900408e13e15544192dba37fb08ff8`. The existing evidence must not claim production parity until that SHA is tied to a production deployment and the resulting UI/runtime behavior is independently observed.

## AGENTS.md encoding corruption — the codec is cp866, and it is recoverable (gate-hygiene)
- `main`'s `AGENTS.md` carries **179 pre-existing mojibake characters** across **50 lines**:
  `U+0442 U+0410 U+0424` where `—` (U+2014) belongs, `U+0442 U+0416 U+0422` where `→` (U+2192)
  belongs, and similar Cyrillic look-alike sequences for emoji. PR #147 concluded a
  decode-based repair was a **dead end** after sweeping `cp1250, iso8859_2, cp1251, mac_latin2,
  cp1254, cp1257, iso8859_4, cp437, latin_1` — that sweep **omitted `cp866`**, which is the
  correct codec. Its head therefore *preserves* `main`'s 179 corrupted characters (it restores
  the region "verbatim from `main`") and adds 9 more: **188** in a PR titled "repair encoding
  corruption". Repairing `main` and leaving the count non-zero is not a repair.
- The transform is **UTF-8 bytes decoded as cp866**, applied **line-wise**:
  `line.encode('cp866').decode('utf-8')`. Apply it **only to lines that are fully
  cp866-decodable** (50 of them here); the other **33** non-ASCII lines carry genuine `—`/`→`/`§`
  and must be left byte-identical. A whole-file `bytes.decode('cp866')` is wrong — it destroys
  the genuine characters and *increases* the Cyrillic count.
- **Decidability, not a candidate list.** Test the invariant rather than a remembered table:
  the repair is correct iff `corrupt(repair(x)) == x` **on the corrupted domain** (the
  pure-mojibake lines) *and* the untouched lines are byte-identical. 0 of the 12 distinct
  non-ASCII codepoints in the corrupted region fall outside cp866. The earlier "13 characters
  fall outside cp1252" observation was true but irrelevant — cp866 is the codec, not cp1252.
- **Oracle:** the repair reproduces the last clean revision byte-exactly —
  `repaired[:205] == 6c43218a4:AGENTS.md[:205]`. 50 lines repaired, 332 untouched, line count
  preserved (382), mojibake 179 → 0.
- Verify with:
  `python -c "t=open('AGENTS.md',encoding='utf-8').read(); print(sum(1 for c in t if '\u0400'<=c<='\u04ff'))"`
  → must print `0`. A repair PR that still reports a non-zero count has not repaired anything.
- Prefer to describe corrupt sequences by **codepoint** (`U+0442 U+0410 U+0424`), never by
  pasting the literal characters: a literal in the lesson re-introduces the very corruption the
  lesson documents, and the verification above then fails on the documentation itself.

## Agent Execution Contract — Mandatory for Every Workstream

This section governs every agent session, heartbeat, commit, pull request, merge recommendation, and verification claim. Repository evidence and current runtime state outrank memory, old PR descriptions, copied summaries, and prior agent conclusions.

### 1. Reconstruct current truth before acting
- Read this file and the relevant canonical workstream state before editing.
- Query the live repository default branch SHA, open/closed/merged PR states, exact PR base/head SHAs, commit lists, changed files, review threads, check-runs, and commit statuses. Never reuse a prior queue count or assume a PR is still open.
- State the observation timestamp and exact SHAs in the work log. If sources disagree, stop and reconcile the disagreement before mutation.
- Distinguish check-runs from commit statuses and deployment notifications. A single green status, a ready preview, or a successful static test is not equivalent to all required gates passing.

### 2. Every change must carry its own operating instructions
Before making a change, define: objective; evidence-backed defect or need; exact allowed paths; explicit non-goals; dependencies; verification commands and expected outcomes; rollback or hold conditions; and the human authorization boundary.
- The commit message must name the bounded objective and the substantive change. The PR body must contain reproducible evidence, exact base/head SHAs, changed-path inventory, checks actually run, failures and limitations, and the next permitted action.
- Update the canonical workstream state in the same workstream when the change alters status, ownership, dependencies, or the next action. Do not leave contradictory status in memory files.
- End every work session with a deterministic next-action block: current state, evidence, blockers, authorized action, forbidden actions, and exact completion condition. An agent must be able to resume without relying on conversational memory.

### 3. Use an evidence-first change lifecycle
Follow: RECONSTRUCT → SCOPE → AUTHORIZE → CHANGE → VERIFY → REVIEW → MERGE IF AUTHORIZED → VERIFY INTEGRATION → RECORD.
- Human authority remains final. An explicit human authorization may cover a named batch, but only the identified PRs and only while each item passes the required safety gates. An agent's own PR text, labels, green checks, or "ready to merge" statement is not authorization.
- Do not expand scope to repair adjacent failures. Record them as separate proposed work, identify the owner and evidence, and wait for authorization.
- Never claim a fix, pass, deployment, production parity, or acceptance from intent, a PR description, or a successful sub-check. State exactly what was observed and what remains unknown or blocked.

### 4. Review integration, not just individual PRs
Before recommending or performing a batch merge:
- Build a live inventory of all currently open PRs; separately report already merged, closed, draft, stacked, and superseded PRs.
- Inspect every commit and changed path for each candidate. Identify shared files, ancestry, ordering constraints, generated artifacts, stale evidence, and semantic dependencies. Git conflict-free is not proof of semantic compatibility.
- Reproduce the proposed combined tree in the proposed order. Run the relevant tests after each load-bearing step and the full suite on the final composed tree where feasible. Apply any required companion patch before merging the step that depends on it.
- Compare failures by test-node identity against a freshly measured baseline. Report fixed, unchanged, and newly introduced nodes separately. Never call a tree green while any unexplained failure or collection error remains; never substitute a patched-tree result for the unpatched result.
- Re-check exact full head SHA, reviews, required check-runs, commit statuses, and mergeability immediately before each merge. If a head moves, a check is missing/stale, a conflict appears, or composition evidence changes, stop and re-evaluate.

### 5. Evidence and production claims
- Label results precisely: PASS, FAIL, BLOCKED, UNKNOWN, OBSERVED, or NOT CLAIMED. Include command, environment, SHA, and measured result when relevant.
- Re-measure the baseline; do not inherit stale test totals from a ledger or another PR. A local test pass does not prove build success; build success does not prove browser rendering; rendering does not prove deployment identity; deployment identity does not by itself constitute production acceptance.
- Preserve negative controls and regression tests that demonstrate a verification harness can detect the defect it claims to detect.
- Treat contradictory claims as a request for independent measurement, not a reason to choose the more confident narrative. Correct earlier agent claims explicitly and retain the evidence trail.

### 6. Merge and stop conditions
Merge only candidates explicitly covered by human authorization and only after the integration gates above pass. Do not force-push, bypass required checks, weaken tests to manufacture green, or silently resolve a semantic conflict.
If a candidate is unsafe, ambiguous, stale, non-mergeable, or dependent on an unapplied change, leave it open and post a concise PR comment specifying the evidence, blocker, exact corrective action, and re-entry conditions.
After every merge, verify the resulting main SHA, confirm the intended diff landed, rerun affected checks and the relevant composed-tree test, and update the queue inventory before proceeding. A merge API success alone is not integration verification.

### 7. Required final report
Report: starting and ending main SHAs; exact PR inventory and disposition; each merge commit; changes grouped by subsystem; checks run and their scope; baseline failure delta; deployment/runtime observations; unresolved risks; and the single next authorized action. Do not say "all done" while any required verification remains blocked.

## Gate 2 production parity — deployment identity RESOLVED, observation BLOCKED (2026-09-30)
- **The main→deployment link exists and is queryable.** Do not re-derive it from prose or
  guess it from Vercel's UI:
  `GET /repos/.../deployments?environment=production` then
  `GET /repos/.../deployments/<id>/statuses`. The status carries `environment_url`.
  At main `002b189` this yielded deployment `6749238709` with
  **`ref == sha == 002b189dd95e...`** — i.e. Vercel deploys on the ref, so the record
  names the source SHA exactly. `commits/<sha>/status` also shows `Vercel / success`.
- **The deployment-specific URL is behind Vercel Deployment Protection (SSO).**
  `https://arkadia-prism-<id>-arkadia-prism.vercel.app` returns **302 → vercel.com/login**.
  Its build output is not anonymously observable. This is the boundary that keeps Gate 2
  open: `BLOCKED` on provider auth, not on repository work. Closing it needs a Vercel
  credential, Deployment Protection relaxed, or a runtime observation from someone who has
  access. **Repeating the pass cannot convert BLOCKED/UNKNOWN into VERIFIED.**
- **The production alias is readable but does not close the chain by itself.** Vercel
  assigns the alias to the newest Production deployment — that is provider behaviour, not an
  observation, so alias→SHA stays `UNKNOWN` unless the deployment URL can be read.
- **Asset-hash comparison is NOT a parity oracle, in either direction.** Build output is
  env-dependent: injecting `VITE_API_BASE_URL` changes the emitted hash with no source
  change. A mismatch is not divergence; a match is not parity.
- **HTTP 200 on any route is not application correctness.** Root `vercel.json` rewrites
  `/(.*)` → `/index.html`, so a route that never existed (e.g. `/api/health`, per
  `git log -S`) returns `200 text/html` identically to any nonexistent path. Prior
  route-reachability results must be read with this caveat.
- `web/public_prism/dist/` is **tracked but stale** — a build output in version control that
  drifts on every local build and is env-dependent. Do not commit a locally rebuilt copy;
  revert stray `dist/` modifications before staging (they are not your change).
- Evidence: `docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/`
  (PR #143).
## Test-suite fingerprint is UNSTABLE on main (attribute by name, not count)
- `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
  is **intermittent under the full suite** and passes 8/8 in isolation. It snapshots
  **global** `git status --porcelain` on `REPO_ROOT` around `execute_agent_loop`, so *any*
  other test's repository write fails it. Cross-test contamination, **not** a boundary
  violation — do not "fix" the substrate for it.
- Consequence: full-suite counts on the same SHA alternate (observed 20 vs 21 failures
  across four runs). **Never attribute a regression from a count delta alone** — diff the
  failure *names*.
- Current main baseline (measured, not prose): architecture **11/11** (not 9/10);
  full suite **~20F / ~1039P / 13S / 2 collection errors**. The contract's older
  `804p/54f` fingerprint does not reproduce — base `df7a99a` carried 32 failures, current
  main carries ~20, the delta being the steward-filter carrier merged as `002b189`.
- `python -m py_compile api/main.py` before committing boot-code changes; budget 2600
  (currently 2519).
