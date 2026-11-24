# ARK-OPS-CONTINUOUS-001 — Cycle 13

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 13 — immediate execution + hourly continuation
- **Observed:** 2026-11-24T16:06Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessors:** cycles 01-05 in this directory. Cycles 06-12 are recorded in their own PRs
  (`#712`, `#713`, `#714`, `#715`, `#716`, `#717`, `#718`, `#719`, `#720`) and are **not** carried
  here; see §6.
- **Substantive change this cycle:** the ledger entry below, plus the PR-title correction in §7.
  No application code changed, because no unowned defect was measurable (§4, §5).

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T17:23:48Z) | `GET /commits/main`; local `HEAD` agrees |
| open PRs | **44**, all `draft`, all `MERGEABLE`, **0** reviews, `reviewDecision` empty | `GET /pulls?state=open`; GraphQL `pullRequests(states:OPEN)` |
| branch protection / rulesets | none (`/branches/main/protection` -> 404) / `0` | REST |
| `api/main.py` | **2597** lines (budget 2600, **3** lines headroom) | `git show HEAD:api/main.py \| wc -l` |
| `main` check-runs | `boot-syntax`, `console-contract`, `engineering-scheduler` x2, `posture-currency`, `test`, `Full-history secret scan` all `completed/success`; `weaver_evolution` x5 `completed/skipped` | `GET /commits/<sha>/check-runs` |

`main` CI is green. No Vercel status appears on `main`, consistent with the retired-Vercel
boundary recorded in the 2026-10-11 addendum.

## 2. Production boundary — VERIFIED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision       bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Source <-> running revision is **VERIFIED** and sha-identical to `main`.

**Transient, recorded not promoted.** The first probe of this cycle exited `28` (curl timeout) at a
5 s ceiling; three subsequent probes returned 200 in 0.28-2.11 s. That is the Render cold-start
behaviour already recorded for this alias, not a runtime fault. A single timed-out probe is not
evidence of an outage.

## 3. Declared-endpoint probe (read-only, GET only)

Every non-templated entry of `web/arkadia_console/src/lib/endpoints.ts` was requested against the
canonical origin. **Zero 5xx responses.** Statuses decompose as expected, not as defects:

| class | statuses | entries |
|---|---|---|
| served anonymously | `200` | `version`, `health`, `transmissions`, `echoes`, `publicCodex`, `stellarCartography`, `knowledgeStatus/Graph/Timeline/Projects/Providers`, `sources`, `providerKeys`, `ttsStatus`, `ttsVoices`, `labNAtlasCatalog` |
| auth-gated | `401` | `me`, `codex`, `identitySpine`, `field`, `arkanaThreads`, `lab*` (7), `canvas`, `canvasSurfaces`, `solspire*` (5), `aisProfile`, `approvals`, `voiceStatus`, `voiceEvents` |
| POST-only, so `GET` 404 is correct | `404` | `arkanaResonance`, `arkanaResonanceStream`, `knowledgeSearch`, `tts` |

The POST-only families were confirmed against the route table, not inferred:
`api/main.py` registers `/api/commune/resonance` and `/api/tts` with `methods=['POST']`;
`api/arkana_stream_routes.py:107` is `@router.post("/api/commune/resonance/stream")`;
`api/knowledge_routes.py:218` is `@router.post("/search")`. A `GET` 404 here is not a defect.

## 4. Baseline — measured, and identical to the recorded fingerprint

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 19 failed, 4250 passed, 22 skipped, 1 error in 295.91s
```

Sorted `FAILED`/`ERROR` node set: **20** nodes,
`sha256 = 8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb`.

That hash equals the fingerprint recorded for this baseline, so the set is unchanged rather than
newly red. **No unowned, non-reserved defect is in the set.** Decomposition:

| nodes | classification |
|---|---|
| 1 | `tests/test_autonomy.py` — CE-01 `weaver.autonomy` module-vs-package collision. **Sovereign-reserved** |
| 1 | `test_m01_persistence::test_deletion_propagates_to_durable_corpus` — FINDING F-01 persistence boundary. **Sovereign-reserved** |
| 1 | `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` — FINDING F-01 proxy-invalidation, deliberately left failing rather than re-pinned to permit `sessionStorage`. **Sovereign-reserved** |
| 10 | `tests/test_mission_lifecycle_adapter_contract.py` — environment-only: needs `web/arkadia_console/node_modules/typescript` |
| 7 | repaired by open PRs: `#700` (2), `#693` (2), `#690` (1), `#691` (1), `#698` (1) |

Independently re-confirmed this cycle: the F-01 node fails on
`assert "sessionStorage" not in src`, and the guard's own docstring states it is left failing by
decision. It is a recorded governance item, not drift.

Other suites measured green at this revision: architecture **11 passed**; gate-integrity bundle
(`test_m02a_ci_gate_integrity`, `test_ci_gate_trigger_coverage`,
`test_ci_suite_collection_continuation`, `test_workflow_injection_boundary`,
`test_boot_syntax_boundary`) **331 passed**.

## 5. Open-queue composition — measured, because each PR is `MERGEABLE` against `main` only

`mergeable` answers "does this merge into its base", never "can these two merge together". File
overlap across the 44 open PRs:

```
paths touched by more than one open PR: 10
  3x api/main.py                                       -> 701, 711, 717
  2x scripts/gate2_production_observation.py
     + tests/test_gate2_production_observation.py      -> 681, 687
  2x scripts/lane_state_refresh.py                     -> 682, 684
  2x web/arkadia_console/src/lib/endpoints.ts          -> 692, 704
  2x .bootstrap/01_STATE.md, MISSION.md, NEXT_AGENT.md -> 693, 716
  2x solspire/console_router.py                        -> 710, 713
  2x api/arkana_stream_routes.py                       -> 717, 721
```

Pairwise merge performed in detached worktrees:

| pair | result |
|---|---|
| `#681` + `#687` | **CONFLICT** in `tests/test_gate2_production_observation.py` |
| `#682` + `#684` | clean |
| `#692` + `#704` | clean |
| `#710` + `#713` | clean |
| `#717` + `#721` | clean |

The one conflict is **already measured and resolved** by open PR `#703`
(`docs/control-plane/evidence/gate-hygiene-gate2-open-pr-composition-01/EVIDENCE.md` §2): the
conflicted region is two whole test sections appended at the same offset, and the composition is
semantically disjoint (the composed node count is exactly the sum of the deltas). This cycle did
not re-derive that record; it confirms the conflict still exists and is still the same one.

**The three-way `api/main.py` composition is safe.** All three branches are cut from the same base
(`bb19aabd`), so the composition is measurable directly:

| branch | delta on `api/main.py` | resulting lines |
|---|---|---|
| `main` | — | 2597 |
| `#701` | +15 / -19 | 2593 |
| `#711` | +2 / -2 | 2597 |
| `#717` | +1 / -6 | 2592 |
| **`#701` + `#711` + `#717` merged** | — | **2588** |

Merging all three in a worktree produced **zero** conflicted files and a composed
`api/main.py` of **2588** lines — 12 lines inside the 2600 budget. Headroom on `main` alone is only
3 lines, so this is worth stating: the queue does not currently threaten the budget, but any single
new PR adding >=4 lines to `api/main.py` would.

## 6. Ledger defect found and corrected

`#705`'s title claimed *"cycles 01-08 evidence"*, but its branch carried cycles **01-05** only, and
cycles 06-12 were recorded in their own PRs. The title therefore overclaimed content in one
direction while omitting real content in the other. Corrected in this commit.

**Cycle-number collisions are recorded, not reconciled.** Independent branches chose overlapping
numbers against the same predecessor: cycle 06 in both `#712` and `#714`; 07 in `#713` and `#715`;
08 in `#715` and `#716`; 09 in `#717` and `#721`. The evidence is not wrong — each record is
internally consistent — but the numbers are not a global sequence. A later pass should either
assign numbers at merge time or key records by PR number. This cycle uses **13**, above the highest
number in the queue (12, `#720`), so it collides with nothing.

## 7. What this cycle changed

1. This ledger entry.
2. `#705`'s title, corrected to describe what the branch actually carries.

No application code changed. §4 found no unowned defect, §5 found no composition defect that is not
already recorded, and the contract forbids opening a PR to appear productive. Under §2.1 the
authorized action on an OpenHands-owned PR is to maintain its description and evidence, which is
what this commit does.

## 8. Next-action block

**Current state.** `main` = `bb19aabd...`; production revision identical and
`revision_conflict: false`; `main` CI green; architecture 11 passed; gate integrity 331 passed;
baseline 20 failing/error nodes, all owned or sovereign-reserved. **44** open drafts, 0 reviews,
0 obsolete, no branch protection and no rulesets.

**Evidence.** This record; `#703` for the `#681`/`#687` composition; `#694` for the executable
open-PR inventory; the per-PR evidence records of `#690`-`#721`.

**Blockers.**
(a) **Merge execution is human-only (GOV-03)** and 44 drafts await human review. This is the
binding constraint on repository progress: `main` has not advanced past `#678` while twelve
further cycles of work have been recorded on branches.
(b) Branch protection and rulesets are **absent**, so no platform control enforces review. Enabling
them is a governance change, not an engineering one.
(c) CE-01 (`weaver.autonomy` collision) and FINDING F-01 (the persistence/proxy-invalidation pair)
are reserved to the sovereign.
(d) The `/api/webhook/github` anonymous push surface remains as disclosed; changing its
authorization is sovereign-gated.

**Authorized next action.** Human review of the queue. An agent may continue to maintain its own
drafts and record cycles, but it cannot reduce the queue: only a human merge can.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; adding an auth guard to
`/api/webhook/github`; re-pinning F-01 to permit `sessionStorage`; weakening a guard to manufacture
green; opening a PR with no measured defect.

**Completion condition.** This cycle is complete when this ledger entry and the corrected `#705`
title are reviewable, with `main` unmodified and no merge, deployment or acceptance claimed.
