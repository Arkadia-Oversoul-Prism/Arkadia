# ARK-OPS-CONTINUOUS-001 — Cycle 17

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`,
  carried by PR #705).
- **Cycle:** 17 — immediate execution + hourly continuation.
- **Observed:** 2026-11-25T06:06Z onward.
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Substantive change this cycle:** two unowned surfaces declared an auth boundary their own
  runtime contradicts. Both are repaired, and both repairs are bound to a guard with a
  negative control (§5, §6).

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T17:30:03Z) | `GET /commits/main`; local `HEAD` agrees |
| last merge | `#722` — GOV-04 bounded merge delegation | `GET /pulls/722` |
| open PRs | **52** — **51 drafts**, **1 non-draft** (`#724`), **0** reviews | `GET /pulls?state=open` |
| obsolete PRs | **0** — every open head is ≥ 1 commit ahead of `main` | `GET /compare/main...<head>` for all 52 |
| branch protection / rulesets | absent (`/branches/main/protection` → 404) / `0` | REST |
| `main` check-runs at `fd0a4fdc` | `Full-history secret scan`, `boot-syntax`, `console-contract`, `engineering-scheduler`, `lane-doc-currency`, `posture-currency`, `test` — all `completed/success` | `GET /commits/<sha>/check-runs` |
| open-PR failing checks | only the external-provider family (`beta-beta-*`, `bundle-beta-evidence`, `native-arkadia-golden-workflow`) plus `Build MIE / Sonata debug APK` on `#716` (owned by `#719`'s class) | per-head `check-runs` over all 52 |

No attributable CI failure is in the queue.

## 2. Production boundary — VERIFIED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision       fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Source ↔ running revision is **VERIFIED** and sha-identical to `main`.

**Transient, recorded not promoted.** The first `/api/version` probe of this cycle hit the 30 s
terminal ceiling with no output; a retry with a 60 s ceiling returned 200. That is the Render
cold-start behaviour already recorded for this alias, not a runtime fault.

**A stale claim corrected by measurement.** A prior record stated the deployed `/openapi.json`
declares no `components.securitySchemes` and no per-operation `security`. Measured this cycle
against the same deployment:

```
deployed  /openapi.json : 300 paths, 344 operations, 4 securitySchemes,
                          344/344 operations carry `security` and `x-arkadia-auth-boundary`
local     app.openapi() : 300 paths, 344 operations, 4 securitySchemes, 344/344
```

The deployed document and the local composition agree exactly at this revision. The older
statement is superseded by this measurement.

## 3. Baseline — measured once this cycle

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 20 failed, 4253 passed, 22 skipped, 6 warnings, 1 error in 284.04s (0:04:44)
```

Sorted `FAILED`/`ERROR` node set: **21** nodes,
sha256 `3410a43109d45954c262cf41af01b51804402b55a83defac937d97719288f057`.

| nodes | classification |
|---|---|
| 1 | `tests/test_autonomy.py` — CE-01 `weaver.autonomy` collision. **Sovereign-reserved** |
| 1 | `test_m01_persistence::test_deletion_propagates_to_durable_corpus` — FINDING F-01. **Sovereign-reserved** |
| 1 | `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` — FINDING F-01 proxy. **Sovereign-reserved** |
| 10 | `tests/test_mission_lifecycle_adapter_contract.py` — environment-only: needs `web/arkadia_console/node_modules/typescript` |
| 1 | `test_gov04_bounded_merge_delegation::test_bounded_merge_is_exact_head_and_protected_fail_closed` — repaired by `#725` |
| 1 | `test_identity_spine_w1::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` — repaired by `#700` |
| 1 | `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` — repaired by `#700` |
| 1 | `test_m05_files::test_update_file_supports_rename` — repaired by `#690` |
| 2 | `test_solspire_r1_governance_convergence.py` — repaired by `#693` |
| 1 | `test_solspire_r3_execution_runtime::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` — repaired by `#691` |
| 1 | `test_static_ingestion_idempotency::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` — order-dependent shared-runtime node; repaired by `#698` |

Totals: **3** reserved + **10** environment-only + **8** repaired by open PRs = **21**.
No unowned, non-reserved defect is in the set, so no competing PR was opened for a baseline node.

**Convention.** Cycle 15 recorded 23 nodes (`3 / 10 / 10`) at the same `main`. The delta is the
two `test_prism_w4_lab_pr_state.py` nodes, which pass in this environment. This record states its
own measurement and does not restate cycle 15's as current.

## 4. The defect — a served contract that contradicts its own runtime

The canonical deployment was probed anonymously (read-only `GET`) with
`scripts/production_runtime_probe.py`, whose artifact is
`artifacts/canonical-render-runtime/production-route-inventory.json` (untracked, not committed).
Re-measured directly for this record at revision `fd0a4fdc`:

```
GET /api/commune/threads                         -> 401
GET /api/commune/threads/x                       -> 401
GET /api/orders                                  -> 403
GET /api/ims/inquiries                           -> 403
```

The **served document for the same revision** declares every one of those operations anonymous:

| operation | declared `security` (deployed `fd0a4fdc`) | declared boundary |
|---|---|---|
| `GET /api/commune/threads` | `[]` | `anonymous_no_auth_guard` |
| `POST /api/commune/threads` | `[]` | `anonymous_no_auth_guard` |
| `PATCH /api/commune/threads/{thread_uuid}` | `[]` | `anonymous_no_auth_guard` |
| `GET /api/commune/threads/{thread_uuid}` | `[]` | `anonymous_no_auth_guard` |
| `GET /api/commune/threads/{thread_uuid}/messages` | `[]` | `anonymous_no_auth_guard` |
| `GET /api/orders` | `[]` | `anonymous_no_auth_guard` |
| `GET /api/ims/inquiries` | `[]` | `anonymous_no_auth_guard` |

Two independent mechanisms produced it:

1. **An enforced guard expressed as a helper, not a dependency.** `api/commune_threads.py`
   resolved the caller through a module-local `_user_id(request)` helper that raises 401. A
   helper is invisible to `api/openapi_security.py`, which classifies from FastAPI's dependency
   graph, so the whole module advertised itself public while refusing every anonymous caller.
2. **A case-sensitive header match on a case-insensitive header.** `api/openapi_security.py`
   tested `"X-Sovereign-Key" in source`. The repository's own sovereign-gated handlers spell it
   `x-sovereign-key` (`request.headers.get("x-sovereign-key", "")`), so the detector declared
   them anonymous. HTTP header names are case-insensitive; the detector was not.

Consequence: a generated client, the console, or any integrator reading `/openapi.json` is told
that five Arkana thread operations and two sovereign-gated reads need no credential. Every one
of them refuses an anonymous request.

## 5. The change

| file | change |
|---|---|
| `api/commune_threads.py` | every route declares `user: dict = Depends(require_auth)`; `_user_id(user)` reads the verified subject instead of re-resolving the request |
| `api/openapi_security.py` | the sovereign-header detector matches case-insensitively (`source.lower()`, `sovereign_key` + `x-sovereign-key`) |
| `tests/test_openapi_security_metadata.py` | three new guards: case-insensitive detection, its negative control, and the thread-declaration guard with its negative control |
| `tests/test_prism_w4_arkana_thread_history.py` | the existing source-level pin now asserts the declaration (`Depends(require_auth)` × 5, `_user_id(user)` × 5) instead of the superseded `await _user_id(request)` shape |

Runtime behaviour is **unchanged**: `require_auth` raises `HTTPException(401, "Authentication
required")` for an anonymous caller, which is exactly what `_user_id` raised. The existing
behavioural contract (`tests/test_arkana_thread_history_contract.py::test_every_route_requires_an_identity`)
still passes, and now runs through the declared dependency.

Declaration after the change, from the composed app:

| operation | `security` | boundary |
|---|---|---|
| 5 × `/api/commune/threads…` | `[{"FirebaseBearer": []}]` | `firebase_bearer` |
| `GET /api/orders` | `[{"SovereignKeyHeader": []}]` | `sovereign_key_header` |
| `GET /api/ims/inquiries` | `[{"SovereignKeyHeader": []}]` | `sovereign_key_header` |
| `POST /api/orders` (public intake) | `[]` | `anonymous_no_auth_guard` — correctly unchanged |

Operation inventory is unchanged: **344** operations before and after
(`tests/test_openapi_security_production_contract.py` pins it).

Classification delta across the whole document, measured before and after the change:

| classification | before | after |
|---|---|---|
| `firebase_bearer` | 211 | 216 |
| `sovereign_key_header` | 1 | 3 |
| `anonymous_no_auth_guard` | 104 | 97 |
| all other classes | unchanged | unchanged |

## 6. Verification

| command | result |
|---|---|
| `pytest tests/test_openapi_security_metadata.py` | **7 passed** (4 new) |
| `pytest tests/test_openapi_security_production_contract.py` | **1 passed** (344-operation pin holds) |
| `pytest` openapi + thread + authority + auth-posture set (9 files) | **78 passed** |
| `pytest tests/architecture tests/test_m02a_ci_gate_integrity.py` | **87 passed** |
| `python -m py_compile` on all four changed files | ok |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths | `Mutation boundary PASS`, exit 0 |

**Negative control 1 — the thread declaration guard bites on the real file.** Removing the
`Depends(require_auth)` declaration from the first thread route in `api/commune_threads.py`
(working tree, real file):

```
FAILED tests/test_openapi_security_metadata.py::test_commune_thread_routes_declare_the_identity_they_enforce
1 failed, 6 passed
```

restored byte-identically → `7 passed`.

**Negative control 2 — the detector guard bites on the real classifier.** Restoring the
pre-repair case-sensitive comparison in `api/openapi_security.py`:

```
FAILED tests/test_openapi_security_metadata.py::test_sovereign_header_detection_is_case_insensitive
1 failed, 6 passed
```

restored byte-identically → `8 passed` across the two openapi suites.

The third new guard is itself a negative control: it feeds the classifier the pre-repair shape
(a helper that refuses anonymous callers but is not a dependency) and asserts it is reported
`anonymous_no_auth_guard`, so the thread assertion cannot become trivially true.

## 7. Residual — recorded, not repaired

1. **`GET /api/dashboard/loops` is still declared anonymous.** It is sovereign-gated by a
   `sovereign_token` **query parameter**, not a header, so neither mechanism repaired here
   covers it. The query-parameter shape is also a secret-in-URL logging hazard. Changing it is
   an API-shape change (a caller's URL stops working), so it is proposed, not executed. It lives
   in `api/main.py`, which four open PRs (`#701`, `#711`, `#717`, `#729`) already touch.
2. **97 operations remain declared `anonymous_no_auth_guard`.** Most are genuinely public
   (`/api/scrolls`, the webhook, product intake). One sub-class is a declaration defect of the
   same kind measured here: `api/knowledge_routes.py` enforces *optional* identity through a
   local `_optional_user_id` helper, so its operations read `anonymous_no_auth_guard` when the
   truthful class is `optional_firebase_bearer`. That module is owned by `#718`; a general
   fix belongs with the classifier (resolve module-local helpers) and is a separate bounded
   change.
3. **`GET /api/keys` is declared protected and answers anonymously with masked key metadata.**
   Already disclosed in the repository's governance record; not touched here.

## 8. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production revision identical and `revision_conflict:
false`; `main` CI green; 52 open PRs (51 drafts, 1 non-draft), 0 obsolete; baseline 21
failing/error nodes, all reserved, environment-only, or repaired by an open PR. Two unowned
declaration defects are repaired on this branch with guards and negative controls.

**Evidence.** This record; the live probe artifact; `POST /pulls` for this branch; the deployed
`/openapi.json` captured at `fd0a4fdc`.

**Blockers.**
(a) **Merge execution is human-only** (GOV-03; GOV-04 delegates only to a designated human
operator) and 51 drafts await owner action and human review. This is the binding constraint.
(b) Branch protection and rulesets are absent, so no platform control enforces review.
(c) CE-01 and FINDING F-01 (three nodes) are reserved to the sovereign.
(d) The residual items in §7 are separate bounded changes.

**Authorized next action.** Human review of the queue. An agent may keep maintaining its own
drafts and recording cycles; it cannot reduce the queue and must not open a PR for a defect
another open PR already owns.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; re-pinning F-01; adding an
auth guard to `/api/webhook/github`; changing the `/api/dashboard/loops` request shape;
weakening a guard to manufacture green.

**Completion condition.** This cycle is complete when this record is reviewable, the branch
carries the repair and its guards, `main` is unmodified, and no merge, deployment or acceptance
is claimed.
