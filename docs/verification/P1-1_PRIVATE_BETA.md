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

*(to fill at verification)*

---

## 6. SECURITY / INVARIANT MATRIX

*(to fill at verification)*

---

## 7. REGRESSION MATRIX (P0 GATES)

*(to fill at verification)*

---

## 8. KNOWN LIMITATIONS

*(to fill)*

---

## 9. DEPLOYMENT / RESUME STATE

*(to fill)*
