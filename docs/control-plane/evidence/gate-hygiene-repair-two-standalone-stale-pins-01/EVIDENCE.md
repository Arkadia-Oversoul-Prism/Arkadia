# Two standalone stale pins, and the silent production `ReferenceError` they were hiding

**Workstream:** `gate-hygiene` (test-side literal pins / frontend runtime)
**Bounded question:** Two full-suite failures are standalone — no open PR owns them
(`test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`,
`test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key`). Are they
test-side stale pins, or do they indicate a production defect? What is the minimal repair?
**Classification:** `IMPLEMENTED` (one production fix + two test-side re-pins).
**Base:** `main` @ `24a00f856a0286cbb464a4b585117dd57a2646fa` (`BASE_MAIN`, observed 2026-10-08T22:06Z)
**Branch:** `gate-hygiene/repair-two-standalone-stale-pins`

---

## 1. Answer

Both failures are test-side stale pins. The second one was **standing on top of a genuine
production defect** that no test asserted:

`web/public_prism/src/pages/NodeEntry.tsx` referenced the identifier `AIS_PROFILE_PATH` in
**two** places (the mount `useEffect` and the `finish()` PATCH) but **never defined it**. The
file instead defined `AIS_URL` from `API_BASE` — and used `AIS_URL` **zero** times. Vite does
not type-check, so this shipped as a runtime `ReferenceError`. The `useEffect` body is wrapped
in `try{...}catch{}`, so the throw was swallowed and the mounted surface silently failed to
read or write the A.I.S capability portfolio.

Measured on the base revision, `NodeEntry.tsx`:

```
AIS_PROFILE_PATH  occurrences: 2      definitions (`const AIS_PROFILE_PATH =`): 0
AIS_URL           occurrences: 1      uses: 0      API_BASE occurrences: 2
```

## 2. Why each pin cannot be satisfied

`test_identity_spine_w1.py:20-27` demanded `"Let's form your node."`, `"Form my node"`,
`"AIS_CAPABILITIES"` and `"GROVE_DOMAINS"`. None is satisfiable and none ever was:

- The live surface carries the A.I.S copy `"Let's see what feels like you."` — the diagnostic
  CTA copy the pin names had already been replaced when the assertion landed.
- `NodeEntry` never imported the Grove catalogue. `test_ais_w2_living_gate_grove_handoff.py`
  already **escalates** that question as a product decision rather than auto-repairing it, so
  forcing the import here would silently take a decision the repository has deliberately left
  open. This pass does not take it.

`test_m02_reasomate_truth.py:165` demanded `"arkanaSessionId"`. Commit `1f872f0` ("feat: wire
Arkana Commune to first-class threads") replaced that call with a shared `ACTIVE_THREAD_KEY`
plus a per-project derived `threadStorageKey`, so the literal cannot occur again. The property
the node names — *one shared, longitudinal conversation* — still holds and is now pinned
directly against the constants that actually implement it.

## 3. Change

**Production** (`web/public_prism/src/pages/NodeEntry.tsx`): define `AIS_PROFILE_PATH =
'/api/me/ais-profile'` and drop the dead `AIS_URL`/`API_BASE` import. `apiFetch` resolves the
base URL itself, so the local `${API_BASE}/…` string was both unused and the wrong shape for
the transport actually in use.

**Test-side** (`tests/test_identity_spine_w1.py`, `tests/test_m02_reasomate_truth.py`): re-pin
each assertion to the property it names, with the superseded literal preserved verbatim in a
comment so the prior revision stays reconstructable.

## 4. Measurements

Both full-suite runs used `-rEf --continue-on-collection-errors` (a `-rf`-only fingerprint is a
subset — see `AGENTS.md`), same environment, same tree except this change:

```
BASE_MAIN 24a00f85 : 16 failed / 1775 passed / 19 skipped / 1 error   17 nodes
BRANCH             : 14 failed / 1777 passed / 19 skipped / 1 error   15 nodes
```

Sorted `FAILED`/`ERROR` node-set delta:

```
base-only   tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
base-only   tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
branch-only (new regressions)  <none>
```

`-2 failed / +2 passed / 0 new nodes`. Node-set sha256 — base
`26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798`, branch
`9a6239ae3aeb4a51d7629ff5a1cd65faaea461b3f1eb697171c84fcd6b01e8c1`. The delta is exactly the
two repaired nodes.

Protected surfaces: `tests/architecture` **11/11 passed** (not 9/10 — the contract's older
figure is superseded, per `AGENTS.md`). `python -m py_compile api/main.py` **OK**; `api/main.py`
**2462** lines, within the 2600 budget and untouched by this pass.

Frontend: `corepack pnpm install` **exit 0**; `corepack pnpm build` **exit 0**, `3447 modules
transformed`, `built in 7.02s` (the contract's "environment-blocked" is superseded in this
environment).

## 5. Not repaired here (recorded, not silently fixed)

- `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` —
  explicit governance decision not to re-pin. Untouched.
- The `AIS_CAPABILITIES`/`GROVE_DOMAINS` question on `NodeEntry` — a product decision, already
  escalated in-repo.
- `test_autonomy.py` collection error (`weaver.autonomy` module-vs-package collision, CE-01) —
  reserved to the sovereign.
- Owned by open PRs, measured with `GET /pulls/{n}/files` — do not duplicate:
  #357 (`test_solspire_r1_governance_convergence`, `test_solspire_r3_execution_runtime`),
  #356 (`test_engineering_lab_api`), #355 (`test_ci_gate_trigger_coverage` via
  `n-atlas-developer-lab.yml`), #347 (`test_ais_capability_profile_onboarding`),
  #354 (`test_m02a_ci_gate_integrity` via `cp10_mutation_boundary_policy.py`).
- Unowned pre-existing `main` debt: `test_steward_filter` (3 nodes),
  `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate`.

## 6. Uncertainty

`AIS_PROFILE_PATH` is exercised at runtime only against an authenticated A.I.S profile endpoint;
this pass proves the identifier is now defined and the file compiles, not that the portfolio
round-trip succeeds end to end. No production/runtime parity claim is made.
