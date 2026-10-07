# Arkadia Voice — Architecture

**Status:** IMPLEMENTED. This document describes the shipped pipeline and its
evidence chain. Every stage below exists in code and is covered by
`tests/test_voice_*.py`.

---

## 1. Design law

> Speech is an input modality, not authorization.

The voice surface never executes anything directly. Every utterance is
converted into the same governed artifacts the console already uses:
VoiceEvent → Transcript → Intent → Context → Authority → Proposal → human
decision → Authorization → execution → WorkEvent → Evidence → Verification.

The repository's governance ordering wins over any prompt ordering:
`ACCEPTED` (human decision) is **not** `AUTHORIZED` (govern authority).

---

## 2. Modules

| Module | Responsibility |
|---|---|
| `solspire/voice_contracts.py` | Canonical types: `VoiceStage`/`STAGE_ORDER`, `VoiceAction`, `RISK_LEVELS`, `VOICE_ERROR_STATES` (all 16 Phase-12 states with recovery + stage), `VoiceEvent`, `Transcript`, `Intent`, `Context`, `VoiceProposal`, `VoiceExecution`, `ChainStage`, `hash_audio` (sha256), `canonical_digest`, `chain_digest`, `new_id` |
| `solspire/voice_asr.py` | ASR provider protocol + Test/Local/N-ATLAS/Cloud providers, selection and status reporting (see `ASR_PROVIDERS.md`) |
| `solspire/voice_intent.py` | Bounded rule parser: transcript → `VoiceAction` (ASK/SEARCH/CREATE/MODIFY/EXECUTE/UNKNOWN) + entities + confidence; human-only phrases (merge/deploy) checked first → `UNKNOWN` + `requested_effect=REFUSED_HUMAN_ONLY`; reuses canonical `IntentRouter().classify()` for `canonical_intent_type` |
| `solspire/voice_context.py` | `resolve_context()` → `KNOWN/AMBIGUOUS/UNKNOWN/UNAUTHORIZED` over projects/knowledge/people via the canonical managers, user-scoped; disambiguation fields = name/target/query/path/recipient |
| `solspire/voice_store.py` | `VoiceStore` on the canonical `data/solspire_projects.db` (`_DB_PATH` module attribute so `conftest.py` sandboxes it): `voice_events` (full chain-linkage columns + `audio_bytes BLOB`) and append-only `voice_chain` (seq/prev_record_id/payload_digest) |
| `solspire/voice_pipeline.py` | The stage driver: `ingest → understand → propose → decide/revise → authorize → execute → verify` plus reads (`get/list/chain/audio`) |
| `solspire/voice_router.py` | Thin FastAPI handlers mounted at `/solspire/voice/*` with `require_auth`; maps every `VoiceError.state` to an HTTP status |

---

## 3. Chain stages (`VoiceStage`, ordered)

```
VOICE_EVENT → TRANSCRIPT → INTENT → CONTEXT → AUTHORITY
  → [CLARIFICATION] → PROPOSAL → APPROVAL → AUTHORIZATION
  → EXECUTION → WORK_EVENT → EVIDENCE → VERIFICATION
(+ PROPOSAL_REVISION on EDIT, ERROR on any failure)
```

Every stage is appended to `voice_chain` as
`{seq, stage, record_type, record_id, payload, payload_digest, prev_record_id}`.
`chain_digest(stages)` hashes the ordered
`[seq, stage, record_id, payload_digest]` tuples, so each stage is
traceable backwards through `prev_record_id` and the whole chain is one
inspectable evidence claim.

**Negatives persist.** `_fail()` writes `status=FAILED`, `error_state`,
`error_detail` and an `ERROR` chain stage **before** raising, so a refused,
blocked or crashed run still leaves evidence (verified by the smoke harness:
the full 14-stage chain includes the ERROR stage produced by negative cases).

---

## 4. Event status machine (stored on `voice_events.status`)

| Transition | Written by |
|---|---|
| `RECEIVED` | `ingest` (event row insert) |
| `TRANSCRIBED` | `ingest` after a non-empty transcript |
| `UNDERSTOOD` / `CLARIFICATION_REQUIRED` | `understand` (context `KNOWN` vs not) |
| `PROPOSED` | `propose` (and `revise`, which supersedes the old proposal) |
| `APPROVED` / `REJECTED` | `decide` — decision only; authorization is separate |
| `AUTHORIZED` | `authorize` (govern authority accepted) |
| `EXECUTED` / `FAILED` | `execute` (and `_fail` on any error path) |

Linkage columns, all inspectable on the event:
`proposal_id → approval_ref → authorization_ref → execution_id →
work_event_id → evidence_ref → verification_ref`.

---

## 5. Governance chain (reused, never forked)

1. **Proposal** — `solspire/proposal_manager.py::create_proposal`
   (`PRESENTED`), scope JSON carries the executor plan, risk level,
   resolved entities and the transcript.
2. **Human decision** — `record_decision` via
   `POST /solspire/voice/events/{id}/decision` (`ACCEPTED|DECLINED|WITHDRAWN`).
   Stage payload explicitly records: *"A human decision is not authorization."*
3. **Authorization** — `authorize()` delegates to the extracted
   `solspire/console_authority_router.py::authorize_proposal_sync` (same
   function the existing `/solspire/authority` route uses): govern authority
   check (Flamekeeper or `access_level ≥ 3`), proposal must be `ACCEPTED`,
   materializes HAE + `Authorization` bound via `bind_authorization`.
   `HTTPException 403 → AUTHORIZATION_DENIED`, `409 → APPROVAL_REQUIRED`,
   `404 → PROPOSAL_REQUIRED`.
4. **Execution** — `solspire/execution_runtime.py::ExecutionRuntime.execute`
   (canonical project executor; additive `project_update` tool added to
   mirror `PUT /solspire/projects/{id}`). Observation-only actions
   (ASK/SEARCH) run through `_execute_observation` with **no** proposal,
   approval or authorization (Engineering Lab voice boundary, READ
   disposition — policy reused from `lab/engineering_lab/voice.py`).
5. **Work event** — for authorized executions the pipeline **references** the
   WorkEvent that `weaver/enterprise_orchestration.py::complete_execution_attempt`
   auto-creates (1:1 with the execution attempt, UNIQUE
   `work_events.execution_attempt_ref`); observation executions create their
   own WorkEvent.
6. **Evidence + verification** — `store.evidence(...)` then a separate human
   `verify(verdict ∈ {VERIFIED, INSUFFICIENT, CONTRADICTED})` through
   `EnterpriseOrchestrationStore.verify`. Execution is never verification.

---

## 6. Risk policy (stored, displayed, enforced)

| Action | Risk | Disposition |
|---|---|---|
| ASK, SEARCH | INFORMATIONAL | observation-only: no proposal, no approval |
| CREATE, EXECUTE | MEDIUM | proposal → decision → authorization → execution |
| MODIFY | HIGH | proposal → decision → authorization → execution |
| UNKNOWN | conservative | refused before any proposal (`INTENT_UNKNOWN`) |

Human-only phrases (merge, deploy) are refused at the voice boundary with
`AUTHORITY_MISSING` regardless of authority level.

---

## 7. HTTP surface (`/solspire/voice/*`)

```
GET  /solspire/voice/status            chain, error states, risk policy, subject, ASR report
GET  /solspire/voice/providers         provider report (config names only, no secrets)
POST /solspire/voice/events            multipart: file + language + provider + session_id
                                       + duration_ms + transcript_hint
GET  /solspire/voice/events            subject-scoped list
GET  /solspire/voice/events/{id}       event + chain + chain_digest + stage_order
GET  /solspire/voice/events/{id}/chain append-only stage list
GET  /solspire/voice/events/{id}/audio raw audio + X-Arkadia-Audio-SHA256
POST /solspire/voice/events/{id}/understand|propose|decision|revise|authorize|execute|verify
```

Status mapping (full table in `voice_router.py::_VOICE_HTTP_STATUS`):
ASR_UNAVAILABLE 503, ASR_FAILED 502, TRANSCRIPT_EMPTY/INTENT_UNKNOWN 422,
CONTEXT_*/APPROVAL_REQUIRED/AUTHORIZATION_REQUIRED/PROPOSAL_REQUIRED/
VERIFICATION_* 409, AUTHORITY_MISSING/AUTHORIZATION_DENIED 403,
EXECUTION_FAILED 500, AUDIO_* 400. Unauthenticated → 401 (router-level
`require_auth`).

---

## 8. What was deliberately not built

- No second database, no second proposal/work-event/evidence system.
- No N-ATLAS endpoint fabrication (see `ASR_PROVIDERS.md`).
- No voice-driven merge/deploy (human-only, refused).
- No client-side "understanding" — the UI renders stored fields only.
