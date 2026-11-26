# Gate hygiene — GitHub push-webhook surface inventory (01)

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`, cycle 05
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed. GOV-03 remains the merge rule.
- **Branch:** `gate-hygiene/github-webhook-surface-inventory-01`
- **Observed:** 2026-11-24T02:06Z onward

---

## 1. Reconstructed state (live, before any change)

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /git/ref/heads/main`; local `HEAD` agrees |
| clone | full history (`is-shallow-repository` -> `false`) | `git rev-parse` |
| open PRs | **33**, all `draft`, all `base: main` | `GET /pulls?state=open` |
| branch protection / rulesets | none / 0 | REST |
| `api/main.py` | **2597** lines (budget 2600) | `wc -l` |
| architecture suite | **11 passed** | `pytest tests/architecture` |
| lane currency (offline) | exit **0** | `python scripts/lane_state.py --check` |

### 1.1 Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version
  200, 643 B
  source_revision    bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source    RENDER_GIT_COMMIT
  revision_conflict  false
GET https://arkadia-qzu4.onrender.com/health
  200 {"status":"radiant","path":"/health"}
```

Source <-> running revision is **VERIFIED** for this revision. That is necessary evidence of
consistency; it is **not** proof of application correctness and **not** deployment acceptance.

**One transient, recorded rather than promoted.** The first `/api/version` probe of this cycle
timed out at the client (`curl -m 20` -> exit 28, `status=000`, 0 bytes). The immediately following
probe of the same URL returned `200 / 643 B`, as did `/health`. Classification: **UNKNOWN - a
single unreproduced cold-start read**, not a defect claim and not a boundary failure.

## 2. Baseline, re-measured with the full dependency set

This sandbox started without `pytest` and without `web/arkadia_console/node_modules`, so the
baseline was re-derived rather than inherited:

```console
$ pip install -r requirements.txt
$ cd web/arkadia_console && corepack pnpm install --frozen-lockfile   # exit 0
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
9 failed, 4260 passed, 22 skipped, 6 warnings, 1 error in 298.51s
```

**10** failing/error nodes, each already classified and owned:

| node(s) | owner |
|---|---|
| `ERROR tests/test_autonomy.py` | sovereign-reserved (CE-01 `weaver.autonomy` collision) |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | sovereign-reserved (FINDING F-01) |
| `tests/test_identity_spine_w1.py::...`, `tests/test_m02_reasomate_truth.py::...` | open #700 |
| `tests/test_m01_persistence.py::...`, `tests/test_m05_files.py::...` | open #690 |
| `tests/test_solspire_r1_governance_convergence.py::...` (2) | open #693 |
| `tests/test_solspire_r3_execution_runtime.py::...` | open #691 |
| `tests/test_static_ingestion_idempotency.py::...` | open #698 |

**No unowned, non-reserved defect is in the failing set.** This also settles the count cycle 04
recorded as 20: the other 10 nodes were the environment-only
`tests/test_mission_lifecycle_adapter_contract.py` set, and with
`web/arkadia_console/node_modules/typescript` present that file is **10 passed**. The 20-node set
therefore decomposes exactly as 10 real + 10 environment, so the "environment-only" classification
is confirmed rather than inferred.

### 2.1 Active application verified at this revision

Previously unmeasurable in this sandbox, so measured now:

| check | result |
|---|---|
| `corepack pnpm build` (`tsc --noEmit && vite build`) | **exit 0**, 170 modules, `dist/assets/index-CYGHeCpJ.js` 425.15 kB |
| `corepack pnpm exec vitest run` | **8 files, 61 tests passed** |

The console typechecks, builds and passes its own unit suite at `bb19aabd`. Build output lands in
gitignored `dist/`; the tree stays clean.

## 3. The defect

`ruff --select F821,F811` over the tracked corpus reported, in the boot file:

```
api/main.py:1734:11: F811 Redefinition of unused `github_webhook` from line 944
```

`api/main.py` defines **two** module-level handlers named `github_webhook`, serving **two different
routes** for the same external event:

| route | handler | posture (from `x-arkadia-auth-boundary`) |
|---|---|---|
| `POST /api/github/webhook` | `github_webhook` (line 943) | `github_webhook_hmac`, guard `X-Hub-Signature-256` |
| `POST /api/webhook/github` | `github_webhook` (line 1733) | `anonymous_no_auth_guard`, `runtime_guard: null` |

Three distinct problems, in increasing order of importance:

1. **The module-level name is shadowed.** FastAPI captured each function at decoration time, so
   runtime routing is unaffected - but the second definition replaces the first binding, so a
   maintainer editing `github_webhook` edits the corpus-resync handler, not the HMAC-verified one.
2. **The surface was only half-pinned.** `tests/test_openapi_security_production_contract.py` pins
   `schema["paths"]["/api/github/webhook"]["post"]["security"]`. Nothing pins
   `/api/webhook/github`, so its posture - or the arrival of a *third* push webhook - could change
   with no test to report it.
3. **The anonymous route performs consequential work.** For any caller sending
   `X-GitHub-Event: push`, it runs `_get_scrolls(force=True)`, i.e. a full corpus re-fetch and
   re-ingest, with no signature check.

The posture itself is **disclosed, not hidden**: `api/openapi_security.py` derives the boundary
from the handler's dependency graph and classifies this route `anonymous_no_auth_guard`, with an
explicit comment that this "is a disclosure of current runtime behavior, not an endorsement that
mutating public routes are safe". Changing that authorization is an authority-boundary change and
is **sovereign-gated**. It is therefore **recorded here and not repaired**.

## 4. The change

Two files, behaviour-preserving where it touches product code:

```diff
-@app.post("/api/webhook/github")
-async def github_webhook(request: Request):
+@app.post("/api/webhook/github", operation_id="github_webhook_api_webhook_github_post")
+async def github_webhook_corpus_resync(request: Request):
```

`operation_id` is set explicitly to the value FastAPI generated before the rename, so the emitted
OpenAPI document is unchanged. `tests/test_github_webhook_surface_inventory.py` (8 tests) pins the
whole surface:

| test | property |
|---|---|
| `test_live_webhook_surface_matches_the_recorded_inventory` | every webhook operation, its classification, runtime guard and security schemes equal the record |
| `test_recorded_inventory_is_exactly_the_two_github_push_webhooks` | the record is content, not a wildcard; the anonymous route is recorded as unguarded |
| `test_resync_route_keeps_its_published_operation_id` | the rename is schema-neutral |
| `test_main_module_defines_no_duplicate_function_name` | the F811 class cannot return to the boot file |
| `test_negative_control_reports_a_third_webhook` | a third push webhook is reported |
| `test_negative_control_reports_a_posture_change` | the anonymous route gaining a guard is reported |
| `test_positive_control_accepts_the_recorded_inventory` | the same detector is silent on a matching surface |
| `test_negative_control_reports_a_duplicate_function_name` | the duplicate-name detector reports a synthetic duplicate |

## 5. Verification

```console
$ python -m pytest tests/test_github_webhook_surface_inventory.py \
    tests/test_openapi_security_production_contract.py -q
9 passed

$ python -m pytest tests/architecture tests/test_boot_syntax_boundary.py \
    tests/test_m02a_ci_gate_integrity.py tests/test_economic_seam_ci_wiring.py \
    tests/test_gate_filter_selection.py tests/test_ci_gate_trigger_coverage.py -q
263 passed

$ python -m ruff check --select F811 api/main.py
All checks passed!

$ wc -l api/main.py
2597 api/main.py        # unchanged; budget 2600
```

The existing 344-operation inventory pin in
`tests/test_openapi_security_production_contract.py` still passes, so no route was added, removed
or re-shaped.

### 5.1 Live negative control

Reverting **only** the rename on the real file, then restoring it byte-identically:

```console
$ git checkout -- api/main.py
$ pytest tests/test_github_webhook_surface_inventory.py -q
1 failed, 7 passed     # test_main_module_defines_no_duplicate_function_name

$ cp /tmp/main_patched.py api/main.py
$ pytest tests/test_github_webhook_surface_inventory.py -q
8 passed
```

The guard reddens on the defect and is silent on the repair. A control that failed on both, or
neither, would be measuring the wrong thing.

## 6. Limitations and non-claims

- **The anonymous route was not exercised.** Sending `X-GitHub-Event: push` to it would trigger a
  real corpus re-ingest; that is a mutation, so its runtime effect is **NOT TESTED**. The
  consequential work it performs is read from source and is stated as such.
- **No authorization was changed.** This PR does not add a guard to `/api/webhook/github`, and it
  does not remove the route. Choosing between "guard it", "retire it", and "keep it anonymous and
  documented" is a sovereign decision.
- **No merge, no deployment, no acceptance.** Production parity at `bb19aabd` is a revision-identity
  observation only.
- The 10 failing/error nodes are pre-existing and owned by other open PRs; this branch neither
  repairs nor adds to them.

## 7. Next-action block

**Current state.** `main` = `bb19aabd...`; production `source_revision` identical,
`revision_conflict: false`; architecture 11 passed; console builds and 61 vitest tests pass;
baseline 10 failing/error nodes, all owned or reserved. This branch adds one guard file and a
2-line, schema-neutral rename.

**Blockers.** (a) Merge execution is human-only (GOV-03); 33 drafts await human review. (b) The
anonymous GitHub push webhook and the CE-01 / FINDING F-01 items are reserved to the sovereign.

**Authorized next action.** A human reviews this branch together with the queue. A later cycle may
re-run the baseline, or take up the sovereign decision on `/api/webhook/github` once it is made.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; adding an auth guard to
`/api/webhook/github` under this authorization; weakening a guard to manufacture green.

**Completion condition.** This cycle is complete when this evidence and the guard are reviewable on
the branch, with `main` unmodified and no merge, deployment or acceptance claimed.
