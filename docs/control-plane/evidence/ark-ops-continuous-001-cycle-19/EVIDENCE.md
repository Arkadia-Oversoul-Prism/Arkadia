# ARK-OPS-CONTINUOUS-001 — Cycle 19

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22` (recorded by this PR)
- **Cycle:** 19 — immediate execution + hourly continuation
- **Observed:** 2026-11-25T09:06Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. This cycle performed no
  merge, no push to `main`, no deployment, and claims no acceptance.
- **Substantive change:** none to production code. The cycle's work is a **complete re-derivation
  by measurement of the baseline decomposition** that cycles 15 and 18 had each asserted from
  different evidence, plus one contradiction between those records resolved empirically. No new
  PR was opened: the binding constraint is human review of the existing queue, not a missing fix.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T18:30:03+01:00) | `git rev-parse HEAD` == `origin/main` after `git fetch`; tree clean |
| last merge | `#722` — GOV-04 bounded merge delegation | `git log -1` |
| open PRs | **56** — 55 drafts, 1 non-draft (`#724`), 0 reviews | `GET /pulls?state=open` (paginated) |
| `main` check-runs at `fd0a4fdc` | 7 `success` + 1 `skipped` (`weaver_evolution`) | `GET /commits/<full sha>/check-runs` |
| combined commit status at `fd0a4fdc` | `pending` with **0** statuses | `GET /commits/<full sha>/status` |
| branch protection | **absent** (`/branches/main/protection` -> 404) | REST |
| rulesets | **0** | `GET /rulesets` |
| `api/main.py` | **2597** lines (budget 2600) | `wc -l`; untouched by this cycle |

The `pending` aggregate is a GitHub artifact of having **no** legacy commit statuses at all; the
check-runs are the authoritative signal and 7/8 are `success`, the eighth `skipped` by design.
Recorded so a later cycle does not read `pending` as a red gate.

## 2. Production boundary — VERIFIED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision       fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Source <-> running revision is **VERIFIED** and sha-identical to `main`. That is consistency
evidence, not acceptance.

**Transient, recorded not promoted.** The first probe of this cycle printed nothing within the
terminal window; the immediate retry answered `200` in **9.76 s** and a third in `0.16 s`. That is
the Render cold-start behaviour already recorded for this alias. One slow probe is not an outage.

## 3. Live surface probes — read-only, all healthy

| route | status | note |
|---|---|---|
| `/health` | 200 | `{"status":"radiant"}` |
| `/api/health` | 404 | **correct** — `/api/health` is not a backend route; only `/health` is |
| `/api/version` | 200 | revision probe |
| `/api/stellar-cartography` | 200 | living readout served |
| `/api/scrolls` | 200 | `{"scrolls":[]}` |
| `/api/echoes` | 200 | public feed served |
| `/api/lab/engineering/n-atlas/catalog` | 200 | effective provider state readable |

## 4. Console contract oracle — 45/45 declared endpoints served

The console's canonical map (`web/arkadia_console/src/lib/endpoints.ts`) declares **45** endpoints.
Each was compared against the **deployed** `GET /openapi.json` (**300** served paths) after
normalizing `{param}` segments on **both** sides:

```
declared=45  served_paths=300
UNSERVED declared endpoints: 0
```

Zero drift. The inverse check (a console surface calling an undeclared path) was run by scanning
`web/arkadia_console/src` for inline `"/api/..."` / `"/solspire/..."` literals outside the map; the
only live call sites outside the map are in `operator/`, and the one consequential example,
`GET /api/operator/security-verification`, **is** served (`['get']`). Recorded as a measured
negative: there is no endpoint drift to repair this cycle.

## 5. Console typecheck — clean

`web/arkadia_console`: `corepack pnpm install --frozen-lockfile` then `npx tsc --noEmit` ->
**exit 0, no diagnostics**. This is the check that catches the dead-identifier class previously
found in this repository (a constant referenced but never defined, swallowed by a `try/catch`). The
active app carries none.

## 6. Baseline — measured once, decomposition re-derived by measurement

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 20 failed, 4253 passed, 22 skipped, 6 warnings, 1 error in 288.57s (0:04:48)
```

Sorted `FAILED`/`ERROR` node set: **21** nodes.

| fingerprint convention | value |
|---|---|
| outcomes (raw `FAILED `/`ERROR ` lines, sorted) | `24a941407c74f98539cd129d58f4cf1527ab736a371ccf5506ce7c5f54c9e2a8` |
| ids (prefix-stripped, sorted) | `3410a43109d45954c262cf41af01b51804402b55a83defac937d97719288f057` |

**Every node was independently re-verified this cycle rather than inherited from a prior record.**
Each "repaired by open PR" claim was tested by merging that PR's branch onto `main` in a detached
worktree and running the named nodes:

| node(s) | n | classification | measured this cycle |
|---|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | sovereign-reserved (CE-01) | `ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'` — module-vs-package collision, confirmed |
| `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` | 1 | sovereign-reserved (FINDING F-01) | `assert 'sessionStorage' not in src` — the deliberate pin; re-pinning it is a sovereign decision, confirmed |
| `tests/test_mission_lifecycle_adapter_contract.py::*` | 10 | environment-only | **10 passed** once `web/arkadia_console/node_modules/typescript` existed (`pnpm install`). Absent in a bare sandbox; CI provisions it |
| `test_gov04_bounded_merge_delegation::test_bounded_merge_is_exact_head_and_protected_fail_closed` | 1 | repaired by **#725** | **1 passed** with `#725` merged |
| `test_identity_spine_w1::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`, `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` | 2 | repaired by **#700** | **2 passed** with `#700` merged |
| `test_m01_persistence::test_deletion_propagates_to_durable_corpus`, `test_m05_files::test_update_file_supports_rename` | 2 | repaired by **#690** | **2 passed** with `#690` merged |
| `test_solspire_r1_governance_convergence::*` | 2 | repaired by **#693** | **5 passed** (file) with `#693` merged |
| `test_solspire_r3_execution_runtime::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | 1 | repaired by **#691** | **4 passed** (file) with `#691` merged |
| `test_static_ingestion_idempotency::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` | 1 | repaired by **#698** | **1 passed** with `#698` merged |

Totals: **1 reserved + 1 reserved + 10 environment-only + 9 repaired by open PRs = 21.**

### 6.1 A contradiction between two cycle records, resolved by measurement

Cycle 15 classified `test_m01_persistence::test_deletion_propagates_to_durable_corpus` as
**FINDING F-01, sovereign-reserved**. Cycle 18 classified the same node as **repaired by open
`#690`**. Both cannot be true, and the difference decides whether a node is reserved to the human
or already has a fix waiting in the queue.

Measured this cycle: with `#690` merged onto `main`, that node and the `#690`-owned
`test_m05_files::test_update_file_supports_rename` both pass (`2 passed in 0.17s`). Cycle 18's
classification is **correct**; cycle 15's is **superseded**. The F-01 reservation applies to the
`sessionStorage` pin in the Living Gate test (row 2 of the table above), not to the corpus-deletion
node — two different failures that a shared label had conflated.

This is recorded rather than argued: a reserved node is a node a human must decide, so an incorrect
reservation both wastes the sovereign's attention and hides an available repair.

## 7. Open-PR queue — the binding constraint, measured

The queue tool from open `#733` was executed against the live repository (read-only):

```
56 open PRs | 0 evidence errors
DRAFT_OWNER_ACTION                  55
MERGEABILITY_UNKNOWN                 1
Composition clusters: [[681, 687], [682, 684], [686, 724], [689, 707, 728], [692, 704],
                       [693, 716], [701, 711, 717, 721, 729], [710, 713], [718, 734]]
READ-ONLY: no PR state or repository mutation performed.
```

**Zero obsolete PRs.** No open head is an ancestor of `main`, and no open diff reverse-applies to
`main`, so nothing is closeable as already-landed. All 56 report `MERGEABLE`.

**The largest cluster is `[701, 711, 717, 721, 729]`** — five PRs whose changed paths overlap. Four
of them touch `api/main.py`, the file under a hard 2600-line budget. That overlap was measured
rather than assumed:

| PR | `api/main.py` lines on its own head |
|---|---|
| `main` | 2597 |
| #729 | 2598 |
| #711 | 2597 |
| #701 | 2593 |
| #717 | 2592 |

All four merged together in a detached worktree (`git merge` each in turn): **zero conflicted
paths**, composed `api/main.py` = **2589 lines** — 11 lines of headroom. So the cluster is a real
review-ordering concern but **not** a budget breach, and this is a measured negative rather than an
open defect.

## 8. Verification of the queue's own claims

An open PR that asserts untested behaviour is a review hazard: the reviewer must either trust the
claim or re-do the work. Five open PRs add or own test files; each was executed at its own head:

| PR | new test file(s) | result |
|---|---|---|
| #733 | `tests/test_pr_batch_reconcile.py` | **5 passed** |
| #734 | `tests/test_prism_coherence_domain.py` | **6 passed** |
| #730 | `tests/test_vacuous_assertion_guard.py` | **3 passed** |
| #726 | `tests/test_gov04_platform_preconditions*.py` | **13 passed** |
| #729 | `tests/test_api_5xx_error_contract.py` | **5 passed** |

`#733`'s body states its tests "were not executed in this connector session"; they were executed
this cycle and pass, and its tool was additionally exercised against live data (§7). That PR's
description is updated with the measured result rather than leaving the caveat standing.

## 9. Static sweep — no unowned code defect found

`pyflakes` over `api/ kernel/ solspire/ lab/ knowledge/ weaver/ scripts/`:

- **undefined names: 0** — the dead-identifier class is absent
- two `redefinition of unused` findings, both pre-existing and not defects: a duplicate `httpx`
  import in `api/ceo_chat_routes.py`, and `github_webhook` naming two *different* routes in
  `api/main.py` (`/api/github/webhook` and `/api/webhook/github`)

The second is worth naming precisely: it is a **name collision, not a routing bug** — both
decorators register distinct handlers. The security asymmetry it exposes (the
`/api/webhook/github` surface validates no HMAC while `/api/github/webhook` does) is the
already-disclosed anonymous surface, and hardening it is **reserved** — adding an auth guard there
is listed as forbidden work in cycle 18 and is not touched here.

## 10. Ledger state

Cycles 01-05, 13 and 15 are carried by this PR as evidence files; cycles 06-12, 14 and 16-18 live in
their own PRs. This cycle uses **19**, above every number in the queue. Keying records by PR number
at merge time remains the unowned fix; it changes what the ledger means, so it is recorded rather
than executed.

## 11. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production revision identical, `revision_conflict:
false`; `main` CI 7 success + 1 skipped; 56 open PRs (55 drafts, 1 non-draft), **0 obsolete**;
baseline 21 failing/error nodes, every one re-verified this cycle as reserved (2),
environment-only (10), or repaired by a named open PR (9). Console typechecks clean; 45/45 declared
endpoints served; the five-PR `api/main.py` cluster composes to 2589 lines with zero conflicts.

**Evidence.** This record; §6's per-PR merge-and-run table; §7's live queue packet; §4's endpoint
oracle; §5's typecheck; §2's deployed revision capture.

**Blockers.**
(a) **Merge execution is human-only** (GOV-03; GOV-04 delegates only to a designated human
operator). 55 drafts await owner action and human review; `main` has not advanced past `#722`
while nineteen cycles of work sit on branches. This is the binding constraint.
(b) Branch protection and rulesets are **absent**, so no platform control enforces review; enabling
them is a governance decision.
(c) CE-01 and FINDING F-01 (2 nodes) are reserved to the sovereign.
(d) The `/api/webhook/github` anonymous surface remains disclosed and reserved.

**Authorized next action.** Human review of the queue. An agent may keep maintaining its own drafts
and recording cycles; it cannot reduce the queue, and it must not open a PR for a defect another
open PR already owns. There is currently **no measured, unowned defect** for a new PR to carry.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; re-pinning F-01 to permit
`sessionStorage`; adding an auth guard to `/api/webhook/github`; weakening a guard to manufacture
green; opening a PR with no measured, unowned defect.

**Completion condition.** This cycle is complete when this record is reviewable, `main` is
unmodified, `#733`'s unverified claim carries its measured result, and no merge, deployment or
acceptance is claimed.
