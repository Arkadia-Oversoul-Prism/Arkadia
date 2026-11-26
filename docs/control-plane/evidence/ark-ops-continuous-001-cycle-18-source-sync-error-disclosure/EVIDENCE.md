# ARK-OPS-CONTINUOUS-001 — Cycle 18

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22` (recorded by open PR `#705`)
- **Cycle:** 18 — immediate execution + hourly continuation
- **Observed:** 2026-11-25T08:05Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. This cycle performed no
  merge, no push to `main`, no deployment, and claims no acceptance.
- **Substantive change:** `POST /solspire/sources/{source}/sync` returned the caught exception's
  own text to the caller (502). Repaired, with a behavioural guard and its executable CI surface.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `git rev-parse HEAD` == `origin/main` after `git fetch --prune`; tree clean |
| open PRs | **55** — 54 drafts, 1 non-draft (`#724`) | `GET /pulls?state=open` + GraphQL inventory |
| obsolete open PRs | **0** | `git apply -R --check` over all 55 PR diffs: **none** reverse-applies to `main`, so no open change is already present |
| `main` check-runs at `fd0a4fdc` | **8**, all `completed/success` | `GET /commits/<sha>/check-runs` |
| `api/main.py` | **2597** lines (budget 2600) | `wc -l` — untouched by this cycle |

## 2. Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision     fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source     RENDER_GIT_COMMIT
  revision_conflict   false
  canonical_deployment one_reconciled_deployment
GET https://arkadia-qzu4.onrender.com/ -> 200 {"message":"Arkadia Mind is breathing."}
```

Source ↔ running revision is **VERIFIED** and sha-identical to `main`. That is consistency
evidence, not acceptance. `GET /` returns the 40-byte liveness JSON without a browser `Accept`
header — the documented SPA-mode behaviour, not a fault.

## 3. Baselines measured this cycle

| surface | result |
|---|---|
| `tests/architecture` | **11 passed** |
| console build (`web/arkadia_console`: `tsc --noEmit && vite build`) | **success** — 170 modules, `dist/assets/index-CYGHeCpJ.js` 425 kB; `dist/` is untracked |
| full suite on `main` | `22 failed, 4251 passed, 22 skipped, 1 error`; failing/error set **23 nodes** |
| full suite on this branch | `12 failed, 4271 passed, 22 skipped, 1 error`; failing/error set **13 nodes** |
| node-set delta, `main` → branch | **zero new nodes.** The 10 nodes that disappear are exactly `tests/test_mission_lifecycle_adapter_contract.py::*`, an *environment* change this cycle caused: the console build ran `corepack pnpm install`, creating `web/arkadia_console/node_modules/typescript`, which those nodes require. The file is byte-identical to `main` (`git diff --stat main -- tests/test_mission_lifecycle_adapter_contract.py` empty) and measures **10 passed** now |
| collected nodes, `main` → branch | `4294` → `4304` (`+10`): **+3** the new guard, **+7** nodes the generic workflow-scanning suites gain by construction from one new workflow file — measured per file: `test_ci_gate_trigger_coverage.py` 99→102, `test_workflow_injection_boundary.py` 50→51, `test_ci_suite_collection_continuation.py` 101→103, `test_gate_filter_selection.py` 51→52 (`+3/+1/+2/+1`) |
| gate-integrity bundle (`test_m02a_ci_gate_integrity`, `test_ci_gate_trigger_coverage`, `test_boot_syntax_boundary`, `test_workflow_injection_boundary`) | **229 passed** after this change |

All 23 baseline nodes are accounted for, and **none is an unowned defect**:

| node(s) | n | classification |
|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | sovereign-reserved (CE-01 `weaver.autonomy` collision) |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | 1 | sovereign-reserved (FINDING F-01) |
| `tests/test_gov04_bounded_merge_delegation.py::test_bounded_merge_is_exact_head_and_protected_fail_closed` | 1 | repaired by open **#725** (`no auto-merge` / `post-merge` near-miss literals) |
| `tests/test_mission_lifecycle_adapter_contract.py::*` | 10 | environment-only — needs `web/arkadia_console/node_modules/typescript`; absent in the baseline sandbox, and CI provisions it via `pnpm install --frozen-lockfile` before the suite. Present in this sandbox after the console build, where the file measures **10 passed** |
| `test_identity_spine_w1::test_node_entry_is_ais_signup…`, `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` | 2 | repaired by open **#700** |
| `test_solspire_r1_governance_convergence::*` | 2 | repaired by open **#693** |
| `test_m01_persistence::…`, `test_m05_files::…` | 2 | repaired by open **#690** |
| `test_solspire_r3_execution_runtime::test_runtime_is_explicitly_non_governed…` | 1 | repaired by open **#691** |
| `test_static_ingestion_idempotency::test_open_loop_content_is_checksum_stable…` | 1 | repaired by open **#698** |
| `tests/test_prism_w4_lab_pr_state.py::test_handler_emits_the_keys_the_projection_reads`, `::test_projection_reads_the_handler_output` | 2 | environment-only in *this* sandbox: the handler reads a live PR when `GH_TOKEN`/`GITHUB_TOKEN` is exported, and the test's premise is "no token in the environment" |

## 4. Queue truth — 21 `UNSTABLE` PRs are blocked by an external provider, not by their diffs

`mergeStateStatus` over the 55 open PRs: **34 `CLEAN`, 21 `UNSTABLE`, 0 `DIRTY`**.

Every one of the 21 reports the same failing checks — `native-arkadia-golden-workflow` and/or
`beta-beta-01-english`, `beta-beta-02-hausa`, `bundle-beta-evidence` — all in
`.github/workflows/n-atlas-external-beta.yml`, which **no open PR modifies**. Read from the run
that failed (run `45565632747`, PR `#733`):

```
JOB beta-beta-02-hausa success
JOB beta-beta-01-english success
JOB native-arkadia-golden-workflow failure
JOB bundle-beta-evidence success

FAILED tests/test_natlas_developer_lab.py::test_native_natlas_route_live_external_gradio
  fastapi.exceptions.HTTPException: 503: N-ATLaS Gradio runtime error:
  provider emitted error event with null/empty data (event_id=b7079aa8…, raw_data='null', events=['error'])
1 failed, 10 deselected
```

The same workflow **succeeds** on sibling branches (`#734` twice, `#731`), and the beta jobs
succeeded while the golden job failed *in the same run*, so the failure is the live external
N-ATLaS runtime, not the diff. It is **not evidence about the repository tree**, and no agent may
weaken that gate to make the queue look green; distinguishing provider-unavailability from a
repository failure is a gate-design decision reserved to the sovereign.

## 5. The defect this cycle repaired — measured

`api/source_routes.py::sync_source` caught every exception, logged it, and **then returned the
same text to the caller**:

```python
except Exception as exc:
    logger.exception("Source sync failed: %s", source)
    raise HTTPException(status_code=502, detail=f"Sync failed: {exc}") from exc
```

`_sync()` delegates to a corpus adapter built by `api.source_connections.build_corpus_source` and
to `knowledge.pipeline.ingest`, so `exc` can carry provider URLs, credential material, filesystem
paths and configuration values. Reproduced with a canary (see the guard's negative control, §7):

```
POST /solspire/sources/github/sync -> 502
{"detail":"Sync failed: adapter exploded: postgres://svc:hunter2@internal-db.example/private"}
```

Repair: the cause stays in the log; the caller receives stable copy that points at the log.

```python
except Exception:
    logger.exception("Source sync failed: %s", source)
    raise HTTPException(
        status_code=502, detail="Source sync failed; inspect server logs for the cause"
    ) from None
```

### The `503` on `/connect` is deliberately untouched

`api/source_routes.py::connect_source` returns `503 detail=str(exc)` for `RuntimeError`. Those
values are **curated configuration copy** raised by `api.source_connections`
(`"SOVEREIGN_KEY is required to store source credentials"`,
`"Stored source credential cannot be decrypted"`) — the operator needs them, and hiding them would
conceal a configuration fault. The guard pins that discrimination as a positive control.

## 6. Why only this site, and the composition constraint on the rest

A repo-wide AST scan finds **32** `5xx` sites whose `detail` is built from the caught exception.
Ownership across the 55 open PRs:

| module | sites | status |
|---|---|---|
| `api/knowledge_routes.py` | 16 | repaired by open **#718** |
| `api/main.py` | 6 | owned by **#729**, **#717**, **#711**, **#701** |
| `api/lab_routes.py` | 2 | owned by **#712**; authority surface (sovereign-gated) |
| `api/ims_products.py`, `api/arkana_signal_routes.py`, `api/ceo_chat_routes.py` | 4 | owned by **#717** |
| `solspire/console_router.py` | 1 | owned by **#710**, **#713** |
| **`api/source_routes.py`** | **2** | **unowned — this cycle repairs the 502** |
| **`api/plan_routes.py`** | **1** | **unowned — deferred, see below** |

Open **#718** builds the repo-wide guard (`tests/test_http_error_contract.py`) and records
`api/plan_routes.py: 1` and `api/source_routes.py: 2` in `RECORDED_DISCLOSURES`. Its assertions
decide what may compose with it:

```python
def test_the_recorded_inventory_may_only_shrink():   # measured <= recorded
def test_the_record_describes_no_repaired_debt():    # a recorded module measuring 0 fails
    stale = [m for m in RECORDED_DISCLOSURES if measured.get(m, 0) == 0]
    assert stale == []
```

- Repairing the `502` here leaves `api/source_routes.py` measuring **1** (≤ recorded 2, ≠ 0), so
  `#718` is green in **either** merge order. That is why this site is the composable one.
- Repairing `api/plan_routes.py` would make it measure **0** while `#718` records `1` — `#718`
  would then fail `test_the_record_describes_no_repaired_debt` on `main`. **Its repair is
  therefore sequenced strictly after `#718`** and must prune the record in the same change. This
  cycle records the constraint instead of opening a repair that would redden the base tree.

## 7. Verification

```
$ python -m pytest tests/test_source_sync_error_disclosure.py -q
3 passed

# negative control — the pre-repair handler restored byte-for-byte
$ python -m pytest tests/test_source_sync_error_disclosure.py -q
1 failed, 2 passed
  FAILED test_sync_failure_hides_the_cause_and_logs_it

# restored
$ python -m pytest tests/test_source_sync_error_disclosure.py -q
3 passed
```

The guard asserts behaviour, not source text: the response must not contain the canary, must
contain `inspect server logs`, and the captured logger must contain the canary. Two controls keep
it honest — the source-level control proves the assertion rejects the old shape, and the
curated-`503` control proves the repair did not blanket-hide operator copy.

CI wiring: `.github/workflows/source-sync-error-contract.yml` selects `api/source_routes.py`,
`api/source_connections.py`, the guard and itself in **identical** `push` and `pull_request`
filters, is `workflow_dispatch`-able, and executes the guard in a step that can fail.
`tests/test_ci_gate_trigger_coverage.py` and `tests/test_workflow_injection_boundary.py` pass
(229 passed in the bundle).

`printf '<path>\n' | python scripts/cp10_mutation_boundary_policy.py --judge` → **PASS** for every
path this change adds.

## 8. Residual — recorded, not repaired

1. **`api/plan_routes.py` 500** returns `detail=str(e)` and logs nothing — the only unowned site
   in the inventory and the *more* severe shape (no diagnostic at all). Blocked on merge
   sequencing with `#718` (§6).
2. **`api/source_routes.py::connect_source` 503** remains by design (§5) but is still counted in
   `#718`'s record as debt; the truthful resolution is a `curated-diagnostic` marker at that site,
   which is `#718`'s mechanism and must ride with it.
3. **Open `#718` carries `data/engineering_lab/agent_events.jsonl`** in its file list — a runtime
   artifact of the Engineering Lab event log. The sandbox that prevents it is open **#688**. This
   is a review finding for the human reviewing `#718`, not a change this cycle may make.
4. **The external-provider gate** (§4) makes 21 PRs read `UNSTABLE`. Changing its classification
   is a gate-design decision reserved to the sovereign.

## 9. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production revision identical, `revision_conflict:
false`; `main` CI 8/8 success; 55 open PRs, 0 obsolete; baseline 23 failing/error nodes, all
reserved, environment-only, or repaired by an open PR. One unowned disclosure repaired with a
guard and a gate.

**Evidence.** This record; `tests/test_source_sync_error_disclosure.py`; the negative-control run
in §7; the deployed `/api/version` capture in §2; the PR-file inventory behind §6.

**Blockers.** (a) Merge execution is human-only (GOV-03; GOV-04 delegates only to a designated
human operator). (b) No branch protection or ruleset enforces review. (c) CE-01 and FINDING F-01
are sovereign-reserved. (d) The remaining error-contract residue is sequenced behind `#718`.

**Authorized next action.** Human review of this branch and of the queue. After `#718` lands, a
bounded follow-up may repair `api/plan_routes.py` and prune `RECORDED_DISCLOSURES` in the same
change.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; weakening
`n-atlas-external-beta.yml` to make the queue green; repairing `api/main.py`, `api/lab_routes.py`
or the `#717`/`#710`/`#713` modules; re-pinning F-01.

**Completion condition.** This cycle is complete when this record is reviewable, the branch
carries the repair and its guard, its gate executes the guard, `main` is unmodified, and no merge,
deployment or acceptance is claimed.

## 10. Runtime verification — the gate executed, not merely configured

Source-level wiring claims are the recurring defect this repository has recorded many times
("a guard no workflow executes is decoration"). The new gate was therefore proven at runtime on
the pull request, not asserted from YAML.

| observation | result |
|---|---|
| PR | **#735** (draft) |
| `source-sync-error-contract` check | **pass**, 37 s — run `45576890775` |
| its step log | `3 passed in 1.05s` — the guard **executed**, it is not a "no tests ran" green |
| all check-runs on the head | **15 / 15 pass** |
| `mergeStateStatus` | **CLEAN**, `mergeable: MERGEABLE`, `isDraft: true` |
| `native-arkadia-golden-workflow` | **pass** on this head — the same job that failed on `#733`, `#730`, `#725`, `#724`, `#721`, `#717`, `#712`, `#709`, `#700`, `#693`, `#681`. Direct confirmation of §4: the failure is external-provider availability, not the diff |

The last row is the negative control for §4: a job cannot be evidence about a branch when the
identical job flips between branches without those branches touching its inputs.

**No merge, deployment or acceptance is claimed.** The pull request is a draft for human review
under GOV-03/GOV-04.
