# EVIDENCE — gate-hygiene/baseline-reconciliation-recovery-frontend-build-01

Bounded workstream: **baseline reconciliation** on `main`, plus the evidence-backed
**recovery of one stale environment claim** (`vite build := environment-blocked`).

This pass makes **no source, test, or policy change**. The only file added is this evidence
directory. Every remaining open queue item is classified as needing a product, architectural,
or sovereign decision, so none is executed here (contract rule: `NO SELF-EXPANSION`).

## 1. Reconstruction (live evidence, not prose)

| item | value |
|---|---|
| canonical repo | `https://github.com/Arkadia-Oversoul-Prism/Arkadia` |
| BASE_MAIN (origin/main) | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| latest commit subject | `Merge pull request #261 ... authority-boundary-control-case-identity-01` |
| open PRs | **0** (`GET /pulls?state=open` -> `[]`) |
| CI runs on BASE_MAIN (full 40-char SHA) | 2, both `success` (`_diagnose_blank_frontend` push, `security-secret-scan` push) |
| working tree | clean at start; only this evidence dir added |

Observation timestamp: `2026-10-04T09:06Z` (automation run).

## 2. Live baseline measurements (this environment, python 3.13)

| gate | command | measured |
|---|---|---|
| architecture | `python -m pytest tests/architecture -q` | **11 passed** (11/11) |
| full suite | `python -m pytest tests/ -q --continue-on-collection-errors` | **9 failed / 1414 passed / 20 skipped / 1 error** in ~126s |
| collection error | (same) | `tests/test_autonomy.py` — `ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'` |
| failure node-set sha256 | `... -rf \| grep -E '^(FAILED\|ERROR)' \| sort \| sha256sum` | `00b3984e7ad487f1c36e1449429834cdf398f5dde8d4591f4079942c180af48b` |
| `api/main.py` | `wc -l` + `python -m py_compile` | **2582 / 2600** lines, compiles OK |
| AGENTS.md encoding audit | `python scripts/agents_md_encoding_audit.py` | `Cyrillic 0`, `oracle_reproduced=True`, `alterations=0`, exit 1 (clean + oracle-corroborated) |
| CP10 mutation boundary | `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, RC 0 |

The 9 failing node names (identical set to PR #260's accepted baseline; only the
`SH-08` control-case node has been repaired since, so the set is unchanged):

1. `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` — `F-01`, proxy-invalidation, **left failing on purpose** (see section 4)
2. `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`
3. `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` — `SH-07`
4. `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver`
5. `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical`
6. `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
7. `test_steward_filter.py::test_blocks_identity_claims` — `SH-06`
8. `test_steward_filter.py::test_allows_mythic_with_action` — `SH-06`
9. `test_steward_filter.py::test_compress_to_choices` — `SH-06`

## 3. Recovery: `vite build` is NOT environment-blocked here

`.bootstrap/BASELINE.json` records `vite_build := environment-blocked`, and ~15 evidence
files carry `environment-blocked (no npm registry access)`. **Measured contrary:**

```
cd web/public_prism
corepack pnpm install   -> Done in 5.8s using pnpm v10.26.1   (registry reachable)
corepack pnpm build     -> vite v5.4.21, 3443 modules transformed, built in 6.96s, exit 0
```

`node v24.21.0`, `corepack 0.36.0`, `packageManager: pnpm@10.26.1` — matching the AGENTS.md
tooling note. This *supersedes* the stale claim **for this environment**. It does **not**
retroactively make any historical BUILD-GREEN claim true: `pnpm build` with no output-diff
gate does not measure anything a frontend change does. The corrected fact is only
"build is runnable here", not "build is green on a specific change".

Note: the build writes untracked `dist/`; `git status --porcelain` confirms the tracked tree
stays clean (`web/public_prism/dist/` is gitignored).

## 4. Every remaining failure is classified — none is a safe test-side repair

| # | node | bucket | why not repaired here |
|---|---|---|---|
| 1 | `test_no_firebase_persistence_in_gate` | `F-01` proxy-invalidation | The test body **already documents** it as a sovereign decision: the gate carries zero `firebase`/`firestore` references, but the `sessionStorage` proxy no longer measures that intent (`LivingGate.tsx` uses `sessionStorage` for the tab-scoped `arkadia.ais.diagnostic-handoff.v1` handoff). Re-pinning would loosen a persistence boundary. |
| 2 | `test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | DRIFT | Reads `web/public_prism/src/pages/NodeEntry.tsx` (now an ESM module, `grep` count 0 for `AIS_CAPABILITIES`, `GROVE_DOMAINS`, and for both copy literals). The AIS signup surface effectively moved to `LivingGate.tsx` (`AIS_CAPABILITIES`, `GROVE_DOMAINS`, `/api/me/ais-profile`). Whether the old literals are retired or a route/component split must return is an identity/product call — the ledger already marks this file group W8 canonical-identity territory. |
| 3 | `test_oracle_runtime_uses_the_shared_session_key` | `SH-07` DRIFT (high) | Genuine unmet architecture — Oracle/ReasoMate shared-session keying. No `arkanaSessionId`; not a copy string. |
| 4 | `test_r1_solspire_builders_delegate_to_weaver` | DRIFT / product | `solspire` emits `mvp1-50c0ee9b89`; test expects the canonical `weaver` spec `mvp1-r1-patch`. Which producer is canonical is a product decision, not a test edit. |
| 5 | `test_r1_weaver_governance_is_canonical` | DRIFT of test-vs-consolidation | Asserts `execute_patch` is *sourced* in `weaver.governance`; the module's `__all__` no longer includes it (`build_patch_approval`, `build_pass_spec_for_patch`, `evaluate_patch_readiness` are present, and `execute_project_patch` lives in `solspire.project_execution`). Whether `execute_patch` must appear in `weaver.governance` (and how it reconciles with `solspire`'s R2/R3 "no mutation/authority via SolSpire" boundaries) is an architecture/authority call. |
| 6 | `test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | CONTRACT | The runtime **does** block `fs_write` (it raises `PermissionError` "Engineering mutation is disabled ... K15 -> K3"), but the test expects a *returned* `execution.results[0]["code"] == "MUTATION_DISABLED"`, not a raise, at `solspire/execution_runtime.py:115`. Whether the contract is "block by returning a result record" or "block by raising" is a design decision. |
| 7-9 | `test_steward_filter.py` (3) | `SH-06` product judgement | `steward_filter("You have transcended")` returns the text; the blocklist has `"transcendent"` (stem), not `"transcended"`. `test_compress_to_choices` fails because `compress_to_choices` filters on `action_verbs` (`do, choose, quit, maintain, release, adjust, continue`) while the test expects the `steward_filter` action words (`act`, `decide`). `test_allows_mythic_with_action` fails because the mythic-density rule blocks `"The field resonates. I will do this."`. Copy, stem-matching policy, and density are all product decisions. |

Consistent with the prior workstream state: **the pre-authorized test-hygiene envelope is
exhausted.** Repairing any of 2-9 would substitute agent judgement for a sovereign/product
decision, which the contract forbids.

## 5. Explicitly out of scope (recorded, not touched)

- `api/main.py` duplicate OpenAPI Operation IDs in `api/lab_routes.py` (e.g.
  `model_gateway_api_lab_engineering_gateway_get`) — lab-routes contract, not this pass.
- The `tests/test_autonomy.py` collection error (`weaver.autonomy` module/package collision) —
  pre-existing, reserved (CE-01).
- `SH-03` (`"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"`) — awaits product decision.
- `SH-05` (`test_gate_serve_script` / `test_gate_status`) — awaits sovereign call.

## 6. Regression boundary

No tracked file changes; therefore **no code-level regression is possible from this pass**.
The measured node-set fingerprint `00b3984e...` is the value a follow-on bounded branch must
compare against.

## 7. Status

**VERIFIED** (reconciliation) — measurements are live, reproducible, and recorded.
The one recovery is a **measured environment fact**, not a code change. Authorization
required: sovereign review of this evidence PR. Merge authority: human sovereign only.

## 8. Evidence commands (reproduce)

```bash
git fetch --all --prune && git log -1 --format='%H' origin/main
python -m pytest tests/architecture -q
python -m pytest tests/ -q --continue-on-collection-errors -rf
cd web/public_prism && corepack pnpm install && corepack pnpm build
python scripts/agents_md_encoding_audit.py
git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge
wc -l api/main.py && python -m py_compile api/main.py
```

---

## 9. ADDENDUM — independent re-measurement (Pass 2, `2026-10-04T10:0xZ`)

This is an **evidence-only** addendum. No source, test, or policy file changed; the working
tree is clean and the diff for this pass is this file only.

### 9.1 What was independently reproduced

Every headline number in sections 1-3 was re-derived here from live evidence, not inherited
from the PR body. Method note: a **depth-1 (shallow/grafted) clone** was used, which changes
the resolvable revision set and therefore the *node set* — see 9.2.

| gate | PR claim | independent re-measure | agreement |
|---|---|---|---|
| architecture | 11/11 | **11 passed** | ✅ |
| frontend build | exit 0, 3443 modules | `corepack pnpm install` + `corepack pnpm build` → **exit 0, 3443 modules, 6.99s** | ✅ |
| `api/main.py` | 2582 / 2600, compiles | **2582 / 2600**, `py_compile` OK | ✅ |
| CP10 boundary | PASS RC 0 | **PASS (RC 0)** over `git ls-files` | ✅ |
| AGENTS.md audit | Cyrillic 0, `alterations=0`, exit 1 | with oracle `6c43218a48a4` present: **Cyrillic 0, `inserted=537 alterations=0 reproduced=True`, exit 1** | ✅ |
| `web/public_prism/dist/` | untracked | `git ls-files` → **0 paths**; build leaves a clean tracked tree | ✅ |
| open PRs on base | 0 | **1** (this PR #262) | ⚠ superseded — #262 opened after section 1 was written |

### 9.2 The full-suite count is clone-depth dependent — and that is now pinned

The PR's section 2 measured **9F / 1414P / 20S / 1E** (`00b3984e…`). A bare shallow clone
measures **13F / 1409P / 21S / 1E**; the whole delta is 4 extra failures in
`tests/test_agents_md_encoding_adjudication.py`, whose fixtures resolve the pinned revisions
`ORACLE_REV = 6c43218a48a4`, `CORRUPTION_COMMIT = e0dde9ad9c5e`, and (for the depth-dependent
sibling) `GATE2_PARENT_REV = 7d79f38bd520…`. **Fetching those three revisions collapses the
delta to 2, then to 1.** The single residual node,
`test_corruption_origin_is_re_derivable`, walks `git log -- AGENTS.md` over all history and
cannot be satisfied by any depth-1 clone — it is a clone-depth artifact, **not a regression**.

Measured on the best-covered clone available to this pass:

```
10 failed, 1416 passed, 17 skipped, 1 error   (~126s)
FAILED/ERROR node-set sha256 = 6ca42572174af4550f35c33d5101467aa5ddb2de514a304f861036b067dc72c5
```

Of those 10, **9 are the PR's own classified set** (section 4) with the same names; the 10th
is the clone-depth node above. The 1 error is the documented `tests/test_autonomy.py`
(`weaver.autonomy` module/package collision, CE-01). **No node in the PR's 9-failure set is
absent here, and no new non-clone-depth failure appears.**

The practical consequence: the load-bearing claim is the *node identity set*, not the count.
A future pass should fetch `6c43218a48a4`, `e0dde9ad9c5e`, `7d79f38bd520…` before comparing,
or attribute a count delta to clone depth rather than a code regression.

### 9.3 NEW material fact — production deploy boundary (Gate 2), not previously recorded

Re-derived from the deployments API (full 40-char SHAs; never `?head_sha=` abbreviated):

- Current `main` `1b7c089f237a1a8ea11791ab060525b0e36e2029` carries a **Vercel commit status of
  `failure`** on *both* contexts, with description **"Deployment rate limited — retry in 24
  hours."** This is a **provider-side build rate limit**, not a code/build failure. It is why
  the PR head's combined status reads `failure` while its own check-runs
  (`Vercel Preview Comments`, `Full-history secret scan`) are `success`.
- The **`Vercel – arkadia-prism` production deployment of `fa1b40787544` SUCCEEDED**
  (`environment_url` `https://arkadia-prism-8q6k5qyn9-arkadia-prism.vercel.app`); the console
  project deployment of the same SHA failed. Production is **5 commits behind** `main`.
- Those 5 commits (`fa1b4078 → 1b7c089f`) touch **only `docs/` (5) and `tests/` (1)** — the
  compare API reports **zero** `web/public_prism/src`, `package.json`, or `vite` build-input
  changes. Therefore the deployed frontend artifact is **source-identical to `main`** on the
  frontend lineage, even though the ref is 5 behind.
- Consequence for the Gate-2/P1-A standing trajectory: the current `main` Vercel status is a
  **provider boundary** (`BLOCKED` on rate limit), and the older "arkadia-prism must be
  investigated" reading is superseded — the arkadia-prism production deploy is `success`. This
  is a **runtime/deployment observation**, not a source claim; it does not by itself close Gate
  2 (production acceptance remains a sovereign act) and it must not be promoted to parity
  without a read of the deployment-specific URL (protected by Vercel SSO).

- **Caution for the next pass — the `?environment=production` filter is exact-match and misses
  the current deploy.** `fa1b40787544` is labelled `Production – arkadia-prism` /
  `Production – console` (project-suffixed), so
  `GET /deployments?environment=production` returns only older, unsuffixed entries
  (top: `57e67c534ff6`, 2026-10-02) and **`?sha=fa1b40787544` returns 0 rows**. The correct
  current-production query is `GET /deployments?per_page=10` (unfiltered) and read the newest
  `Production – *` rows; their statuses resolve via `/deployments/<id>/statuses` —
  `6838852040` (`fa1b4078`, arkadia-prism) = **success**, `6838848273` (console) = **failure**.
  Do not conclude "no production deploy" from the filtered 0-row result.

### 9.4 Classification of this addendum

**VERIFIED (reconciliation)** — reproduced measurements, a pinned clone-depth explanation for
the count delta, and one new deployment-boundary fact with exact SHAs. Authorization required:
sovereign review → merge. No merge, no push to `main`.

_Independent re-measurement and addendum written by an AI agent (OpenHands) on behalf of the
sovereign._

---

## 10. ADDENDUM — root cause of the duplicate-Operation-ID warning (Pass 3, 2026-10-04)

This pass makes **no source, test, or policy change**; the only file touched is this evidence
doc. It supersedes section 5's classification of the duplicate OpenAPI Operation IDs.

### 10.1 Superseded attribution

Section 5 recorded: *"`api/main.py` duplicate OpenAPI Operation IDs ... — lab-routes contract,
not this pass."* That is **wrong on the mechanism**, and this addendum corrects it against a
controlled reproduction. The warning is a **test-order-dependent artifact** of
`api.nodes.configure_routers` mutating a module-level singleton; it is **not** a static defect
in `api/lab_routes.py`, and `api/lab_routes.py` is not the thing to change.

### 10.2 The ordering fact (reproduced)

```
pytest tests/test_nodes_composition_seam.py tests/test_production_health_route.py -q  ->  29 warnings
pytest tests/test_production_health_route.py tests/test_nodes_composition_seam.py -q  ->   0 warnings
```

The 29 = **5 (`api/ais_profile.py`) + 24 (`api/lab_routes.py`)**, i.e. every operation of
both injected sub-routers is reported, once each. A defect local to `lab_routes.py` would
not also report all 5 `ais_profile` operations; the boundary of the set is the injection seam,
not either file.

### 10.3 Mechanism (pinned with an isolated repro)

1. `tests/test_nodes_composition_seam.py::test_injected_sub_routers_serve_through_nodes_router`
   calls `nodes.configure_routers(ais_router, lab_router)` — the module-level pair
   `api.nodes.router`, a process-wide singleton, is mutated.
2. `tests/test_production_health_route.py` imports `api.main.app` (which already ran
   `configure_routers` at composition) and calls `app.openapi()`.
3. `api/nodes.py` (ADR-014 Decision 4) keeps the literal
   `router.include_router(_ais_profile_router)` / `router.include_router(_lab_router)` inside
   `configure_routers` — **not idempotent** when called twice on the same router.
   `tests/test_ais_w8_canonical_identity.py` asserts that literal, so the non-idempotency
   cannot be removed without a separate, authorization-requiring change.
4. FastAPI's openapi generator's own **message** is "Duplicate Operation ID id for function f",
   but `config.openapi_duplicate_operation_ids` (FastAPI 0.142.2) only *warns*; the emitted
   schema still de-duplicates by path, so a read of `app.openapi()` returns a schema with
   **0** duplicate operation IDs. The warning and the schema therefore disagree: the warning
   says a duplicate exists, the schema says none does.

Isolated repro (`python -W ignore` around the seam action, then `app.openapi()`):

```
dup warnings after TestClient(local) : 0
dup warnings after app.openapi()     : 29
schema duplicate op ids              : 0
```

### 10.4 Why this is a real, if narrow, test-isolation issue

Warnings are not failures, and this contamination does not corrupt any assertion in either
test (the composed app's routes/schema are correct; see §10.5). But it is the **same class**
already recorded for `test_engineering_lab_agent_loop` (a test that mutates global state and
is order-sensitive). A future pass that greps `-W error` or asserts a warning-free run would
fail for a reason unrelated to the code under test. Recorded here so the next heartbeat does
not mis-attribute it to `api/lab_routes.py`.

### 10.5 Route integrity is unaffected — verified

The production app is correct; the contamination is confined to double-inclusion:

- `GET /api/lab/overview` on `api.main.app` -> **401** (mounted once, authenticated).
- `app.openapi()["paths"]` -> **258 paths / 298 ops**, **0** duplicate operation IDs.
- Injecting twice grows `api.nodes.router.routes` 11 -> 13 -> 15, but the composed app still
  yields one schema entry per path. No route is missing and none is shadowed.

### 10.6 Classification and disposition

**CONTRADICTED (of §5's attribution) / VERIFIED (of the new mechanism).** Recommended
disposition: a **separate** bounded workstream — *test-isolation hardening* — that either
(a) makes `configure_routers` idempotent (guarded by a router-identity check) and re-anchors
the `test_ais_w8_canonical_identity.py` literal, or (b) has the seam test exercise injection
against a fresh, non-singleton `APIRouter` instead of the shared `api.nodes.router` singleton.
Either option changes a test or a layer-3 module and therefore requires the normal review
boundary; it is **out of scope** for this evidence-only PR and is **not** executed here.

The Gate-2 harness was re-pulsed in this pass and the repository-side chain is unchanged from
§9.3; the deployment-specific URL still resolves to the Vercel SSO boundary
(`BLOCKED` on provider auth), so Gate 2 stays open.

_Additional addendum written by an AI agent (OpenHands) on behalf of the sovereign._
