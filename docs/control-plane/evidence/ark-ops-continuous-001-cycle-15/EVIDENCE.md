# ARK-OPS-CONTINUOUS-001 — Cycle 15

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 15 — immediate execution + hourly continuation
- **Observed:** 2026-11-25T02:05Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Substantive change this cycle:** repaired a **newly failing node on an open OpenHands-owned PR**
  (§5). Every failing node on `main` remains owned or reserved (§4), so no competing PR was opened
  for those.
- **Cycle numbering:** 15 is above every number present across the open-PR set (13 here, 14 in
  `#723`), so it collides with nothing. The numbers are still not a global sequence (§7).

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T17:30:03Z) | `GET /commits/main`; local `HEAD` agrees |
| last merge | `#722` — GOV-04 bounded merge delegation | `GET /pulls/722` |
| open PRs | **49** — **48 drafts**, **1 non-draft** (`#724`), **0** reviews | `GET /pulls?state=open` |
| branch protection / rulesets | absent (`/branches/main/protection` → 404) / `0` | REST |
| `main` check-runs at `fd0a4fdc` | `Prism Console Contract`, `Operator Console Posture Currency`, `Lane Doc Currency`, `economic-seam-engine`, `Boot Syntax Boundary`, `Full-history secret scan` all `completed/success` | `GET /actions/runs?branch=main` |

`main` CI is green at the current revision. No Vercel status appears on `main`, consistent with the
retired-Vercel boundary.

## 2. Production boundary — VERIFIED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200 (2.20 s)
  source_revision       fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Source <-> running revision is **VERIFIED** and sha-identical to `main`.

**Transient, recorded not promoted.** The first probe of this cycle hit the 30 s terminal ceiling
with no output; the next returned 200 in 2.2 s. That is the Render cold-start behaviour already
recorded for this alias, not a runtime fault. A single timed-out probe is not evidence of an outage.

## 3. Obsolete-PR audit — measured over the whole open set

All 49 open heads were fetched as `refs/pull/*/head` and compared against `main`:

- heads that are an **ancestor of `main`**: **0**
- heads whose diff against `main` is **empty**: **0**

So the queue holds no obsolete PR that an agent could close. The queue is not stale work; it is
unreviewed work (§8).

## 4. Baseline — measured once this cycle

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 22 failed, 4251 passed, 22 skipped, 6 warnings, 1 error in 299.51s
```

Sorted `FAILED`/`ERROR` node set: **23** nodes.

| fingerprint convention | value |
|---|---|
| outcomes (raw `FAILED `/`ERROR ` lines, sorted) | `013c588c213eecd626f5b89e9ca0c0447b3fe75c1d11ddb741bf00c3a173ec09` |
| ids (prefix-stripped, sorted) | `17b3b70467b8d5c3730770b25518f00fa8c257ab0e3fdd48299bc8e8d6713a1d` |

**No unowned, non-reserved defect is in the set.** Decomposition:

| nodes | classification |
|---|---|
| 1 | `tests/test_autonomy.py` — CE-01 `weaver.autonomy` collision. **Sovereign-reserved** |
| 1 | `test_m01_persistence::test_deletion_propagates_to_durable_corpus` — FINDING F-01. **Sovereign-reserved** |
| 1 | `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` — FINDING F-01 proxy-invalidation. **Sovereign-reserved** |
| 10 | `tests/test_mission_lifecycle_adapter_contract.py` — environment-only: needs `web/arkadia_console/node_modules/typescript` |
| 1 | `test_gov04_bounded_merge_delegation::test_bounded_merge_is_exact_head_and_protected_fail_closed` — repaired by `#725` |
| 1 | `test_identity_spine_w1::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` — repaired by `#700` |
| 1 | `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` — repaired by `#700` |
| 1 | `test_m05_files::test_update_file_supports_rename` — repaired by `#690` |
| 2 | `test_prism_w4_lab_pr_state.py` — repaired by `#690` |
| 2 | `test_solspire_r1_governance_convergence.py` — repaired by `#693` |
| 1 | `test_solspire_r3_execution_runtime::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` — repaired by `#691` |
| 1 | `test_static_ingestion_idempotency::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` — order-dependent shared-runtime node; repaired by `#698` |

Totals: **3** reserved + **10** environment-only + **10** repaired by open PRs = **23**.

**Reconciliation note.** `#727` recorded **21** nodes at the same `main` (20 failed / 4253 passed)
with a `2 reserved / 9 environment / 10 repaired` table whose repaired breakdown sums to 9. This
cycle's measurement is **23** (`3 / 10 / 10`). Both the reserved and environment counts are higher
here. The environment-only class and the order-dependent node are known to move with the installed
dependency set and with run order, so the two figures are **not** reconciled by argument: this
record states its own measurement and its own convention, and does not restate `#727`'s as current.

## 5. The defect this cycle repaired — a PR broke the guard that pins activation

`#724` (the only non-draft PR, a documentation reconciliation of GOV-04's post-merge state) had a
**failing `provider-routing` check that was attributable to its own diff**. Its first head
`1ab40328` rewrote the `**State:**` line of
`docs/control-plane/evidence/gov-04-bounded-merge-delegation/AUTHORIZATION.md` from `PROPOSED` to
`ACTIVE`, deleting three literals pinned by
`tests/test_gov04_bounded_merge_delegation.py::test_activation_requires_human_merge_of_this_governance_pr`.

Measured from the PR's own gate — run `45449878172`, head `1ab40328`:

```
verdict:        FAIL
baseline_nodes: 21     candidate_nodes: 22
newly_failing:  tests/test_gov04_bounded_merge_delegation.py::test_activation_requires_human_merge_of_this_governance_pr
reasons:        1 newly failing node(s)
```

Reproduced locally on that head: `2 failed, 2 passed` — the new node plus
`test_bounded_merge_is_exact_head_and_protected_fail_closed`, which already fails on `main` and is
repaired by `#725`.

**Repair.** The authorization-time sentence is restored verbatim and the verified activation is
recorded on its own dated line, so the document states both facts and the guard keeps its teeth:

```diff
-**State:** ACTIVE — activated by human merge of PR #722 on 2026-11-24. Merge commit: `fd0a4fdc…`
+**State:** PROPOSED at authorization; effective only after this dedicated PR is independently reviewed and human-merged. This PR cannot self-authorize.
+**Activation:** ACTIVE since 2026-11-24 — PR #722 was human-merged at `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`. This record documents the verified repository state; it does not grant itself authority.
```

This is the repository's established convention (correct a pinned line by appending, never by
rewriting) and it does not relax the guard: an edit that drops the pre-activation obligations, or
that claims activation without naming a human merge, still fails it.

**Negative control, live on the real file:**

| step | result |
|---|---|
| delete the restored authorization-time line | `2 failed, 2 passed` — the node reddens |
| restore byte-identically | `1 failed, 3 passed` — only `main`'s own node remains |

**Verification run:**

```
tests/test_gov04_bounded_merge_delegation.py                          1 failed, 3 passed
gov04 + m02a + agents-md adjudication + boot-syntax + lane currency   171 passed, 2 skipped
cp10_mutation_boundary_policy.py --judge (both changed paths)         PASS (exit 0)
```

Pushed to `#724` as `dd77cd85` (repair), `d67a3c63` (evidence + PR body) and `7e32149a` (the CI
verdict below). `#724` is **OpenHands-owned**, so maintaining it is authorized; nothing was opened,
merged or deployed.

**Runtime confirmation — the gate that reported the defect confirms its repair.** `provider-routing`
on head `d67a3c63` (run `45532222870`, 9m30s) completed **success** with gate verdict `PASS`,
`baseline_nodes 21 == candidate_nodes 21`, `newly_failing: []` — against `FAIL`, `21 -> 22`, one
newly failing node on `1ab40328`. The two checks still red on that head
(`beta-beta-01-english`, `bundle-beta-evidence`) fail with
`"reason": "external runtime did not return usable inference"` (§6), so they are not this tree.

## 6. CI attribution — the external-provider class, measured again

`#724`'s check set flipped across two heads of the same tree in about forty minutes:

| check | at `1ab40328` | at `d67a3c63` |
|---|---|---|
| `beta-beta-01-english` | pass (13 s) | fail (16 s) |
| `beta-beta-02-hausa` | pass (18 s) | pass (15 s) |
| `bundle-beta-evidence` | pass (4 s) | fail (3 s) |
| `native-arkadia-golden-workflow` | pass (39 s) | skipping |

A documentation-only diff cannot change those outcomes, and the same family fails on `#709` with
`"reason": "external runtime did not return usable inference"`. So `beta-beta-*`,
`bundle-beta-evidence` and `native-arkadia-golden-workflow` are **external-provider intermittent**
and are never evidence about the repository tree. `Build MIE / Sonata debug APK` on `#716` belongs
to the pre-existing class repaired by `#719`; it was not re-derived here.

## 7. Ledger state

Cycles 01-05 and 13 are carried by this PR as evidence files; cycles 06-12 and 14 live in their own
PRs. The numbers remain **not** a global sequence (06, 07, 08, 09 were each used twice by
independent branches). This cycle uses **15**, above every number in the queue. Keying records by
PR number at merge time remains the unowned fix; it changes what the ledger means, so it is recorded
rather than executed.

## 8. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production revision identical and `revision_conflict:
false`; `main` CI green; 49 open PRs (48 drafts, 1 non-draft); 0 obsolete; baseline 23
failing/error nodes, all reserved, environment-only, or repaired by an open PR. `#724`'s
attributable red check is repaired and its evidence is recorded.

**Evidence.** This record; `#724`'s
`POST-ACTIVATION-RECONCILIATION-2026-11-24.md` §"Gate repair"; run `45449878172` for the measured
verdict; `#725`/`#727` for the remaining GOV-04 nodes.

**Blockers.**
(a) **Merge execution is human-only** (GOV-03; GOV-04 delegates only to a designated human
operator) and 48 drafts await owner action and human review. `main` has not advanced past `#722`
while fifteen cycles of work sit on branches. This is the binding constraint.
(b) Branch protection and rulesets are **absent**, so no platform control enforces review; enabling
them is a governance decision.
(c) CE-01 and FINDING F-01 (two nodes) are reserved to the sovereign.
(d) `/api/webhook/github`'s anonymous surface, and `scripts/prism_coherence_check.py`'s unwired 31
findings, remain disclosed and reserved.

**Authorized next action.** Human review of the queue. An agent may keep maintaining its own drafts
and recording cycles; it cannot reduce the queue, and it must not open a PR for a defect another
open PR already owns.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; re-pinning F-01 to permit
`sessionStorage`; adding an auth guard to `/api/webhook/github`; weakening a guard to manufacture
green; opening a PR with no measured, unowned defect.

**Completion condition.** This cycle is complete when this record is reviewable, `#724` carries the
repair and its evidence, `main` is unmodified, and no merge, deployment or acceptance is claimed.
