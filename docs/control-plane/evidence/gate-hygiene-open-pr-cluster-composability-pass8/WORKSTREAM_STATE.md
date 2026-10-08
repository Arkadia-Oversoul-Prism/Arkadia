# WORKSTREAM STATE — gate-hygiene/open-pr-cluster-composability-01

| field | value |
|---|---|
| workstream | gate-hygiene — measured composability of the uncovered-debt PR cluster |
| gate | GATE-07 / GATE-10 hygiene (baseline-debt reduction; no authority change) |
| status | **READY FOR SOVEREIGN MERGE** |
| PR | (this branch → PR) |
| base main | `f96d5fd27d40110196ec22b114808efc0eb9dc05` |
| changed paths | `tests/test_open_pr_cluster_composability.py`, this evidence dir |
| production code | **none** |
| node delta measured | cluster #354→#357 composed: `main` 17 nodes → 8 nodes, `-9 / +0` |

## What was measured

Merging the four newest uncovered-debt PRs onto `f96d5fd2` in the order **#354 → #355 → #356 →
#357** reduces the failing-node set from **17 to 8** with **zero added nodes**. `#354`/`#355`
compose cleanly; `#356`/`#357` collide only on the tail of `AGENTS.md`, resolved by a union
append. The remaining 8 nodes are all sovereign-reserved or explicitly unscheduled.

## Next action (deterministic)

**Sovereign:** review and merge. No agent action is required or permitted before that.

Merge order that the measurement supports (mechanical `AGENTS.md` union-append resolution
required at each tail collision):

1. #354 → 2. #355 → 3. #356 → 4. #357

After each merge, re-measure `main` and confirm the node set shrinks by the owned cluster,
with zero added nodes.

## Forbidden in this workstream

- Touching `test_autonomy.py` (CE-01, sovereign-reserved).
- Editing any PR's source or test to force composition (the conflicts are mechanical only).
- Widening scope to any cluster already carried by an open PR.
- Any change to production code, authority paths, or mutation paths.

## Completion condition

Sovereign merges the cluster and the post-merge `main` re-measurement shows the six
PR-owned clusters absent (`-9` nodes) with zero added nodes.
