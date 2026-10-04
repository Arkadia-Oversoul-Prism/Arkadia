# EVIDENCE — gate-hygiene/open-pr-queue-merge-order-map-01 — Pass 7

**Pass:** hourly bounded execution, 2026-10-04
**BASE_MAIN:** `1b7c089f237a1a8ea11791ab060525b0e36e2029` (confirmed live on `origin/main`)
**Branch:** `gate-hygiene/open-pr-queue-merge-order-map-03`
**Classification:** composition `VERIFIED` · evidence-only, no source/test/governance mutation
**Authority:** none required for this pass. No merge, no push to `main`, no force-push.

Pass 6 recorded the `#215–#219` cluster at base `162f574b` (PR #219, now merged). The
open-PR queue has since turned over completely: a **new four-PR cluster** (#262–#265) sits on
base `1b7c089`. No composition record existed for it. This pass re-derives the cluster from
live evidence in isolated `git worktree`s / throwaway branches and leaves the working tree
clean.

---

## 1. Live cluster inventory (derived from the API, not prose)

| PR | head SHA | branch | state | mergeable | mergeState |
|---|---|---|---|---|---|
| #262 | `3eefcb03f2d1e5cd9baac8fb52020c273d9f097f` | `gate-hygiene/baseline-reconciliation-recovery-frontend-build-01` | OPEN | MERGEABLE | UNSTABLE |
| #263 | `46abb15eb59d2b9e9fa38212e12ad983d869c3ef` | `gate02/production-deploy-fetch-suffixed-labels` | OPEN | MERGEABLE | UNSTABLE |
| #264 | `c158487c3b340b6259c5a9e4b0fcb5ef07cea831` | `gate-hygiene/nodes-configure-routers-idempotency-01` | OPEN | MERGEABLE | UNSTABLE |
| #265 | `f9859c874024a4fbaa866333b8793c0e41086d08` | `gate-hygiene/baseline-node-set-live-reconciliation-01` | OPEN | MERGEABLE | UNSTABLE |

All four are non-draft and `MERGEABLE`. `UNSTABLE` is driven **entirely** by the inherited
`Vercel – console` commit status (see §5).

## 2. Path-overlap inventory (semantic-dependency screen)

Every changed path for every PR, pairwise-intersected. **Zero overlap** across all four.

| PR | files | paths |
|---|---|---|
| #262 | 2 | `docs/control-plane/evidence/gate-hygiene-baseline-reconciliation-recovery-frontend-build-01/{EVIDENCE,WORKSTREAM_STATE}.md` |
| #263 | 3 | `docs/control-plane/evidence/gate02-production-deploy-fetch-suffixed-labels/EVIDENCE.md`, `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py` |
| #264 | 4 | `api/nodes.py`, `docs/control-plane/evidence/gate-hygiene-nodes-configure-routers-idempotency-01/{EVIDENCE,WORKSTREAM_STATE}.md`, `tests/test_nodes_composition_seam.py` |
| #265 | 11 | `.bootstrap/01_STATE.md`, `AGENTS.md`, `MISSION.md`, `NEXT_AGENT.md`, `docs/control-plane/evidence/gate-hygiene-baseline-node-set-live-reconciliation-01/{EVIDENCE,WORKSTREAM_STATE}.md`, `docs/phase1/CONTINUATION_LEDGER.md`, `scripts/baseline_fingerprint.py`, `tests/fixtures/baseline_node_set.txt`, `tests/fixtures/superseded_baseline_node_set_18.txt`, `tests/test_baseline_fingerprint.py` |

`comm -12` over each pair returned empty. Each PR owns a disjoint evidence directory. The
only files touched by more than one PR are none.

## 3. Composition proof (order-insensitivity)

Two compositions on a fresh throwaway branch from `main @ 1b7c089`:

| order | sequence | result |
|---|---|---|
| queue order | #262 → #263 → #264 → #265 | merge clean, rc=0 ×4 |
| shuffled | #264 → #262 → #265 → #263 | merge clean, rc=0 ×4 |

- Queue-order tree: `80a4b060fdc7900a99c455653ec38aef25d44c92`
- Shuffled-order tree: `80a4b060fdc7900a99c455653ec38aef25d44c92`

**Identical tree object.** This is the strong form of the claim: no pair of the four PRs can
interact, regardless of merge order — not merely "the default order is conflict-free". Zero
conflict markers in either composition.

> Note: the first composition attempt appeared to "conflict" on #263–#265. The cause was a
> missing `user.email`/`user.name` for the *merge commit*, not a content conflict; retried
> after `git config user.email` the merges are clean. Recorded so a future pass does not
> re-diagnose it as a semantic conflict.

## 4. Protected-surface checks (composed tree `80a4b060…`)

| check | command | result |
|---|---|---|
| boot code compiles | `python -m py_compile api/main.py` | OK |
| line budget (2600) | `wc -l api/main.py` | **2582** — within budget |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** (11/11) |
| CP10 boundary, composed diff | `cp10_mutation_boundary_policy.py --judge` | PASS (rc=0) |
| CP10 boundary, each PR alone | per-PR `--judge` | PASS (rc=0) ×4 |

Targeted tests on the composed tree: `test_baseline_fingerprint.py`,
`test_gate2_production_observation.py`, `test_nodes_composition_seam.py`,
`tests/architecture` → **58 passed**.

## 5. Full-suite integration delta

Composed tree, `pytest tests/ -q --continue-on-collection-errors -rEf`:

| tree | result | fingerprint (outcomes) | fingerprint (ids) |
|---|---|---|---|
| `main @ 1b7c089` | 9F / 1416P / 18S / 1E | `9a54f5b4…` | `124bfdfd…` |
| composed #262–#265 | 9F / **1425P** / 18S / 1E | `9a54f5b4…` | `124bfdfd…` |

The failing/error **node set is identical** (10 nodes, same pair on both trees). The `+9
passed` is exactly the test additions the cluster carries: #265 `+5` (19 → 24 in
`test_baseline_fingerprint.py`) and #264 `+4`. **Zero regression by node identity.**

### 5.1 Vercel `UNSTABLE` attribution (pre-existing, not from this cluster)

`mergeStateStatus=UNSTABLE` on all four PRs comes **solely** from the `Vercel – console`
commit status, which fails identically on `main @ 1b7c089` and across many earlier commits
(`832a64f6`, `fa1b4078`, `213b4313`, `92c35652`, `e10f365b`, `ddc08f86`, `f10fef92`, …) with
`?upgradeToPro=build-rate-limit`. On #265's head `f9859c8`, `Vercel – arkadia-prism` is
**success** while `Vercel – console` is **failure** — the same context that fails on base.
Check-runs on the head are green (`Full-history secret scan`, `Vercel Preview Comments`).

**Required-check context: `UNKNOWN`.** `GET /branches/main/protection` returns
`403 Resource not accessible by integration` for the available token, so this pass cannot
assert which contexts actually gate the merge. A `UNSTABLE` state is not proof that a
required check failed; the sovereign reads the required set in the PR UI. This is recorded as
an explicit `UNKNOWN`, not converted to a pass or a fail.

## 6. What this pass does NOT claim

- **No production parity.** Gate 2 remains `BLOCKED` (provider auth); nothing here observes
  a deployment.
- **No merge authorization.** The cluster is `READY FOR SOVEREIGN MERGE`, not merged.
- **No source/test/governance change.** Evidence-only; the working tree carries only this
  pass's two documents.
- **No `AGENTS.md` edit.** The insertion-only constraint is untouched by this pass.
- **No fix to the 9 live failures.** Each remains a product/architecture/sovereign decision
  (PR #262 §4); this pass changes no debt, only the composition record.

## 7. Next bounded task (pinned)

- **State:** #262–#265 composable, conflict-free, order-insensitive, CP10-clean, zero
  regression by node identity; architecture 11/11; boot code compiles and is within budget.
- **Evidence:** this document.
- **Blockers:** none for the composition workstream. `Vercel – console` is pre-existing debt
  requiring a provider (Vercel) action, not repository work.
- **Authorized action:** sovereign review of the cluster → merge in any order. Then a
  *separately authorized* workstream may take `SH-06` (steward filter policy) or `SH-03`
  (DERIVED contract); PR #265 §Next carries those.
- **Forbidden:** merging; pushing to `main`; widening this PR; editing a classified failure's
  test literal without a decision.
- **Completion condition:** the cluster merged (any order) → next heartbeat reconstructs from
  live evidence and re-derives the queue.

_Evidence written by an AI agent (OpenHands) on behalf of the sovereign._
