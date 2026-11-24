# ARK-OPS-CONTINUOUS-001 — Cycle 10: the HTTP 5xx error contract

**Cycle:** 10 · **Date:** 2026-11-24 · **Contract:** `ARK-OPS-CONTINUOUS-001` (rev. 2026-11-22)
**Branch:** `gate-hygiene/knowledge-5xx-error-contract-01` · **Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`

This cycle performs no merge, no deployment and claims no acceptance. Merge execution is
human-only under GOV-03; `main` is connected to production, so a merge is a release event.

## 1. Reconstructed state

| fact | measured |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` |
| local HEAD at cycle start | `bb19aabd` (identical; no drift) |
| production `/api/version` | `source_revision` = `bb19aabd…`, `revision_conflict: false`, `canonical_deployment: one_reconciled_deployment` |
| open pull requests | **40**, all drafts, all `base: main` |
| previous cycle | 09 (`#717`, Gemini model ladder) |

Production identity is necessary evidence of source↔runtime consistency. It is **not** proof
that the application behaves correctly and **not** deployment acceptance.

## 2. The verified gap

The Knowledge OS HTTP surface returned the **uncaught exception's own text** as the `detail` of
every 5xx. Sixteen sites in `api/knowledge_routes.py` were written as:

```python
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

The router resolves identity *optionally* (`_optional_user_id`), so these routes are reachable
without an authenticated identity, and the response was produced **without logging the cause** —
the operator lost the diagnostic at the same moment the caller received it.

Measured on `main` @ `bb19aabd` by driving the real route with a failing collaborator:

```console
$ # knowledge.pipeline.ingest patched to raise
$ #   RuntimeError("sqlite3.OperationalError: unable to open database file /srv/app/vault/private/secret-index.db")
POST /api/knowledge/ingest -> 500
{"detail":"sqlite3.OperationalError: unable to open database file /srv/app/vault/private/secret-index.db"}
```

An internal exception message can carry filesystem paths, SQL fragments and provider internals.
The same module already imported a logger (`arkadia.knowledge_routes`) and used it for warnings,
so the omission was not a missing capability.

The second half of the gap was already visible in the repository's own convention.
`api/economic_seam_routes.py` returned stable copy —

```python
raise HTTPException(status_code=500, detail="Seam assessment failed; inspect server logs for internal details.")
```

— and **never wrote to a log at all** (`grep -n logger api/economic_seam_routes.py` → no match
before this change). The instruction pointed at an empty record.

### Why this was not already owned

`api/knowledge_routes.py` is touched by **no** open pull request (`GET /pulls/{n}/files` over the
queue → 0 matches). `api/ceo_chat_routes.py` and `api/main.py` **are** touched (`#717`), and
`api/lab_routes.py` is an authority surface in `tests/architecture/LAYER_MAP.py`, so all three
were **recorded, not repaired** here.

## 3. The change

| file | change |
|---|---|
| `api/knowledge_routes.py` | 15 generic 5xx sites now call one helper that logs the cause and returns stable copy; the curated `RuntimeError` → `503` diagnostic is retained and marked |
| `api/economic_seam_routes.py` | the two generic 5xx handlers now log the cause they hide |
| `tests/test_http_error_contract.py` | the class guard: AST invariant + inventory ratchet + behavioural canary tests |
| `tests/test_http_error_contract_ci_wiring.py` | judges that a gate executes, selects and can fail on the guard |
| `.github/workflows/http-error-contract.yml` | the executable surface (selected by `api/**`, dispatchable) |
| `.github/workflows/economic-seam-engine.yml` | the guard entered that gate's content-derived domain (it names `api/economic_seam_routes.py`), so it is added to the executing step in the same change, as that gate's own contract requires |

The helper:

```python
def _internal_failure(operation: str) -> HTTPException:
    logger.exception("%s failed", operation)
    return HTTPException(
        status_code=500,
        detail=f"{operation} failed; inspect server logs for internal details.",
    )
```

The curated diagnostic is preserved rather than flattened:

```python
    except RuntimeError as e:
        # curated-diagnostic: the provider layer raises configuration copy
        # ("OPENAI_API_KEY not configured") that the caller needs.
        raise HTTPException(status_code=503, detail=str(e))
```

## 4. Verification

### 4.1 The guard bites — live negative control on the real module

One repaired site was reverted to `detail=str(e)` in the working tree, the guard was run, and the
file was restored byte-identically (`sha256` equal before and after):

```console
$ pytest tests/test_http_error_contract.py -q
FAILED test_repaired_modules_do_not_return_the_exception_text[api/knowledge_routes.py]
FAILED test_the_recorded_inventory_may_only_shrink
FAILED test_a_failing_knowledge_route_hides_the_cause_and_logs_it
3 failed, 9 passed
$ # restore
d6fdd2a2101b6b86205420ef28c4dc2ff73963498c655ba60afe1c92cdeddd17  api/knowledge_routes.py
d6fdd2a2101b6b86205420ef28c4dc2ff73963498c655ba60afe1c92cdeddd17  /tmp/kr.bak
$ pytest tests/test_http_error_contract.py -q
12 passed
```

The behavioural node reddens too, so the guard is not merely matching source text: with the
leak restored, the canary appears in the response body and the test reports it.

### 4.2 The guard's own controls

| control | assertion |
|---|---|
| pre-repair shape | `disclosed_details` reports `(5, 500, "str(e)")` |
| interpolated shape | an f-string carrying the cause is reported (`502`) |
| curated marker | a marked site is silent — a decision, not a leak |
| 4xx | a validation message is not the defect class |
| mention ≠ execution | `echo pytest <file>` and `# pytest <file>` do not count as execution |
| exemptions | step-level and job-level `continue-on-error`, and `if: false`, are reported |

### 4.3 Suites run

```console
$ python -m py_compile api/main.py api/knowledge_routes.py api/economic_seam_routes.py
COMPILE_OK
$ wc -l api/main.py
2597 api/main.py                       # budget 2600; untouched by this change

$ git diff --cached --name-only | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)

$ pytest tests/test_http_error_contract.py tests/test_http_error_contract_ci_wiring.py -q
23 passed

$ pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py \
    tests/test_ci_suite_collection_continuation.py tests/test_gate_filter_selection.py \
    tests/test_m02a_ci_gate_integrity.py tests/architecture \
    tests/test_http_error_contract.py tests/test_http_error_contract_ci_wiring.py -q
418 passed                            # includes architecture 11/11

$ pytest tests/test_knowledge_notes_boundary.py tests/test_knowledge_project_detail_boundary.py \
    tests/test_knowledge_projects_boundary.py tests/test_knowledge_timeline_boundary.py \
    tests/test_knowledge_graph_provenance_boundary.py tests/test_knowledge_graph_health_read_boundary.py \
    tests/test_knowledge_status_read_boundary.py -q
122 passed

$ pytest tests/test_economic_seam_ci_wiring.py -q
21 passed                             # after the guard joined the derived domain
```

### 4.4 Full suite

Measured on this branch (full session, one pass):

```console
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
21 failed, 4278 passed, 22 skipped, 1 error in 284.25s (0:04:44)
```

22 failing/error nodes. Attribution is by **node identity**, never by totals — the passed count
moves with the installed dependency set and with the nodes this change adds (`+23` from the two new
guards, plus the generic workflow-scanning suites gaining nodes by construction from the new
workflow file).

**Superseding measurement (full session on both trees, same environment).** The same full
command was run on pristine `main` @ `bb19aabd` in a detached worktree:

```console
main   (bb19aabd): 21 failed, 4248 passed, 22 skipped, 1 error in 283.43s   -> 22 nodes
branch (c25e9d0a): 21 failed, 4278 passed, 22 skipped, 1 error in 284.25s   -> 22 nodes
$ comm -13 <main nodes> <branch nodes>   # branch-only: (none)
$ comm -23 <main nodes> <branch nodes>   # main-only:   (none)
```

The failing/error **node sets are identical**, so this change introduces no node. The `+30 passed`
is the two new guards' 23 nodes plus the generic workflow-scanning suites gaining nodes by
construction from the new workflow file — attributable by `--collect-only`, not inferred from the
count.

The earlier targeted measurement is retained because it isolates the one node that moves. A
re-run of the same eleven files on pristine `main` @ `bb19aabd` yielded **21** of the 22 nodes; the
single difference was

```
tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
```

which **passes in isolation on both trees** (`tests/test_m01_persistence.py
tests/test_static_ingestion_idempotency.py -q` → `1 failed, 14 passed` on both, the failure being
the pre-existing `test_deletion_propagates_to_durable_corpus` `TypeError: delete_file() missing 1
required positional argument: 'file_id'`, identical on `main`). It is the order-dependent
shared-runtime class already recorded for this node — it reads the canonical oracle store, and no
file this change touches participates in that path. It is **not** attributed to this branch.

The environment-only `test_mission_lifecycle_adapter_contract.py` nodes fail for a missing
`web/arkadia_console/node_modules/typescript`; they fail identically on `main`.

## 5. Limitations

- **No route was repaired in `api/main.py`, `api/ceo_chat_routes.py` or `api/lab_routes.py`.**
  The first two are edited by an open pull request; the third is an authority surface whose
  repair is sovereign-gated. They remain in `RECORDED_DISCLOSURES`, which the guard ratchets:
  the record may only shrink, and a module that reaches zero must be pruned in the same change.
- The detector recognises the two shapes present in the corpus (a bare `str(e)` and an f-string
  carrying the cause). A handler that launders the cause through another variable is not
  detected; the behavioural tests cover the two repaired modules, not the recorded ones.
- `logger.exception` writes to the process log. Whether the deployment's log sink retains it is
  **NOT TESTED** — this cycle proves the call is made, not that an operator can read it.
- The new gate is path-filtered to `api/**`. A change that touches only `tests/` still reaches the
  guard through `economic-seam-engine.yml` (which selects `tests/**` and now executes it), but a
  change outside both filters does not.
- No provider call was made; no production route was exercised.

## 6. Next-action block

**Current state.** `main` = `bb19aabd…`, unmodified. Production `source_revision` identical,
`revision_conflict: false`. 40 open drafts. This branch adds one repair, one guard, one wiring
judge and one gate.

**Evidence.** This record; the live negative control in §4.1; the suites in §4.3–4.4.

**Blockers.** (a) Merge execution is human-only (GOV-03). (b) CE-01 (`weaver.autonomy`
module-vs-package collision) and FINDING F-01 remain reserved to the sovereign. (c) The remaining
`RECORDED_DISCLOSURES` need their own bounded change; `api/main.py` and `api/ceo_chat_routes.py`
must wait for `#717` to land.

**Authorized next action.** Human review of this draft. A later cycle may take the recorded
disclosure inventory, beginning with `api/source_routes.py` and `api/plan_routes.py` (neither is
owned by an open PR nor an authority surface).

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; broadening
`RECORDED_DISCLOSURES` to make a new leak pass; flattening the curated 503 diagnostic.

**Completion condition.** This cycle is complete when this record and its draft PR are
reviewable, with `main` unmodified and no merge, deployment or acceptance claimed.
