# Arkadia Voice — Validation

**Status:** VERIFIED. Every claim below was produced by a command in this
workspace; commands and their outputs are reproducible.

---

## 1. Test inventory (new)

| Suite | Covers | Result |
|---|---|---|
| `tests/test_voice_contracts.py` | stages/STAGE_ORDER, actions, risk policy, all 16 error states (recovery + stage), canonical/chain digests, `hash_audio` | pass |
| `tests/test_voice_asr.py` | four providers, selection pin fails loudly (no silent substitution), N-ATLAS env-only + no fabricated URL, status report leaks no secrets | pass |
| `tests/test_voice_intent.py` | bounded action parsing, human-only refusal first, confidence semantics, canonical intent reuse | pass |
| `tests/test_voice_context.py` | KNOWN/AMBIGUOUS/UNKNOWN/UNAUTHORIZED, ownership checks, disambiguation fields, transfer resolution | pass |
| `tests/test_voice_pipeline.py` | full chain incl. negative paths (blocked-before-approval, blocked-before-authorization), observation-only execution, work event/evidence linkage, ERROR-stage persistence | pass |
| `tests/test_voice_api.py` | HTTP surface: auth 401, status/providers, multipart ingest, status-code map (422/409/403/503), audio roundtrip + sha256 header, chain reads | pass |

**Voice total: 118 passed.** With `tests/architecture` (11/11 fitness files,
42 assertions incl. authority/proposal suites): **129 passed**.

## 2. End-to-end smoke harness

`python3 scripts/voice_smoke.py` (no `env |`, no shell env reads, no secrets):

```
SMOKE PASSED: all checks green   (36 checks)
```

Covers: status board → ingest + audio hash roundtrip → understand → propose →
blocked without approval (negative, persisted) → decision → blocked without
authorization (negative, persisted) → 403 for non-govern subject → authorize →
execute (0.08 s; project actually created through ExecutionRuntime) → work
event referenced → evidence → verify VERIFIED → full 14-stage chain **including
the ERROR stage produced by the negative cases** → backwards linkage →
unknown-intent 422 → empty-transcript 422 → natlas 503 → unauthenticated 401.

## 3. Regression parity (pre-existing failures proven unchanged)

Baseline: pristine `main @ 17e626c` worktree (`/tmp/arkadia-pristine`).

| Tree | Command | Result |
|---|---|---|
| pristine | `pytest tests --ignore=tests/test_autonomy.py --ignore=tests/test_gitleaks_config_guard.py` | **11 failed / 1581 passed / 17 skipped** |
| with Voice | same command | **11 failed / 1699 passed / 17 skipped** |

Identical failure set in both trees (zero regressions; +118 = exactly the new
voice tests). The 11 pre-existing failures are outside mission scope and were
**not** touched:
`test_agents_md_encoding_adjudication::test_corruption_origin_is_re_derivable`,
`test_ais_capability_profile_onboarding`, `test_ais_w2_living_gate_grove_handoff`,
`test_identity_spine_w1`, `test_m02_reasomate_truth`,
`test_solspire_r1_governance_convergence` (2), `test_solspire_r3_execution_runtime` (1),
`test_steward_filter` (3).
Two additional **collection** errors are pre-existing environment issues
(py3.10 lacks `tomllib`; one unrelated import error) and occur identically in
both trees.

`tests/architecture` fitness: **11/11 files, 42 passed** after the change.

## 4. Frontend validation (`web/public_prism`)

| Check | Command | Result |
|---|---|---|
| Install | `pnpm install --frozen-lockfile` | OK (pnpm 10.26.1, lockfile unchanged) |
| Build | `pnpm run build` (`vite build`) | ✓ 3447 modules transformed, `dist/` emitted, ~16 s |
| Type sanity | `tsc --noEmit --strict` on `SolspireVoice.tsx` + `App.tsx` | **0 errors in the new page**; remaining diagnostics are pre-existing patterns in untouched files (this frontend has no tsconfig and has never been type-gated) |

Fixed while verifying: `App.tsx` pre-existing typo `setSolSpireSection` →
`setSolspireSection` (broke `history.pushState` on **every** in-app
navigation, including `/solspire/voice`).

Manual route checks: `/solspire/voice` resolves through `resolvePath`, renders
inside the SolSpire experience frame, sign-in threshold shows when signed out,
and the rail/drawer entries navigate to the route.

## 5. Truthfulness checks (negative-space)

- `rg -i "n-atlas|natlas"` before implementation: 0 hits → no integration was
  reused or faked; the provider is env-config only and reports
  `UNAVAILABLE · OFFICIAL_ACCESS_NOT_CONFIGURED` here.
- `freebuff-env list` → no keys set → cloud provider reports
  unavailable/misconfigured (expected, not a defect).
- Provider status payloads verified to contain configuration **names** only.
- The UI renders stored fields and chain payloads only — no client-side
  synthesis of intent/context/authorization state.

## 6. Known limitations

- N-ATLAS/cloud transcription requires the operator to add the documented env
  keys; until then ingest with those providers pinned returns a truthful 503.
- The local ASR engine (faster-whisper/whisper) is optional and not installed
  in this workspace.
- The 11 pre-existing suite failures remain open (report-only, out of scope).
- Browser mic capture requires a secure context (localhost/HTTPS); the typed
  test-provider path exists for micless environments.
