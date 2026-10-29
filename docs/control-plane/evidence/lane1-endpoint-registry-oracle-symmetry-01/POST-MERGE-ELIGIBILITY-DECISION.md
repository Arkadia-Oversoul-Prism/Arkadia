# Post-merge eligibility decision — #588 reddens `main` on merge

Pass: 2026-10-29. `main` = `b5bc34cb178d0ec8a804ce6f5761e4bd5e0c7989`.
PR #588 head = `a01948669be11eb96994492c906d78acf3c0bac7`, base = `b5bc34cb`, draft = false,
`mergeable = MERGEABLE`, `mergeStateStatus = CLEAN`, all 14 checks pass.

## Decision

**NOT ELIGIBLE AS-IS — HUMAN AUTHORITY REQUIRED on the guard semantics.**

Every *pull_request*-event check is green, including `lane-doc-currency`. That is the
false negative: the `lane-doc-currency` gate runs **twice** — on `pull_request`, and again
on `push` to `main` (`.github/workflows/lane-doc-currency.yml`, `on.push.branches: ["main"]`
+ `paths: docs/control-plane/parallel-ui/**`). #588 touches that path, so merging it fires
a second run whose outcome is not visible on the PR.

The final step of that run is `python scripts/lane_state.py --check --verify-live`. It
fetches authoritative live PR state and requires every PR the snapshot claims is open to
*be* open. Post-merge, GitHub reports #588 **MERGED** while the snapshot #588 itself
commits still claims it open. The step exits 1 and `main` goes red.

## Mechanism (measured, not inferred)

#588's committed snapshot
(`docs/control-plane/parallel-ui/lane-state.json`) records:

```json
"1": { "active_pr": 588,
       "open_prs": [{ "number": 588, "branch": "feat/prism-l1-endpoint-registry-oracle-symmetry-01", ... }],
       "doc_guard": "deferred", "deferred_to_pr": 588 }
```

`claimed_open_prs()` collects **both** `open_prs` and `deferred_to_pr`, so #588 is claimed
open twice. Simulating the post-merge live response against that committed snapshot, using
the guard's own function:

```
claimed_open_prs(state) -> {588: ['lane 1 open_prs', 'lane 1 deferred_to_pr']}
_pr_state_findings(state, {588: {"state": "closed", "merged": true, ...}})
  -> DRIFT: PR #588 (lane 1 open_prs, lane 1 deferred_to_pr) is recorded as open but is
     MERGED (merge commit a0194866); re-measure the lane PRs and re-point the lane
  -> 1 finding  =>  --verify-live exits 1  =>  push run fails  =>  main red
```

### Runtime proof (not only a simulation)

The mechanism is not hypothetical. Push run **`40676215628`** (`event=push`, head
`fe6701a8`, 2026-10-28, conclusion `failure`) is a real red `main` produced by this exact
function. Its log carries the DRIFT lines verbatim:

```
DRIFT PR #499 (lane 4 open_prs) is recorded as open but is CLOSED without merging; ...
DRIFT PR #548 (lane 3 open_prs, lane 3 deferred_to_pr) is recorded as open but is CLOSED ...
DRIFT PR #550 (lane 1 open_prs, lane 4 open_prs) is recorded as open but is CLOSED ...
```

Same function, same message template, same exit path — the only difference for #588 is the
status word (`MERGED` instead of `CLOSED without merging`). So the push-event failure mode
this record predicts has already been observed on `main` in the same step.

Live confirmation of the historical instance: PRs #507 and #529 (the pair `341867eb`'s
snapshot claimed open) are both `state=closed merged=false` today.

This is the same class that has already reddened `main` from a push run at least twice:
`341867eb` (2026-10-15, snapshot claimed lane 1 `open_prs=[507, 529]`), and `fe6701a8` /
`0df79cbd` (2026-10-28). The two most recent green pushes are green for the same reason —
`6d299eb8` and `b5bc34cb` both record **every lane idle**, and `b5bc34cb` lists its own PR
#587 under `unassigned_open_prs`, which `grep -rn unassigned_open_prs scripts/lane_state.py`
shows is **never read** by any decision. #587 therefore sidestepped the trap rather than
solving it; #588 is the next instance.

## Why this is a design decision, not a bug to patch

A snapshot is a point-in-time measurement. At PR time #588 genuinely *is* open, so a
truthful refresh records it open — and the `pull_request` gate *requires* the lane doc to
point at it. A snapshot cannot know about the merge of the PR that carries it. So there are
exactly two coherent configurations, and the repository has not chosen between them:

| | snapshot / doc | `pull_request` gate | post-merge `push` gate | truthful? |
|---|---|---|---|---|
| **(a)** | #588 stays `unassigned`; lane 1 `idle`; doc declares no active thread | green | **green** (claims nothing open) | no — a Lane 1 PR is attributed to no lane |
| **(b)** | #588 assigned to lane 1; doc points at it (current head) | green | **red** until a follow-up refresh commit lands | yes |

The head under review is **(b)**. It is the truthful configuration, and the appended repair
reached it deliberately: `LANE-DOC-CURRENCY-GUARD-REPAIR.md` adds
`tests/test_console_endpoint_registry_contract.py` to lane 1's `LANE_OWNERSHIP` precisely
because the omission "made a Lane 1 PR unassignable to Lane 1". But that one-line ownership
repair is what *creates* the post-merge red: before it, #588 fell to `unassigned`, lane 1
stayed `idle`, and the snapshot claimed nothing open.

Both options are defensible; they differ in what the guard is *for* (accurate attribution
vs. a `main` that is never red). That is an authority question about the lane-state guard's
contract, so it is recorded and escalated rather than decided here.

## What is NOT the problem

- **Not a shallow clone.** An earlier reading attributed the single failing node
  (`test_detector_flags_a_merged_pr_left_recorded_as_open`) to clone depth. It fails
  identically on unmerged `main` in a shallow clone and passes in a full clone; the finding
  above is derived in a **full** clone and does not depend on that node.
- **Not `declared_idle`.** The appended repair (idle compared against the *last* `_PR_RE`
  match instead of the first) is sound and stays green here; it is orthogonal.
- **Not a CI-skipped check.** The check runs; it passes pre-merge and fails post-merge.

## Verification performed at this head

| check | result |
|---|---|
| `pytest tests/test_lane_instruction_doc_currency.py` | **46 passed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py` | **58 passed** |
| `python scripts/lane_state.py --check` | exit **0** |
| `python scripts/lane_state.py --check --verify-live` (pre-merge, #588 open) | exit **0** |
| `_pr_state_findings` against a simulated post-merge response | **1 finding**, exit 1 |
| `gh pr checks 588` | 14/14 pass (all `pull_request` event) |
| `git merge-base --is-ancestor 8f4a6ea0 origin/main` | **ancestor** — the staleness claim was STALE |

## Recommendation (for the human sovereign)

1. **Do not merge #588 as-is** if `main` must stay green through the merge.
2. Choose the guard semantics: adopt **(a)** (drop the `LANE_OWNERSHIP` line, let lane 1
   idle, remove the `**Active PR:** #588` pointer block) — smallest change, green on both
   events, at the cost of the attribution the repair was written to fix; **or** adopt **(b)**
   and make the guard tolerate a snapshot that records its own carrier open, which is a
   change to a fail-closed decision table gating all four lanes.
3. Either way the fix is a guard-semantics change to `scripts/lane_state.py` and belongs in
   its own bounded workstream with its own negative control.

## Authorization boundary

This record changes no authority, identity, governance, approval, or deployment surface, and
edits no lane-owned source. Merge and acceptance remain the human sovereign's. Nothing was
merged and nothing was pushed to `main` by this pass.
