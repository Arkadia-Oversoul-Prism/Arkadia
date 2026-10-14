# PRISM-W4 · Arkana thread history — timestamp time-truth (bounded repair)

**Lane:** 4 — Arkana / Weaver / Engineering Lab
**Branch:** `feat/prism-w4-arkana-thread-time-truth`
**Base main:** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` (2026-10-13, *fix(ci): allow five minutes for Render revision rollout*)
**Status:** IMPLEMENTED — targeted proof and build pass; human merge authority untouched.
**Authority:** no merge, deployment, or acceptance is claimed or performed by this pass.

## 1. The defect (measured, not inferred)

`ArkanaThreadHistory.tsx` rendered the thread contract's timestamps with a
hand-rolled local helper:

```ts
const normalized = value.includes("T") ? value : value.replace(" ", "T");
const parsed = new Date(normalized);
```

The wire value is SQLite's `datetime('now')` — `YYYY-MM-DD HH:MM:SS` in **UTC with no zone
designator** — passed through unchanged by `api/commune_threads.py` (`_public_thread` reads the
row and re-emits `created_at` / `updated_at` verbatim; the schema default is
`TEXT NOT NULL DEFAULT (datetime('now'))`). Per ECMA-262 a date-time string with no offset is
read as **local** time, so the same stored instant was placed at a different moment in every
zone. The rendered reading was correct only on a UTC host — CI and a UTC container are
accidentally right, which is why a green build never noticed.

Measured on the shipped helper, stored value `2026-10-14 06:06:12`:

| `TZ` | rendered before repair | shift vs. the stored instant |
|---|---|---|
| `UTC` | `10/14/2026, 6:06:12 AM` | 0 (masked) |
| `America/New_York` | `10/14/2026, 6:06:12 AM` | **+240 min** |
| `Europe/London` | `10/14/2026, 6:06:12 AM` | **−60 min** |
| `Asia/Kolkata` | `10/14/2026, 6:06:12 AM` | **−330 min** |

## 2. The bounded change

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/arkana/arkanaThreadTime.ts` | **new** — the canonical reading: a zoneless date-time is UTC and gains the designator; a value that already states an offset is left untouched; the reading is labelled with the reader's zone; an unreadable value is surfaced verbatim and marked. |
| `web/arkadia_console/src/components/arkana/ArkanaThreadHistory.tsx` | the local `readableTime` definition is removed and the canonical module imported (the two call sites — `turn.created_at`, `thread.updated_at` — are unchanged). |
| `web/arkadia_console/src/components/arkana/arkanaThreadsContract.ts` | doc-only: the `created_at` note now states the value is **zoneless UTC** and names the reader. |
| `tests/test_prism_w4_arkana_thread_time_truth.py` | **new** — the executable guard. |

After the repair, the same stored value renders as
`10/14/2026, 2:06:12 AM GMT-4` (New York), `10/14/2026, 7:06:12 AM GMT+1` (London),
`10/14/2026, 11:36:12 AM GMT+5:30` (Kolkata) — one instant, three local clocks, each labelled.

Two judgement calls, stated rather than implied: the reading is **not** re-derived per surface
(two readings drift apart, which is how this defect arrived), and the zone label is kept because
a displayed time with no zone cannot be told apart from one that was silently shifted — the exact
ambiguity being repaired.

## 3. Proof

Commands run in this environment at the branch tree.

| Check | Command | Result |
|---|---|---|
| New guard | `python -m pytest tests/test_prism_w4_arkana_thread_time_truth.py -q -rEf` | **10 passed** |
| Related lane-4 guards | `… tests/test_prism_w4_arkana_thread_time_truth.py tests/test_prism_w4_arkana_thread_history.py tests/test_arkana_thread_history_contract.py -q -rEf` | **42 passed** |
| Console contract domain (the gate's own inventory) | `python -m pytest -q $(python scripts/console_contract_domain.py)` | **436 passed** |
| Console-contract CI-wiring judge | `python -m pytest tests/test_prism_console_ci_wiring.py -q` | **30 passed** |
| Architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| Typecheck + build | `corepack pnpm build` (`tsc --noEmit && vite build`) | **clean** — `84 modules transformed`, `dist/assets/index-DPphKgro.js` |
| Mutation boundary | `printf '%s\n' $(git diff --name-only HEAD) \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** (M02A legitimate-surface + constitutional denylist) |

### 3.1 Negative control — the detector fires on the real defect

Mutating the **shipped** module (dropping `+ "Z"`) and re-running the guard:

```
2 failed, 8 passed
FAILED …::test_the_stored_instant_is_identical_in_every_zone
FAILED …::test_each_zone_renders_its_own_clock
```

The module was then restored byte-identically (`grep -n 'replace(" ", "T") + "Z"'` →
line 41) and the guard returned to **10 passed**. The guard is therefore proven to detect the
defect it exists to catch, not to pass on any implementation.

The guard also carries a **second, independent** control: it executes the *pre-repair body*
verbatim through the same Node probe and asserts that body renders the same wall-clock in
`America/New_York` and `Asia/Kolkata` — i.e. that the defect reproduces — while the shipped
module disagrees with it. A control that reproduced nothing would make the property vacuous.

## 4. Baseline comparison (one full-suite pass, on pristine `main`)

Run **once**, on the stashed (pristine) `main` tree, per the pulse contract:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
8 failed, 2985 passed, 20 skipped, 2 warnings, 1 error in 207.38s (0:03:27)
```

The failing/error **node set** (the baseline, not the counts) — 9 nodes, recovered from
`pytest`'s own `lastfailed` cache rather than a second run:

```
tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
tests/test_autonomy.py                                   # CE-01 module-vs-package collision
tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

All nine are **pre-existing `main` debt**, unrelated to this slice, and none is repaired here.
Attribution is by node identity, never by totals: the branch tree collects **3022** nodes against
the baseline's **3012** — a **+10** delta that is exactly the new guard's node count
(`--collect-only` on both trees, same environment). The `+10 passed` is therefore attributable,
not a coincidental total.

`api/main.py` is untouched by this slice and its budget is unaffected. The frontend build input
set changed, so `python -m py_compile api/main.py` is not applicable to this pass.

## 5. Contract, ownership and overlap

- **Backend contract:** unchanged and already verified — `GET /api/commune/threads` and
  `GET /api/commune/threads/{uuid}/messages` in `api/commune_threads.py`, identity-scoped. This
  slice is display-only and issues no request; the read-only ceiling asserted by
  `test_prism_w4_arkana_thread_history.py` still holds (no mutating method is introduced).
- **Ownership:** every changed path is Lane 4's own — `src/components/arkana/**` and a
  lane-4 test. No shared file (`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`, `types.ts`,
  `SurfaceLenses.tsx`, shared shell tests, `SHARED-CONTRACTS.md`, `AGENTS.md`) is touched.
- **Overlap scan:** zero open PRs modify any changed path. Checked the Lane-4 cohort —
  #531 (`api/commune_threads.py`, `tests/test_arkana_thread_history_contract.py`), #530, #525,
  #524, #512, #515, #504, #501 — none touches `ArkanaThreadHistory.tsx`,
  `arkanaThreadsContract.ts`, or `arkanaThreadTime.ts`. `git cat-file` over every remote branch
  shows `arkanaThreadTime.ts` exists on none, so no lane has already carried this slice.
- **Gate selection:** `scripts/console_contract_domain.py` derives its domain from
  `git ls-files` at run time; the new guard names `web/arkadia_console` and so joins the domain
  automatically, which is asserted from the gate's own output by
  `test_the_guard_is_selected_by_the_console_contract_domain`. No workflow edit was needed.

## 6. Unresolved / next bounded move

- **Not claimed:** production behaviour. No runtime observation of the console was made, and the
  repaired reading has not been seen in a deployed bundle. `readableTime` is proven at module
  level and by build only.
- **Pre-existing `main` debt** (the nine nodes above) is recorded, not repaired — including the
  two `tests/test_engineering_lab_api.py` authority pins, which are a separate bounded workstream.
- **Next bounded move (Lane 4):** the Agent-04 brief's primary continuation — the
  run-to-evidence trace view over the Lab's session/run/work-event/evidence records, read-only,
  distinguishing run completion from evidence existence and verification from human acceptance.
- **Branch-map update** is requested from Workstream 1 in the PR comment, not performed here:
  `SHARED-CONTRACTS.md` §1 is coordinator-owned and Lane 4 must not edit it.
