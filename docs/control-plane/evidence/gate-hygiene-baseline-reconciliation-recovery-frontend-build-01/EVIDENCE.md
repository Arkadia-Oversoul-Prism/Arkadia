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
