# ARK-OPS-CONTINUOUS-001 — Cycle 16

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`,
  recorded by open PR `#705`)
- **Cycle:** 16 — immediate execution + hourly continuation
- **Observed:** 2026-11-25T04:06Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Substantive change this cycle:** repaired the **5xx error contract of `api/main.py`** — eight
  handlers returned the uncaught exception's own text to the caller, and three of them logged
  nothing. One of the eight was failing **in production** at the deployed revision (§2).

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T17:30:03Z) | `GET /commits/main`; local `HEAD` agrees, tree clean |
| last merge | `#722` — GOV-04 bounded merge delegation | `git log` |
| open PRs | **50** — **49 drafts**, **1 non-draft** (`#724`), **0** carrying any comment | `GET /pulls?state=open` |
| branch protection / rulesets | absent (`/branches/main/protection` → 404) / `0` | REST |
| `main` check-runs at `fd0a4fdc` | 7 `completed/success` (`Full-history secret scan`, `boot-syntax`, `console-contract`, `engineering-scheduler`, `lane-doc-currency`, `posture-currency`, `test`) | `GET /commits/<sha>/check-runs` |

`main` CI is green at the current revision.

## 2. Production boundary — source↔runtime VERIFIED, one route FAILING

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision       fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Source ↔ running revision is **VERIFIED** and sha-identical to `main`.

Every one of the 15 declared console surfaces resolves to the SPA document at the canonical
origin (all `200 text/html`, `Accept: text/html`), so the serving path is intact for the product
shell.

**A bounded read-only inventory of the deployed API found exactly one server error.**
`scripts/production_runtime_probe.py` (anonymous, GET-only, output to `/tmp`, no mutation):

```
main_openapi_path_count 300   openapi_operation_count 344   get_routes_probed 160
classifications: reachable 39, protected 105, failing 1,
                 resource_not_found_route_present 6, route_reachable_request_shape_rejected 9
```

```
GET /api/codex/github-tree -> 502
{"error":"Client error '401 Unauthorized' for url
 'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main?recursive=1'\n..."}
```

The handler was:

```python
async def github_tree():
    try:
        tree = await _fetch_github_tree()
        return {"total": len(tree), "files": tree}
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})
```

Two defects in one line: the caller receives the **internal upstream host and the credential
state**, and the handler **logs nothing**, so the operator loses the cause at the same moment the
caller is told it. The upstream failure itself is owned elsewhere (§6).

## 3. Scope of the repair — measured, not assumed

A source-level AST scan of `api/main.py` for *a 5xx response carrying the exception bound by its
own `except` clause* found **eight** sites, not the one the probe exposed:

| line (pre-repair) | status | operation | logged before? |
|---|---|---|---|
| 1388 | 502 | Oracle resonance | yes, without traceback |
| 1777 | 502 | Spiral Codex GitHub tree | **no** |
| 1976 | 500 | personal file ingest | warning only |
| 2009 | 500 | personal note ingest | **no** |
| 2192 | 502 | TTS synthesis | yes, without traceback |
| 2402 | 500 | tool execution | **no** |
| 2531 | 502 | Oracle reply (spawn) | yes, without traceback |
| 2562 | 500 | spawn enqueue | yes, without traceback |

Fixing only the route the probe reached would have left seven instances of the same class, and a
guard written against one literal would have been trivially evadable.

## 4. Change

New module `api/http_failure.py`:

```python
def internal_failure_detail(operation: str) -> str:
    """Log the active exception and return caller-safe copy."""
    logger.exception("%s failed", operation)
    return f"{operation} failed; inspect server logs for internal details."
```

Each of the eight sites now calls it, e.g.

```diff
-    except Exception as e:
-        return JSONResponse(status_code=502, content={"error": str(e)})
+    except Exception:
+        return JSONResponse(status_code=502, content={"error": _internal_failure_detail("Spiral Codex GitHub tree")})
```

The helper is a separate module rather than an in-file function because `api/main.py` is at
**2598** lines against a **2600** budget (`tests/architecture/test_layer_boundaries.py:415`).
The import sits in the stdlib block, seven lines from the anchor `#701` inserts at, because a
worktree merge measured a one-line composition conflict when it sat beside `import os as _os`
(§6). The ingest site names the file the caller asked for, so it interpolates:
`_internal_failure_detail(f"Ingest of {file_name!r}")`.

**Deliberately preserved:** `POST /api/forge` still returns the per-image failure text in its
`200` body. That route is behind `X-Sovereign-Key` — the caller *is* the sovereign operator, so
the curated diagnostic is the point of the field, not a disclosure. The guard is scoped to 5xx
responses for the same reason: a `4xx` echoes a caller-caused message, which is not server-side
evidence.

## 5. Verification

**The guard** — `tests/test_api_5xx_error_contract.py`, 5 tests:

| test | property |
|---|---|
| `test_api_main_5xx_handlers_do_not_echo_the_exception` | the live `api/main.py` has no 5xx response carrying its handler's exception |
| `test_the_repaired_sites_use_the_shared_helper` | all eight sites still route through the helper |
| `test_detector_flags_the_pre_repair_shape` | negative control: the exact measured shape, and an f-string variant, are reported |
| `test_detector_is_silent_on_repaired_and_out_of_scope_shapes` | positive control: repaired code and a `4xx` echo are not reported |
| `test_github_tree_502_keeps_the_cause_in_the_log` | behaviour: the route returns `502` with no `api.github.com`/`401` in the body, and the cause appears in the log |

**Live negative control on the real file** (the only control that proves the guard reads the
deployed surface):

| step | result |
|---|---|
| revert `github_tree` to `except Exception as e: … str(e)` | `3 failed, 2 passed` |
| restore byte-identically (`sha256sum -c`) | `api/main.py: OK`, then `5 passed` |

**Suites actually run:**

```
tests/test_api_5xx_error_contract.py                          5 passed
tests/test_corpus_cache_coordination.py + tests/architecture   15 passed
tests/test_tool_execution_perimeter.py, test_authority_boundary.py,
  test_gate2_backend_observation.py, test_console_read_aloud_contract.py,
  test_engineering_lab_dispatch_truth.py,
  test_execution_workevent_boundary.py                        109 passed
tests/architecture + test_boot_syntax_boundary.py + new guard  21 passed
cp10_mutation_boundary_policy.py --judge (all changed paths)  PASS (exit 0)
python -m py_compile api/main.py                              OK
```

**Full suite once this cycle**, `PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q
-rEf --continue-on-collection-errors`:

```
20 failed, 4258 passed, 22 skipped, 1 error in 289.84s
sorted FAILED/ERROR node set: 21 nodes, sha256 cdf25fd81aa63bfa64e5845fba4944902f3ff2c1207c4e64df36f31a508dcfd8
```

**Regression attribution by node identity, not count.** The same eleven files were re-run on
unmodified `main` in the same environment (`git stash`, targeted run, `git stash pop`):
**20 nodes**, and the only difference is
`tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`
— the recorded **order-dependent shared-runtime node** (it passes in isolation: `2 passed` on
this branch; it is present in the `main` baseline cycle 15 measured at the same SHA; repaired by
open `#698`). No 5xx, ingest, spawn or TTS node is in the set. This diff introduces **zero**
failing nodes.

## 6. Ownership — what this cycle did not touch

| measured defect | owner |
|---|---|
| `github-tree`'s 401 against `api.github.com` (credential refused, public corpus read fails) | open `#701` — anonymous fallback in `api/github_corpus.py` |
| 5xx error contract in `api/knowledge_routes.py` / `api/economic_seam_routes.py` | open `#718` — same class, different modules; this change does not overlap its diff |
| Gate-2 deployment identity / marker oracle | open `#681`, `#687`, `#703` |
| runtime revision identity workflow | open `#697` |
| lane snapshot completeness | open `#684` |

The `github_tree` **route body** is not in `#701`'s diff (its `api/main.py` hunks are the corpus
client call sites, `sources()`, and the header helpers), so repairing the response contract here
does not duplicate it: `#701` removes the common cause, this change bounds what any remaining
cause can disclose.

**Composition measured, not assumed.** Three open PRs edit `api/main.py` (`#701`, `#711`,
`#717`). In a detached worktree at this branch's head, `git merge --no-edit` of each in turn
produced **zero** unmerged files at every step, and the composed tree ran:

```
tests/test_api_5xx_error_contract.py + tests/architecture +
  tests/test_corpus_cache_coordination.py + tests/test_github_corpus_credential_fallback.py
-> 29 passed          api/main.py 2589 lines
```

The first attempt did conflict: with the helper import beside `import os as _os`, `#701`'s own
insertion lands in the same three-line window (`CONFLICT (content): Merge conflict in
api/main.py`, 1 unmerged path). Moving the import into the stdlib block removed it — so this is
a measured repair of a real composition defect, not a claim that git is conflict-free.

## 7. Limitations

- `--continue-on-collection-errors` means the CE-01 `weaver.autonomy` collection error is still
  present in the full run; it is sovereign-reserved and untouched.
- The anonymous probe cannot distinguish `401` (unauthenticated) from `403` (unauthorized):
  `ARKADIA_PROBE_LOW_PRIVILEGE_BEARER` is unset. Recorded, not claimed.
- The 21-node set differs from cycle 15's 23-node measurement at the same `main` (two
  `test_prism_w4_lab_pr_state.py` nodes are absent here). Dependency set and run order move
  those classes; this record states its own measurement and does not restate cycle 15's.
- The 15-surface check proves the SPA document is served, not that the browser renders it
  correctly; no browser observation was taken this cycle.

## 8. Next-action block

**Current state.** `main` = `fd0a4fdc…`, production revision identical (`revision_conflict:
false`), `main` CI green, 50 open PRs (49 drafts, 1 non-draft, 0 comments), one production 5xx
repaired on a branch. The queue remains the binding constraint: fifteen cycles of work sit on
branches while `main` has not advanced past `#722`.

**Evidence.** This record; the probe artifact under `/tmp/arkadia-probe/` (read-only, not
committed); the node sets above; the negative control table in §5.

**Blockers.** (a) Merge execution is human-only (GOV-03; GOV-04 delegates only to a designated
human operator). (b) No branch protection or rulesets, so review is unenforced. (c) CE-01 and
FINDING F-01 are sovereign-reserved. (d) `/api/webhook/github`'s anonymous surface and
`scripts/prism_coherence_check.py`'s unwired findings remain disclosed and reserved.

**Authorized next action.** Human review of the queue. An agent may maintain its own drafts and
record cycles; it must not merge, deploy, or open a PR for a defect an open PR already owns.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; weakening a guard to
manufacture green (in particular, allowlisting a 5xx site instead of repairing it); re-pinning
F-01; adding an auth guard to `/api/webhook/github`.

**Completion condition.** This cycle is complete when this record is reviewable, the branch
carries the repair, its guard and this evidence, `main` is unmodified, and no merge, deployment
or acceptance is claimed.
