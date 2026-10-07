# ARKADIA VOICE — BUILD REPORT (GATE 0–12)

**Mission:** voice-first control surface: speech → canonical VoiceEvent → ASR
transcript → bounded intent → context → authority → proposal → human approval →
execution via existing substrate → work event → evidence → verification.

**Verdict: ALL GATES PASS.** Every gate below was verified by a command run in
this workspace; commands and evidence paths are listed per gate.

Reproduction commands:

```bash
python3 -m pytest tests/test_voice_contracts.py tests/test_voice_asr.py \
  tests/test_voice_intent.py tests/test_voice_context.py \
  tests/test_voice_pipeline.py tests/test_voice_api.py -q   # 118 passed
python3 scripts/voice_smoke.py                              # SMOKE PASSED: all checks green (36 checks)
cd web/public_prism && pnpm install --frozen-lockfile && pnpm run build   # ✓ 3447 modules
```

---

## GATE 0 — Architecture discovery

**Scope:** recon of the canonical substrate before any Voice code; no capability
claimed from a filename.

**Result:** PASS.

- Discovered and read: FastAPI `api/main.py`, `solspire/console_router.py`
  (`prefix=/solspire`), `api.auth.require_auth`, proposal/authority/workevent/
  execution-runtime/enterprise-orchestration chains, canonical frontend
  `web/public_prism`, store `data/solspire_projects.db` + `conftest.py` sandbox.
- Corrected the AUTHORIZATION-before-PROPOSAL ordering to the repository's
  canonical chain: proposal → decision → authorization → execution.
- N-ATLAS absence proven: `rg -i "n-atlas|natlas"` → 0 hits pre-implementation.

**Evidence:** `docs/voice/ARCHITECTURE_DISCOVERY.md`

## GATE 1 — Canonical contracts

**Scope:** single source of truth for stages, actions, risk, error states,
digests.

**Result:** PASS.

- `solspire/voice_contracts.py`: `VoiceStage`/`STAGE_ORDER`, `VoiceAction`,
  `RISK_LEVELS`, all **16** `VOICE_ERROR_STATES` (each with recovery + stage),
  event/transcript/intent/context/proposal/execution/chain types,
  `hash_audio` (sha256), `canonical_digest`, `chain_digest`, `new_id`.

**Evidence:** `tests/test_voice_contracts.py` (pass), `docs/voice/ARCHITECTURE.md` §2–4

## GATE 2 — ASR provider boundary

**Scope:** replaceable ASR (Test/Local/N-ATLAS/Cloud); env-config only; loud
failures, never silent substitution.

**Result:** PASS.

- `solspire/voice_asr.py`: provider protocol, `ProviderInfo` truthfulness
  fields, selection (`explicit/env pin` fails with `ASR_UNAVAILABLE` 503 when
  unavailable; default priority `natlas→cloud→local→test` falls through),
  `provider_status_report()` leaks configuration names only.
- N-ATLAS: `NATLAS_TRANSCRIBE_URL`/`NATLAS_API_KEY`/`NATLAS_MODEL` only →
  otherwise `UNAVAILABLE · OFFICIAL_ACCESS_NOT_CONFIGURED`. No fabricated URL.
  This workspace has no env keys (`freebuff-env list` empty) → truthful
  unavailable states.

**Evidence:** `tests/test_voice_asr.py` (pass), smoke negative `ASR_UNAVAILABLE — status=503`,
`docs/voice/ASR_PROVIDERS.md`

## GATE 3 — Bounded intent

**Scope:** transcript → bounded action + entities; human-only operations
refused at the voice boundary.

**Result:** PASS.

- `solspire/voice_intent.py`: rule parser (ASK/SEARCH/CREATE/MODIFY/EXECUTE/
  UNKNOWN), human-only phrases checked **first** → `UNKNOWN` +
  `requested_effect=REFUSED_HUMAN_ONLY`, confidence = rule coverage, canonical
  `IntentRouter().classify()` reused for `canonical_intent_type`
  (`HUMAN_ONLY` from `lab.engineering_lab.contracts`).

**Evidence:** `tests/test_voice_intent.py` (pass)

## GATE 4 — Context resolution

**Scope:** resolve referents with ownership checks; ambiguity surfaced, never
guessed.

**Result:** PASS.

- `solspire/voice_context.py`: `KNOWN/AMBIGUOUS/UNKNOWN/UNAUTHORIZED` over
  projects (ownership → UNAUTHORIZED), knowledge/people (user-scoped),
  CREATE collision → AMBIGUOUS, transfer resolution, disambiguation fields
  name/target/query/path/recipient.

**Evidence:** `tests/test_voice_context.py` (pass)

## GATE 5 — Persistence

**Scope:** canonical store, append-only evidence chain, test sandboxing.

**Result:** PASS.

- `solspire/voice_store.py`: `voice_events` (chain-linkage columns
  `proposal_id → approval_ref → authorization_ref → execution_id →
  work_event_id → evidence_ref → verification_ref` + `audio_bytes BLOB`) and
  `voice_chain` (`seq/prev_record_id/payload_digest`), both on
  `data/solspire_projects.db` via module `_DB_PATH` so `conftest.py`
  sandboxes voice tests; `_UPDATABLE` whitelist for updates.

**Evidence:** `tests/test_voice_pipeline.py`, `tests/test_voice_api.py` (pass),
GATE 12 regression parity

## GATE 6 — Capture → transcript

**Scope:** audio reaches the backend, is bounded, hashed, transcribed;
negatives persist.

**Result:** PASS.

- `ingest`: ≤ `MAX_AUDIO_BYTES` (5 MiB, else `AUDIO_CAPTURE_FAILED`), workspace
  `get_or_create`, event insert (`RECEIVED`) + `VOICE_EVENT` stage, provider
  selection, `TRANSCRIPT` stage, empty → persisted `TRANSCRIPT_EMPTY`,
  success → `TRANSCRIBED`.
- Audio roundtrip: `GET /events/{id}/audio` returns bytes with
  `X-Arkadia-Audio-SHA256` matching the stored sha256.

**Evidence:** smoke checks (ingest + hash + audio roundtrip; empty-transcript
422 with ERROR stage), `tests/test_voice_api.py` (pass)

## GATE 7 — Understanding

**Scope:** intent → context → authority stages with explicit derived state and
clarification path.

**Result:** PASS.

- `understand`: `INTENT/CONTEXT/AUTHORITY` stages, `CLARIFICATION` stage on
  re-understand with disambiguations, status
  `UNDERSTOOD|CLARIFICATION_REQUIRED`, derived error dict for the UI
  (`AUTHORITY_MISSING` human-only, `INTENT_UNKNOWN`, `CONTEXT_AMBIGUOUS`,
  `CONTEXT_UNKNOWN`, `AUTHORIZATION_DENIED`) with recovery copy.

**Evidence:** `tests/test_voice_pipeline.py` (pass), smoke understand checks

## GATE 8 — Proposal → human decision

**Scope:** explicit proposal for consequential actions; observation-only has no
approval; human controls APPROVE / REJECT / EDIT.

**Result:** PASS.

- `propose`: refuses human-only/unknown/unauthorized/ambiguous/unresolved;
  observation-only (ASK/SEARCH) → `proposal=None` + Engineering-Lab READ note;
  otherwise `create_proposal` with scope JSON (executor plan, risk, transcript)
  → `PROPOSED`; `NO_CANONICAL_EXECUTOR` warning when unmapped.
- `decide` → `APPROVED|REJECTED` + approval stage ("a human decision is not
  authorization"); `revise` → WITHDRAWN + superseding proposal.
- Smoke: **blocked without approval** (negative, persisted).

**Evidence:** `tests/test_voice_pipeline.py` (pass), smoke negative check

## GATE 9 — Authorization (govern authority)

**Scope:** reuse the canonical authorization path; ACCEPTED ≠ AUTHORIZED.

**Result:** PASS.

- `solspire/console_authority_router.py` refactored: route body extracted to
  `authorize_proposal_sync(...)`; the async route delegates (paths/behavior
  unchanged). Voice `authorize()` calls the same function: govern authority
  (Flamekeeper / `access_level ≥ 3`), proposal must be `ACCEPTED`, HAE +
  `Authorization` bound via `bind_authorization`, scope carries executor tools
  + `voice.pipeline`.
- Error mapping: 403 → `AUTHORIZATION_DENIED`, 409 → `APPROVAL_REQUIRED`,
  404 → `PROPOSAL_REQUIRED`.

**Evidence:** smoke: **blocked without authorization**, **403 for non-govern
subject**, then successful authorize; `tests/test_voice_api.py` (pass)

## GATE 10 — Execution → work event → evidence → verification

**Scope:** execute via canonical substrate; reference the canonical WorkEvent;
evidence and verification as separate acts.

**Result:** PASS.

- `execute`: guards (intent/context/human-only), `ExecutionRuntime.execute`
  (owner-scoped; new additive `project_update` tool mirrors
  `PUT /solspire/projects/{id}`), `_wait_for_execution`, success = completed +
  all steps ok. WorkEvent = orchestration-created record referenced by
  `execution_attempt_ref` for authorized runs; own WorkEvent for observations.
  Evidence via `store.evidence` with `chain_digest`; `EXECUTION/WORK_EVENT/
  EVIDENCE` stages; failures `_blocked()`/`_fail()` persist before raising.
- `verify`: `EnterpriseOrchestrationStore.verify` with
  `VERIFIED|INSUFFICIENT|CONTRADICTED` — a separate human act.

**Evidence:** smoke: execute 0.08 s (project actually created), work event,
evidence, verify VERIFIED, full 14-stage chain incl. ERROR stage, backwards
linkage; `tests/test_voice_pipeline.py` (pass)

## GATE 11 — HTTP surface + operator UI + docs

**Scope:** authenticated `/solspire/voice/*` surface; operator console at
`/solspire/voice`; six docs.

**Result:** PASS.

- `solspire/voice_router.py` mounted from `solspire/console_router.py`
  (`prefix=/voice`, router-level `require_auth`); full status-code map
  (`_VOICE_HTTP_STATUS`); unauthenticated → 401 (smoke).
- UI `web/public_prism/src/pages/SolspireVoice.tsx` — panels: status board,
  providers (config names only), recent events, voice control (mic
  start/stop/cancel + timer + `MIC_DENIED` recovery + typed test-provider
  fallback), transcript & provenance (sha256, playback), understanding with
  clarification inputs, ARKADIA PROPOSES (approve/reject/edit), gated
  authorize/execute, evidence & verification, evidence-chain drawer with
  clickable stage payloads. Registered in `App.tsx` (`View`, `routeForView`,
  `resolvePath`, render branch in `ExperienceConsolidationFrame`), plus
  `ArkadiaNavigation`/`PrismInteriorShell` entries.
- Docs (six): `docs/voice/{ARCHITECTURE_DISCOVERY, ARCHITECTURE,
  ASR_PROVIDERS, INTEGRATION, UI_EXPORT, VALIDATION}.md`.

**Evidence:** `tests/test_voice_api.py` (pass), smoke 401, frontend build
(GATE 12), `docs/voice/UI_EXPORT.md`, `docs/voice/INTEGRATION.md`

## GATE 12 — Validation, regression parity, build

**Scope:** tests, end-to-end smoke, zero regressions vs pristine baseline,
frontend build.

**Result:** PASS.

| Check | Command | Result |
|---|---|---|
| Voice suites | `pytest tests/test_voice_*.py -q` | **118 passed** (4.48 s) |
| Architecture fitness | `pytest tests/architecture` | **42 passed (11/11 files)** |
| End-to-end smoke | `python3 scripts/voice_smoke.py` | **SMOKE PASSED — all 36 checks green** (re-run after final changes) |
| Pristine baseline | `pytest tests --ignore=tests/test_autonomy.py --ignore=tests/test_gitleaks_config_guard.py` on `/tmp/arkadia-pristine` @ `17e626c` | **11 failed / 1581 passed / 17 skipped** |
| With Voice | same command | **11 failed / 1699 passed / 17 skipped** — identical failure set (pre-existing, out of scope), +118 = exactly the new tests → zero regressions |
| Frontend install | `pnpm install --frozen-lockfile` | OK (lockfile unchanged) |
| Frontend build | `pnpm run build` (`vite build`) | ✓ 3447 modules, `dist/` emitted (~16 s) |
| Type sanity | `tsc --noEmit --strict` on `SolspireVoice.tsx` + `App.tsx` | **0 errors in the new page** |

Pre-existing failures (not touched): `test_agents_md_encoding_adjudication`,
`test_ais_capability_profile_onboarding`, `test_ais_w2_living_gate_grove_handoff`,
`test_identity_spine_w1`, `test_m02_reasomate_truth`,
`test_solspire_r1_governance_convergence` (2), `test_solspire_r3_execution_runtime` (1),
`test_steward_filter` (3); two collection errors (py3.10 `tomllib`, unrelated
import) occur identically in both trees.

One pre-existing runtime bug fixed because it degraded the new route:
`App.tsx` `setSolSpireSection` → `setSolspireSection` (broke
`history.pushState` on every navigation).

**Evidence:** `docs/voice/VALIDATION.md`

---

## Files changed

```
NEW  solspire/voice_contracts.py voice_asr.py voice_intent.py voice_context.py
     voice_store.py voice_pipeline.py voice_router.py
NEW  scripts/voice_smoke.py
NEW  tests/test_voice_{contracts,asr,intent,context,pipeline,api}.py
NEW  web/public_prism/src/pages/SolspireVoice.tsx
NEW  docs/voice/*.md (six)
MOD  solspire/console_router.py            (+ include voice_router)
MOD  solspire/console_authority_router.py  (+ authorize_proposal_sync extraction; route delegates)
MOD  solspire/execution_runtime.py         (+ project_update tool, additive)
MOD  web/public_prism/src/App.tsx          (+ voice route/view; typo fix setSolspireSection)
MOD  web/public_prism/src/components/ArkadiaNavigation.tsx   (+ voice view/label/nav entry)
MOD  web/public_prism/src/components/PrismInteriorShell.tsx  (+ voice surface mapping)
```

## Known limitations (truthful states, not defects)

- N-ATLAS and cloud ASR report `UNAVAILABLE` until the operator sets the
  documented env keys; pinning them then fails loudly with 503 (by design).
- Local ASR engine optional and not installed here.
- Mic capture needs a secure context; the typed test-provider path covers
  micless environments.
- The 11 pre-existing suite failures remain open (report-only).
