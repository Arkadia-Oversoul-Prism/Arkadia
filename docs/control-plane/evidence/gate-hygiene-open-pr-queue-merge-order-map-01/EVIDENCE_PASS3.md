# gate-hygiene — open-PR queue Pass 3: the baseline failing-node set is CLONE-DEPTH-DEPENDENT; the composed tree is regime-invariant

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01` (continuation; branch `-03`)
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence **correction**. No source, test, or governance change.
Supersedes the *baseline attribution* of `EVIDENCE_PASS2.md` §5 and §7. Pass 2's
queue inventory, overlap map, git-composability result, merge order, and CP10 result
all stand — they are re-confirmed below.

---

## 1. Why this pass exists

Pass 2 §5 asserted: *"Attribution is by node **set**, which is environment-independent."*
That sentence conflates two different node sets. Re-measured here, the **composed** tree's
failing-node set is indeed regime-invariant — but the **baseline** (`main`) failing-node set
is **not**. A clone that carries the PR-head refs (this automation's clone does: 216
`refs/remotes/pr/*`) resolves revision `7d79f38…`, which a CI-like clone does not, and the
adjudication module's failure set moves accordingly. Pass 2 measured the CI-like regime and
presented it as universal; this pass states the result **per regime**.

## 2. Two clone regimes, measured

Both trees at `main 162f574`; `PYTHONPATH=archive/legacy_python`, `--continue-on-collection-errors`.

| node (`tests/test_agents_md_encoding_adjudication.py`) | refs-present | CI-like (no refs) |
|---|---|---|
| `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` | **PASS** | **FAILED** |
| `test_exit_code_does_not_call_a_divergent_clean_file_verified` | **FAILED** | **FAILED** |
| `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` | **FAILED** | **SKIPPED** |

`refs-present` = `git for-each-ref 'refs/remotes/pr/*'` → 216 refs; `git cat-file -t 7d79f38…` → `commit`.
`CI-like` = `git clone --no-local --single-branch --branch main file://…` → 0 remote refs;
`git cat-file -t 7d79f38…` → `fatal: could not get object info`.

Consequence for the full suite (baseline `main 162f574`):

| tree | regime | failed | passed | skipped | errors |
|---|---|---|---|---|---|
| baseline `main` | refs-present | 20 | 1308 | 17 | 1 (`tests/test_autonomy.py`) |
| baseline `main` | CI-like | 20 | 1306 | 17 | 1 (`tests/test_autonomy.py`) |
| composed (`eb4a0f9`) | refs-present | 18 | 1311 | 18 | 1 |
| composed (`eb4a0f9`) | CI-like | 18 | 1308 | 18 | 1 |

The counts are equal in magnitude (20F → 18F) but the **failing-node identities differ**
between regimes; only the composed tree converges. Fingerprints (FAILED/ERROR lines,
`- Assert…` truncation stripped, `sha256` of the sorted set):

| set | sha256[:16] |
|---|---|
| baseline, refs-present | `4d84e7eb2524d4a5` |
| baseline, CI-like | `a59453b8a1e5a028` |
| **composed, refs-present** | **`c9ffdb6216c70314`** |
| **composed, CI-like** | **`c9ffdb6216c70314`** |

## 3. What is invariant

**The composed failing-node set is identical in both regimes** (`c9ffdb6216c70314`). Set
difference, measured in each regime:

- refs-present: fixed `{exit_code_does_not_call_a_divergent_clean_file_verified,
  gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline}`, newly-failing **0**.
- CI-like: fixed `{exit_code_does_not_call_a_divergent_clean_file_verified,
  shadow_adjudication_is_proved_by_the_oracle_not_the_codec}`, newly-failing **0**.

Both composed sets contain **neither** of the three adjudication nodes — in the composed
tree all three are green (PASS or a legitimate SKIP). This is the load-bearing, environment-
independent claim Pass 2 was reaching for, now stated precisely.

## 4. Correction to Pass 2

- §5's fixed-set `{exit_code, shadow_adjudication}` is correct **for the CI-like regime only**.
  In the refs-present regime the fixed set is `{exit_code, gate2_parent}`.
- §7's *"the sibling node crashes, it does not skip"* holds **only when `7d79f38…` is absent**.
  When the revision is resolvable (as in this automation's clone) the node does not crash and
  does not need the `None` guard: it **passes**. Both readings are correct descriptions of
  *different clones*.
- §7.1's *"on the current tree that node **passes**"* is the **opposite** of what the
  refs-present regime measures: there `test_gate2_parent…` **FAILS**, because its fixture
  dereferences the **moving branch** `origin/main`, whose `AGENTS.md` is now repaired
  (`cyrillic == 0`). #218's pin therefore removes an *active* expiry in that regime, not a
  merely *latent* one.
- §5's environment line should read "node set **of the composed tree** is environment-
  independent", not "attribution is environment-independent".

Pass 2's **core** conclusion is unaffected and re-confirmed: the three PRs are complementary,
the composed tree fixes nodes and introduces none, and all five PRs are git-clean together.

## 5. Merge order (advisory; merge is HUMAN)

Re-measured this pass: merging `#215 → #216 → #217 → #218 → #219` onto `main 162f574` is
**git-clean at every step** (`git merge --no-ff` rc=0, composed HEAD `a3e5111`). The order is
insensitive within this set (disjoint hunks). Recommended narrative-aligned order unchanged:
**#216, #218, #215, #217**, then **#219** (evidence, safe to merge last or first).

## 6. Remaining uncertainty

- The regimes differ only in whether the clone carries `refs/remotes/pr/*`. This automation's
  clone does; a fresh `git clone --single-branch` does not. Neither is "the" environment — the
  correct statement is the **per-regime table** in §2, plus the regime-invariant composed set.
- Composability probes are git-object merges and local suite runs; **no** build, deployment, or
  production-parity claim. Counts are environment-sensitive; attribution is by node set.
- No PR here touches `api/main.py`: budget measured **2582 / 2600**, `py_compile` OK.
- CP10 mutation boundary on the composed diff: `--judge` exit 0.
