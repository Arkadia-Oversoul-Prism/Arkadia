# EVIDENCE — gate-hygiene/economic-seam-authority-pin-01

Gate: GATE-10 / gate-hygiene (human-authority boundary pin)
Branch: `gate-hygiene/economic-seam-authority-pin-01`
Base main: `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
Observed: 2026-10-10
Authority: evidence + test only. No merge, no product behaviour change, no push to `main`.

## 1. Reconstruction (live, this pass)

- Clone present, on `main` @ `f9ced6b6` = `origin/main` = `origin/HEAD` (real commit).
- Live full suite (canonical command, see §4): **15 failed / 1854 passed / 20 skipped / 1 collection error**.
- Architecture: **11 passed**.
- Boot code: `python -m py_compile api/main.py` OK; `api/main.py` = **2450** lines (budget 2600).
- Open PRs: 40+ (see §6 queue reconciliation).

## 2. Defect (measured, not asserted)

The sovereign economic-seam surface was merged by `f9ced6b6` ("Expose sovereign economic
seam scan in canonical Opportunity Radar") on top of `2a8f3c32` ("Repair economic seam
provider evidence paths"). Its contract is **sovereign-only**: the UI hides the action
behind `isSovereign` (`access_level >= 3`, `web/public_prism/src/contexts/AuthContext.tsx:223`),
and the server dependency is `require_sovereign` (`api/economic_seam_routes.py`).

**No test reached the router.** `grep -rln "economic_seam_routes" tests/` → 0 matches;
the only suite touching economic seams, `tests/test_market_data.py`, drives
`engine._scan_*` helpers directly and never constructs the router. A later refactor could
swap `require_sovereign` → `require_auth` on `POST /api/economic-seams/scan` or
`/assess` — silently widening a sovereign mutation surface to every authenticated node —
without reddening the suite.

The prohibition in `AGENTS.md` is explicit: *"Never declare VERIFIED without runtime
evidence"* and the ARK-01 precedent (*"a frozen schema that nothing validates against is
not a contract"*). An authority boundary that no test exercises is the same class.

## 3. Change

New file: `tests/test_economic_seam_authority_boundary.py` (9 tests).

- Structural pins: `POST /scan` and `POST /assess` depend on `require_sovereign`;
  `GET /status` and `GET /opportunities` depend on `require_auth` (not sovereign).
- Behavioural pins: no token → **401** and `scan_once` never called; authenticated
  non-sovereign → **403** and `scan_once` never called; sovereign → **200** with the
  action's result.
- Negative control (`test_detector_is_not_self_satisfying`): a route built with
  `Depends(require_auth)` is reported as `require_auth`, proving the structural detector
  fires on the weakened form it claims to detect.
- Positive control (`test_detector_resolves_sovereign_when_present`): a route built with
  `Depends(require_sovereign)` is reported as `require_sovereign`.

Empirical pre-check that grounds the pins (200 only for sovereign; 401 without a token;
401 when only `require_auth` is overridden and the sovereign gate stays live):

```
scan no-auth: 401
status no-auth: 401
scan sovereign-override: 200
scan with ONLY require_auth overridden (sovereign gate live): 401
```

## 4. Verification

Canonical command:
`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors`

| Check | main @ f9ced6b6 | branch | result |
|---|---|---|---|
| full-suite failing/error node set (sha256) | `facc29a91e12fa3437362c6c4d40ac837393da7f4856c1bf018795d1032f87ed` | `facc29a91e12fa3437362c6c4d40ac837393da7f4856c1bf018795d1032f87ed` | **identical**, zero regression |
| passed | 1854 | 1863 | +9 = exactly the new file |
| tests/architecture | 11 passed | 11 passed | unchanged |
| `py_compile api/main.py` | OK | OK (untouched) | unchanged |

The load-bearing check is node **identity**, not totals: the sorted `FAILED`/`ERROR`
node list hashes identically on both trees.

## 5. Authority / scope

- No product code, workflow, `api/main.py`, mutation path, or authorization path changed.
- Human merge required. This PR does **not** merge and does **not** authorize.
- Not claimed: the two sovereign-reserved baseline nodes (F-01 LivingGate persistence
  proxy; CE-01 `weaver.autonomy` module-vs-package) remain failing by design and are out
  of scope here.

## 6. Open-PR ownership map (measured live this pass)

Ownership was derived by querying each open PR's changed-file list
(`gh pr view <n> --json files`) and matching it to the failing node's file. Do not
restate an owner from prose — re-measure.

| failing node | owning file | owner PR (measured) |
|---|---|---|
| `test_m02a_ci_gate_integrity.py::test_allowlist_*` (3) | `tests/test_m02a_ci_gate_integrity.py` | **#388** (not #354 — #354 does not change this file) |
| `test_solspire_r1_governance_convergence.py::*` (2) | `tests/test_solspire_r1_governance_convergence.py` | #357 |
| `test_solspire_r3_execution_runtime.py::*` (1) | `tests/test_solspire_r3_execution_runtime.py` | #357 |
| `test_engineering_lab_api.py::*` (2) | `tests/test_engineering_lab_api.py` | #356 |
| `test_steward_filter.py::*` (3) | `tests/test_steward_filter.py` | #365 |
| `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | `tests/test_m02_reasomate_truth.py` | #363 |
| `test_identity_spine_w1.py::test_node_entry_*` | `tests/test_identity_spine_w1.py` | #363 |
| `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_*` | `tests/test_ais_capability_profile_onboarding.py` | #347 |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | — | **none** — F-01, sovereign-reserved (proxy invalidation, documented in-test) |
| `ERROR tests/test_autonomy.py` | — | **none** — CE-01, `weaver.autonomy` module-vs-package collision, sovereign-reserved |

Every failing/error node on `main` is owned by an existing open PR except the two
sovereign-reserved nodes above, so no unowned baseline repair exists. The economic-seam
authority boundary is likewise unowned: `git log -- api/economic_seam_routes.py` shows it
last touched by `f0b4c212` / `84381e1b` / `8b3b2bca` (already on `main`), and no open PR
changes that file (#373 touches only `economic_seams/engine.py`,
`economic_seams/market_data.py`, and its workflow). The smallest genuine unowned bounded
task is therefore the authority pin in §3.
