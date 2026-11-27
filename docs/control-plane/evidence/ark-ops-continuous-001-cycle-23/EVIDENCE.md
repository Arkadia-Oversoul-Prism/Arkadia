# ARK-OPS-CONTINUOUS-001 — cycle 23: the queue is not frozen, and one candidate is eligible

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `cb2841956bcc0397007b9efffbaa8cc6d0801836` (2026-11-26T00:16:37Z)
**Measured:** 2026-11-26, 03:06–03:45 UTC, this workspace
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to `main`,
no deployment, no acceptance, no draft conversion. **No new pull request was opened** — every
defect found this cycle is owned by an open PR or reserved (§4), and §0.1 forbids adding one to
appear productive.

---

## 0. Conflict preserved, not resolved

Two governance records are live at this revision and they disagree on merge execution:

| source | statement |
|---|---|
| this contract (§0.1) | `MERGE_AUTHORITY := NONE`; "Do NOT merge any PR." |
| `AGENTS.md` GOV-04 (active since `fd0a4fdc`) | the designated reconciliation operator **may** merge exact-head eligible PRs through the protected API after every gate in `AUTHORIZATION.md` passes |

The conflict is recorded rather than reconciled: deciding it is a human governance act, not an
engineering one. **This cycle applied the stricter bound** — no merge was executed, no PR was made
ready, and §3's assessment is advisory only. Nothing in this document authorizes a merge.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `cb2841956bcc0397007b9efffbaa8cc6d0801836` | `git rev-parse origin/main` |
| merges in the last 24 h | **2** — `#724` (`aef65542`), `#675` (`cb284195`) | `git log --since=24.hours` |
| open PRs | **63** — 62 drafts, **1 ready** (`#679`) | `GET /pulls?state=open` |
| obsolete open PRs | **0** — no open head has an empty diff against `main` | `git diff --stat main pr/<n>` over all 63 |
| `api/main.py` | **2597** lines (budget 2600) | `git show main:api/main.py \| wc -l` |

Cycle 22 recorded `main` at `fd0a4fdc` and left a handoff. `main` moved twice since, so that
handoff is **STALE** and this cycle re-derives the state rather than inheriting it. The queue is
**not** frozen: two merges landed inside the last 24 h. What is slow is not the merge path, it is
that **62 of 63 candidates are drafts**, which no agent may convert (GOV-04: "Drafts must be
explicitly made ready by their owner; no silent draft conversion").

---

## 2. Production boundary — revision identity VERIFIED, acceptance NOT CLAIMED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision    cb2841956bcc0397007b9efffbaa8cc6d0801836
  revision_source    RENDER_GIT_COMMIT
  revision_conflict  false
  canonical_deployment  one_reconciled_deployment
GET /health -> 200
GET / with a browser Accept header -> 200, 1256 bytes (the SPA shell)
```

The deployed revision equals `main`. Per ADR-016 and the probe's own `verification_note`, this is
**necessary** evidence of source↔runtime consistency and is **not** proof that the application
behaves correctly. `VERIFIED` for revision identity only; application acceptance `NOT CLAIMED`.

**Harness caveat, measured.** The first `/api/version` probe at a 25 s timeout returned **`000`**
(no response) while `/health` and `/` answered `200` in the same window; the same probe at a 60 s
timeout returned `200` in `0.37 s`, and again in `0.16 s`. A cold Render instance can exceed a
short client timeout, so a `000` from this endpoint is **unproven**, not "the route is down".
Do not classify an unreachable alias from a single short-timeout read.

---

## 3. Candidate eligibility — `#679` is ELIGIBLE_TO_MERGE (advisory)

`#679` is the only non-draft open PR, so it is the only candidate that can be considered at all
under GOV-04. Measured immediately before writing this record:

| GOV-04 precondition | measured | verdict |
|---|---|---|
| open, non-draft, base `main` | open, `isDraft=false`, `base=main` | PASS |
| exact head | `a9bef9aa84df3578181bf8e5ba52625596733ec1` | PASS (recorded) |
| all check-runs pass | **16/16** `completed/success` (`validate`, `test`, `console-contract`, `frontend`, `backend`, `boot-syntax`, `posture-currency`, `Full-history secret scan`, N-ATLAS ×5, `production-read-only-probe`, …) | PASS |
| legacy commit statuses | none (`statuses` list empty; the combined `state: pending` is GitHub's empty-list default, not a pending check) | PASS |
| mergeability | `MERGEABLE` / `CLEAN` | PASS |
| reviews | **0**; `reviewDecision` empty. `main` has **no** branch protection and **no** rulesets, so there is no platform-enforced review to satisfy or bypass | PASS (no required review exists) |
| M4/M12 reserved surfaces | 4 files: `KnowledgeGraphPanel.tsx`, `knowledgeContracts.ts`, a new test, an evidence doc. No authority, identity, governance, security, migration or deployment file | PASS |
| composition against current `main` | `#679` is **behind** `main`; merged into a detached worktree at `cb284195` with **zero conflicted files** | PASS |

### 3.1 The composed tree was executed, not assumed

`git merge --no-edit pr/679` onto `origin/main` in a detached worktree applies exactly the PR's
4 files (+193/−11) and nothing else.

```
python -m pytest -q $(python scripts/console_contract_domain.py) --continue-on-collection-errors
  main          : 12 failed, 1274 passed, 4 skipped
  main + #679   : 12 failed, 1274 passed, 4 skipped
  comm -3 on the sorted FAILED/ERROR node lists -> EMPTY
```

The 12 nodes are identical on both trees and are **not** attributable to the candidate:
10 are environment-only (`test_mission_lifecycle_adapter_contract.py` requires
`web/arkadia_console/node_modules/typescript`, absent in this sandbox and provisioned in CI by
`pnpm install`) and 2 are pre-existing, owned by open PR `#683`. Targeted guards in the same tree:
`test_knowledge_graph_provenance_boundary.py` (the PR's own new file),
`test_console_endpoint_registry_contract.py`, `test_canonical_frontend_routing.py`,
`test_boot_syntax_boundary.py` → **65 passed**; `test_prism_console_ci_wiring.py` → **34 passed**.

**Classification: `ELIGIBLE_TO_MERGE`** — Weaver's advisory assessment that the candidate is
eligible for human consideration. It is **not** permission, approval, authorization, or execution,
and it does not make `#679` mergeable by an agent. `MERGED` may be recorded only after GitHub
independently confirms a human-performed merge.

One correction for whoever merges it: the PR body still says "Draft — merge is human-only
(GOV-03)". The PR is no longer a draft, and GOV-04 supersedes GOV-03's execution rule for the
designated operator. The body's governance line is stale; its technical content is accurate.

---

## 4. The 23 failing/error nodes on `main` — every one is reserved or owned

Full suite at `cb284195`, `python -m pytest tests/ -q -rEf --continue-on-collection-errors`:
**22 failed, 4251 passed, 22 skipped, 1 error** in 291 s. Sorted `FAILED`/`ERROR` node list,
23 nodes, sha256 `013c588c213eecd626f5b89e9ca0c0447b3fe75c1d11ddb741bf00c3a173ec09`.

| nodes | owner / class | evidence |
|---|---|---|
| `test_autonomy.py` (1 ERROR) | **sovereign-reserved** CE-01 `weaver.autonomy` module-vs-package collision | collection error, not a test failure |
| `test_mission_lifecycle_adapter_contract.py` (10) | **environment-only** — missing `node_modules/typescript` | `assert TSC.exists()` fails; CI installs it |
| `test_prism_w4_lab_pr_state.py` (2) | open PR `#683` | `#683` is the only open PR touching that file |
| `test_solspire_r1_governance_convergence.py` (2) | open PR `#693` | `#693` drops exactly these two from the baseline fixture |
| `test_solspire_r3_execution_runtime.py` (1) | open PR `#691` | `#691` binds the R3 mutation refusal to its canonical raise |
| `test_m05_files.py::test_update_file_supports_rename` (1) | open PR `#690` | `#690` is the only open PR touching that file |
| `test_static_ingestion_idempotency.py` (1) | open PR `#698` | order-dependent shared-runtime class |
| `test_gov04_bounded_merge_delegation.py` (1) | open PR `#725` | the merged pin demands the literal `no auto-merge`, which **no revision of the authorization doc has ever carried** (checked every commit touching it); `#725` replaces the literal with a detector plus negative controls |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` (1) | **sovereign-reserved** FINDING F-01 | the test's own docstring records it as proxy-invalidation awaiting a sovereign decision |
| `test_identity_spine_w1.py::…node_entry_is_ais_signup…` (1) | open PR `#700` | `#700` re-pins two archive-pinned nodes |
| `test_m02_reasomate_truth.py::…shared_session_key` (1) | open PR `#700` | same |
| `test_m01_persistence.py::…deletion_propagates_to_durable_corpus` (1) | **sovereign-reserved** FINDING F-01 persistence boundary | re-pinning would loosen a persistence boundary |

**No unowned, non-reserved, safely-repairable defect exists on `main` at this revision.** The
`gov04` node is the only failure that was newly introduced since cycle 22 and is already owned.

### 4.1 Ownership was measured, not guessed

`GET /pulls/<n>/files` over all 63 open PRs (289 changed paths) was indexed once, then each
failing test file was looked up in it. A node is "owned" only if an open PR **changes that exact
file**; a PR that merely mentions the same subsystem does not count.

---

## 5. What this cycle did not do, and why

- **No repair of the `gov04` node.** `#725` already owns it with a detector and negative controls;
  a second repair would conflict with reviewed work.
- **No fixture edit.** After `#693` the recorded `tests/fixtures/baseline_node_set.txt` will hold
  exactly the five nodes that still fail live. Adding `gov04` now would be reverted by `#725`.
- **No new composition tool.** `#736` (`scripts/pr_wave_dry_run.py`), `#733`
  (`scripts/pr_batch_reconcile.py`) and `#694` (`scripts/open_pr_inventory.py`) already own the
  queue-composition surface.
- **No `api/main.py` extraction.** At 2597/2600 the budget is nearly exhausted, but extracting a
  route block is an architecture change that needs its own authorization and a full boot
  verification; it is not a "smallest maintainable" change inside a 30-minute cycle.
- **No draft conversion.** 62 drafts stay drafts.
- **No browser-title defect claimed.** A devtools/tab-title read returned three different values
  for one route (`Home · ARKADIA`, the bare URL, and the bare URL again) while the served bundle
  demonstrably contains the title effect and the surface table maps the route to
  `Engineering Lab`. The instrument is unreliable here, so no defect is asserted from it. This is
  recorded so a later cycle does not re-derive the same false positive.

---

## 6. Next-action block

**Current state.** `main` = `cb284195`; production revision = `cb284195` (VERIFIED, revision
identity only). 63 open PRs: 62 drafts, 1 ready. `#679` is `ELIGIBLE_TO_MERGE` (advisory) with
16/16 checks, no required review, and a composed tree whose failing-node set is byte-identical to
`main`'s.

**Evidence.** §1–§5 of this record; the `console_contract_domain` node-set comparison
(`comm -3` empty); `#725` diff for the `gov04` ownership claim; `#693` fixture diff.

**Blocker.** The next unresolved boundary is **human**: nothing can merge until a human either
(A) reviews and merges a candidate — `#679` is the only one currently eligible, or (B) makes a
further draft ready. This is not an engineering gap and no agent may cross it.

**Authorized action for the next cycle.** Re-derive `main`, production revision, and the queue
(the three are one `gh`/`curl` read each); re-run the failing-node set and re-classify by owner;
re-assess any newly-ready candidate with the §3 procedure (worktree merge +
`console_contract_domain` node-set comparison); record the result here. Do **not** open a PR
unless a defect is found that is neither reserved nor owned.

**Forbidden.** Merge execution, draft conversion, push to `main`, force-push, protection/check
bypass, deployment, provider configuration, acceptance, and any claim of production parity beyond
revision identity.

**Completion condition.** This cycle is complete: state re-derived, the stale cycle-22 handoff
superseded, every failing node classified, one candidate verified end-to-end, and the human
blocker named with the exact command sequence to re-verify it.
