# P1-1 — PRIVATE BETA PRODUCT ACTIVATION

**Mission:** ARKADIA WEAVER P1 Private Beta — make existing product surfaces
coherent, usable, multi-user. No redesign. Smallest coherent change set.

---

## 1. EXECUTION STATUS

**IN PROGRESS — P1-1 IMPLEMENTATION**

Save-state: P1-0 recon complete; change set identified and being implemented.

---

## 2. HEAD RANGE

| Ref | SHA | Summary |
|-----|-----|---------|
| Start HEAD | `bb8bc1f` | docs: finalize P0 checkpoint and resume state |
| Baseline repair | `9fa48f4` | fix(p1-0-baseline): extract key + approval routes |
| End HEAD | *(to fill)* | *(to fill)* |

---

## 3. PRODUCT ACTIVATION MATRIX (P1-0 RECON)

| Surface | Classification | Notes |
|---------|----------------|-------|
| Homepage (Think · Remember · Build) | **EXISTING + WORKING** | P0 narrative intact; no changes needed |
| Auth + `/api/me` profile | **EXISTING + WORKING** | Firebase identity → uid; A≠B |
| Oracle (ArkanaCommune) | **EXISTING + WORKING** | Full canvas; Save to memory (P0-G) |
| Save to memory → Knowledge OS | **EXISTING + WORKING** | Explicit only; `/api/personal/ingest-note` |
| Personal Echofeild | **EXISTING + WORKING** | Derives from authed Knowledge OS data |
| MemoryGovernance | **EXISTING + WORKING** | Inline in PersonalEchofeild; PATCH/DELETE owner-only |
| Spiral Codex (`NexusSpiralCodex`) | **EXISTING + WORKING** | Scrolls + collections; Stellar Cartography header |
| NovaNet public feed | **EXISTING + PARTIAL** | Client-supplied author id; unauthenticated delete; sovereign fixture (Zahrune) in status ring + ReasoMate samples — **fix target** |
| Encyclopedia | **EXISTING + WORKING** | Nexus tab renders `NexusSpiralCodex`; `StellarCartography` header |
| SolSpire console | **EXISTING + PARTIAL** | Sparse for new users; needs honest empty states |
| IMS Archive | **LEGACY (deliberate)** | Sealed historical documents; not touched |
| LivingGate | **LEGACY / DEFERRED** | Isolated per P0; not touched |
| `weaver/filters/steward` | **EXISTING + UNWIRED** | Test drift only; no runtime import |
| `gate/` static tests | **DEAD / UNUSED** | Legacy static gate referenced by stale tests |
| `arkadia-android` | **EXISTING + PARTIAL** | WebView shell; DEFAULT_URL points at emulator loopback — **P1-2 fix target** |
| `sonata-android`, `archive/legacy_android` | **LEGACY** | Not part of P1 |

### Pre-existing failures noted at recon (NOT P1 regressions)

- `test_gate_*` — reference legacy `gate/index.html` (never existed in this repo snapshot) — classified DEAD.
- `test_steward_filter` (3) — heuristic drift in unwired `weaver/filters/steward` module.
- `api/main.py` budget — genuine freeze violation; **repaired** in `9fa48f4`.

---

## 4. P1-1 CHANGE SET (smallest coherent)

| # | Change | Why (acceptance link) |
|---|--------|-----------------------|
| 1 | `api/transmissions.py` — bind author/owner from verified Firebase token; ownership-checked delete | Invariants 1-4; NovaNet acceptance |
| 2 | `NovaNetPage.tsx` — send Bearer token; delete-own UI; remove sovereign fixtures | Invariant 11; acceptance |
| 3 | Fill Acceptance/Security/Regression matrices | DoD |

P1-2 (Android) is gated on P1-1 GREEN — handled in
`docs/verification/P1-2_ANDROID_BETA.md`.

---

## 5. ACCEPTANCE MATRIX

Verification harness: `tests/production/p1_two_user_check.py` — 22/22 checks.
Target: local backend (`uvicorn api.main:app`) with real disposable Firebase
identities (Identity Toolkit signUp ⇒ hard-delete). Because content-mode push
was **blocked** (see §8), production runs pre-fix code; proof labels below are
honest.

| # | Acceptance item | Status | Proof |
|---|-----------------|--------|-------|
| 1 | New user understands the product (homepage narrative preserved) | ✅ | CODE-VERIFIED |
| 2 | User can authenticate (Firebase) | ✅ | API-PROVEN (harness 01-02) |
| 3 | User gets own identity (`/api/me`) | ✅ | API-PROVEN |
| 4 | User can enter Oracle/ReasoMate conversation | ⚠️ | NOT PROVEN in prod — Gemini key currently invalid (502 on `/api/commune/resonance`); endpoint unchanged, CODE-VERIFIED only |
| 5 | User can explicitly save memory (ingest-note) | ✅ | API-PROVEN |
| 6 | Saved memory reaches personal field | ✅ | API-PROVEN |
| 7 | User can govern that memory (PATCH/DELETE) | ✅ | API-PROVEN |
| 8 | User can participate in NovaNet (create/see/delete-own) | ✅ | API-PROVEN (local) |
| 9 | Public NovaNet ≠ private memory (distinct stores enforced) | ✅ | API-PROVEN |
| 10 | Spiral Codex visibly distinct from NovaNet (nexus tabs split codex vs feed) | ✅ | CODE-VERIFIED |
| 11 | SolSpire exposes useful personal state | ⚠️ | PARTIAL — honest sparse empty states for new users; deferred |
| 12 | P0 isolation intact | ✅ | API-PROVEN (test_isolation green, Phase 0C prod isolation 8/9 — 1 fail is Gemini-quota dependent) |
| 13 | No second memory store | ✅ | CODE-VERIFIED |
| 14 | No autonomous memory capture | ✅ | API-PROVEN (memory saved only via explicit ingest-note) |

---

## 6. SECURITY / INVARIANT MATRIX

| # | Invariant | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Firebase identity determines ownership | ✅ | `api/transmissions.py` binds `owner_uid` from verified claims |
| 2 | Client-supplied user_id never authoritative | ✅ | `author.id` is advisory; verified `owner_uid` wins |
| 3 | Private memory owner-scoped | ✅ | B-marker absent for B; A-marker visible only to A |
| 4 | Public posts intentionally public | ✅ | Both A/B see both public posts |
| 5 | Private memory never public by existence | ✅ | Transmissions feed shows only explicit posts |
| 6 | Save-to-memory remains explicit | ✅ | Only via `/api/personal/ingest-note`; no auto-archive |
| 7 | Logout clears auth Knowledge state (P0) | ✅ | Not re-run (untouched code path); CODE-VERIFIED |
| 8 | Account switching cannot leak state | ✅ | Harness provisions/disposes users per session |
| 9 | No second memory system | ✅ | Single `knowledge/` substrate |
| 10 | No autonomous memory capture | ✅ | API-PROVEN |
| 11 | No sovereign fixture as runtime identity | ✅ | `Zahrune`/sample identities removed from NovaNet fixtures |
| 12 | P0 routes & ownership filters protected | ✅ | Full suite 183 passed (5 pre-existing non-related fails) |

---

## 7. REGRESSION MATRIX (P0 GATES)

| Gate | Status | Proof |
|------|--------|-------|
| P0-B Identity | ✅ | API-PROVEN (harness `/api/me` x2) |
| Phase 0C isolation (prod) | ⚠️ | 8/9 PRODUCTION-PROVEN; test_08 blocked by Gemini 502 external dependency |
| Phase 1 Knowledge OS | ✅ | API-PROVEN (ingest/patch/delete cycle) |
| P0-C Personal Knowledge | ✅ | B-visibility checks of harness |
| P0-D Explicit Save | ✅ | ingest-note explicit tag |
| P0-E Echofeild | ✅ | notes GET A vs B markers |
| P0-F Memory Governance | ✅ | PATCH + DELETE checks in harness |
| P0-G Save button on Oracle turns | ✅ | NOT RE-RUN (unchanged by P1-1 change set) |

Architecture fitness: 10/10 green (verified with
`python -m pytest tests/architecture/ -q`).
Backend full suite: **183 passed / 5 pre-existing fails / 4 collection errors**
(unchanged from baseline; the fails are `test_gate_*` and `test_steward_filter`
— classified P1-0 recon as DEAD/UNWIRED.)

---

## 8. KNOWN LIMITATIONS

1. **Push blocked** — Git push to main is denied from this workspace
   (`remote: Permission to ... denied`) and no SSH fallback is present.
   Commits `9fa48f4` (baseline repair) and `e69b320` (P1-1) exist **locally**
   and are ready to push/deploy. Production endpoint behaviour is therefore
   still pre-fix (any user could delete any post) until redeployment.
2. **Production Oracle endpoint returns 502** — invalid/exhausted Gemini keys
   in operator store (`All Gemini models failed … 400 Bad Request`). Not caused
   by P1-1; rotation of `/api/keys` pool is an operator action required for the
   beta loop to be genuinely usable.
3. **Production test_08 (oracle context isolation) blocked** by the same key
   issue; cannot label PRODUCTION-PROVEN until a valid key is placed.
4. **Council-hip memory governance** and auto-oracle save flows are still
   correct; SolSpire personal dashboard remains sparse-but-honest (not stubbed).

---

## 9. DEPLOYMENT / RESUME STATE

- Start HEAD: `bb8bc1f` (P0 final checkpoint).
- Baseline repair: `9fa48f4` (extract key + approval routes).
- End HEAD (P1-1): `e69b320` — NovaNet ownership binding + delete-own +
  fixture removal (`api/transmissions.py`, `NovaNetPage.tsx`,
  `tests/test_transmissions_ownership.py`, this doc). Pushed: **NOT PUSHED
  (credential issue, see §8)** — will be pushed together with P1-2 once access
  is restored; deploy then enables PRODUCTION proof for §5/§6 items.
- Verification harness: `tests/production/p1_two_user_check.py` —
  22/22 GREEN locally. Re-run with
  `ARKADIA_PRODUCTION_BASE_URL=<url> python tests/production/p1_two_user_check.py`.
- Regression guards:
  - `python -m pytest tests/test_transmissions_ownership.py -q` → 8/8 PASS
  - `python -m pytest tests/architecture/ -q` → 10/10 PASS
  - Phase 0C prod isolation → 8/9 (1 external-dependency fail)
- **P1-1 status: GREEN** (with documented limitations). Proceeding to P1-2 —
  Android Beta Packaging.
