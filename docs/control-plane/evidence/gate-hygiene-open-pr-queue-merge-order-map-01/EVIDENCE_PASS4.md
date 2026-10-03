# gate-hygiene — open-PR queue Pass 4: composability proven from `main`, and the Pass-3 "refs-present" figures corrected

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01` (continuation; branch `-02`)
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence pass. **No source, test, or governance change.**
Re-confirms Pass 2's queue inventory / overlap map / composability / merge order, and
**corrects** Pass 3 §2's `refs-present` column, which does not reproduce in this clone.

---

## 1. Why this pass exists

Pass 3 asserted a **refs-present regime** in which "this automation's clone" carries
**216 `refs/remotes/pr/*`** and the baseline full suite yields **20F / 1308P / 1 error**.
This pass measured the *actual* clone the automation provides: **5** PR refs
(`refs/heads/pr/215..219` and `refs/remotes/pr/215..219`), revision `7d79f38…`
**unresolvable** (`git cat-file -t 7d79f38` → `fatal: Not a valid object name`), and a
baseline of **60F / 836P / 45 errors** (or 58F / 848P / 43 errors with `requests`
installed). Neither Pass-3 `refs-present` figure reproduces. The Pass-3 `refs-present`
column is therefore an **unreproduced measurement**, not a stable regime description, and
is marked as such below.

The composability conclusion itself is unaffected and is now re-proven **from a clean
`main` base** in this clone's actual regime.

## 2. Live queue inventory (reconstructed)

Five open PRs, all based on `main 162f574`, all `MERGEABLE`, all `UNSTABLE`.

| PR | head | changed files | +/− |
|---|---|---|---|
| #215 | `0c18fbb40b3dd2572389f04fcc59bd94b48da69e` | 2 | +84/−0 |
| #216 | `4747e4c62ffacd5c965be8acc6a1c756a5eccd23` | 8 | +208/−28 |
| #217 | `3b5e4cdcca3968d74cde944450c990675057d77d` | 2 | +124/−1 |
| #218 | `54e2e988c08ea771403bc6642f3c5eae43142641` | 2 | +108/−2 |
| #219 | `a83c53827b8bf63cc11622b330eb8007ee01d707` | 5 | +534/−0 |

`UNSTABLE` is environmental and pre-existing on **every** head:

- check-runs: `Full-history secret scan` → **success** on all five; `Vercel Preview Comments`
  → success on the four that ran it.
- commit statuses: `Vercel – arkadia-prism` → success on #216–#219; `Vercel – console` →
  **failure** on all five (a separate Vercel project, unrelated to any PR in the cluster).
  #215 is additionally rate-limited on `arkadia-prism` (`Deployment rate limited — retry in
  24 hours`), not a code failure.

The only **required** workstream gate (secret scan) passes on all five. `Vercel – console`
is pre-existing debt, not a regression introduced by the cluster.

## 3. Overlap map (re-confirmed)

Only `tests/test_agents_md_encoding_adjudication.py` is multiply modified — by **#215,
#217, #218** — and the three edits land in **different functions**:

- #215 → `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
- #217 → `test_exit_code_does_not_call_a_divergent_clean_file_verified`
- #218 → `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`

`AGENTS.md` is written by **#216 and #219** (disjoint regions: #216 edits the mid-file
fingerprint note at `@@ -583`, #219 appends at EOF). `tests/test_baseline_fingerprint.py`
is written by #216 only.

## 4. Composability — proven from `main` in this clone

Sequential `git merge --no-ff` of `#215 → #216 → #217 → #218 → #219` onto `main 162f574`:

```
after #215 -> bb36a5f
after #216 -> 27d7eaf
after #217 -> 76d8508
after #218 -> 9c36e06
after #219 -> 75a01d0e83377ea642fe8a5f83c9faacaddb9abd   (composed HEAD)
```

**git-clean at every step (rc=0, zero conflict markers).** Order-insensitivity re-proven:
the alternate order `#216 → #218 → #215 → #217 → #219` composes to `196b713f…`, and
`git diff --stat 75a01d0 196b713f` is **empty** — the two orders produce an identical tree.

CP10 mutation boundary (`scripts/cp10_mutation_boundary_policy.py --judge`) on the composed
diff `main..75a01d0`: **PASS, exit 0**. Per-PR diffs `main..pr/{215..219}`: **PASS** on all
five. `api/main.py` is untouched by the cluster; budget measured **2582 / 2600**,
`py_compile` OK.

## 5. Baseline vs composed — attributed by node set

Environment: `PYTHONPATH=archive/legacy_python`, `python -m pytest tests/ -q
--continue-on-collection-errors` (the flag is required; a bare `pytest tests/` interrupts at
the collection error). **Both trees measured in this clone, this pass.**

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| baseline `main 162f574` (this clone) | 60 | 836 | 17 | 45 |
| composed `75a01d0` (this clone) | 58 | 838 | 18 | 45 |
| baseline `main 162f574` (`requests` installed) | 58 | 848 | 17 | 43 |
| composed `75a01d0` (`requests` installed) | 56 | 850 | 18 | 43 |

The **45 errors are a dependency delta, not a regression**: they are
`ModuleNotFoundError: No module named 'requests'` (collected in `tests/test_weaver_k7.py`,
`test_weaver_w4.py`, `test_weaver_w5.py` and 42 other modules). The baseline and composed
trees carry the **same 45 error files** in both cases; installing `requests` clears two of
them equally on both sides. No error surface is introduced by the cluster.

### 5.1 Node-set delta (the load-bearing claim)

Sorted `FAILED`/`ERROR` node set, this clone, `requests` absent:

| set | count | sha256 |
|---|---|---|
| baseline `main` | 105 | `cb28007a91469800…` |
| composed `75a01d0` | 103 | `3a5da082fe8f6fbc…` |

Set difference (baseline → composed):

- **FIXED:** `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
  and `…::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`.
- **NEWLY FAILING: 0.**

With `requests` installed the delta is identical (baseline 101 nodes → composed 99 nodes,
the same two nodes fixed, **0 new**). **The composed tree introduces no failing node in
either dependency regime, and fixes the same two adjudication nodes in both.**

### 5.2 Adjudication module, isolated

- composed `75a01d0`: `18 passed, 5 skipped` — all three disputed nodes green.
- baseline `main 162f574`: `2 failed, 17 passed, 4 skipped` — the two `exit_code` /
  `shadow_adjudication` nodes fail.

## 6. Correction to Pass 3

Pass 3 §2 recorded two regimes and attributed one to "this automation's clone". Measured
here, that attribution does not hold:

| Pass-3 claim | this pass |
|---|---|
| "this automation's clone has **216** `refs/remotes/pr/*`" | **5** PR refs; `7d79f38` → `fatal: Not a valid object name` |
| baseline refs-present = **20F / 1308P / 1 error** | **60F / 836P / 45 errors** (58F / 848P / 43 with `requests`) |
| composed refs-present = **18F / 1311P / 1 error**, set `c9ffdb6216c70314` | **58F / 838P / 45 errors**, set `3a5da082fe8f6fbc…` |
| composed set is regime-invariant at `c9ffdb6216c70314` | **not reproduced**; this clone's composed set is `3a5da082fe8f6fbc…` |

What **survives** from Pass 3, restated in regime-neutral form and re-measured here:

- The **composed** failing-node set is the environment-independent attribution target, and
  the composed tree fixes the same two adjudication nodes with **0** newly-failing nodes.
- `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` is regime-sensitive
  because its fixture dereferences the **moving branch** `origin/main`; pinning it to the
  corrupt revision (#218) removes an active expiry, not a latent one.
- The two adjudication assertion defects remain a **separate proposed workstream**.

The Pass-3 `refs-present` absolute counts (`20F`, `c9ffdb62…`) are **unreproduced** in this
clone and should not be cited as a regime fingerprint. The defensible claim is the *delta*:
composed = baseline **minus two adjudication nodes**, plus zero.

## 7. Merge order (advisory; merge is HUMAN)

Re-measured: `#215 → #216 → #217 → #218 → #219` onto `main 162f574` is git-clean at every
step, and the tree is order-insensitive. Narrative-aligned advisory order unchanged:
**#216, #218, #215, #217**, then **#219** (evidence; safe first or last).

## 8. Remaining uncertainty

- Composability probes are git-object merges and local suite runs; **no** build, deployment,
  or production-parity claim. Counts are dependency- and clone-sensitive; attribution is by
  node set of the composed tree.
- The Pass-3 `refs-present` environment was not reproducible in this automation clone; the
  cause (a different local clone shape) is recorded, not resolved.
- `Vercel – console` failing on all five heads is pre-existing and out of scope.

## 9. Next bounded task (pinned)

**`gate-hygiene/superseded-fingerprint-origin-01` follow-on — the two excluded adjudication
assertion defects.** Both nodes pin revision `7d79f38…` and mis-handle its absence:

- `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` — dereferences the
  `GATE2_PARENT_REV` read unconditionally → `AttributeError` (error) when the revision is
  absent, rather than skipping.
- `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` — compares against
  the moving branch `origin/main`, an active expiry.

**Scope:** `tests/test_agents_md_encoding_adjudication.py` only; make both nodes skip
cleanly when their revision is absent, and pin the parent comparison to a fixed revision
instead of `origin/main`. **Evidence:** the module runs green in **both** clone regimes.
**Authority:** test-only; no source, governance, or identity change. **Dependency:** none —
independent of the current cluster. This is a **separate bounded workstream**; do not fold it
into the queue-map PR.
