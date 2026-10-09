# EVIDENCE — gate-hygiene / current-tip branch mergeability 01

Bounded objective: close the gap PR #376 §7 explicitly left open — *"the composition
was measured by patch application, not by merging the PR branches … branch ancestry
is not itself proven mergeable by this method."* This record proves the **branch
merge / ancestry** property (a real `git merge` sequence), not the patch-composition
property already established by #375/#376.

Evidence-only. No product code, workflow, mutation path, authorization path, or
governance surface is changed. No merge performed, proposed, or authorized.

Status: **VERIFIED** (repository-source measurement: real sequential merge reproduces
the two reserved nodes with 0 introduced). No production claim.

## 1. Revision under measurement

| Field | Value |
|---|---|
| BASE_MAIN | `a47ea92817436675c15d472ca80f39d7295e880a` (2026-10-09 10:56:38 +0100) |
| Subject | Add read-only operator security verification control |
| Python | 3.13 · pytest 9.1.1 · git 2.47 |
| Env | `PYTHONPATH=archive/legacy_python`, `-p no:randomly`, `--continue-on-collection-errors -rEf` |
| Head refs (live, verified vs GitHub API) | `#354 536a8c43` · `#356 1bfbcc4f` · `#357 4c3d8fb8` · `#363 aa77f364` · `#365 d8679b49` · `#347 3f3024d9` |

All six `pr-<n>` refs used below were confirmed byte-equal to the live PR head SHAs
returned by `GET /repos/.../pulls/{n}` before the merge sequence was run.

## 2. Baseline fingerprint (`main` @ `a47ea928`) — re-derived

Full-suite run on the unmodified tip:

```
15 failed, 1823 passed, 36 skipped, 3 warnings, 1 error in 148.49s
```

- **16** failing/error nodes.
- outcomes `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`
- ids `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833`

Both fingerprints reproduce the baseline recorded independently by PRs #375/#376 at
this revision. Node ownership (unchanged): #354 (3 CP10 allowlist nodes), #356 (2 Lab
authority nodes), #357 (3 SolSpire nodes), #363 (2 nodes), #365 (3 steward nodes),
#347 (1 landing node) — plus the two sovereign-reserved nodes CE-01
(`tests/test_autonomy.py`, ERROR) and F-01
(`test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate`).

## 3. Real sequential merge — the property #376 §7 did not prove

A detached worktree at `a47ea928` was built and the six branches merged **with real
`git merge --no-ff`** (not `git apply`), in the order
`#354 → #356 → #357 → #363 → #365 → #347`. Git identity was configured first (see §5,
hazard A).

| Step | Branch | Result |
|---|---|---|
| 1 | `pr-354` | CONFLICT — `AGENTS.md` only; union-append, block 92 lines |
| 2 | `pr-356` | CONFLICT — `AGENTS.md` only; union-append, block 35 lines |
| 3 | `pr-357` | CONFLICT — `AGENTS.md` only; union-append, block 39 lines |
| 4 | `pr-363` | CONFLICT — `AGENTS.md` only; union-append, block 87 lines |
| 5 | `pr-365` | clean merge |
| 6 | `pr-347` | clean merge |

**Every conflict is `AGENTS.md`-only** — a non-code file. No product, test, authority,
or workflow surface conflicted in a real branch merge, matching #376 §4's `merge-tree`
inventory. The branches therefore **compose by ancestry**, not merely by patch.

### AGENTS.md resolution — insertion-only preserved

Each of `#354/#356/#357/#363` edits `AGENTS.md` as a **pure single-hunk append at EOF**
(prefix-stable over its own merge-base; 0 deletions). The union of the append blocks in
merge order is therefore the only resolution consistent with the standing insertion-only
constraint, and it was constructed explicitly:

```
main(938 lines) + block(#354, 92) + block(#356, 35) + block(#357, 39) + block(#363, 87)
= 1191 lines
```

`wc -l` on the merged file → **1191**. No product/test file is touched by the resolution;
every prior lesson's text is preserved verbatim (append-only).

## 4. Proof on the real merged tree

Full suite on the composed **merge** tree:

```
1 failed, 1841 passed, 36 skipped, 3 warnings, 1 error in 149.39s
```

- **2** failing/error nodes — exactly the two sovereign-reserved nodes:
  `ERROR tests/test_autonomy.py` (CE-01) and
  `FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` (F-01).
- outcomes `f607dffd1abda8bc667897a4366c6afe1498ae6e5b02635ff682cbc6daeb2ad1`
- ids `48e2b758b3194bd267e7babf13609b3467ff46985a879c72a55ad5201f44b3a9`

Both fingerprints **match #375/#376 exactly**, though this pass reached them by real
`git merge` rather than `git apply --3way`. Node delta vs baseline: **16 → 2 (`-14`),
0 unexplained new nodes**. A `comm` of the sorted `FAILED/ERROR` node lists shows the
14 repaired nodes are exactly the PR-owned set and nothing else is introduced.

Protected regressions on the merged tree:

- architecture fitness (`tests/architecture`): **11 passed** (same as `main`).
- CP10 mutation-boundary judge (`scripts/cp10_mutation_boundary_policy.py --judge`
  over the 22 merged change paths): **PASS** (exit 0).
- `AGENTS.md` encoding audit against oracle `6c43218a48a4`: **`alterations=0`,
  `oracle_reproduced=True`, cyrillic `0` → `0`, exit 1** (clean, oracle-corroborated —
  the append-only status, not a divergence).

Changed paths on the merged tree (`git diff --name-only a47ea928 HEAD`, 22 paths):
`AGENTS.md`, the six PR evidence docs (`docs/control-plane/evidence/gate-hygiene-*`,
`gate10-cp10-allowlist-deploy-surface-01`), `scripts/cp10_mutation_boundary_policy.py`,
`tests/test_ais_capability_profile_onboarding.py`, `tests/test_engineering_lab_api.py`,
`tests/test_identity_spine_w1.py`, `tests/test_m02_reasomate_truth.py`,
`tests/test_solspire_r1_governance_convergence.py`,
`tests/test_solspire_r3_execution_runtime.py`, `tests/test_steward_filter.py`,
`weaver/filters/steward.py`, `web/public_prism/src/pages/NodeEntry.tsx`.

## 5. Two construction hazards — negative controls, corrected

Both wrong measurements encountered this pass are recorded so a future pass does not
repeat them.

**Hazard A — an unset git committer identity silently no-ops a merge.** With
`user.email`/`user.name` unset, `git merge --no-commit` returns without applying the
merge; a loop that then reads `HEAD` reports every step "clean" while nothing merged.
The first run produced exactly this false negative. Configure identity before a merge
loop, or a "clean composition" result is unproven.

**Hazard B — a stage-index union is not a valid append-union.** Resolving an
`AGENTS.md` conflict as `ours + theirs[main_len:]` reads `:3:` (the PR's own
contribution over *its* merge-base) sliced by the *current* file length. Because the PR
blocks are appended over three different merge-bases (`f96d5fd2` for #354/#356/#357,
`24a00f85` for #363), the slice offset is wrong and the resolution silently
deletes/downsizes blocks (observed: two negative block lengths; assembled line
arithmetic `938 + 22 - 35 - 31 + 17 = 911` did not match the resulting file). The valid
construction is per-PR **`pr_version[merge_base_len:]`**, which §3 uses; its line
arithmetic closes (`938 + 92 + 35 + 39 + 87 = 1191` = measured).

## 6. What this changes, and what it does not

- **Adds:** the branch-ancestry property. A real `git merge` sequence composes the six
  branches; the only conflict is the shared non-code `AGENTS.md` tail; the merged tree
  reproduces the two reserved nodes with 0 introduced.
- **Does not add:** a merge decision. `#356` repairs a pin over `api/lab_routes.py`
  (Lab mutation boundary, authority surface) and `#354` touches the CP10 boundary
  policy; merging remains **sovereign-only**. This record measures and reports.
- **Does not close:** Gate-2, which remains `BLOCKED` on provider SSO (see #376 §5).
  Per the contract, `BLOCKED` is never promoted to `VERIFIED` by repetition.
- **Does not touch:** the disjoint #361 fixture-drift workstream, the #366/#368/#370
  Gate-2 harness stack, or the product-repair PRs themselves.

## 7. Remaining uncertainty

- The merge was performed with a local union-append resolution of `AGENTS.md`. That is
  the only resolution consistent with insertion-only, and it is proven clean by the
  encoding audit (§4), but a GitHub merge-queue resolution is produced by GitHub, not by
  this record; the operator must still confirm the post-merge `AGENTS.md` is
  mojibake-clean.
- Absolute passed/skipped totals differ from #375/#376 (1841/36 vs 1857/20) with an
  identical 1875 total test count; the load-bearing invariant is the failing/error node
  **set**, which matches exactly. This is an environment difference (skips vs passed
  split), not a regression — do not attribute a delta from a count alone.
