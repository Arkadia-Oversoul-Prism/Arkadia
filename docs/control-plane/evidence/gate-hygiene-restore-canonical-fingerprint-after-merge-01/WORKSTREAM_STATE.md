# WORKSTREAM: gate-hygiene/restore-canonical-fingerprint-after-merge-01

- **Class:** gate-hygiene · continuous recalibration (GATE-13)
- **Base main:** `1a2fc21ee7e9497270c712065b9f06a6b525a642`
- **Branch:** `gate-hygiene/restore-canonical-fingerprint-after-merge-01`
- **Commit:** `e49a82a37184165f392225d089930d9a45c032ef`
- **PR:** #231
- **Status:** READY FOR SOVEREIGN MERGE (loss restoration; 3 nodes fixed, 0 introduced)

## Objective
Restore the clone-depth-stable canonical baseline fingerprint trio that the hand-resolved
merge `59ca893` discarded: `MISSION.md`, `NEXT_AGENT.md`,
`tests/test_baseline_fingerprint.py`.

## Root cause (measured)
`59ca893` ("Merge branch 'main' into gate-hygiene/stale-gate-fixture-retirement-01")
merged `0893987` (branch side — the pass that retired the two archived-surface gate nodes
and republished the canonical fingerprint) with `c80b25c`. The resolution kept the canonical
test/const changes from the branch side but took `MISSION.md`, `NEXT_AGENT.md`, and
`tests/test_baseline_fingerprint.py` from the superseded side.

- `59ca893^1 == 0893987`; `59ca893^2 == c80b25c`; `a82ebde` (#220) `== 59ca893^2`;
  `9202b92` (#226) inherited it. `91b4471` is the explanation pass; it is an ancestor of
  HEAD and a **descendant** of `0893987` (`git merge-base --is-ancestor` → YES/NO), but its
  blobs were then reverted by the lossy merge.
- At HEAD the docs advertised `a578a766…/8036fc06…` as canonical while
  `tests/fixtures/baseline_node_set.txt` (18 nodes) hashes to the canonical
  `6c7bf821…/2bc35996…`. `tests/test_baseline_fingerprint.py` also **duplicated**
  `CLONE_DEPENDENT_SIBLING_NODE` and asserted the superseded value
  `0cc09dd0…` against the target `a59453b8…`.

## Repair (mechanical — not design)
`git checkout 0893987 -- MISSION.md NEXT_AGENT.md tests/test_baseline_fingerprint.py`.
`git diff 0893987 -- <those files>` is **empty**, so every restored blob is byte-identical
to the revision the discarded branch side already carried — loss restoration, not invention.

## Verification
- `tests/test_baseline_fingerprint.py` → **19 passed** (was 3 failing at HEAD).
- `tests/architecture` → **11 passed**.
- Full suite `--continue-on-collection-errors`:
  - HEAD `1a2fc21`: 22 failed / 1319 passed / 18 skipped / 1 error
  - branch `e49a82a`: 19 failed / 1323 passed / 18 skipped / 1 error
- Node-set delta by identity: fixed exactly the 3 fingerprint nodes; **0** newly introduced.

## Scope / non-goals
- `api/main.py` untouched (boot-code budget unaffected).
- Not touched: `test_solspire_p1_experience_01` / `test_solspire_project_instantiation_01`
  (authored debt of #226) and `tests/test_steward_filter.py` — orthogonal pre-existing red
  nodes, each a separate bounded workstream.

## Authorization
Merge is the human boundary. No merge performed; no push to `main`.
