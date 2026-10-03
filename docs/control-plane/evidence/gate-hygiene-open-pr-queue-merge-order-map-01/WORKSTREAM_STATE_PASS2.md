# WORKSTREAM STATE — `gate-hygiene/open-pr-queue-merge-order-map-01` (Pass 2)

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01` (continuation; branch `-02`)
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
Status: **IMPLEMENTED** (evidence only; no code/test/governance change; sovereign review only)

Supersedes the queue facts in `WORKSTREAM_STATE.md` (Pass 1, base `002b189`, 16-PR queue).
Pass 1 is **not stale as a method** — its unshallow-first precondition and its
"test ancestry, not branch names" rule still hold. Only its *queue inventory* is superseded:
the queue drained from 16 PRs to **4**, and `main` advanced from `002b189` to `162f574`.

## Current state (derived from live evidence, not prose)

| item | value |
|---|---|
| `main` | `162f574b05dd839540d803aadda7608342618a84` |
| open PRs | **4** (#215, #216, #217, #218) — all `gate-hygiene`, all `MERGEABLE`, all `UNSTABLE` |
| architecture suite (composed tree) | **11 passed** |
| `api/main.py` | **2582 / 2600** lines; `py_compile` OK |
| CP10 mutation boundary (composed diff) | `--judge` exit 0 |
| baseline full suite | **20 failed / 1306 passed / 17 skipped / 1 error** |
| composed full suite | **18 failed / 1308 passed / 18 skipped / 1 error** |

## The four open PRs — file overlap

| PR | branch | files touched | head |
|---|---|---|---|
| #215 | `baseline-node-depth-stability-01` | `tests/test_agents_md_encoding_adjudication.py`, evidence doc | `0c18fbb` |
| #216 | `superseded-fingerprint-origin-01` | `AGENTS.md`, `MISSION.md`, `NEXT_AGENT.md`, `.bootstrap/01_STATE.md`, `docs/phase1/CONTINUATION_LEDGER.md`, `tests/test_baseline_fingerprint.py`, 2 evidence docs | `4747e4c` |
| #217 | `live-file-fixture-revision-pin-01` | `tests/test_agents_md_encoding_adjudication.py`, evidence doc | `3b5e4cd` |
| #218 | `adjudication-fixture-commit-pin-01` | `tests/test_agents_md_encoding_adjudication.py`, evidence doc | `54e2e98` |

**Only `tests/test_agents_md_encoding_adjudication.py` has >1 writer** (#215, #217, #218).
#216 is disjoint from the other three.

## Composability — measured, not asserted

- **Git-level:** all 6 pairwise combinations and all 4 PR-onto-`main` merges are
  **conflict-free** (`git merge-tree --write-tree`, 0 conflict markers). #215/#217/#218 share
  a file but edit **different hunks**:
  - #215 → `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` (~line 361)
  - #217 → `test_exit_code_does_not_call_a_divergent_clean_file_verified` (~line 424)
  - #218 → `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` (~line 387)
- **Semantic-level:** #215/#217/#218 together repair **both** adjudication nodes that pin the
  absent `7d79f38` — #218 fixes the *skip* branch, #215 fixes the *crash* branch, #217 fixes
  the *moving-branch* fixture. They are complementary, not redundant. #216 is additive: it
  only rewrites prose around an existing cluster of node-set fingerprints, and its own guard
  test passes on `main` **before** any of #215/#217/#218 (17 passed → 18 passed).
- **Composition is strictly beneficial** (see §Baseline): the composed tree fixes **2** nodes
  and introduces **0**.
- **Deterministic composed tree** (`tmp/compose2`, merge order **#215 → #216 → #217 → #218**):
  merge SHAs `0c18fbb` → `6d7d77c` → `ddf1aee` → `db5510a`. Byte-identical to the earlier
  `tmp/compose` (`git diff --stat tmp/compose tmp/compose2` empty), so the result is
  order-insensitive within this set.

## Baseline vs composed — proof by node **set**, not counts

Counts vary by environment (see AGENTS.md: full-suite fingerprint is UNSTABLE). Attribute by
name:

- **Baseline (main `162f574`):** 20 failed / 1306 passed / 17 skipped / 1 error (121.68s).
- **Composed (`db5510a`):** 18 failed / 1308 passed / 18 skipped / 1 error (122.55s).
- **Nodes fixed by composition (in baseline, absent composed):**
  - `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
  - `tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
- **Nodes newly failing in composition:** **none** (set difference empty).
- The `passed` delta (+2) and `skipped` delta (+1) are the same effect: #215 converts the
  sibling from `FAILED` to `skipped` (absent `7d79f38`), #217 converts the divergent-file node
  from `FAILED` to `passed`, and the extra `skipped` is the composing count.

## Merge order (advisory; merge is HUMAN)

The set is order-free at the git level, but the documented origin explanations in #216 should
land with the behavior they describe:

1. **#216** first (disjoint; describes the recorded set and the depth-dependent sibling).
2. **#218** (repairs the skip branch of the pinned gate-2 parent fixture).
3. **#215** (repairs the crash branch of the sibling fixture).
4. **#217** (repairs the moving-branch fixture in the divergent-file node).

Any permutation is conflict-free; the order above keeps each PR's evidence narrative aligned
with the tree it describes.

## CI state

- `Full-history secret scan`: **success** on all four heads.
- `Vercel Preview Comments`: success where reported.
- `Vercel – console` / `Vercel – arkadia-prism`: **failure — deployment rate limit /
  deployment has failed**, i.e. **environmental**, not a code failure. This is why every open
  PR is `UNSTABLE`; it is not a repository defect.
- `SG-02-FE.2-V` (CP10) does **not** trigger on any of these four PRs — none touches its path
  filter (`web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`, or the named
  test files). Verified against the workflow trigger, and the CP10 `--judge` on the composed
  diff exits 0.

## Gate-2 regime check — is `7d79f38` "unavailable" or hiding a defect?

**Classification: legitimately unavailable in a CI-shaped clone — and the exclusion is
defensible, not a cover-up.**

- `7d79f38bd520a99637785db80bbe786192900d6d` is absent from this clone (not shallow; 1604
  commits) but **exists on GitHub** (commit "gate2: close backend runtime link VERIFIED
  (discriminating), main 002b189"). It is a PR-head revision that a normal clone never carries.
- Without it, the **sibling** node `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
  **crashes** with `AttributeError` (read of `None`) rather than skipping — measured on `main`.
  #215 adds the missing `None` guard → `skip`. This is **exactly** the "excluded node's own
  assertion defect" that Pass-1-adjacent `AGENTS.md` (from #216) says is *a separate proposed
  workstream*. #215 **is** that workstream.
- The other sibling, `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`,
  already guarded against `None` but then dereferences **`origin/main`** — a **moving branch**
  premise. #218 replaces it with the pinned `CORRUPTION_COMMIT`. Measured: that node currently
  **passes** on `main` (because `origin/main` is still corrupt at the pinned revision), so #218
  is a **latent**-expiry fix, not an active-failure fix — #218 introduces **0** new passes and
  **0** regressions on the current tree.
- `AGENTS.md` (from #216) records the sibling as crashing "unconditionally **without** the
  PR-head revision `7d79f38…`". After #215 the node no longer crashes; it skips. The AGENTS.md
  wording describes the *pre-#215* behavior but is not falsified: with the revision **present**
  the node's assertion path is the same and the text is a true statement about the absent-rev
  case *without the guard*. A future pass may refine the wording; it is **not** a merge
  blocker, and no test asserts on that sentence.
- **Verdict:** the skip is a **correct, bounded** repair of a missing `None` guard on a
  revision the environment genuinely lacks. It does **not** hide a defect — the node still
  asserts its full oracle-determined codec property whenever the revision is present, and the
  recorded baseline set deliberately excludes the depth-dependent node so the published debt
  fingerprint is clone-depth-stable.

## Residual risk / uncertainty

- Composed-tree tests are **local** (`PYTHONPATH=archive/legacy_python`,
  `--continue-on-collection-errors`), not a CI run and not a deployment. No production-parity
  claim.
- `main` has moved (`002b189` → `162f574`) and **the `AGENTS.md` line count grew** since #216's
  authoring base (`64cbe74`). The merged result must be re-measured on the exact final tree; a
  prose merge conflicts are impossible (docs are disjoint from other writers) but the composed
  sizing claim (`2582/2600`) is measured on `main` **before** #216 only — **no** PR here touches
  `api/main.py`, so the budget is unaffected.
- `test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository` is known
  intermittent under the full suite (AGENTS.md). It did **not** appear in either run here;
  treat any future appearance as cross-test contamination, not a regression.

## Next bounded task

**None created by this pass** (no self-expansion). Candidates the sovereign may bound:

1. **Drain #215–#218** (order above) — pure merge actions, human authority.
2. Refine the `AGENTS.md` sentence in #216 to read "…crashes **in the revision before the guard
   added by `baseline-node-depth-stability-01`**" — documentation precision, only if the
   sovereign wants it.
