# ARK-OPS-CONTINUOUS-001 — cycle 14

_This evidence record was created by an AI agent (OpenHands) on behalf of the repository
owner. It records measurements only. **No merge was performed, nothing was deployed, and
no acceptance is claimed.** Merge execution is human-only under GOV-03._

- Observed at: `2026-11-24T17:23:58Z`
- Canonical branch: `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`
- Canonical production: `https://arkadia-qzu4.onrender.com`
- Work branch: `gate-hygiene/documented-route-extractor-http-verb-gate-01`

## 1. Reconciled state

| Boundary | Classification | Evidence |
|---|---|---|
| Canonical `main` | VERIFIED | live `GET /repos/.../commits/main` == local `origin/main` == `bb19aabd` |
| Source → runtime identity | VERIFIED | `GET /api/version` on the canonical alias returns `source_revision: bb19aabda34d59594615b0279a45e9cbd3d8204d`, `revision_source: RENDER_GIT_COMMIT`, `revision_conflict: false` |
| `main` CI | VERIFIED | 11 check-runs on `bb19aabd`: 11 success (5 × `weaver_evolution` skipped by design) |
| Lane-currency gate | VERIFIED | `python scripts/lane_state.py --check` exit 0; `--check --verify-live` exit 0 (`doc-guard lanes ['1','2','3','4']; deferred: []`) |
| Architecture suite | VERIFIED | `pytest tests/architecture` → 11 passed |
| Application behaviour | NOT CLAIMED | a matching revision is necessary evidence of source↔runtime consistency, not proof of correct behaviour |

Revision identity is not acceptance. Production acceptance remains **NOT CLAIMED**.

## 2. Baseline debt on `main` (measured, not inherited)

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
19 failed, 4250 passed, 22 skipped, 1 error in 284.20s
```

20 failing/error nodes; node-set sha256
`31653a5cc1e70e0cbac26c98b2bde3b7cec6fc27b93fcbadfb7c422da10b5505`.

Every node is accounted for. None is unattributed:

| Nodes | Disposition |
|---|---|
| 8 | repaired by an **open** PR: `test_identity_spine_w1` + `test_m02_reasomate_truth` (#700), `test_m01_persistence` + `test_m05_files` (#690 — stale scalar call into the project-scoped store), `test_solspire_r1_governance_convergence` ×2, `test_solspire_r3_execution_runtime` (#693/#691), `test_static_ingestion_idempotency` (#698) |
| 10 | **environment-only**: `tests/test_mission_lifecycle_adapter_contract.py` needs `web/arkadia_console/node_modules/typescript`, which is absent from this sandbox (`ls -d web/arkadia_console/node_modules` → absent) |
| 1 | **sovereign-reserved**: `ERROR tests/test_autonomy.py` — the CE-01 `weaver.autonomy` module-vs-package collision |
| 1 | **deliberate**: `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` — F-01 proxy-invalidation awaiting a sovereign decision; its own docstring says it is left failing on purpose |

## 3. Open-PR inventory (44 drafts, 0 reviews)

All 44 open PRs are drafts authored by `Arkadia-Oversoul-Prism`, `MERGEABLE`, with
`reviewDecision = none` and zero human reviews. `main` has not moved since
`2026-11-22T17:23:48Z`, so **nothing has landed for two days** while the queue grew.

Path overlap (measured over 211 PR-file rows):

| Path | PRs |
|---|---|
| `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md` | 716, 693 |
| `api/arkana_stream_routes.py` | 721, 717 |
| `api/main.py` | 717, 711, 701 |
| `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py` | 687, 681 |
| `scripts/lane_state_refresh.py` | 684, 682 |
| `solspire/console_router.py` | 713, 710 |
| `web/arkadia_console/src/lib/endpoints.ts` | 704, 692 |

## 4. Composition of the whole open set (the load-bearing measurement)

Reconstructing each PR's own tree and merging them sequentially onto `bb19aabd`, in
descending PR number order:

- **43 of 44 merge with zero textual conflicts.**
- **One conflict**: `#681` × `#687`, in `tests/test_gate2_production_observation.py` only
  (the script itself merges). `#703` already measures that pair; this record does not
  re-derive it. Recommended disposition: merge `#687` first, then rebase `#681`.
- Pairwise `git merge-tree --write-tree` over every overlapping pair agrees: the other
  seven collision groups are textually clean.

Gates on the composed tree (43 PRs, `#681` excluded):

| Gate | Result |
|---|---|
| `python -m py_compile api/main.py` | pass |
| `api/main.py` size | **2588 lines** (budget 2600) — the three PRs touching it (717: 2592, 711: 2597, 701: 2593) compose *below* budget |
| `pytest tests/architecture` | 11 passed |
| `scripts/cp10_mutation_boundary_policy.py --judge` over `git diff --name-only bb19aabd HEAD` | PASS |
| `scripts/lane_state.py --check` | exit 0 |
| full suite | `15 failed, 4734 passed, 22 skipped, 1 error` — 16 nodes, sha256 `284a6e019f85880d0cf8ec27c726dbda5d87adbf457629515cd1af6c42517b41` |

**Node-set delta against `main` (attributed by node identity, not by count):**

- **8 nodes repaired** (exactly the set listed in §2).
- **3 nodes added that did not fail on `main`** — three composition defects, each
  invisible to its own branch's CI:

| New failing node | Cause | Owner |
|---|---|---|
| `tests/test_repo_hygiene_gitignore.py::test_engineering_lab_event_log_is_not_tracked` | commit `c25e9d0a` in **#718** commits the runtime log `data/engineering_lab/agent_events.jsonl` (11,528 B) into the tree. `main` does not track it (`git ls-files data/engineering_lab/` → empty). **#688** adds the guard that forbids exactly this. | #718 (remove the file from the branch); #688 is correct |
| `tests/test_prism_ui_inventory_currency.py` ×2 | **#707** adds a guard that binds the Prism UI inventory to the console's declared surfaces; **#704** adds a `/reasomate` surface that the inventory does not carry. Reported: `surface 'reasomate' at /reasomate is not accounted for in the inventory`. | #707 must carry the `reasomate` row once #704 lands |
| `tests/test_documented_route_contract.py::test_every_documented_route_is_served` | **#709** rewrites `DEPLOYMENT_GUIDE.md` with component and environment-variable tables. The pre-existing guard's row regex read **any** two-cell backticked markdown row as an endpoint row, so it reported `ELEVENLABS_API_KEY kernel/tts.py` and `PORT entrypoint.sh` as documented-but-unserved routes. | **repaired in this PR** (below) |

Why the three defects were invisible on their own branches: the full-suite steps in
`sg-02-fe-2-v.yml` (CP10-B) and `provider-routing.yml` are non-judging (`continue-on-error`
/ candidate-vs-baseline), so a red node in the broad suite does not redden the PR. This is
the recorded "a broad-suite CI step does not gate" class; it is why a per-PR green is not
a composition proof.

## 5. The repair carried by this PR

`tests/test_documented_route_contract.py` now requires a table row to name HTTP methods in
its first cell before it is read as an endpoint:

```python
HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"})

def _is_endpoint_row(methods: str) -> bool:
    tokens = [token.strip().upper() for token in methods.split(",")]
    return bool(tokens) and all(token in HTTP_METHODS for token in tokens)
```

`_documented_routes()` skips rows that are not endpoint rows, and now takes an optional
`guide=` path so the detector can be exercised on a planted document.

Two controls keep the detector honest:

- `test_non_endpoint_rows_are_not_read_as_routes` — a `PORT` / `entrypoint.sh` row is not
  an endpoint row; a `GET` / `/api/heartbeat` row is.
- `test_the_detector_still_flags_a_documented_route_the_app_does_not_serve` — a planted
  guide naming `POST /api/totally-unserved-probe` must still be reported as
  documented-but-unserved. A `PORT`/`entrypoint.sh` row must not be.

Measured:

```
# on main (guide has only endpoint tables)
$ python -m pytest tests/test_documented_route_contract.py -q
11 passed

# on the composed tree (43 PRs) carrying #709's rewritten guide
$ python -m pytest tests/test_documented_route_contract.py -q
11 passed          # was: 1 failed, 10 passed

# live negative control on that same composed tree: delete the verb gate
$ python -m pytest tests/test_documented_route_contract.py -q -rEf
2 failed, 9 passed  # the real node AND the planted-route control both redden
```

The control therefore bites on the defect and stays silent on a legitimate non-endpoint
table — the detector was tightened, not disarmed.

Regression on the repair branch against `main`, measured in the same environment:

```
main   : 19 failed, 4250 passed, 22 skipped, 1 error   (20 nodes, 31653a5c…)
branch : 19 failed, 4252 passed, 22 skipped, 1 error   (20 nodes, 31653a5c…)
```

The failing/error node set is byte-identical (`diff` empty); the `+2 passed` is exactly the
two new controls.

Net effect on the composition: the composed-tree node set falls from 16 to **15**, leaving
only the two defects owned by other PRs (#718's tracked runtime log, #707's missing
`reasomate` row).

## 6. Disposition and next action

**Nothing here is mergeable by an agent.** Recommended human sequence:

1. Merge the 43 conflict-free PRs in any order, **or** merge `#687` before `#681` and
   rebase `#681` onto it.
2. Before merging `#718`, remove `data/engineering_lab/agent_events.jsonl` from that
   branch — otherwise `#688`'s guard reddens `main` on the merge commit.
3. Merge `#707` after `#704` and add the `reasomate` inventory row in the same change, or
   merge `#707` first and let `#704` add it.
4. This PR (`#709`-independent) can land at any point; it makes `#709` composable.

**Next authorized action for the next cycle:** with `main` frozen and 44 drafts open, the
highest-value unresolved work is not another PR. It is the two repairs above (owned by
already-open branches) plus the newly measured, **unowned** hygiene defect on `main`:
`data/weaver/continuation/current.json` is written at run time by
`weaver/continuation.py` (`DEFAULT_REL`) and is **tracked**, so every operator run dirties
the tree (5 commits of churn on that path). `.gitignore` has no rule for it and no open PR
owns it. That repair (untrack + ignore + guard, with a negative control) is proposed as the
next bounded cycle; it is not performed here because it must be measured against the
composed tree rather than inside this one.
