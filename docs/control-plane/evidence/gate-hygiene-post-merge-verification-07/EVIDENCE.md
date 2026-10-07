# EVIDENCE — gate-hygiene/post-merge-verification-07

Pass: `gate-hygiene/post-merge-verification-07` (Weaver hourly bounded execution)
Reconstructed: 2026-10-07T18:06–18:25 UTC
BASE_MAIN: `af3a3541d9fedf8c2d38bb7a0aac56856a879523`
Authority: human sovereign · Artifact-only pass (evidence only, no code/test/workflow change)

## 1. Provenance (live)

| item | value |
| --- | --- |
| canonical clone | `main`, ancestry intact |
| `HEAD` == `origin/main` | `af3a3541d9fedf8c2d38bb7a0aac56856a879523` |
| first-parent tip | `af3a3541` = merge of #346 (`67aec9d2`) |
| `gh` auth | valid (`Arkadia-Oversoul-Prism`, HTTPS) — write-capable session, no push performed |
| boot code | `python -m py_compile api/main.py` → OK |
| `api/main.py` | **2434 / 2600** lines (under budget) |
| CP10 boundary policy | PASS on this pass's two paths (`JUDGE_EXIT=0`) |

First-parent chain reconstructed from live history:

```
af3a3541  Merge PR #346 (post-merge verification 06)
75d18b2d  Merge PR #334 (gate07: schema ⊆ router vocabulary closure)
1a9d5ce5  Merge PR #331 (gate07: scheduler failure-path reporting)
```

## 2. GATE-07 chain — merged and closed (reconstruction)

At the previous pass's reconstruction (#346) the frontier was recorded as: #334 open with a
stale base, and #329/#330/#342/#343 "open and superseded". **Both statements are now
superseded by live state.** Measured via the GitHub API:

| PR | title | live state | mergedAt / closedAt | head |
| --- | --- | --- | --- | --- |
| #334 | gate07: schema ⊆ router vocabulary seam + CI wiring | **MERGED** | 2026-10-07T17:52:18Z (merge `75d18b2d`) | `9ce560bc3` |
| #344 | gate07: strict-xfail composition reconciliation | MERGED | 2026-10-07T17:34:21Z (merge `7f5ec610`) | `0127780cb` |
| #346 | gate-hygiene: post-merge verification 06 | MERGED | 2026-10-07T17:52:32Z (merge `af3a3541`) | `67aec9d2c` |
| #329 | gate07: worker→attention composition seam | **CLOSED (not merged)** | 2026-10-07T17:36:08Z | `9c7c57644` |
| #330 | gate07: verification record for the seam guard | **CLOSED (not merged)** | 2026-10-07T17:36:05Z | `918337cc9` |
| #342 | gate07: router clean stop vs blocked frontier | **CLOSED (not merged)** | 2026-10-07T17:36:03Z | `55ad358cf` |
| #343 | gate07: strict-xfail composition reconciliation | **CLOSED (not merged)** | 2026-10-07T17:36:00Z | `b3ec78c94` |

The four superseded PRs were **closed four seconds apart** at 17:36, i.e. immediately after
the #344 merge at 17:34 and *before* the #346 evidence pass closed at 17:52. The #346
evidence therefore recorded a state that had already changed — a stale snapshot, not a
defect in the merge. **GATE-07 has no remaining open PR.**

## 3. Baseline test-debt fingerprint (node set)

Full suite run with errors visible, as the repository requires:

```
python -m pytest tests/ -q --continue-on-collection-errors -rEf -p no:randomly
```

| revision | result | nodes | outcomes fingerprint | ids fingerprint |
| --- | --- | --- | --- | --- |
| `af3a3541` BASE_MAIN (live) | 10F / 1760P / 21S / 1E | 11 | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` | `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` |
| recorded fixture (`tests/fixtures/baseline_node_set.txt`) | — | 10 | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` | `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |

The recorded fixture is a **strict subset** of the live set. Set difference (live − fixture)
is exactly **one** node:

```
FAILED tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points
```

That node is **owned by open PR #347** (`gate-hygiene/landing-headline-repin-01`). Zero
fixture nodes are absent from the live run. The previous pass (#346) measured the same pair
`92d344d0…` on both its BASE and MERGED trees; this pass reproduces `92d344d0…` on the
current tip, so the merged #334/#346 cluster introduced **no new failing node**.

## 4. Classification of every live failing/error node

Attribute by **node identity**, never by counts (the passed count is order-dependent via
`test_agent_loop_does_not_mutate_repository`).

| # | node | classification | evidence |
| --- | --- | --- | --- |
| 1 | `ERROR tests/test_autonomy.py` | **CE-01 — sovereign, pre-existing** | `weaver/autonomy` package shadows `weaver/autonomy.py`; `ImportError: cannot import name 'load_autonomy_config'`. Interrupts collection (hence `--continue-on-collection-errors`). Reserved to the sovereign. |
| 2 | `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | **F-01 — sovereign, deliberate** | Docstring: proxy-invalidation awaiting a sovereign decision; deliberately left failing; re-pinning would loosen a persistence boundary (governance, not hygiene). |
| 3 | `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | recorded fixture debt | `assert "Let's form your node." in src` — near-miss copy pin; the boundary intent (NodeEntry is the AIS signup surface) is intact. |
| 4 | `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | recorded fixture debt | `assert "arkanaSessionId" in commune` — the shared-session wiring moved to `lib/arkanaSession.ts`; assertion pins the old identifier location. |
| 5 | `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | recorded fixture debt | R1 `pass_id` delegation — recorded as an open proposal in `.bootstrap/01_STATE.md`. |
| 6 | `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical` | recorded fixture debt | `assert "execute_patch" in source` — the name is not in `weaver/` governance primitives; R1 delegation item. |
| 7 | `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | **proposed workstream — needs sovereign product decision** | Contradiction recorded in `gate-hygiene-commit-file-refusal-contract-01/WORKSTREAM_STATE.md`: the R3 test expects a **blocked-result** (`results[0]["code"] == "MUTATION_DISABLED"`) while `solspire/execution_runtime.py::execute` **raises `PermissionError`** (line 115) and `test_convergence_mutation_boundary.py` asserts the raise. Refusal *shape* (raise vs blocked-result) is a product/governance call. **Not in this pass's envelope.** |
| 8–10 | `test_steward_filter.py::{test_allows_mythic_with_action, test_blocks_identity_claims, test_compress_to_choices}` | recorded fixture debt | Real assertion failures in `steward_filter` behaviour (identity-claim filter and choice compression), merged as `002b189`. |
| 11 | `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | **owned by open PR #347** | Stale landing-headline literal. Independently reproduced below. |

Every node is classified. No node is unowned.

## 5. Independent verification of open PR #347 (step-04, do not extend its scope)

PR #347 · branch `gate-hygiene/landing-headline-repin-01` · head
`3f3024d97290183d2c5014f5d102c38354c53ad6` · base `main` · MERGEABLE · created
2026-10-07T18:05:44Z.

Applied `gh pr diff 347` to a detached worktree at `af3a3541` (clean apply) and measured the
affected test file, with the unpatched tree as a **negative control**:

| tree | `tests/test_ais_capability_profile_onboarding.py` |
| --- | --- |
| `af3a3541` (control) | **1 failed, 3 passed** — the stale literal |
| `af3a3541` + #347 patch | **4 passed** |

The diff re-pins the landing headline to the live architecture copy
(`"One Prism. Many ways to work with it."`) and attributes the drift to `2b87e8e` (#276),
a source change with no test-side re-pin. The change is **test-side only**; it does not
touch `api/main.py`, any workflow, or any product surface.

**Per the sovereign-merge contract step 11, this pass performs no follow-on work inside
#347.** The verification above is read-only measurement. #347 is `READY FOR SOVEREIGN MERGE`.

## 6. Open-PR inventory (live)

| PR | branch | head | state | role |
| --- | --- | --- | --- | --- |
| #347 | `gate-hygiene/landing-headline-repin-01` | `3f3024d97` | MERGEABLE | landing-headline re-pin (this workstream's frontier) |
| #337 | `aeas-01-native-operator-surface` | `afc3c3d76` | MERGEABLE / UNSTABLE | AEAS-01 operator surface (different workstream) |
| #338 | `aeas-browser-runner-01` | `903acf415` | **CONFLICTING / DIRTY** | AEAS browser runner (different workstream) |

No open GATE-07 PR. No open PR in this hygiene workstream other than #347.

## 7. Declared proposals — live disposition

`.bootstrap/01_STATE.md` records three "proposed bounded work" items and several standing
non-K candidates. Each measured this pass:

| proposal | live state | disposition |
| --- | --- | --- |
| *Reconcile `tests/fixtures/baseline_node_set.txt`* (10 recorded vs 20 live) | recorded fixture = 10; live = 11, of which the single extra node is #347's | **Already reconciled** by the `18→10` retirement pass; the live−fixture delta is now just the open #347 node. Superseded prose. |
| *Widen `provider-routing.yml` to `api/**`* | `provider-routing.yml` still filtered to `weaver/**`, `providers/**`, `tests/architecture/**`, named tests | **Still open.** Held back deliberately: the same workflow runs the full suite, which carries baseline debt, so widening first would redden every API PR with debt it did not introduce. Prerequisite (baseline not red) is **not met** (11 debt nodes). **Not selectable now.** |
| *Resolve PR #294's review-record boundary regression* | #294 **MERGED**; `tests/test_verification_review_boundary.py` → **10 passed** | **Resolved.** Proposal is stale. |

Standing candidates still requiring a sovereign ruling: `weaver.autonomy` module/package
shadowing (CE-01, node 1 above), Spiral Grove registry ordering contract, baseline test debt.
**None is authorized to this pass.**

## 8. Why this pass is evidence-only

The pass applied the mandated selection rule — *smallest valid next task, with explicit
scope / completion condition / evidence requirement / regression boundary / authority
boundary* — to the live queue and found **no node that is both unowned and inside the
pre-authorized engineering envelope**:

- The one live node owned by an open PR (#347) is already fixed on that PR; step 11 forbids
  beginning follow-on work inside it.
- Every other live node is either CE-01 (sovereign), F-01 (sovereign, deliberate), a
  recorded fixture-debt item whose home proposal needs a sovereign ruling (R1/R3/steward),
  or the documented-but-unclaimed CP10 defect — which is **consequential** (it re-arms a
  currently self-satisfying CI enforcement step and would newly redden `main` while baseline
  debt is red). Step 05 forbids patching around that without authority.

Creating a redundant second PR for #347's already-fixed node would violate step 03
(preserve continuity / no duplicate work). The correct bounded act is therefore to record
the reconstruction — correcting two stale ledger claims — and stop at the sovereign
boundary.

## 9. Corrections recorded

1. `gate-hygiene-post-merge-verification-06/EVIDENCE.md` §5 and its `WORKSTREAM_STATE.md`
   state that #329/#330/#342/#343 "remain open and superseded". **Measured:** all four are
   **CLOSED (not merged)** at 17:36. The corrected inventory is §2 above.
2. `.bootstrap/01_STATE.md` records the fixture reconciliation and the #294 regression as
   open proposals; both are **already resolved** (§7). Recorded here rather than edited,
   because `.bootstrap/01_STATE.md`'s prose is itself under reconciliation ownership and this
   pass does not widen scope into it.

## 10. Authority boundary

- No merge. No push to `main`. No force-push.
- No change to `api/main.py`, to any workflow, to any test, or to any product surface.
- Artifacts confined to
  `docs/control-plane/evidence/gate-hygiene-post-merge-verification-07/`.
- The next permitted action is **sovereign review**. The next bounded engineering task is
  recorded in `WORKSTREAM_STATE.md` and requires a sovereign decision.
