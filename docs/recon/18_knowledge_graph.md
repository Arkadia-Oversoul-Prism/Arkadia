# 18 — Knowledge Graph

Relationship graph of major subsystems. `A USES B` means A depends on / calls / reads from B.

```
User (Web browser)
  USES  Prism Frontend (web/public_prism/)
    USES  ArkadiaNavigation (state-based View router)
    USES  AuthContext (Firebase Auth)
    USES  ArkanaCommune (chat UI)
      USES  /api/commune/resonance
      USES  Firestore conversationService (persistence)
      USES  localStorage (arkadia-commune-messages)
    USES  LivingGate (onboarding + reset + IMS booking + calibration)
      USES  /oracle-reset.mp3 (static asset)
      USES  /api/ims/inquiry (booking)
    USES  NexusPage
      USES  IMSArchiveSection --> /static/ims/*.html (backend-served)
      USES  EncyclopediaGalacticaMatrix --> /ims/*.html (frontend-public-served)
      USES  NexusSpiralCodex --> /api/codex
      USES  AISUniversity, LivingLarder
    USES  IMSArchivePage (standalone) --> IMSArchiveSection ONLY (incomplete vs NexusPage)
    USES  ShereSanctuary --> duplicate IMS archive list
    USES  Dashboard/* pages --> React Query --> /api/jobs, /api/goals, /api/metrics, /api/job/{id}/trace, /api/tools

User (Discord)
  USES  bot/discord-bot.mjs
    USES  /api/commune/resonance
    USES  [fallback] Gemini SDK directly (bypasses backend entirely)

User (Telegram)
  USES  bot/telegram-bot.mjs
    USES  /api/commune/resonance
    USES  /api/job/create (if TELEGRAM_ASYNC_JOBS=true)
    USES  [fallback] Gemini SDK directly

User (WhatsApp)
  USES  openclaw/gateway.js
    USES  (unconfirmed backend endpoint — flagged uncertain)

api/main.py (FastAPI entrypoint)
  USES  api/auth.py (Firebase Admin SDK / dev-mode fallback)
  USES  corpus/manager.py
    USES  corpus/github.py, corpus/gdrive.py, corpus/joplin.py, corpus/obsidian.py
    USES  docs/CORPUS_MANIFEST.json (label/category overrides)
  USES  kernel/* (worker lifecycle, jobs, goals, tools)
    USES  kernel/oracle_store.py --> data/oracle_store.json
    USES  kernel/jobs.py --> data/job_store.json --> [mirrored to] Firestore (jobs)
    USES  kernel/goals.py --> data/goal_store.json --> [mirrored to] Firestore (goals)
    USES  kernel/planner.py --> Gemini API (Phase 7)
      FALLS BACK TO  kernel/execution.py:classify_input (regex, Phase 4)
    USES  kernel/tools.py (registry) + kernel/tools_real.py (shell/file/image tools)
    USES  kernel/memory.py --> data/oracle_store.json (keyword-match context)
  USES  api/arkadia_engine.py (deterministic verse/compress/expand)
  USES  api/nodes.py --> data/nodes_seed.json
  USES  api/ims_products.py --> Gemini API (archetypal analysis) + Paystack (purchase)
  USES  api/pulse.py --> Gemini API (Likert diagnostic summary)
  USES  api/distribution.py (music release flow)
  USES  solspire/console_router.py
    USES  solspire/project_store.py --> data/solspire_projects.db (SQLite)
    USES  solspire/llm.py --> Gemini API
  MOUNTS  /static --> static/ims/*.html (real IMS deliverables)

weaver/ (autonomy layer — separate from kernel/)
  USES  weaver/echofield/vector_stack.py + retrieval.py (6-axis symbolic vectors, cosine similarity)
  USES  weaver/llm.py --> Gemini API
  READS  governance/*.json (manifest, permissions, roles, boundaries, autonomy, vows.md)
  WRITES  weaver/notes/*.txt (runtime autonomy step logs)

Unconfirmed-caller subsystems (no traced edge into the graph above):
  engine/task_engine.py
  parsers/intent_parser.py + schemas/intent_schema.py
  arkana_rasa/ (Rasa NLU)
  sanctum/status.py
```

## Key Structural Observations from the Graph
- **Three independent Gemini call graphs** exist that never intersect at runtime: (1) `api/main.py` + `kernel/planner.py` + `api/ims_products.py` + `api/pulse.py` (main product), (2) `weaver/llm.py` (autonomy loop), (3) `solspire/llm.py` (project console). All three could theoretically be unified behind one Gemini client wrapper but currently are not.
- **`kernel/` and `weaver/` are structurally siblings, not parent/child** — despite similar-sounding "memory"/"vector" language, they do not share code or data.
- **The frontend has three separate paths into IMS content** (`NexusPage`, `IMSArchivePage`, `ShereSanctuary`), each independently constructing its own file list rather than importing a shared one — this is the graph-level root cause of the redundancy flagged in section 15.
