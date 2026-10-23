# PRISM-REC-STELLAR-01 — Stellar Cartography lens (Encyclopedia Galactica header)

**Status: IMPLEMENTED, VERIFIED (slice-local). NOT ACCEPTED. NOT DEPLOYED.**

Build ID: `PRISM-REC-STELLAR-01`
Parent build: `PRISM-REC-SPIRAL-CODEX-01` (PR #560)
Base: `e11d93b4` — **the head of PR #560, NOT `main`** (see *Stacking* below)
Canonical production: `https://arkadia-qzu4.onrender.com` (runs `main` `68403b9e`; this
change is not in it)

---

## 0. Stacking — declared, not hidden

This slice is **stacked on PR #560** and does not stand alone on `main`. That is a measured
dependency, not an accident:

- The archive mounts the readout at **exactly one** site —
  `archive/frontend/arkadia-prism/web/public_prism/src/pages/NexusSpiralCodex.tsx:953` —
  and `App.tsx:134` binds `NexusSpiralCodex` to the **`encyclopedia`** view.
- `main` `68403b9e` has **no `codex` lens**: its `NovaNetPage.tsx` declares only
  `field`, `echoes`, `hub` (`LENSES`, line 36-38), and its registry has no `publicCodex`
  entry. The lens that this readout heads is created by **#560**.
- So the panel has no correct mount site on `main`. Creating one would duplicate #560.

**Consequence for review:** the branch is `#560's head + 1 commit`. Until #560 merges, a PR
against `main` shows **both** commits' diffs. After #560 merges, the diff reduces to this
slice alone. Merge order: **#560 first, then this** — or this rebased onto the post-#560
`main` (a no-op rebase, since #560's head is an ancestor).

This corrects an error made mid-slice: work began on #560's branch without declaring it,
and a full-suite run was mislabeled "baseline on main" when it was measured on
`e11d93b4`'s tree. The measurement is still the correct one for isolating this slice (it is
this slice's own base); the **label** was wrong and is corrected here.

---

## 1. Capability

**ID:** `CAP-STELLAR-CARTOGRAPHY`
**Purpose:** the Encyclopedia Galactica living star-date readout — Ark Date, Schumann
resonance, lunar phase, planetary sky ("bone report"), cosmic weather, the day's Oversoul
blind-pull transmission, and the volume index.

| | |
|---|---|
| Legacy route | `/encyclopedia` → `NexusSpiralCodex` |
| Legacy component | `components/StellarCartography.tsx` (230 lines), mounted at `NexusSpiralCodex.tsx:953` |
| Current surface | NovaNet → `codex` lens ("Encyclopedia Galactica") |
| Endpoint | `GET /api/stellar-cartography` |
| Router | `api/main.py:1648` (`@app.get`) |
| Service | `kernel/stellar.py::readout()` — pure Python, no `httpx`/`fastapi` import |
| Identity / authority | **none required** — anonymous open read |
| State change | **none** — read-only |
| Classification before | `UNSURFACED` |
| Classification after | `CONNECTED` |

### Contract, measured — not inferred

`200` anonymously on the canonical deployment. Seven sections, all present, **no null
fields** observed in the live payload:

```
ark_date{12}  schumann{bands[7], dominant_hz, dominant_name, quality, dominant_index}
lunar{7}  planetary{bodies{Sun,Moon,Mercury,Venus,Mars,Jupiter,Saturn}, sun_sign,
moon_sign, bone_report, zodiac[12]}  cosmic_weather{5}
oversoul_blind_pull{transmission, pull_index, method}  galactica{volumes[5],
current_volume, total_volumes}  timestamp_utc
```

Live sample: `ARK Y1 · D207 · 09:38`, `20.8 Hz · Third Harmonic · Mental Coherence`,
`Waxing Gibbous · 91.7% · Hunter's Moon`, `Calm · Kp 0.9 · wind 559 km/s`, `Vol II`.

### Why it was a gap

`grep -rn 'stellar' web/arkadia_console/src/` → **0 matches**. A verified anonymous read
with a rich, fully-populated contract had no surface, while its archive mount site is the
lens this workstream had just created.

---

## 2. Deliverables

| File | Change |
|---|---|
| `web/arkadia_console/src/components/novaNet/stellarCartographyContract.ts` | new — types, shape guard, ordering helper, refresh constant |
| `web/arkadia_console/src/components/novaNet/StellarCartographyPanel.tsx` | new — the readout |
| `web/arkadia_console/src/lib/endpoints.ts` | `stellarCartography: "/api/stellar-cartography"` |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | mount above `SpiralCodexPanel` on the `codex` lens |
| `tests/test_console_stellar_cartography_contract.py` | new — 13 guards |
| `docs/control-plane/evidence/prism-rec-stellar-01/EVIDENCE.md` | this file |
| `docs/.../prism-rec-spiral-codex-01/FOLLOW-UPS.md` | the human's three follow-ups + the set-definition caveat |
| `docs/.../prism-rec-spiral-codex-01/RECON-IMS-AUTH.md` | separate recon finding (sovereign-gated, not repaired) |

`api/main.py` untouched (budget 2600).

---

## 3. Three deliberate departures from the archive

A faithful port would have carried two defects. Both are now detectors.

1. **Failures are shown.** The archive did
   `.catch(() => {})` with `setData` guarded on non-null, so a failed fetch rendered
   `Calibrating the star date…` **forever** — an outage was indistinguishable from a slow
   load. The panel routes failure through `ContractState` (`unavailable` + retry), and the
   guard fails on an empty `catch`.
2. **No client-side clock.** Every value is the server's. The Ark Date epoch
   (`March 31 2026 — Birthday Seal`) is not a UTC calendar derivation, so a client-side
   recomputation would silently disagree with the kernel. Guarded.
3. **No read-aloud control.** The archive attached a `ScrollListenButton` to the Oversoul
   transmission. That component is **not on this branch** (it is PR #559), so no control is
   rendered — an honest absence rather than a dependency on unmerged work.

---

## 4. Attack the implementation — detectors falsified on real source

Every detector was run against the **real** files with the mutation asserted applied
(a no-op `sed` reads as "detector broken"). Each mutation was reverted and the tree
verified byte-identical.

| # | Mutation (real source) | Result |
|---|---|---|
| M1 | unmount `<StellarCartographyPanel />` | **2 failed** — mount + archive-order |
| M2 | replace the `.catch(...)` with the archive's `.catch(() => {})` | **1 failed** — failure surfacing |
| M3 | hard-code `"/api/stellar-cartography"` in the panel | **2 failed** — registry bypass |
| M4 | **control** — add a *comment* naming the path | **13 passed** (silent on prose) ✓ |
| M5 | neuter `isStellarReadout(payload)` to `if (false)` | **1 failed** — guard unused |

M4 is the load-bearing control: without comment-stripping a doc comment mentioning the path
reads as a use of it, and the detector would fail correct code. It is silent on prose and
bites on code.

---

## 5. Verification

### 5.1 Targeted + neighbouring guards

`90 passed` — `test_console_stellar_cartography_contract.py` (13),
`test_console_spiral_codex_contract.py`, `test_console_legacy_route_coverage.py`,
`test_prism_console_ci_wiring.py`, `test_console_endpoint_registry_contract.py`.

### 5.2 Build

`corepack pnpm exec tsc --noEmit` → exit 0.
`corepack pnpm build` → `built in 1.81s`, no warnings.

### 5.3 Browser journey — against the real production contract

The console's own Vite dev server with `server.proxy: {"/api": <canonical origin>}` so
requests are same-origin (production sends no ACAO for localhost; the preflight is 400).
Temp config kept in `/tmp` and deleted from the repo — **never staged**.

At `/novanet/codex`:

- readout renders **above** the corpus, with **live production values**: `ARK Y1 · D207 ·
  09:38`, `Vol II`, `20.8 Hz · Third Harmonic`, `Waxing Gibbous · 91.7% · Hunter's Moon`,
  `Calm · Kp 0.9 · wind 559 km/s`;
- the Oversoul transmission renders with its `blind-pull · rotated by Ark Day` method line;
- `Full atlas` expands → `Collapse atlas`, `aria-expanded` toggles, all **5 volumes**,
  **7 Schumann bands** (dominant highlighted), and **7 sky bodies** render;
- the corpus below reports the server's own `661` documents / `4,469,876` characters;
- search: typing `roadmap` narrows the list to **2** (`ROADMAP.md`,
  `docs/recon/21_prioritized_refactor_roadmap.md`); the filter logic was independently
  reproduced against the real 661-document payload (empty→661, `roadmap`→2, `zzzznope`→0);
- **no console or Vite errors.**

**Measurement trap recorded:** `browser_get_content` returned a **stale cache** and showed
"661 matches" after typing, which reads as a broken search. The live DOM
(`browser_get_state`) showed 2 results. Trust the DOM state over a content dump, and
cross-check logic against the real payload before calling a defect.

### 5.4 Regression — same environment, same session

Full suite, `PYTHONPATH=archive/legacy_python`, `-q -rEf --continue-on-collection-errors`:

| Tree | Result | Node set |
|---|---|---|
| base `e11d93b4` (**#560 head**, not `main`) | 8 failed / 3378 passed / 17 skipped / 1 error | `c280ddc6…` (9 nodes) |
| this branch | 8 failed / 3391 passed / 17 skipped / 1 error | `c280ddc6…` (9 nodes) |

`comm -3` on the sorted failing/error node sets is **empty**. Passed delta **+13** equals
`--collect-only` for the new file → **13**. Zero regression; the delta is exactly this
slice's guard.

### 5.5 CI wiring

`scripts/console_contract_domain.py` derives the console-contract domain from
`git ls-files`. With the new guard tracked it reports **47** (was 46), and the gate executes
`python -m pytest -q $(python scripts/console_contract_domain.py)` — so the new guard is
inside the executed set **without editing the workflow**. This is the derived-inventory
repair from PR #439 working as designed.

---

## 6. What is NOT claimed

- **No production observation.** Production runs `main` `68403b9e`, which contains neither
  this change nor #560. The browser journey was against a dev server proxying to the
  canonical origin — the *contract* and the *journey* were exercised, the *deployed UI* was
  not.
- **No acceptance.** Deployment is not verification; verification is not acceptance.
- **`/api/ark-date`** (the Ark Date section alone) is **not** reconciled here — registered
  as a distinct path, deliberately out of scope.
- **`/api/codex/upload`** (a mutation on the shared corpus) is not wired — separate slice,
  separate authority review.
- **The IMS authorization asymmetry** is recorded (`RECON-IMS-AUTH.md`), **not repaired** —
  `api/ims_products.py` is an authority surface and the repair is sovereign-gated.

---

## 7. Rollback

Revert the branch. All changes are additive: two new files, one registry line, one JSX
mount, one new test file. No shared file is restructured, and the base (#560) is unaffected.
