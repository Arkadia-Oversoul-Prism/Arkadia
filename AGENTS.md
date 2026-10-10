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
  convention. The npm registry is reachable and a clean install + build succeeds here
  (`corepack pnpm install && corepack pnpm build`, node 24 / pnpm 10.26); attempt it and
  report the measured result. `pnpm`'s activation symlink can hit `EACCES` — `corepack pnpm`
  is the working invocation. Build output lands in untracked `dist/`.

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
- Measured at `0c8a9f6`: **1** collection error, not 2 — `tests/test_render_codex.py` does not
  exist (only the non-collected `tests/render_codex_probe.py`, renamed by `00271b2`). The
  remaining error is the CE-01 `weaver.autonomy` module-vs-package collision, reserved to the
  sovereign; the count above is superseded by this measurement.
- Also measured at `0c8a9f6`: the reproducibility command above is incomplete — a **bare**
  `pytest tests/` *interrupts* at the collection error (exit 2) and under-reports the run
  (`1 skipped, 1 error in ~1.3s`). Add `--continue-on-collection-errors` to reach the
  documented 20F / 1252P / 17S / 1E. The `pyyaml` + `PYTHONPATH` requirements still hold.

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

## Canonical deployment model — ONE reconciled deployment (governing invariant)

**Arkadia has ONE canonical, reconciled deployment.** The UI, API, authentication/authorization
boundary, shared relational substrate, execution runtime, evidence systems, and product
interfaces belong to one coherently governed deployment. Distinct modules, services, routes, and
processes are implementation detail; they do **not** create independent canonical deployment
authority.

This is a sovereign decision, recorded as `docs/adr/ADR-016-single-canonical-deployment.md`.
Agent rule: **an observed hostname is not proof of canonical ownership, and a successful HTTP
response from an alternate deployment does not establish acceptance.** Do not interpret a
separately observed Vercel deployment, historical frontend project, alternative Render hostname,
or stale deployment record as authorization to establish a second canonical deployment.

Keep these six concepts separate — conflating them is a defect:

1. canonical source revision, 2. canonical deployment identity, 3. actual running revision,
4. internal module/route registration, 5. runtime verification, 6. explicit acceptance.

Runtime evidence must always identify the **actual deployment under examination** (host +
revision). Deployment drift must be reported explicitly. No agent may establish an alternative
canonical deployment, change production routing, or retire an alias without explicit
authorization. `GET /api/version` is the read-only revision probe; a matching revision is
necessary evidence of source↔runtime consistency but is **not** sufficient proof the application
works, and it cannot prove what an already-running deployment serves until a build containing it
is deployed.

## AEAS Runtime Boundary Pulse — current open trajectory

The current runtime-integrity boundary is explicitly:

**current main → canonical deployment → production verification → UI/runtime evidence**

The deployment boundary has exactly one canonical target (ADR-016). Alternate hostnames
(e.g. a separate Render hostname or the legacy Vercel alias) are drift to be recorded
and classified, never adopted as a second authority.

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
- **The live file is under a standing insertion-only constraint — editing it in place is a
  regression, not a neutral edit.** `scripts/agents_md_encoding_audit.py` (oracle
  `6c43218a48a4`, the last clean revision) audits the *working tree* and asserts the recovered
  text relates to the oracle by **insertions only** (`oracle_alterations == []`). Rewriting a
  line that the oracle already contains yields `alterations=1` → `decidable=False` → exit 2,
  which breaks `test_live_file_verdict_matches_its_state` and
  `test_cli_summarises_the_oracle_without_crashing` (2 new failures) even though the bytes are
  clean and `cyrillic == 0`. Proven: an in-place rewrite of the reproducibility sentence moved
  `tests/test_agents_md_encoding_adjudication.py` from 2F/17P to 4F/15P and the full-suite
  fingerprint from `a59453b8…` (21 nodes) to `f1c7c0c3…` (23 nodes).
- **To change text an oracle line carries, append a correction — never rewrite the line.**
  Stale claims that sit on oracle lines get a dated "measured at `<sha>`: … supersedes the
  above" insertion instead. Lines added *after* the oracle are not constrained. Verify with
  `python scripts/agents_md_encoding_audit.py` → `alterations=0`, `oracle_reproduced=True`,
  **exit 1** — the clean-and-oracle-corroborated status, not a failure. Exit 2 is the
  divergent/undecided one; exit 0 is a successful mojibake *recovery*. Then re-derive the
  fingerprint with `scripts/baseline_fingerprint.py`; the node set must be unchanged.

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
- **The deployment-specific URL is behind Vercel Deployment Protection (SSO).** The correct
  host is **`environment_url` from `/deployments/<id>/statuses`** — at `002b189` that is
  `https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app`, which returns **302 →
  vercel.com/sso**. Do **not** build the URL from the deployment id: `environment_url` is
  `null` on the deployment *record*, and the hostname segment (`ey2ozd5u4`) is a
  provider-generated hash, not the id. Constructing `arkadia-prism-<id>-…vercel.app` yields
  HTTP **404** and reads as "deployment missing" — a mis-diagnosis made and corrected in the
  Pass 3 run. Its build output is not anonymously observable. This is the boundary that keeps
  Gate 2 open: `BLOCKED` on provider auth, not on repository work. Closing it needs a Vercel
  credential, Deployment Protection relaxed, or a runtime observation from someone who has
  access. **Repeating the pass cannot convert BLOCKED/UNKNOWN into VERIFIED.**
- **The alias→SHA binding is UNKNOWN *and immaterial* — do not chase it.** `git log -1 --
  web/public_prism/ ':!web/public_prism/dist'` gives the last commit touching *any* frontend
  build input (`b377a01`, 2026-09-29). **All 12** Production deployments on record are its
  descendants, so all twelve compile byte-identical frontend source and the artifact
  **cannot** discriminate between them. The alias→SHA fact stays unobservable, but
  build↔source lineage does not depend on it. This is strictly stronger than a
  `--since=<deploy time>` window, which only excludes divergence *after* one deployment.
  Recorded so a future pass does not re-spend effort trying to extract a binding the build
  cannot carry.
- **Marker counts are convention-dependent — always name the convention.** The minified
  bundle is a handful of enormous lines, so `grep -c` (*matching lines*) and an
  occurrence-counting harness disagree for the same marker on the same artifact:
  `solspire-object-summary` is **3 lines / 6 occurrences**, `opportunity-radar` **2 / 4**.
  Both are correct. Only the **presence/absence contrast** is load-bearing (marker present
  vs. pre-change control absent); magnitudes are reproducibility detail. Do not read a
  count difference between two evidence sections as drift — Pass 2 recorded line counts and
  Pass 3 records occurrences, and reconciling them took a re-download of the deployed asset.
- **The production alias is readable but does not close the chain by itself.** Vercel
  assigns the alias to the newest Production deployment — that is provider behaviour, not an
  observation, so alias→SHA stays `UNKNOWN` unless the deployment URL can be read.
- **Asset-hash comparison is NOT a parity oracle, in either direction.** Build output is
  env-dependent: injecting `VITE_API_BASE_URL` changes the emitted hash with no source
  change. A mismatch is not divergence; a match is not parity. (Observed: deployed bundle
  is 84,551 bytes larger than a clean local build of the same SHA.)
- **Marker-set comparison IS a valid lineage oracle — use this instead of hashes.** Pick
  string literals unique to a source file that must survive minification (testids, storage
  keys, distinctive prose — they are runtime data, not identifiers), then fixed-string
  `grep` them in the deployed asset. Include a **pre-change control** string that must be
  absent. At `002b189` the deployed asset and a clean local build matched on **every**
  marker and count, while the pre-SG-03 wording was absent from both — and
  `git log -- web/public_prism/src/ --since=<deploy time>` showed zero commits, closing the
  divergence window. Marker sets are robust to env injection; hashes are not.
- **Verify a route from source, not from an HTTP status.** `App.tsx:51 resolvePath()`
  matches `^/solariun(?:/([^/]+))?$` and accepts the segment only when
  `SOLSPIRE_LENSES.has(candidate)`; `/solariun/opportunity-radar` is therefore a real lens
  route. Because `vercel.json` rewrites everything to `/index.html`, a 200 proves nothing —
  read the router. Marker `opportunity-radar` is present in the deployed bundle.
- **`ActivityRuntime` (SG-04) absence was real for its revision and is repaired in source.**
  The historical observation stands: `activity-runtime-draft.v1:` → 0 occurrences in the
  deployed asset while every SG-03 marker → 1; the SG-03 chamber rewrite had displaced the
  SG-04 mount. Repaired in **source** by PR #174 (merge `adf3df29…`), not by PR #185:
  `CapabilityChamber.tsx` imports and renders `ActivityRuntime` from `adf3df2` onward
  (`git show adf3df2:…/CapabilityChamber.tsx` → import + render present), restoring the mount
  the PR #166 squash (`47e4128`) had dropped. PR #185 (merge `52973d99…`) is **test-only** — it
  repairs the expanded-literal pin in `tests/test_spiral_grove_activity_runtime.py`, which is
  now **12 passed** (was 1F/11P at its head, 4F/8P before the source repair). Production parity
  still requires a post-#174 deployment — this is a repository-source claim only, not a
  production-parity claim. Do not reclassify the historical observation as stale.
- **HTTP 200 on any route is not application correctness.** Root `vercel.json` rewrites
  `/(.*)` → `/index.html`, so a route that never existed (e.g. `/api/health`, per
  `git log -S`) returns `200 text/html` identically to any nonexistent path. Prior
  route-reachability results must be read with this caveat.
- `web/public_prism/dist/` is **untracked** (`git ls-files web/public_prism/dist` → 0 paths;
  `web/public_prism/.gitignore` covers `dist/`). It *was* tracked historically — 41 commits
  touched it, the last deletion being `4366c55` (2026-10-01) — so the earlier "tracked but
  stale" wording is superseded by this measurement at `0c8a9f6`. A local build therefore leaves
  a clean tree; do not `git add` a build output, and revert a stray `dist/` modification if one
  appears on an older revision (it is not your change).
- **Gate-2 observation is now one read-only command — use it instead of repeating the manual
  sequence.** `python scripts/gate2_production_observation.py` (add `--json` for machine
  output). Stdlib-only, no Vercel credential, no mutation, never prints a token. It
  re-derives every link from live evidence and prints the boundary classification. Two
  trust properties: it **checks the marker list against source every run** (a literal gone
  from `web/public_prism/src/` is reported as `stale_list` rather than counting 0 and
  masquerading as a regression), and it **re-proves the ancestry closure** in §10.1 via live
  `git merge-base --is-ancestor`. Run it before making any Gate-2 claim.
- Evidence: `docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/`
  (PR #143).

  (PR #143; Pass 3 = §10, closure argument + harness).
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
- **Superseded fingerprints have an explained origin — they are not "unreproducible".**
  The pair `a59453b8…` (outcomes) / `9a35c812…` (ids) equals the recorded **20-node**
  baseline set **plus** its depth-dependent *sibling*
  `tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`.
  That node dereferences the `GATE2_PARENT_REV` read **unconditionally**, so without the
  PR-head revision `7d79f38…` it **errors** (`AttributeError`) rather than skipping — a bare
  clone's live 21-node run hashes to exactly that pair, while the recorded 20 nodes hash to
  the canonical `a578a766…` / `8036fc06…`. (`AGENTS.md` itself recorded `a59453b8…` as a
  21-node fingerprint — the earlier "not reproducible by any convention" verdict was a
  measurement gap, not a true UNKNOWN.) The pair stays **superseded** (clone-depth
  dependent), but its origin is now guarded by
  `tests/test_baseline_fingerprint.py::test_superseded_values_are_the_recorded_set_plus_its_sibling`
  and explained in `docs/control-plane/evidence/gate-hygiene-superseded-fingerprint-origin-01/`.
  The two excluded nodes' own assertion defects (both pin `7d79f38…` and mis-handle its
  absence) remain a **separate proposed workstream** — do not "fix" them inside a
  fingerprint workstream.

## Merge-loss forensics — a merge can invent a state present in neither parent
- A hand-resolved merge is not "one side or the other." `ff80b8c` took the inline
  work-surface from its **second** parent (`5c78fcb`) but the import line from its **first**
  (`cef5a59`), producing `CapabilityChamber.tsx` in a state that existed in *neither* parent:
  a dangling `import ActivityRuntime` (imported, never rendered), a dropped `useEffect`
  binding, and a dropped `surfaceMeta` anchor.
- **Diagnosis procedure that works:** compare the merge against **both** parents token by
  token (`git show <merge>^1:<p>`, `^2:<p>`, `<merge>:<p>`). Never compare against only the
  first parent — that is exactly the diff that hid the defect. A "hybrid" reading (some
  tokens from parent 1, some from parent 2) is the signature of an un-recompiled resolution.
- **Repair is mechanically determined when the loss is real:** if the repaired blob equals
  the merge's own discarded parent blob (`git diff <merge>^2 -- <p>` is empty), the change is
  *loss restoration*, not design. Say so — it removes the need for a design argument and
  bounds review. Prefer this over reconstructing intent by hand.
- **Do not attribute every failure near a merge to merge-loss.** In this case
  `test_chamber_preserves_sg03_downstream_boundary` was *not* merge-loss: the demanded
  literal (`...updates remain separate downstream stages.`) is absent in **every** revision
  including the coherent pre-merge one — the file contains two *near-miss* variants
  (`...mutation remain explicit downstream stages`,
  `...updates remain separate explicit downstream stages`). Check the literal against the
  coherent revision before blaming the merge; otherwise you build an unfalsifiable "repair
  didn't work" signal. `:110` was a test-side literal defect.
- **Prove no regression with the failing-node *set*, not the counts.** Counts vary by
  environment (this sandbox: 761 passed / 48 failed / 27 errors vs the contract baseline's
  804 / 54 / 2 collection errors — a dependency delta, not a regression). Normalise to the
  sorted `FAILED`/`ERROR` node list and compare `sha256`; the environment-independent claim
  is "no node-set delta," and it holds even when the absolute baseline does not match.

## Open-PR budget composition — measure the PR's *own* file, and correct stale citations
- When a branch is suspected of breaching the `api/main.py` 2600-line budget, measure
  **that branch's own blob**, not a commit on `main`. `git show <branch>:api/main.py | wc -l`
  (or the Contents API at `?ref=<branch>`) is the only correct source. A figure quoted for a
  PR can silently be a `main` commit: the Arkana Signal Gate 02 branch was recorded as 2719
  lines, but 2719 is `main` @ `71cbcb8` (the Gate 01 commit) — the live tip `2d0970a`
  measures **2894**. Re-measure before repeating a number.
- To test whether two open PRs compose, apply the other PR's patch onto this one and
  measure the composed file: `git worktree add --detach /tmp/wt <this-branch-sha>` then
  `git apply --3way` the other PR's `api/main.py` diff. A clean apply proves *no textual
  conflict*; it does **not** prove the composed tree passes the gate. Measured: this
  branch 2594 (PASS), branch + #293 = **2683** (FAIL). Report both facts separately.
- **A stale citation is a defect to correct, not to reconcile.** When a PR body or commit
  message carries a superseded measurement, fix it in place (evidence doc + PR body) and
  say which measurement supersedes it. Leaving it standing is what makes the next pass
  re-derive a number that was already wrong.
- **`git push` in this sandbox needs the `gh` credential helper explicitly.** The ambient
  env tokens are unusable (empty `GITHUB_TOKEN`, `GITHUB_PERSONAL_ACCESS_TOKEN` → 401), and
  the remote URL's embedded credential is stripped, so a bare `git push` blocks on an
  interactive username prompt. Configure once per clone:
  `git config credential.helper '!gh auth git-credential'` and push with
  `GIT_TERMINAL_PROMPT=0` so a missing credential fails fast instead of hanging. The ambient
  `gh` session is valid and has push rights; the env tokens are not a substitute.
- `Vercel – arkadia-prism` / `Vercel – console` are **failure on `main` itself** (measured at
  `4550531`), so a Vercel failure on any PR is not attributable to that PR. Classify it as
  pre-existing and say so, rather than reporting it as a new red gate.

## Contradicting PRs: resolve by measurement, not argument
- Two PRs asserting opposite designs for one file can both be **wrong about the conflict**.
  Here `main`, `#163` head, and `#165` head all resolved `CapabilityChamber.tsx` to the *same
  blob*; zero of the 23 open PRs modified it. Before adjudicating a "conflict," hash the
  revisions and query `GET /pulls/{n}/files` across all open PRs — there may be no conflict
  at all.
- Resolve the *design* question empirically: find which test files pin each variant, then
  build the competing variant faithfully and measure. A faithful "restore the mount" variant
  here moved failures 4 → 6 — it satisfied its own mount test while breaking the downstream-
  boundary and draft-persistence pins. The inline design is canonical.
- **A cited test that does not exist is a non-reproducible citation — record it, don't
  reconcile it.** `#165` pass 4 cited `test_spiral_grove_boundary_is_enforced`; `git grep`
  over its head tree, over `main`, and over its own evidence returned 0 matches. Treat such a
  fingerprint as untrusted until re-derived.
- Do **not** "fix" the competing PR's premise by widening scope. The four remaining SG-04
  failures are test-side defects; repairing them is a separate bounded workstream.

## Test-side literal pins are a recurring defect class in this repo
- Frontend/SG tests are source-level string assertions. Two failure modes recur:
  (1) the test demands an **expanded** literal while the source emits a **template** —
  e.g. test wants `data-testid="activity-surface-research"`, `ActivityRuntime.tsx` emits
  ``data-testid={`activity-surface-${kind}`}``; the property holds, the assertion does not
  match its own template. (2) the test demands a **near-miss** of the actual copy.
  When a source-level assertion fails, read the source literal before assuming a code bug.

## MIE MVP-01 — a green CI claim is scoped to the revision that produced it (gate-hygiene)
- `musical-intention-engine/BUILD-STATE.md` cited run `37007483734` (`a336ec30`) as "Kotlin unit
  tests: SUCCESS" while `MieMusicalInterpreterTest.kt` **did not exist** at that revision — it
  arrived four hours later in `bd98696`. The run was real; the conclusion was not transferable.
  A CI result is evidence about one tree. Check the test file is in the run's tree before
  promoting its conclusion onto the current one.
- The same document marked **Gate 02 "CI VERIFIED"** on a revision where the interpretation test
  could not compile, so no assertion had ever executed. A job that *runs* `testDebugUnitTest` is
  not evidence that any test *ran*: the MIE workflow compiles tests before `assembleDebug`, so a
  test-compilation failure reddens the job and suppresses the APK artifact too.
- **Test dependencies can be absent from a repository's entire history, not merely the tip.**
  `MieMusicalInterpreterTest.kt` imports `org.junit.*`, yet
  `grep -rn junit sonata-android --include=*.kts --include=*.toml --include=*.gradle` was empty
  and `git log --all -- sonata-android/gradle/libs.versions.toml` never contained JUnit. Prefer
  the history-wide query over a tip-only look before concluding "it used to work".
- **A copy-paste PR body is a real review hazard.** PR #214's description was byte-identical to
  PR #213's (`39153c6b…`, same md5). A reviewer opening #214 would have read a CP10 allowlist
  proposal against an Android diff and merged on the strength of the wrong evidence. When a PR
  body and its diff disagree, treat the body as unproven and rewrite it from the diff.

## Autocorrelation pitch detection — the subharmonic trap (MIE)
- Keeping the lag of the **global** correlation maximum reports a subharmonic, because a periodic
  signal correlates strongly at every multiple of its period. Measured on the MIE interpreter:
  440 Hz -> 146.8 Hz (`lag = 109` ~ 3 periods), 220 Hz -> 73.4 Hz, 880 Hz -> 80.0 Hz. 110 Hz
  passed only because its first peak was the sole in-range one — a passing case can hide the
  defect.
- The repair is to return the **first local maximum within `PEAK_RATIO` (0.85) of the global
  peak** — the smallest lag that nearly matches — plus parabolic sub-sample interpolation.
- This class of defect is invisible to a single-tone test. A regression suite needs a
  **negative control** (white noise must yield no pitch, not a spurious one) and a
  harmonic-rich case, or the "fix" can be tuned to the one frequency under test.


## Lazy schema materialization — a fixture that constructs a store has not created its schema (gate-hygiene)
- `EnterpriseOrchestrationStore()` does **not** create `data/*.db` or its tables; the
  constructor only resolves `_DB_PATH`. The schema is materialized lazily by the first
  store *operation* (`weaver/enterprise_orchestration.py::_db()` runs the
  `CREATE TABLE IF NOT EXISTS …` script). A test that only *constructs* the store and then
  probes a table with a raw `sqlite3.connect(db)` measures an **uninitialized database**,
  not the invariant it claims.
- Observed on `tests/test_upstream_causal_continuity_01.py::test_api_approval_does_not_create_enterprise_authorization`:
  `sqlite3.OperationalError: no such table: ew_authorizations`, raised before any boundary
  assertion. `os.path.exists(db)` was `False` right after `EnterpriseOrchestrationStore()`.
- **Repair is test-side and mechanical:** call `with ew._db(): pass` in the fixture so the
  schema exists before the probe; the probe then returns `0` and the assertion is real.
  Repaired in PR #228 (merge pending human authority).
- When a raw-SQL test fails on a missing table, read the fixture first: a store that was
  constructed but never *used* leaves no schema. Do not "fix" it by adding schema DDL to the
  production constructor — the lazy materialization is the intended design.
- Full-history vs shallow clone changes the *node set*: `test_agents_md_encoding_adjudication.py`
  adds `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` on a shallow clone
  (oracle-revision access), so its live fingerprint differs from the recorded
  `tests/fixtures/baseline_node_set.txt`. Attribute that delta to clone depth / PR #215, not
  to a regression. Measured at `162f574b`: main 20F/1306P (`a59453b8…`), branch 19F/1307P
  (`b45c0753…`) — a `-1/+0` node delta that is exactly the repaired node.

## Workflow trigger injection — `${{ }}` is substituted before the shell parses (gate-hygiene)
- `.github/workflows/gemini-agent-genesis.yml` (`weaver_evolution`) ran on `issue_comment` and
  interpolated `${{ github.event.comment.body || github.event.inputs.task }}` **inside a `run:`
  block**, under `permissions: contents: write`. GitHub expands `${{ }}` before bash parses the
  script, so any commenter posting a `/weaver` comment could append shell metacharacters and
  execute commands with a write token and `GEMINI_API_KEY` in the environment. This is the class
  **ADR-013 §1** closed for the runtime shell tool; it was still open at the CI boundary.
- **The observable symptom was an ordinary CI failure, which is why it went unnoticed.** The real
  trigger was the benign multi-line engineering glance (comment `5974892742` on PR #250). The
  interpolated multi-line glance became the script body and the step died at `exit 126`
  (`run 37164268026` / job `111323865208`) because `python3 weaver.py` named a file that is not in
  the repository — `git log --all -- weaver.py` shows only `9ab26fc` / `377cdb3` ("fix stale URLs,
  **archive legacy Python**"). A dead entrypoint was hiding a live injection.
- **Repair pattern, in order of importance:** (1) drop `contents: write` → `read` when the job only
  reads; (2) pass untrusted event text through `env:` and reference the variable *quoted* — never
  interpolate `github.event.*.{body,title}` into `run:`; (3) point the step at a real governed
  entrypoint. `python3 -m weaver.workbench recon` is the canonical one: read-only by default,
  cannot originate authority, and its state machine stops at `awaiting human authorization`.
  `weaver/__main__.py` and `weaver/cli.py` do **not** exist — do not invent an entrypoint.
- **The workflow also pushed directly to `main`** (`git add . && git commit && git push origin main`).
  Removed. A comment-triggered job must not carry a self-merge path; this is a repository-source
  claim, not a production observation.
- **Guard:** `tests/test_workflow_injection_boundary.py` (22 tests) is parametrized over **every**
  `.github/workflows/*.yml`, so a new workflow interpolating untrusted event text into `run:` fails
  CI rather than shipping. It carries a **negative control** (`test_detector_flags_the_vulnerable_form`)
  that feeds the detector the pre-fix line and asserts it is reported — the detector cannot be
  disarmed by rewriting the workflow without failing that control.
- Measured at `357fbd83` / rebased onto `73b65bac`: failure node-set sha256
  `762a38ae2f38b0025395e547a8627ce8e99f7d2599dfe0fe5c30b518e5b092ee` (24 nodes) on both sides —
  zero regression; the `+22 passed` is exactly the new file. Evidence:
  `docs/control-plane/evidence/security-gemini-agent-genesis-injection-01/`.
- **Baseline fingerprints for one SHA genuinely disagree across measurements.** At `357fbd83`,
  PR #254's body records `57453143…` (29 nodes) while this environment measures `762a38ae…`
  (24 nodes); `tests/fixtures/baseline_node_set.txt` records yet a third (18 nodes, with
  `test_upstream_causal_continuity_01` present and `test_solspire_project_instantiation_ui`
  absent). The clone is **not** shallow (`git rev-parse --is-shallow-repository` → false, 1983
  commits) and pyyaml is installed, so the delta is neither of the two documented causes. Do not
  treat a fingerprint mismatch with a PR body as a regression: re-measure the same tree locally,
  compare **node identity**, and state which measurement is yours.
- Independently verified PR #254 in this environment: its head fixes exactly
  `tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write`
  and introduces nothing new (23 nodes vs 24 on `main`). Its documented `+2` in
  `solspire/tools_github.py` is the `"code": "MUTATION_DISABLED"` refusal field.

## Baseline fingerprint — a recorded node set drifts, and `-rf` hides errors (gate-hygiene)
- `tests/fixtures/baseline_node_set.txt` recorded **18** nodes while a live full-suite run on
  `main` `1b7c089` reports **10**. Eight recorded entries had been repaired by later merges yet
  stayed in the fixture as debt, so the "canonical" fingerprint described debt that no longer
  existed. All 8 were verified passing in isolation (17 passed) before removal — the reduction
  is measurement-backed, not a clone-depth artifact. The era-correct set is retained as
  `tests/fixtures/superseded_baseline_node_set_18.txt` (it still hashes to the superseded pair
  `6c7bf821…`/`2bc35996…`), so the prior values stay reproducible rather than deleted.
- **The documented evidence command used `-rf`, which suppresses pytest's `ERROR` summary
  lines.** pytest's default is `-r fE`; `-rf` alone prints only `FAILED` lines, so a collection
  error is invisible to a line-based extractor. Same run, same tree: `-rf` -> **9** nodes
  (`7d1bf895…`), `-rEf` -> **10** nodes (`9a54f5b4…`). The subset fingerprint looked
  well-formed. `scripts/baseline_fingerprint.py::extract` now raises `ValueError` when the
  summary reports more failures/errors than the log carries `FAILED`/`ERROR` lines, and
  `summary_counts()` anchors on the trailing `in <n>s` duration (optional `(H:MM:SS)` suffix)
  so a synthetic fragment is not mistaken for a summary. Always run the full suite with
  `-rEf`; a fingerprint derived from `-rf` is a **subset**, not a baseline.
- **The load-bearing invariant is the failing/error node SET, not the counts.** Passed counts
  move with how many tests are present (`1414` on `main` vs `1419` with two new controls);
  only the sorted `FAILED`/`ERROR` node list is stable. Compare node identity, never totals.
- Two tests pin the guard so it cannot be disarmed by editing the workflow or the script
  without reddening CI: a **negative control** feeding the exact `-rf` shape (must raise) and a
  **positive control** (must parse). Canonical pair at `1b7c089`:
  `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` /
  `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f`.

## A green CI job can execute ZERO tests - read the step log, not the conclusion (gate-hygiene)
- `sg-02-fe-2-v.yml` step 21 (`CP10-B broader backend regression`, `python -m pytest tests/ -q`)
  is `continue-on-error: true`, so its step `outcome` is `failure`. Step 35
  (`Enforce CP10 executable gates`) tests it with `test '${{ steps.backend.outcome }}' = success`
  - but **`steps.<id>.outcome` is not available inside a `run:` block**; GitHub exposes it only
  to a step's `if:`. The CI log prints every one of those 16 assertions as the *literal string*
  `test 'success' = success`, because with `continue-on-error: true` the step's conclusion is
  `success` and the substitution is a constant. The enforcement step is **self-satisfying** and
  cannot fail for any outcome. A `run:`-block guard must read `steps.<id>.conclusion`, or the
  decision must move to an `if:`.
- **A collection error makes the suite exit 0 while running nothing.** `weaver/autonomy` is a
  *tracked package* (`__init__.py` + `guard.py` + `proposal_engine.py`, `__status__ = "disabled"`)
  and `weaver/autonomy.py` is a *tracked module* (91 lines) that actually defines
  `load_autonomy_config` / `validate_autonomy_config` / `run_scheduled_once`. `import weaver.autonomy`
  resolves to the **package**, so `tests/test_autonomy.py:2` raises
  `ImportError: cannot import name 'load_autonomy_config'`. Because this is not the first error,
  pytest **interrupts the whole session**: the CI log reads `Interrupted: 1 error during collection`
  and `1 skipped, 1 error in 2.96s`. A `passed|failed` grep over that log returns **0** - the full
  suite ran no tests, yet the job is green. This is the CE-01 module-vs-package collision reserved
  to the sovereign; do not "fix" it inside an unrelated workstream.
- **Consequence worth stating plainly:** `tests/architecture` is executed by exactly one workflow,
  `provider-routing.yml`, path-filtered to `weaver/**` / `providers/**` / two named test files / one
  doc. A commit touching only `api/main.py` runs the architecture suite **nowhere**, so the
  2600-line budget (`test_api_main_line_count_within_budget`, `main` @ `4550531` = **2805**) is a
  repository convention, not a gate. Add `--continue-on-collection-errors` before trusting any
  full-suite CI count.
- **The mutation boundary is a different story - it has teeth.** Step 32 runs
  `scripts/cp10_mutation_boundary_policy.py`, the same module the fitness tests prove, and
  `sg-02-fe-2-v.yml` lists that script and `tests/test_m02a_ci_gate_integrity.py` as trigger paths,
  so a PR that rewrites the boundary is judged by the boundary it rewrites. Verified on PR #295
  (head `fda0091`): 35/35 steps success including step 32, and the branch touches both trigger paths.
- **A frozen schema that nothing validates against is not a contract.** `schemas/arkana/signal/1.0/`
  was admitted to `LEGIT` but `grep -rn "arkana-signal.schema.json" tests/ scripts/ api/` returns 0
  producer/consumer references, so the merged ARK-01 route (`/api/arkana/signal/ingest`) emits
  `arkana.signal` objects that fail its own contract for ordinary model output - candidates without
  the required `status`, and `null` written into the `number`-only `interpretation.confidence` map
  (`$defs.candidate` allows `null` confidence, the top-level map does not). Pin the producer with a
  conformance test, including a negative control per violation, or the schema is decoration.


## A strict xfail is a serialization constraint, not a preference (gate-hygiene)
- `strict=True` records a defect a PR *expects* to be repaired — which means the repair is
  the exact event that turns the node into a **failure** (XPASS). Two open GATE-07 PRs
  (#329 = the guard with a strict xfail; #342 = the clean-stop repair that flips it) are
  each green alone and **cannot both merge in either order**. Measured in a worktree at
  `#329`'s tree with `#342`'s `weaver/` patch applied: `1 failed (strict XPASS), 5 passed`.
- A PR body's suite delta can be true and still blind to the conflict. `#342` reported
  `10 failed -> 9 failed` — correct **for `main` alone**, which counts the xfail as an
  *expected* failure the repair resolves. It cannot see a *strict* xfail on another branch.
  Before composing PRs, check whether any of them records the defect another one repairs.
- Reconciliation rule (decision record, not an implementation):
  `docs/control-plane/evidence/gate07-strict-xfail-composition-reconciliation-01/`. Merge
  order is `#329` (with a companion change re-materializing the xfail as a strict positive
  quiet-stop assertion) **then** `#342`, or one composed PR. The pre-repair literal is
  preserved verbatim in the guard so the node stays reconstructable.
- Guard: `tests/test_gate07_strict_xfail_composition_reconciliation.py` — a pure-source
  detector (imports no `weaver` module) with a negative control that feeds it the measured
  pre-repair pair and a positive control proving it is silent when the repair is absent.
  It fails on the composed tree and passes on `main`: a guard that is silent on both is not
  a guard.

## Gate-2 deployment window — an ordered, paginated endpoint makes a fixed window a false absence (gate-hygiene)
- `scripts/gate2_production_observation.py` read a **single fixed** `/deployments` window
  (`per_page=60`) and filtered it client-side to `environment == Production`. `/deployments` is
  ordered by **creation time across every environment**, so Preview traffic dominates: at `main`
  `24a00f85` the newest Production deploy sat at **index 71** — past the window — and the harness
  printed `main -> deployment identity := UNKNOWN` while main **was** deployed and sha-identical.
  The `UNKNOWN` read as *no deployment evidence*, which is exactly the dangerous direction for a
  boundary whose purpose is to detect a missing deployment. A standing hourly pulse must not
  report a false `UNKNOWN`/absent boundary when main is deployed.
- **Proof of the artifact, not the deployment:** same SHA, same token — pre-repair `UNKNOWN` /
  0 Production records; repaired `VERIFIED` / 4 records, newest `sha == main`. Slice check:
  first 60 unfiltered records -> 0 Production; first 100 -> 4. Newest Production record was at
  index 71 of the unfiltered list.
- **Repair:** bounded newest-first page walk (`DEPLOYMENT_SCAN_PAGES = 5`, <=500 records, never
  full history) that stops as soon as a Production record appears; plus a **window guard** — a
  window shorter than the scan ceiling carrying **no** Production record returns `[]`
  (unprovable absence -> `UNKNOWN`), never a `STALE` claim drawn from a truncated view.
  `production_deployments()` stays a `scan_ceiling=limit` wrapper so existing call sites hold.
- Generalise: **a fixed-size window over a time-ordered, paginated feed is not an absence
  oracle.** Either page until the predicate matches (bounded), or treat an exhausted window as
  unprovable. The negative control (`test_negative_control_truncated_window_hides_a_production_record`)
  feeds the pre-repair shape a window one record short and asserts it yields nothing, so the
  guard cannot be disarmed by narrowing the window.
- Regression: full-suite failing/error **node set** unchanged vs `main` `24a00f85` (133 vs 133,
  `comm -3` empty); the `+5 passed` is the new tests. Architecture 11/11. `api/main.py` untouched.
- PR #368 (branch `gate-hygiene/gate2-deployment-window-01`). Does **not** close the standing
  Gate-2 boundary — `deployment build output observed` stays `BLOCKED` on Vercel Deployment
  Protection (SSO); production parity remains **NOT CLAIMED**.

## Gate-2 deployment window vs marker oracle — two PRs, one file, independently necessary (gate-hygiene)
- Measured 2026-10-09 at main `24a00f85`. `scripts/gate2_production_observation.py` has **two**
  open bounded repairs touching it and its test, and **both are needed**: PR #368
  (`gate-hygiene/gate2-deployment-window-01`) and PR #366
  (`gate-hygiene/gate2-marker-oracle-soundness-01`).
- #368 is the *deployment-window* fix: `GET /deployments` is ordered by creation time across
  *every* environment, so a busy Preview cohort pushes the newest Production record off a single
  page and the harness reports `main -> deployment identity := UNKNOWN` while main **is** deployed
  (the absent state, not the real one). The fix **pages** the window
  (`per_page=100&page=N`, bounded by `DEPLOYMENT_SCAN_PAGES`) instead of trusting one page.
- #366 is the *marker-oracle* fix and does **not** paginate — it widens the fixed window with
  `per_page = max(args.limit * 5, 50)`, which is strictly weaker: a cohort can still exceed any
  fixed bound. #366 repairs a different soundness defect: the harness scored the **console**
  artifact against **Prism** literals after the root `vercel.json` was repointed at `404452e0`
  (2026-10-02), so every marker read 0 — which is "this is a different application", not
  "the artifact disagrees with the source". #366 also introduces `KNOWN_FRONTENDS`/`MARKER_APP`.
- **Textual conflict is real and measured, not assumed.** `git apply --3way` of #366's patch onto
  #368's head in a detached worktree yields `UU` on **both** files; the script has one conflicted
  region and the test two. The hunks are the adjacent constant blocks at `BUILD_INPUTS`
  (`DEPLOYMENT_SCAN_PAGES` vs `KNOWN_FRONTENDS`/`MARKER_APP`). Git conflict-free is not proof of
  semantic compatibility — and here it is not even conflict-free.
- **The ABSENT marker rows do not contradict the lineage summary.** The run prints e.g.
  `separate explicit downstream stages  0  (expect>0)  <-- ABSENT` for the deployed bundle, which
  reads as a Prism divergence. It is not: the alias manifest is `assets/index-*.js` while the
  Prism build emits `dist/assets/index-*.js`, so the harness **falls back** to `alias_bundle`
  (printed explicitly) — the Console artifact. The marker table measures the Console artifact;
  `SOURCE-LINEAGE CLOSURE` (ancestry-only) is independently `True`. The two are consistent. Do
  not read the ABSENT rows as a Prism regression, and do not "repair" them inside #368.
- A running harness can still *cite* a verification it never performs: `classify_source_lineage`
  returns the literal `"VERIFIED (marker set matches, source closed)"` while never receiving the
  marker comparison — the computed `match` is printed but fed to no classifier. PR #366 fixes
  this (its `classify_source_lineage` comment says claiming a match "from closure alone" is
  unsound) by splitting out `classify_marker_oracle`. Leave it to #366; do not duplicate it in
  #368 (would compound the conflict).
- **Merge order is the human sovereign's.** Recommended: **#366 first**, then **#368 rebased**
  onto it retaining both the page loop and `KNOWN_FRONTENDS`/`MARKER_APP`. Do not open a third
  competing PR on this file — compose into #368. Do not merge both unreconciled.
## Baseline-fingerprint guard is now executable — and its inputs are derived, not restated (gate-hygiene)
- `tests/test_baseline_fingerprint.py` pins `tests/fixtures/baseline_node_set.txt` to a
  published fingerprint; it does **not** measure live. Measured at `main` @ `24a00f85`:
  the live suite reports **17** failing/error nodes while the fixture holds **10**, and the
  guard passes on both. Its verdict is a function of the fixture and the four
  `FINGERPRINT_DOCS`, not of the repository's live debt. At that revision **no workflow ran
  it** either (`grep -rn baseline_fingerprint .github/workflows/` → 0), so even the narrower
  reconciliation held only when a human invoked it by hand — a guard no workflow executes is
  decoration. `.github/workflows/baseline-fingerprint.yml` is the executable surface.
- **A workflow's trigger filter must name every input the guard reads, not just the test
  file.** The first draft named the guard, the script and `tests/fixtures/**` — incomplete,
  because the guard also asserts that four published documents carry the canonical
  fingerprint (`FINGERPRINT_DOCS`). A commit editing `.bootstrap/01_STATE.md` would change
  what the guard asserts without executing the guard. The detector bit on that real
  defect before it bit on any synthetic one.
- `tests/test_baseline_fingerprint_ci_wiring.py` reads `FINGERPRINT_DOCS` from the guard's
  source **by AST** rather than restating the list. A second hand-maintained copy drifts,
  and a drifted copy makes the coverage assertion vacuous. Accepted consequence: adding an
  entry to `FINGERPRINT_DOCS` requires adding the same path to the workflow filter in the
  same change. Proven by a negative control that edits only the guard's list.
- The invariant is stated over **every** workflow that runs the guard (parametrized), not
  against this one file, so a second wiring is judged by the same rule and deleting this
  one cannot make the assertions vacuous. Five negative controls cover: workflow omitting
  its own file, a shallow checkout (`fetch-depth: 0` removed — the node set is
  clone-depth sensitive), a dropped fixture glob, a dropped published doc, and a
  guard-side-only input addition.
- **A new workflow adds passing nodes to the generic scanner suites by construction**
  (`test_ci_gate_trigger_coverage.py` +3, `test_ci_suite_collection_continuation.py` +1,
  `test_workflow_injection_boundary.py` +1), so the branch's `+14 passed` exceeds its own
  test file's 9. Measured by diffing `--collect-only` per file across both trees
  (1809 → 1823), not inferred from the count delta.
- Measured at `24a00f85`: full-suite node set **identical** on `main` and the branch —
  outcomes `26c2b4c7…`, ids `571e599f…` (17 nodes, 16F/1E) on both. Architecture suite is
  **11 passed** (the contract's "9/10" does not reproduce). Evidence:
  `docs/control-plane/evidence/gate10-baseline-fingerprint-ci-wiring-01/`.
- The **seven** pre-existing failures on live `main` were recorded, not repaired. Four are
  owned: the CP10 `deploy/` allowlist omission (PR #354, `deploy/n-atlas-server/` added by
  `e074a63b` / merged `a27c6c80` 2026-10-07) and the `n-atlas-developer-lab.yml` trigger
  filter (PR #355). Three are **unowned drift** and must not be "fixed" opportunistically:
  the Landing copy pin (`2b87e8ef`, 2026-10-04), and two `tests/test_engineering_lab_api.py`
  pins broken by the new `/api/lab/engineering/n-atlas/*` mutating endpoints (`72432353`)
  and by `require_auth` → `require_lab_auth` (`f96d5fd2`, PR #353). `api/lab_routes.py` is an
  authority surface in `LAYER_MAP.py` and carries the Lab mutation boundary, so repairing
  those two is an authority-boundary change — sovereign-only. Propose; do not execute.
- At the reconciliation commit `05e031a1` (2026-10-04) neither `deploy/n-atlas-server/Dockerfile`
  nor `.github/workflows/n-atlas-developer-lab.yml` existed (`git cat-file -e 05e031a1:<path>`
  → absent) and the CP10 `LEGIT` list had no `deploy` rule, so the seven-node delta is **drift
  after** the reconciliation, not debt it chose to ignore. A fixture-vs-live gap on `main` is
  therefore not automatically a stale fixture — date the surfaces before classifying it.

## Baseline-fingerprint guard: wiring is runtime-proven, scope is fixture-only (gate-hygiene)
- The wiring is no longer a source-level claim. At branch head `26aa0d9a` run **`37863051418`**
  (`event=pull_request`, `completed/success`) is the first execution of the guard under CI;
  before this branch `grep -rn baseline_fingerprint .github/workflows/` was **0 matches**, so
  the guard held only when a human invoked it by hand. All **7** check-runs on that commit are
  `completed/success`, and the PR is `MERGEABLE` / `CLEAN`.
- **Do not restate the scope overclaim this pass corrected.** The guard pins the *fixture* to
  hardcoded constants (`grep -nE "subprocess|pytest\.main|--collect"
  tests/test_baseline_fingerprint.py` → nothing); it does **not** measure live. Measured at
  `24a00f85`: live suite 17 failing/error nodes vs fixture 10, guard green on both trees. A green
  guard is therefore **not** evidence that the recorded set describes live debt — the
  live-measurement gap is a recorded, non-executed follow-on.
- The `+14 passed` a branch adding one workflow file carries is **not** a regression signal:
  three generic suites iterate `.github/workflows/*.yml` and gain passing nodes by construction
  (1809 → 1823). Compare the failing/error node **set**, never the totals.
- The `tests/test_engineering_lab_api.py` pins (2) and the Landing-copy pin are **unowned drift**,
  not fixture debt. Repairing the Lab ones edits `api/lab_routes.py` — an authority surface
  carrying the Lab mutation boundary — so it is sovereign-only and was proposed, not executed.



## The P1-A boot-syntax guard was real but executed by no gate (gate-hygiene)
- `tests/test_boot_syntax_boundary.py` (PR #297, `8d2d251a`) makes the P1-A guard
  continuous: `api/main.py` and every tracked Python file must `compile()`. Measured at
  `f9ced6b6`, `grep -rn test_boot_syntax .github/workflows/` returned **0** - it ran only
  when a human invoked the suite by hand. `api/main.py` is named by exactly one workflow
  path filter (`n-atlas-developer-lab.yml:12`, three named tests), and the CP10 workflow
  is filtered to `web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`
  and named test files, so a P1-A-shaped boot break runs the guard nowhere. This is the
  same "a guard no workflow executes is decoration" class already closed for
  `test_baseline_fingerprint.py` and `scripts/baseline_preflight.py`.
- **A wiring filter for a whole-corpus guard must select the corpus, not a file list.**
  The guard's domain is every tracked `.py` file (556 at `f9ced6b6`); a `paths:` list of
  a few files omits the tree where the next boot-broken module lands. Use `**/*.py` plus
  `*.py` (a leading `**/` also matches root). `tests/test_boot_syntax_ci_wiring.py`
  derives the domain from `git ls-files -- '*.py'` at test time rather than restating it,
  so a new module is judged by the same rule. Its glob is a real glob->regex translation
  (`**/` -> `(?:.*/)?`), not a segment-count match - a naive matcher both misses root
  files and passes incomplete filters.
- **The boot guard uses `compile()`, not `import`**, so its CI job needs no application
  dependency (only `pytest` + `pyyaml`): a dependency gap cannot be misreported as a boot
  break. Keep it that way when wiring similar syntax guards.
- Prove the wiring bites with a **live** negative control, not a synthetic one: replace
  `**/*.py` with `api/main.py` in the working tree and the coverage test must fail.
