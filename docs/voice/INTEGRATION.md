# Arkadia Voice — Integration Guide

**Status:** IMPLEMENTED. How Arkadia Voice plugs into the canonical substrate
without creating parallel systems.

---

## 1. Backend mounting

`solspire/console_router.py` (mounted by `api/main.py` at `prefix=/solspire`):

```python
from solspire import voice_router
router.include_router(voice_router)   # prefix=/voice → /solspire/voice/*
```

- Every route inherits the router-level `Depends(require_auth)` — Firebase ID
  token in production, dev unsigned JWT only when
  `FIREBASE_SERVICE_ACCOUNT_JSON` is absent and `ENVIRONMENT != production`.
- No new database: `VoiceStore` opens `data/solspire_projects.db`
  (`SOLSPIRE_PROJECTS_DB`), the same store as proposals, work events and
  projects. `conftest.py`'s session sandbox (`_DB_PATH`) covers voice tests
  automatically because the store reads the module attribute.
- `api/main.py` line budget respected (untouched — routes are added via the
  console router, not the composition root).

## 2. Files modified (additive only)

| File | Change | Why |
|---|---|---|
| `solspire/console_router.py` | `include_router(voice_router)` | mount point |
| `solspire/console_authority_router.py` | route body extracted into `authorize_proposal_sync(proposal_id, body, user)`; async route now delegates | voice must reuse the exact govern-authority path; HTTP paths and behavior unchanged |
| `solspire/execution_runtime.py` | new `case "project_update":` tool in `_execute_step` | voice MODIFY maps to the same field-write path as `PUT /solspire/projects/{id}` (`project_manager.apply_fields`); blocks nothing, adds one tool |

No existing route, schema, contract or test was altered.

## 3. New backend files

```
solspire/voice_contracts.py    solspire/voice_asr.py      solspire/voice_intent.py
solspire/voice_context.py      solspire/voice_store.py    solspire/voice_pipeline.py
solspire/voice_router.py
```

## 4. Subsystems reused (call points)

- **Workspace** — `workspace_manager.get_or_create(subject)` before the first
  event of a session.
- **Intent routing** — `IntentRouter().classify()` for
  `canonical_intent_type`; bounded voice rules on top, never replacing it.
- **Knowledge/people** — `knowledge.search.fulltext_search` / `people_search`
  for context resolution, always user-scoped.
- **Proposals** — `proposal_manager.create_proposal` / `record_decision`;
  voice events only store the `proposal_id` pointer.
- **Authorization** — `console_authority_router.authorize_proposal_sync`
  (HAE + Authorization + ARK-WEAVER-01, `bind_authorization`).
- **Execution** — `ExecutionRuntime.execute` with owner-scoped plans;
  engineering-mutation tools remain blocked (`_ENGINEERING_MUTATION_TOOLS`).
- **Work events** — references the orchestration-created WorkEvent for
  authorized executions (`work_events.execution_attempt_ref` UNIQUE); creates
  its own WorkEvent for observations.
- **Evidence/verification** — `EnterpriseOrchestrationStore.evidence/verify`.
- **Lab boundary** — `lab.engineering_lab.contracts.HUMAN_ONLY` phrase set
  reused for the human-only refusal (EL-07 policy, not replaced).

## 5. Frontend integration (`web/public_prism`)

- New page: `src/pages/SolspireVoice.tsx`.
- Route: `App.tsx` — `View` union + `routeForView` (`voice → /solspire/voice`)
  + `resolvePath` (`/solspire/voice` exact match, before `/solspire`) +
  render branch wrapped in `ExperienceConsolidationFrame surface="SolSpire"`
  (same pattern as the SolSpire console).
- Navigation: `ArkadiaNavigation.tsx` (`View` union, `VIEW_LABEL`, Workspaces
  drawer entry) and `PrismInteriorShell.tsx` (`activeSurfaceFor('voice') →
  solspire`, `solariunSurface` includes `voice` so the authenticated identity
  bar + surface rail render; `SECONDARY` gains "Voice Console").
- Transport: existing `apiClient` (`apiFetch`/`apiRequest`) — Bearer token is
  set centrally by `AuthContext.setApiAuthToken(idToken)`; the page also
  mirrors the `useLayoutEffect(setApiAuthToken)` pattern used by
  `EnterpriseConsole`/`SolariunConsole`.
- Auth: unauthenticated visitors get the existing `.solspire-auth-threshold`
  card whose button enters the established sign-in flow (`gate`), matching
  `SolariunConsole`'s threshold pattern.
- No `vite.config.*` change (HMR/proxy untouched). In dev, `/solspire/*` calls
  follow the same precedent as every existing solariunApi/WorkspaceAction
  surface.

## 6. Environment keys (names only; never committed)

| Key | Purpose |
|---|---|
| `ARKADIA_VOICE_ASR_PROVIDER` | optional pin; fails loudly when unavailable |
| `NATLAS_TRANSCRIBE_URL` / `NATLAS_API_KEY` / `NATLAS_MODEL` | N-ATLAS official access |
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | cloud provider |

None are set in this workspace; providers report truthful UNAVAILABLE states.

## 7. Running

- Backend tests: `python3 -m pytest tests/test_voice_*.py` (118 tests).
- End-to-end: `python3 scripts/voice_smoke.py` (36 checks, no env reads).
- Frontend: `cd web/public_prism && pnpm install --frozen-lockfile && pnpm run build`.
- API console: open `/docs` (FastAPI) → "Arkadia Voice" tag.
