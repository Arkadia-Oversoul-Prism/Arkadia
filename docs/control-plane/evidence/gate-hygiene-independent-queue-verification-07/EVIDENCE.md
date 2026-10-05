# Gate hygiene — independent verification of open PR cluster #267/#268/#270/#271/#273/#274

- **Mode**: read-only, evidence-only. No source, test, or policy file modified.
- **Constraint honoured**: no merge, no push to `main`, no PR modified. This record is
  published on a dedicated branch → PR for human merge.
- **Observed**: 2026-10-04T23:06Z (automation run).
- **Environment**: full clone (not shallow), Python 3.13 / pytest 9.1.1, FastAPI 0.142.2,
  node v24.21.0 + corepack/pnpm.
- **Independence**: every claim below was re-derived locally in this environment. CI check
  conclusions are reported separately from local measurements and are never promoted into
  production/runtime truth.

---

## 1. Reconstructed state

| Ref | SHA | Note |
|---|---|---|
| `main` (origin) | `2b87e8efdbcbd777def07bb71c720e5b234ae6ac` | `canon: make Arkadia Oversoul Prism the canonical system identity (#276)` |
| recorded baseline | `89f9e78` | the revision the queue's evidence documents claim to measure |
| PR #267 head | `51b0a3f4` | docs-only |
| PR #268 head | `ab427481` | docs-only |
| PR #270 head | `1a264efe` | solspire/buyer_recon + opportunity radar |
| PR #271 head | `6598c26d` | docs-only |
| PR #273 head | `93ea19549aab` | ArkanaWeaverCanvas |
| PR #274 head | `0239ff110c1d` | commune threads / ArkanaCommune |

Ancestry verified: `ca67b006` and `89f9e78` are both ancestors of `main`.

---

## 2. Baseline and main fingerprints (re-measured, not inherited)

Command, both trees: `python -m pytest tests/ -q -rEf`

| Tree | Result | Nodes |
|---|---|---|
| `89f9e78` (recorded baseline) | 9 failed / 1426 passed / 17 skipped / 1 error | **10** |
| `main` `2b87e8ef` | 10 failed / 1425 passed / 17 skipped / 1 error | **11** |

- outcomes fingerprint `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38`
- ids fingerprint `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f`
  (matches the canonical value recorded in `AGENTS.md`)

Full `main` node set:

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_compress_to_choices
```

**main regression (attributed to #276, merge `2b87e8ef`).** Node-set diff against the
recorded baseline is exactly `+1 / -0`:
`tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points`.
No node was fixed. Attribution to the `canon:` identity commit is by node identity, not by
count delta.

---

## 3. PR #270 — CONTRADICTED (severe defect, #275's allegation independently reproduced)

**Allegation (PR #275): a severe defect exists in #270.** Independently confirmed, and the
mechanism is more precise than "a test errors".

### 3.1 Root cause

`solspire/buyer_recon_router.py` adds a symbol that does not exist:

```diff
-from api.auth import require_auth
+from api.auth import require_auth, require_project_owner
```

Measured fact: `require_project_owner` is defined in **`solspire/console_router.py:68`** and
nowhere in `api/auth.py` — on `main` **or** on the #270 head. The import is unsatisfiable.

### 3.2 Blast radius — the whole SolSpire Console router is lost, silently

`solspire/console_router.py:45` imports `buyer_recon_router`, so the bad import propagates:

```
PR270 import FAILED: ImportError cannot import name 'require_project_owner' from 'api.auth'
```

`api/main.py:332-337` mounts that router inside a **bare `except Exception`** that only
logs a warning:

```python
try:
    from solspire.console_router import router as _solspire_router
    app.include_router(_solspire_router)
    logger.info("[SOLSPIRE] Console kernel router mounted at /solspire")
except Exception as _ss_err:
    logger.warning(f"[SOLSPIRE] Console router mount skipped: {_ss_err}")
```

Consequence, measured by counting mounted routers on the composed app:

| Tree | `len(app.routes)` | mounted `_IncludedRouter` | SolSpire Console |
|---|---|---|---|
| `main` `2b87e8ef` | 55 | **15** | mounted |
| PR #270 `1a264efe` | 54 | **14** | **silently dropped** |

This is **not a test-only failure**. On #270 the application **boots and serves without the
entire SolSpire Console surface**, emitting only a warning line. This is the same failure
class as the P1-A incident recorded in `AGENTS.md`: a boot-path exception suppressed rather
than surfaced.

### 3.3 Local node-set delta on #270

`+4` nodes versus `main`, none of them fixed:

```
ERROR  tests/test_solspire_ownership.py                       (collection error)
FAILED tests/test_android_console_contract.py::test_console_client_paths_exist_on_the_served_app
FAILED tests/test_weaver_w4.py::test_solspire_weaver_routes_owner_isolation
FAILED tests/test_weaver_w5.py::test_http_knowledge_isolation
```

`tests/test_solspire_ownership.py` passes on `main` (51 passed) and **errors** on the #270
head. The other three are the observable symptoms of the dropped router.

### 3.4 CI contradiction

PR #270's `weaver-mvp2-validation` and `validate` checks are recorded green while the tree
carries the defect. Both run **named** test files only (§5), none of which import the
console router. Green CI on #270 is therefore **scoped to those files** and does not attest
to the tree.

---

## 4. PR #273 — CONTRADICTED (build-breaking unresolved import)

- `tests/test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_the_canvas_into_the_project_dashboard`
  → **FAILED (FileNotFoundError)**. The guard pins
  `web/public_prism/src/components/solspire/ArkanaWeaverCanvas.tsx`, which is absent.
- Independent real build (`corepack pnpm build` in `web/public_prism`):

```
Could not resolve "../components/solspire/ArkanaWeaverCanvas" from "src/pages/ProjectDashboard.tsx"
2328 modules transformed — build FAILED (3.19s)
```

#273 is not mergeable: the frontend does not compile.

---

## 5. Why no gate caught Defect A / Defect B — coverage gap (the root hygiene finding)

**No workflow in this repository runs the full test suite.**

- `.github/workflows/weaver-mvp2-validation.yml:55` contains a `python -m pytest -q`
  *inside a folded block* — the effective command is the seven explicitly named files
  `tests/test_weaver_mvp2_05.py tests/test_weaver_mvp2_07.py
  tests/test_evidence_verification_boundary.py tests/test_workevent_evidence_boundary.py
  tests/test_verification_review_boundary.py tests/test_execution_workevent_boundary.py
  tests/test_authority_boundary.py`. The bare form is a **folded scalar, not an executed
  command** — reading it as "the full suite runs in CI" is the mis-diagnosis to avoid.
- Every other workflow names individual files (path-filtered, e.g.
  `solspire-project-execution.yml`).

Scale: **42** test files are named anywhere in `.github/workflows/*.yml` against **179**
`tests/test_*.py` files on disk. No failing/defect node in this report is inside the
covered set:

| Node | Covered by CI? |
|---|---|
| `tests/test_solspire_ownership.py` | **UNCOVERED** |
| `tests/test_weaver_w4.py` | **UNCOVERED** |
| `tests/test_weaver_w5.py` | **UNCOVERED** |
| `tests/test_android_console_contract.py` | **UNCOVERED** |
| `tests/test_ais_capability_profile_onboarding.py` | **UNCOVERED** |
| `tests/test_arcana_weaver_fusion.py` | **UNCOVERED** |

The coverage gap is the mechanism that lets a green PR carry a build-breaking import and a
silently-dropped production router. The green check is real; its scope does not reach the
defect.

---

## 6. Remaining queue — no regression introduced

| PR | Head | Changed files | Verdict |
|---|---|---|---|
| #267 | `51b0a3f4` | 2 docs | IMPLEMENTED — docs-only, no code surface |
| #268 | `ab427481` | 1 docs | IMPLEMENTED — docs-only, no code surface |
| #271 | `6598c26d` | 2 docs | IMPLEMENTED — docs-only, no code surface |
| #274 | `0239ff11` | `api/commune_threads.py`, `ArkanaCommune.tsx`, `WorkspaceActionSurfaces.tsx` | IMPLEMENTED — **no regression** |

#274 evidence:
- `python -m py_compile api/main.py api/commune_threads.py` → OK
- Surface tests on the #274 head: `1 failed, 24 passed`. The single failure
  `tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` is
  **identical on `main`** (same 1 failed / 24 passed) — pre-existing main debt, not a #274
  delta.
- Independent frontend build on the #274 head: `corepack pnpm build` → **EXIT=0**,
  `✓ built in 7.01s`.

---

## 7. Defect register

| ID | PR | Class | Statement | State |
|---|---|---|---|---|
| D-07-1 | #270 | boot-path / severe | `require_project_owner` imported from `api.auth` where it is not defined; `console_router` import fails; bare `except Exception` silently drops the **entire SolSpire Console router** (15 → 14 mounted routers) while the app still boots | CONTRADICTED |
| D-07-2 | #270 | test | `tests/test_solspire_ownership.py` errors on collection (passes on `main`) | CONTRADICTED |
| D-07-3 | #273 | build | Unresolved import `../components/solspire/ArkanaWeaverCanvas`; frontend build fails; guard test FAILED | CONTRADICTED |
| D-07-4 | #276 → `main` | regression | `main` gained exactly one failing node (`test_home_is_offer_led_and_keeps_arkadia_entry_points`), zero fixed | CONFIRMED |
| D-07-5 | CI (all) | gate coverage | No workflow runs the full suite (179 files on disk vs 42 named); none of the defect nodes is CI-covered | CONFIRMED |

---

## 8. Classification

- **#270**: CONTRADICTED — must not merge. Defect is boot-path, not test-only.
- **#273**: CONTRADICTED — must not merge. Frontend does not compile.
- **#274**: IMPLEMENTED, no regression — safe for sovereign review.
- **#267 / #268 / #271**: docs-only, no code surface.
- **`main` `2b87e8ef`**: carries one new failing node attributable to #276.
- **Gate coverage (D-07-5)**: CONFIRMED gap; the reason green CI and a broken tree coexist.

## 9. Proposed bounded next work (NOT executed — requires sovereign authorization)

1. Repair `solspire/buyer_recon_router.py` import on #270 (source change; separate PR).
2. Repair #273 canvas component/import (source change; separate PR).
3. Narrow the bare `except Exception` around router mounts in `api/main.py` so a mount
   failure is surfaced at boot instead of silently dropping a surface (constitutional
   boot-path surface — needs explicit authorization).
4. Make at least one CI workflow run the full suite (or the uncovered node set) so the
   coverage gap in §5 closes. Highest-leverage hygiene fix.

Each is a distinct bounded workstream. None is begun here.
