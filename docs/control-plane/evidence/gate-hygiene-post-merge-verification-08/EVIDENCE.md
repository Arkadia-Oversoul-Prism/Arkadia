# EVIDENCE — gate-hygiene/post-merge-verification-08

Pass: `gate-hygiene/post-merge-verification-08` (Weaver hourly bounded execution)
Reconstructed: 2026-10-07T19:06–19:40 UTC
BASE_MAIN: `af3a3541d9fedf8c2d38bb7a0aac56856a879523`
Authority: human sovereign · documentation-only pass (no code, test, workflow, or product change)

## 1. Provenance (live)

| item | value |
| --- | --- |
| canonical clone | `main`, ancestry intact |
| `HEAD` == `origin/main` | `af3a3541d9fedf8c2d38bb7a0aac56856a879523` |
| first-parent tip | `af3a3541` = merge of #346 (`67aec9d2`) |
| credential | valid, **write-capable** (`Arkadia-Oversoul-Prism`; `permissions.push == true`) — no push to `main` performed |
| boot code | `python -m py_compile api/main.py` → OK |
| `api/main.py` | **2434 / 2600** lines (under budget) |
| architecture fitness | **11 passed** |
| `tests/test_m02a_ci_gate_integrity.py` | **64 passed** |
| CP10 boundary policy | PASS on this pass's staged paths (`exit=0`) |

**Correction to prior ledger:** earlier passes (and the automation contract) state the env
`GITHUB_TOKEN` is historically **read-only** for this repository, requiring a user-supplied PAT
to push. Measured this pass: the ambient credential returns
`permissions: {admin, maintain, push, triage, pull}` all `true` for the repo, and
`GET /user` → `Arkadia-Oversoul-Prism`. The read-only claim does **not** hold at `af3a3541`.
This is recorded so a future pass does not treat a working credential as a hard stop.

## 2. Baseline test-debt fingerprint (node set)

Full suite run with errors visible, as the repository requires:

```
python -m pytest tests/ -q --continue-on-collection-errors -rEf -p no:randomly
-> 10 failed, 1760 passed, 21 skipped, 1 error in 144.26s
```

| revision | result | nodes | outcomes fingerprint | ids fingerprint |
| --- | --- | --- | --- | --- |
| `af3a3541` BASE_MAIN (live) | 10F / 1760P / 21S / 1E | 11 | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` | `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` |
| recorded fixture (`tests/fixtures/baseline_node_set.txt`) | — | 10 | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` | `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |

Both fingerprints are **byte-identical to the pass-07 measurement** at the same SHA
(`f3e73647…` / `92d344d0…`). The node set is therefore stable and reproduced, not merely
re-counted. The recorded fixture remains a strict subset (10 of 11); the single extra live
node is `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points`,
owned by open PR #347.

## 3. Classification of every live failing/error node

Attributed by **node identity**, never by count. Reasons measured this pass with `--tb=line`.

| # | node | classification | measured reason |
| --- | --- | --- | --- |
| 1 | `ERROR tests/test_autonomy.py` | **CE-01 — sovereign, pre-existing** | `ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'` — the tracked package `weaver/autonomy/` shadows the tracked module `weaver/autonomy.py`. Interrupts collection. Reserved to the sovereign. |
| 2 | `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | **F-01 — sovereign, deliberate** | `assert 'sessionStorage' not in <LivingGate src>` — proxy invalidation awaiting a sovereign decision; re-pinning would loosen a persistence boundary. |
| 3 | `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | recorded fixture debt | `assert "Let's form your node." in <NodeEntry src>` — near-miss copy pin; the boundary intent is intact. |
| 4 | `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | recorded fixture debt | `assert 'arkanaSessionId' in <ArkanaCommune src>` — the shared-session wiring moved to `lib/arkanaSession.ts`; the assertion pins the old location. |
| 5 | `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | recorded fixture debt | `assert 'mvp1-50c0ee9b89' == 'mvp1-r1-patch'` — R1 `pass_id` delegation drift. |
| 6 | `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical` | recorded fixture debt | `assert 'execute_patch' in <weaver governance source>` — the name is absent from the `weaver/` primitives. |
| 7 | `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | **proposed workstream — sovereign product decision** | The test expects a blocked-result (`code == "MUTATION_DISABLED"`) while `solspire/execution_runtime.py:115` **raises `PermissionError`** ("Engineering mutation is disabled … Blocked tools: fs_write"). Refusal *shape* is a product/governance call. |
| 8–10 | `test_steward_filter.py::{test_blocks_identity_claims, test_allows_mythic_with_action, test_compress_to_choices}` | recorded fixture debt | Real assertion failures in `steward_filter` behaviour (identity-claim filter, choice compression), merged as `002b189`. |
| 11 | `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | **owned by open PR #347** | `assert 'One intelligence. Four ways to work with it.' in <landing src>` — stale headline literal; the live copy is `"One Prism. Many ways to work with it."` |

Every live node is classified. No node is unowned.

## 4. Open-PR inventory (live)

| PR | branch | base | state | role |
| --- | --- | --- | --- | --- |
| #349 | `feat/voice-of-belonging-content-pipeline` | `af3a3541` | open | content pipeline (different workstream) |
| #348 | `gate-hygiene/post-merge-verification-07` | `af3a3541` | open, `mergeable_state=clean` | pass-07 artifacts (this workstream, prior pass) |
| #347 | `gate-hygiene/landing-headline-repin-01` | `af3a3541` | open | landing-headline re-pin (owns live node 11) |
| #338 | `aeas-browser-runner-01` | `17e626cd` | open, `dirty` | AEAS browser runner (different workstream) |
| #337 | `aeas-01-native-operator-surface` | `af3a3541` | open | AEAS operator surface (different workstream) |

No open GATE-07 PR. Stale claims from earlier passes verified closed/unmerged this pass:
#329 (`9c7c5764`), #330 (`918337cc`), #342 (`55ad358c`) — all `CLOSED` at ~17:36Z.

## 5. New sovereign instruction discovered (this pass's selected task)

Issue **#345** — `ARK-$200K-G01 · Canonical Portfolio Substrate` (open, created
2026-10-07T17:32:09Z) carries one comment, `6043270954` at 17:32:27Z, whose body **begins with
`/weaver`** — the sovereign instruction token. Verbatim:

> `/weaver ARK-$200K-G01 implementation target: inspect the canonical relational substrate and
> Engineering Lab first; map the existing portfolio/initiative/budget/vendor/contract/milestone/
> work-event/evidence/acceptance/invoice/decision/outcome primitives; identify the smallest
> evidence-preserving implementation; produce a Gate 01 plan and proof-test proposal. Do not
> fabricate data, create a parallel store, merge, or deploy. Stop at any human/provider
> authorization boundary.`

The pass-07 `WORKSTREAM_STATE.md` explicitly directed: *"If a new sovereign instruction exists
on a PR/issue → execute that bounded task."* This pass executes it.

The instruction authorizes **four verbs** — inspect, map, identify, produce a plan and
proof-test proposal — and prohibits fabricating data, creating a parallel store, merging, and
deploying. It does **not** authorize committing a new substrate. The bounded deliverable is
therefore the plan document, and the pass stops at the authorization boundary the instruction
itself names.

### 5.1 Deliverable

`docs/readiness/ARK-200K-GATE-01-PLAN.md` — canonical-substrate inventory (14 `ew_*` tables,
the WorkEvent spine, Engineering Lab contracts, economic seams, the Decision primitive, the
enterprise structure), the twelve named nodes mapped to REUSE / STAGE / UNRESOLVED, the edge
carrier for each relation, the smallest additive schema that keeps a single store, the
proof-test harness with eight assertions and three negative controls, the regression and
rollback boundaries, and four staged options for sovereign selection.

### 5.2 `docs/readiness/ARK-200K-GATE-01-EVIDENCE.md` is deliberately NOT produced

Issue #345 requires that artifact to contain an *implementation commit SHA*, *test results*,
and *exact proof-test output*. None of those exist, because no substrate was implemented. The
instruction forbids *"mark[ing] the gate PASS without the proof test."* Producing the evidence
artifact now would be exactly that failure, so it is withheld and its absence is the honest
recorded state.

## 6. What this pass did **not** do

- No substrate implemented; no new table, model, or endpoint.
- No change to `api/main.py`, any workflow, any test, or any product surface.
- No merge, no push to `main`, no force-push.
- No baseline debt repaired (rule: do not fix baseline debt while executing an unrelated gate).
- No follow-on work inside #347 (sovereign-merge contract step 11).

## 7. Authority boundary

- Artifacts confined to `docs/readiness/` and
  `docs/control-plane/evidence/gate-hygiene-post-merge-verification-08/`.
- Human authority remains final for merge, deployment, and Gate 02 advancement.
- The next permitted action is **sovereign selection of an option in
  `ARK-200K-GATE-01-PLAN.md` §7**. Until then, no Gate 01 code is written.

*Where evidence stops, claim stops.*
