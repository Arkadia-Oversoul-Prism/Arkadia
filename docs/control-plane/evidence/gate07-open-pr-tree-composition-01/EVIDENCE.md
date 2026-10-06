# GATE-07 — Open-PR tree composition evidence (01)

> Artifact-only. No runtime code, no test change, no `.gitignore` change. This document
> records a measurement of the currently open PR tree against `main`; it is not a merge
> authorization and not an acceptance claim.

## 1. Bounded objective

Record the integration result of the **full open-PR tree** on `main` at the time of
measurement: which heads compose without textual conflict, which collide, whether the
collision is semantic, and whether the composed tree regresses the failure node set.

`docs/control-plane/evidence/gate07-chain-integration-01` (PR #324) already measures the
**runtime chain** `scheduler → trajectory → router → attention` over
`#319/#320/#321/#322/#323`. That evidence explicitly excludes the remaining open heads
(`#324/#325/#326/#327/#306`). This artifact is the complementary measurement and does not
supersede it.

## 2. Reconstructed state (observation timestamp 2026-10-06T07:0xZ)

- `BASE_MAIN = 1775f3e1271842688f5026b59bfb0d393db6db04`
  ("Merge pull request #318 from …/fix/prism-arkana-surface-consolidation", 2026-10-06 05:05 +0100)
- Open PR heads (full SHA), all `mergeable=true` / `mergeable_state=unstable`:

| PR | head | base |
|---|---|---|
| #306 | `ddc1a1b3f356ae56c1977a32a8b0925f2188e722` | main |
| #319 | `3d1829db87ee2e436354002842c9586e7bd58350` | main |
| #320 | `d5adcba6d8b187e1bf2b86cee35915fe75b46728` | main |
| #321 | `e611edd80ef1b0fe51213630702fa766bf57f6c5` | `gate-hygiene/scheduler-trajectory-conformance-01` (#319) |
| #322 | `9d0f1cea7f8e6e51feb795018b90733fddfbbcbc` | main |
| #323 | `cd749ea424c6ce2af35cb1d72eabde55e261cb21` | main |
| #324 | `e6784c305a67c591cdb77ebe35d1f967d4ed67a6` | main |
| #325 | `77ae53ef01a790984fcc1cd7002ba45951842752` | main |
| #326 | `55acddb5ce17a05989810954ac3d96dfbe569bb7` | main |
| #327 | `0f5584f65ebc2bbaa506438886763c0c8ff2bf74` | main |

`#321` is genuinely stacked: its base is `#319`'s head branch, not `main`.

## 3. Method

1. Fresh detached worktree at `BASE_MAIN` (`git worktree add --detach`).
2. Sequential `git merge --no-edit` of every open head, in the order
   `#319 #320 #321 #322 #323 #325 #326 #327 #306 #324`.
3. Recorded conflict set; resolved the single collision by **union**.
4. Full suite on the composed tree with the documented reproducibility invocation:
   `PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors`
5. Compared the sorted `FAILED`/`ERROR` node set against a same-invocation `BASE_MAIN`
   baseline. Node **identity**, not counts, is the load-bearing comparison.

## 4. Result — composition

Nine of ten heads merge cleanly. **One collision**, and it is isolated to a single pair:

- `#320` ↔ `#327`, in exactly two files:
  - `.gitignore` — both append a rule at the same anchor (end of the runtime-output block).
  - `tests/test_repo_hygiene_gitignore.py` — both append new test functions at the same anchor (EOF).
- No other pair collides. In particular `#319 + #321` apply cleanly (stacked), and
  `#322/#323/#325/#326/#306/#324` apply cleanly onto the union.

### The collision is positional, not semantic

`#320` ignores the scheduler's attention outbox
(`docs/control-plane/evidence/**/attention-events.jsonl`) and pins it with two tests
(`test_attention_outbox_is_never_stageable` + a negative control).
`#327` ignores the scheduler's root-level run result (`engineering-session-result.json`) and
pins it with two tests (`test_scheduler_session_result_is_never_stageable` + a negative control).
Distinct artifacts, distinct rules, distinct tests. Neither PR edits the other's lines; they
disagree only about which one occupies the append position.

**Union resolution is mechanically determined:** keep both hunks in both files. Resolved file
sizes are `+3/+4` gitignore rules and `+2/+2` tests; no line of either PR's intent is dropped.

### Verification of the resolution

- `python -m pytest tests/test_repo_hygiene_gitignore.py -v` on the composed tree →
  **10 passed**. All six pre-existing tests plus **all four** new tests from `#320` and `#327`
  collect and pass; no name shadowing, no accidental duplicate.
- `python -m pytest tests/architecture -q` on the composed tree → **11 passed**
  (matches `BASE_MAIN`; the architecture ledger is unchanged by the composition).

## 5. Result — regression boundary

| tree | failing/error nodes | passed | skipped |
|---|---|---|---|
| `BASE_MAIN` `1775f3e` | 12 | 1509 | 20 |
| composed (union) `d1c46cf` | 11 | 1585 | 20 |

Node-set delta (`diff` of sorted `FAILED`/`ERROR` lines):

```
4d3
< FAILED tests/test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime
```

- **Zero newly introduced nodes.** The composed tree introduces no failure that `BASE_MAIN`
  does not already carry.
- **One node repaired:** `test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime`
  is repaired by `#326` — which is that PR's stated purpose (restore the Arkana/Weaver fusion
  lost in the `#273` merge resolution).
- `+76 passed` is the new tests contributed by the composed heads; it is not a repair claim.

Baseline node-set sha256: `5e782bf9b1ecb962bd66e8a8dd082a2091c589145cee727e3f0b2cfe073404e6` (12 nodes).
Composed node-set sha256: `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` (11 nodes).

### Baseline composition note

The measured `BASE_MAIN` set is 11 failed + 1 error. `#326` repairs one of those failures.
`#322`, `#323`, `#325` are all attributed to `tests/test_steward_filter.py` (3 nodes) in the
composed tree, but those nodes are **pre-existing `BASE_MAIN` debt** — the composed tree does
not introduce them, and their presence in the composed run is not attributable to any PR in
the tree. The CE-01 `tests/test_autonomy.py` collection error persists identically in both
trees (the `weaver.autonomy` module-vs-package collision reserved to the sovereign).

## 6. Merge-order constraint (proposed, not authorized)

Derived from the composition, not from prose:

1. `#321` **must** be merged after `#319` (its base is `#319`'s branch).
2. `#320` and `#327` **both** touch `.gitignore` and `tests/test_repo_hygiene_gitignore.py` at
   the same anchors. Whichever merges second will conflict; the second merge must be resolved
   by union (keep both rules, keep all four tests). This is safe but is **not** a conflict-free
   GitHub merge — the sovereign should expect to resolve it, or apply the union resolution
   recorded here.
3. No ordering constraint among `#322`, `#323`, `#324`, `#325`, `#326`, `#306`.

## 7. What this artifact does NOT claim

- **Not** a production-parity claim. Gate 2 remains open and `BLOCKED` on provider auth for
  the deployment-specific URL; nothing here changes that boundary.
- **Not** an acceptance claim for any PR. Merge is human-only.
- **Not** a merge of the composed tree. The composed worktree `d1c46cf` is a local
  measurement; the union resolution is recorded here so the sovereign can reproduce it, and
  is **not** committed to any PR branch.
- **Not** a statement about the PRs' own CI. Their `unstable` state reflects the CE-01
  collection error and pre-existing debt, per `AGENTS.md`, not their content.

## 8. Reproduction

```bash
git worktree add --detach /tmp/compose 1775f3e
cd /tmp/compose
for n in 319 320 321 322 323 325 326 327 306 324; do
  git merge --no-edit "$(git -C <repo> rev-parse refs/remotes/pr/$n)" || echo "conflict #$n"
done
# resolve .gitignore + tests/test_repo_hygiene_gitignore.py by union, then:
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```
