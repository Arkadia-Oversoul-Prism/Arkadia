# Arkadia Voice — Architecture Discovery (GATE 0)

**Status:** IMPLEMENTED discovery — recorded before any Voice code was written.
**Repository:** `Arkadia-Oversoul-Prism/Arkadia` @ `17e626c` (main)
**Method:** files inspected, run, and executed. No capability is claimed here on the
basis of a filename; every "canonical" claim below was verified by reading the
implementation or running an existing test.

---

## 1. Discovered substrate

| Concern | Canonical implementation | Evidence |
|---|---|---|
| Backend | FastAPI composition root `api/main.py` (2434 lines, budget 2600) | `wc -l api/main.py`; routers mounted via `app.include_router` |
| Frontend | `web/public_prism/` React + Vite + TS + Tailwind + framer-motion | `AGENTS.md` line 8: "Frontend: `web/public_prism/`"; build command line 35 |
| Secondary console | `web/console/` derived read-only operator console (root `vercel.json` builds it) | `web/console/src/api/client.ts` ("This console reads… no POST/PATCH/PUT/DELETE") |
| API namespace (governance) | `/solspire/*` — all mounted from `solspire/console_router.py` (`prefix="/solspire"`) | `solspire/console_router.py:50-65` |
| Database | SQLite: canonical SolSpire store `data/solspire_projects.db` (`SOLSPIRE_PROJECTS_DB`), Knowledge OS `knowledge/arkadia.db` | `solspire/*_manager.py` module `_DB_PATH`; `conftest.py` sandbox fixtures |
| Auth | `api/auth.py::require_auth` — Firebase ID token in production; unsigned-JWT **dev-mode only** when `FIREBASE_SERVICE_ACCOUNT_JSON` absent and `ENVIRONMENT != production` | `api/auth.py:31-91, 395-401` |
| Identity / role | `api/auth.py::build_user_profile` → `role`, `access_level` from node registry via Firebase `node_key` claim | `api/auth.py:311-356` |
| Workspace / session | `solspire/workspace_manager.py` — one canonical workspace per subject; `GET /solspire/workspace` = idempotent `get_or_create` | `solspire/console_router.py:345-367` |
| Proposal | `solspire/proposal_manager.py` + `solspire/proposal_router.py` (`/solspire/proposals`) — statuses `PRESENTED → UNDER_REVIEW → ACCEPTED/DECLINED/WITHDRAWN` | `proposal_manager.py:235-330, 481-514`; `proposal_router.py:36-199` |
| Human decision (approval) | `POST /solspire/proposals/{id}/decision` — "Human decision only. ACCEPTED does not authorize execution." | `proposal_router.py:130-157` |
| Authority / authorization | `solspire/console_authority_router.py` (`/solspire/authority`) — proposal must be `ACCEPTED`; requires Flamekeeper role or `access_level ≥ 3`; materializes ARK-WEAVER-01 proposal → `EdenOps.decide_proposal(APPROVE)` → `HumanAuthorityEvent` + `Authorization`, bound back via `bind_authorization` | `console_authority_router.py:70-155` |
| Execution (governed) | `POST /solspire/authority/authorizations/{id}/execute` → `EnterpriseOrchestrationStore.execution_attempt` + `WeaverConsoleAdapter.dispatch` (read-only tool envelope) | `console_authority_router.py:157-210`; `weaver/console_adapter.py` |
| Execution (project workflow) | `solspire/execution_runtime.py::ExecutionRuntime` — plan lifecycle, `project_create` / `fs_*` / `github_*` tools, **blocks** engineering-mutation tools, owner-scoped | `execution_runtime.py:99-145, 223-286` |
| Work event spine | `solspire/workevent_manager.py` + `POST /solspire/workevents` — append-only continuity records with `execution_attempt_ref`, `artifact_refs`, `decision_ref` | `workevent_manager.py:21-60, 119-167` |
| Evidence + verification | `weaver/enterprise_orchestration.py` — `evidence()` and `verify()` are **separate** acts; `POST /solspire/authority/executions/{id}/evidence`, `POST /solspire/authority/verification` | `console_authority_router.py:212-267` |
| Tool-level approval gate | `api/approval_routes.py` — Govern authority (`Flamekeeper` or `access_level ≥ 3`); "approve records a decision; it does **not** execute the tool" | `approval_routes.py:1-90` |
| Existing voice boundary (Lab, EL-07) | `lab/engineering_lab/voice.py` + `GET/POST /api/lab/engineering/voice[/resolve]` — provider-neutral *text-transcript* boundary, `recognizer_state = UNCONFIGURED`, human-only intents refused | `voice.py:1-46, 174-204`; `api/lab_routes.py:375-391` |
| Intent classification (canonical) | `solspire/intent_router.py::IntentRouter` → 7 `IntentType`s (rule-first, LLM fallback) | `intent_router.py:24-99` |
| Knowledge / context retrieval | `knowledge/search.py` (`fulltext_search`, `people_search`, `project_search`, …), `knowledge/pipeline.py::ingest` | `knowledge/search.py:33-300` |
| Projects | `solspire/project_manager.py` (`create`, `list_projects`) — also reachable as an `ExecutionRuntime` step tool `project_create` | `project_manager.py:82-100`; `execution_runtime.py:270-274` |
| Tests | pytest, root `conftest.py` sandboxes every `solspire_projects.db` module constant at session scope | `conftest.py:56-93` |

### Existing route inventory relevant to Voice

```
/solspire                     (console_router — projects, workspace, executions, tools, status)
/solspire/proposals           POST/GET, /{id}/feedback, /{id}/decision, /{id}/prepare-execution
/solspire/workevents          POST/GET, /{id}
/solspire/workloads, /solspire/pulses, /solspire/syntheses
/solspire/authority/proposals/{id}/authorize
/solspire/authority/authorizations/{id}/execute
/solspire/authority/executions/{id}/evidence
/solspire/authority/captures, /solspire/authority/verification
/api/approvals                tool-run approval gate (decision ≠ execution)
/api/lab/engineering/voice    EL-07 transcript boundary (recognizer UNCONFIGURED)
```

### Existing data structures reused

- `Workspace` (subject binding), `Proposal` (+ `proposal_status`, `decision_ref`,
  `authorization_ref`, `feedback_refs`), `ProposalFeedback`, `ExecutionPreparation`
- `WorkEvent` (event_type, execution_attempt_ref, artifact_refs, state_before/after_ref,
  decision_ref, status ∈ {PROPOSED, OBSERVED, RECORDED, VERIFIED, …})
- Enterprise `Proposal` / `HumanAuthorityEvent` / `Authorization` / `ExecutionAttempt` /
  `Evidence` / `Verification` (`weaver/enterprise_orchestration.py`)
- `ExecutionRuntime.Plan` / `Execution` (status lifecycle, owner_uid)

---

## 2. Reused components (no duplicates created)

1. **Identity/auth** — `api.auth.require_auth` on every Voice route. No new auth path.
2. **Workspace/session** — `workspace_manager.get_or_create/get_for_subject`.
3. **Proposal ledger** — `proposal_manager.create_proposal / record_decision / bind_authorization`
   reached through the existing `/solspire/proposals` routes.
4. **Authorization** — the existing `console_authority_router.authorize_proposal`
   (govern-authority enforced). Voice does **not** mint authority.
5. **Execution** — `execution_runtime.ExecutionRuntime` (project-workflow executor) and,
   for read-only governed tools, `WeaverConsoleAdapter` through the existing
   `/solspire/authority/authorizations/{id}/execute` route. Voice creates **no second executor**.
6. **Work events** — `workevent_manager.create`.
7. **Evidence + verification** — `EnterpriseOrchestrationStore.evidence / verify`.
8. **Intent typing** — `solspire.intent_router.IntentRouter` for the canonical `IntentType`;
   Voice adds only its own bounded *action* vocabulary (ASK/SEARCH/CREATE/MODIFY/EXECUTE),
   which the canonical router does not model.
9. **Context retrieval** — `knowledge.search` (read-only) and `solspire.project_manager`.
10. **Engineering Lab voice boundary** — `lab/engineering_lab/voice.py` remains the
    canonical *Lab command* boundary (human-only intents). Arkadia Voice maps onto it
    rather than replacing it: human-only operations (merge/deploy) are refused by the
    same policy and never dispatched.

## 3. Integration points chosen

```
web/public_prism  route /solspire/voice  (page namespace already owned by this SPA)
        │  API_BASE (apiConfig.ts)
        ▼
/solspire/voice/*   ← NEW voice_router.py, mounted by solspire/console_router.py
        │
        ├── solspire/voice_contracts.py   canonical VoiceEvent/Transcript/Intent/Context/…
        ├── solspire/voice_asr.py         ASRProvider registry (Test/Local/NAtlas/Cloud)
        ├── solspire/voice_intent.py      bounded deterministic action parser
        ├── solspire/voice_context.py     entity resolution → KNOWN/AMBIGUOUS/UNKNOWN
        ├── solspire/voice_store.py       SQLite persistence in data/solspire_projects.db
        └── solspire/voice_pipeline.py    orchestration across EXISTING primitives:
              workspace → VoiceEvent(audio hash) → Transcript → Intent → Context
              → ProposalManager.create_proposal → record_decision (human approval)
              → console_authority_router.authorize_proposal → ExecutionRuntime
              → EnterpriseOrchestrationStore.evidence → workevent_manager.create
              → EnterpriseOrchestrationStore.verify (separate human act)
```

Storage: voice tables live in the canonical SolSpire store
(`data/solspire_projects.db`, gitignored, `*.db` ignored) so the existing
`conftest.py` session sandbox covers them automatically.

## 4. Files intentionally not modified

- `api/main.py` — at line budget; Voice is mounted through `solspire/console_router.py`.
- `api/auth.py`, `api/approval_routes.py`, `solspire/proposal_manager.py`,
  `solspire/console_authority_router.py`, `solspire/workevent_manager.py`,
  `solspire/execution_runtime.py`, `weaver/*` — reused as-is; no governance change.
- `lab/engineering_lab/voice.py` — remains the Lab's canonical transcript boundary.
- `web/console/` — read-only derived console; the Voice surface needs governed
  mutations, which that console deliberately does not expose.
- `.env*` files, deployment configs, `vite.config.*` — untouched.
- `tests/architecture/*` fitness tests — untouched.

## 5. Unresolved assumptions (explicit)

1. **N-ATLAS access**: no endpoint, credential, or mention of N-ATLAS exists anywhere in
   the repository (`rg -i "n-atlas|natlas"` → 0 hits). The N-ATLAS adapter is therefore
   configured-from-environment only and reports `UNAVAILABLE / OFFICIAL_ACCESS_NOT_CONFIGURED`
   until official access exists. No endpoint is fabricated.
2. **Real ASR in this environment**: no ASR library (whisper/vosk/speech_recognition) is
   installed and none is declared in `requirements.txt`. `LocalProvider` probes for an
   installed local engine and reports `UNAVAILABLE` when absent (no huge dependency stack
   added). A real cloud ASR path exists through the repository's already-approved Gemini
   provider (`google-generativeai` is declared) — it activates only when
   `GEMINI_API_KEY`/`GOOGLE_API_KEY` is present, and is `UNAVAILABLE` otherwise.
3. **Production auth**: dev-mode unsigned JWT is a pre-existing substrate behaviour. The
   Voice routes use `require_auth` exactly like every other SolSpire route; no new
   development-auth fallback was introduced. Production still requires
   `FIREBASE_SERVICE_ACCOUNT_JSON` (fail-fast, unchanged).
4. **Governance order**: the mission's §8 order lists AUTHORIZATION before PROPOSAL;
   the repository's canonical chain requires a proposal to be `ACCEPTED` *before*
   authorization (`console_authority_router.py:87`). The repository wins; the effective
   order is IDENTITY → AUTHORITY → PROPOSAL → APPROVAL → AUTHORIZATION → EXECUTION →
   WORK_EVENT → EVIDENCE → VERIFICATION → REVIEW.
5. **Which executor runs a voice action**: read-only governed tools go through Weaver
   (read-only envelope); project-workflow actions go through `ExecutionRuntime`
   (its own engineering-mutation refusal still applies). Which channel a voice action
   uses is recorded explicitly in the evidence chain.
