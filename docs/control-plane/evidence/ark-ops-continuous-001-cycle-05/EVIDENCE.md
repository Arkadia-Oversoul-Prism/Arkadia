# ARK-OPS-CONTINUOUS-001 — Cycle 05

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 05 — immediate execution + hourly continuation
- **Observed:** 2026-11-24T02:06Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessors:** cycles 01-04 in this directory.
- **Substantive change this cycle:** **PR #711**
  (`gate-hygiene/github-webhook-surface-inventory-01`). It carries its own evidence at
  `docs/control-plane/evidence/gate-hygiene-github-webhook-surface-inventory-01/EVIDENCE.md`.
  This entry is the ledger pointer, not a duplicate of that record.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /git/ref/heads/main`; local `HEAD` agrees |
| clone | full history (`is-shallow-repository` -> `false`) | `git rev-parse` |
| open PRs | **33**, all `draft`, all `base: main` | `GET /pulls?state=open` |
| branch protection / rulesets | none / `0` | REST |
| `api/main.py` | **2597** lines (budget 2600) | `wc -l` |

## 2. Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version  -> 200, 643 B
  source_revision    bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source    RENDER_GIT_COMMIT
  revision_conflict  false
GET https://arkadia-qzu4.onrender.com/health       -> 200 {"status":"radiant","path":"/health"}
```

Source <-> running revision is **VERIFIED**. That is necessary evidence of consistency; it is not
proof of application correctness and not deployment acceptance.

**Transient, recorded not promoted.** The first `/api/version` probe of this cycle timed out at the
client (`curl -m 20` -> exit 28, `status=000`, 0 bytes); the next probe of the same URL returned
`200 / 643 B`, as did `/health`. Classification: **UNKNOWN — a single unreproduced cold-start
read**, not a defect claim.

## 3. Baseline re-derived, not inherited

The sandbox started without `pytest` and without `web/arkadia_console/node_modules`, so the
baseline was measured from scratch:

```console
$ pip install -r requirements.txt
$ cd web/arkadia_console && corepack pnpm install --frozen-lockfile   # exit 0
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
9 failed, 4260 passed, 22 skipped, 6 warnings, 1 error in 298.51s
```

**10** failing/error nodes, each owned or sovereign-reserved:

| node(s) | owner |
|---|---|
| `ERROR tests/test_autonomy.py` | sovereign-reserved (CE-01) |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | sovereign-reserved (FINDING F-01) |
| `tests/test_identity_spine_w1.py::...`, `tests/test_m02_reasomate_truth.py::...` | open #700 |
| `tests/test_m01_persistence.py::...`, `tests/test_m05_files.py::...` | open #690 |
| `tests/test_solspire_r1_governance_convergence.py::...` (2) | open #693 |
| `tests/test_solspire_r3_execution_runtime.py::...` | open #691 |
| `tests/test_static_ingestion_idempotency.py::...` | open #698 |

**No unowned, non-reserved defect is in the set.** This resolves cycle 04's 20-node count: the
other 10 nodes were the environment-only
`tests/test_mission_lifecycle_adapter_contract.py` set, which is **10 passed** with
`web/arkadia_console/node_modules/typescript` present. The 20-node set decomposes as 10 real + 10
environment.

## 4. Active application verified at this revision

Previously unmeasurable in this sandbox:

| check | result |
|---|---|
| `corepack pnpm build` (`tsc --noEmit && vite build`) | **exit 0**, 170 modules, `dist/assets/index-CYGHeCpJ.js` 425.15 kB |
| `corepack pnpm exec vitest run` | **8 files, 61 tests passed** |

## 5. What this cycle changed

`ruff --select F821,F811` found `api/main.py:1734:11: F811 Redefinition of unused github_webhook`.
Two module-level handlers shared one name across two routes: `/api/github/webhook`
(`github_webhook_hmac`) and `/api/webhook/github` (`anonymous_no_auth_guard`, no runtime guard,
forces a full corpus re-ingest on `X-GitHub-Event: push`).

Only the HMAC route was pinned by a test. **PR #711** renames the second handler
(behaviour-preserving, `operationId` pinned so the schema does not move) and binds the whole
webhook surface — operation set, classification, runtime guard, security schemes — to a recorded
inventory with negative controls.

**No authorization was changed.** The anonymous posture is disclosed by
`api/openapi_security.py`; altering it is sovereign-gated and is recorded, not repaired.

## 6. Next-action block

**Current state.** `main` = `bb19aabd...`; production revision identical; architecture 11 passed;
console builds and 61 vitest tests pass; baseline 10 failing/error nodes, all owned or reserved.
**33** open drafts, `MERGEABLE`, 0 obsolete.

**Evidence.** PR #711 and its evidence record; sections 1-5 above.

**Blockers.** (a) Merge execution is human-only (GOV-03); 33 drafts await human review.
(b) The anonymous GitHub push webhook and CE-01 / FINDING F-01 are reserved to the sovereign.

**Authorized next action.** Human review of the queue, including #711. A later cycle may re-run
the baseline or take up the sovereign decision on `/api/webhook/github`.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; adding an auth guard to
`/api/webhook/github` under this authorization; weakening a guard to manufacture green.

**Completion condition.** This cycle is complete when this ledger entry and #711 are reviewable,
with `main` unmodified and no merge, deployment or acceptance claimed.
