# WORKSTREAM_STATE — gate-hygiene/baseline-reconciliation-recovery-frontend-build-01

| field | value |
|---|---|
| base main | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| branch | `gate-hygiene/baseline-reconciliation-recovery-frontend-build-01` |
| objective | re-measure live baseline on `main`; recover one stale environment claim (`vite build`) with evidence; confirm the hygiene envelope is exhausted |
| change set | this evidence dir only (no source/test/policy change) |
| architecture | 11/11 |
| full suite (Pass 1 clone) | 9F / 1414P / 20S / 1E |
| full suite (Pass 2 clone, see EVIDENCE §9.2) | **10F / 1416P / 17S / 1E** — 9 classified + 1 clone-depth node |
| failure node-set sha256 (Pass 2) | `6ca42572174af4550f35c33d5101467aa5ddb2de514a304f861036b067dc72c5` |
| failure node-set sha256 (Pass 1) | `00b3984e7ad487f1c36e1449429834cdf398f5dde8d4591f4079942c180af48b` |
| frontend build | **now runnable** here — `corepack pnpm install` + `corepack pnpm build` exit 0 (supersedes `environment-blocked`) |
| AGENTS.md encoding audit | `Cyrillic 0`, `reproduced=True`, `alterations=0`, exit 1 (requires oracle `6c43218a48a4` fetched) |
| CP10 mutation boundary | PASS (RC 0) |
| api/main.py | untouched, compiles, 2582 / 2600 |
| Vercel on `main` `1b7c089f` | `failure` = **provider rate limit** ("retry in 24 hours"), NOT a build failure |
| production deploy | `fa1b40787544` arkadia-prism `success`; 5 commits behind main; those 5 = docs+tests only → frontend source-identical |
| status | **VERIFIED** (reconciliation + independent re-measurement, EVIDENCE §9) |
| authorization | sovereign merge only |

## Count-delta attribution (Pass 1 → Pass 2)

The 9→10 failure delta is **clone depth**, not a regression. The depth-1 clone cannot resolve
`tests/test_agents_md_encoding_adjudication.py`'s pinned revisions (`ORACLE_REV`
`6c43218a48a4`, `CORRUPTION_COMMIT` `e0dde9ad9c5e`, `GATE2_PARENT_REV` `7d79f38bd520…`).
Fetching them collapses 4 extra failures to 1 residual (`test_corruption_origin_is_re_derivable`,
which needs full `git log -- AGENTS.md` history). No node in Pass 1's 9-failure set is absent in
Pass 2, and no new non-clone-depth failure appears. **Fetch the three revisions before comparing
counts.**

## Open queue (all need a decision — none executed)

| id | item | disposition |
|---|---|---|
| `SH-01` | test-session env leak | RESOLVED earlier (`fc3743f`) |
| `SH-02` | 35 stale string assertions (batched) | resolved in prior passes for touched files; remaining live failures are DRIFT/product, not copy |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` | product decision |
| `SH-04` | `CapabilityRegistry` cycle detection reachable? | **RESOLVED — no defect** (`tests/test_spiral_grove_registry.py` 10 passed) |
| `SH-05` | gate serve/status tests | sovereign call |
| `SH-06` | `steward_filter` stem-match `transcend*` | product judgement (3 live failures) |
| `SH-07` | Oracle/ReasoMate shared-session key | architectural gate (high) |
| `SH-08` | control-case identity assertion | COMPLETE (PR #261, `213b431`) |
| `F-01` | `sessionStorage` persistence proxy | sovereign decision; test body already documents it |

## Next bounded task (deterministic resume block)

- **State**: baseline reconciled and recorded; independent re-measurement recorded (EVIDENCE §9);
  hygiene envelope exhausted; production deploy boundary characterized.
- **Evidence**: `EVIDENCE.md` in this dir (sections 2-4, §9 addendum).
- **Blockers**: every remaining node requires product/architectural/sovereign input. Separately,
  the current-`main` Vercel status is `BLOCKED` on a **provider build rate limit**; it is not a
  repository action.
- **Authorized action**: sovereign review of this evidence PR -> merge. Then a *separately
  authorized* product/architecture workstream may take `SH-06` (steward filter policy) or
  `SH-03` (DERIVED contract) as its own bounded task. The Gate-2 deployment boundary should be
  re-pulsed after the rate limit expires, using `scripts/gate2_production_observation.py`.
- **Forbidden**: merging, pushing to `main`, widening this PR, "fixing" any classified failure
  by editing a test literal without a decision.
- **Completion condition**: this PR merged -> next heartbeat reconstructs from live evidence.

## Pass 3 (2026-10-04) - duplicate-Operation-ID warning characterized

- **Change**: EVIDENCE §10 only (this file + EVIDENCE.md). No source/test/policy file touched;
  `git diff --numstat` = 1 file, +87, -0.
- **Finding**: the 29 duplicate-Operation-ID warnings are NOT a lab-routes defect (EVIDENCE §5
  attribution is CONTRADICTED). They are test-order-dependent: the seam test mutates the
  module-level `api.nodes.router` singleton via `configure_routers` (non-idempotent,
  `include_router` kept literal by ADR-014 D4 / `test_ais_w8_canonical_identity.py`); the health
  test then calls `app.openapi()` on the already-composed app. 29 = 5 ais_profile + 24 lab_routes.
- **Route integrity verified**: `GET /api/lab/overview` on `api.main.app` -> 401 (mounted once);
  `app.openapi()` -> 258 paths / 298 ops / 0 duplicate ids. No route missing or shadowed.
- **Architecture gate re-measured**: `tests/architecture` -> **11 passed**.
- **Classified as** CONTRADICTED (of §5) / VERIFIED (of new mechanism).
- **Next bounded task (NEW, separate authorization)**: test-isolation hardening - either make
  `configure_routers` idempotent or have the seam test use a fresh `APIRouter`. NOT executed here;
  it changes a test/layer-3 module and needs normal review. Not in this PR's scope.
- **Blockers**: unchanged from the block above; Gate-2 deployment URL still Vercel-SSO-blocked.
