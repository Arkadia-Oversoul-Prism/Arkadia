# gate-hygiene — open-PR queue Pass 5: the composed tree is re-derived on the live #219 tip, and Pass 4's clone-regime claims are corrected by direct measurement

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01` (continuation; branch `-02`)
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence pass. **No source, test, or governance change.**
Re-proves the cluster `#215–#219` composable from a clean `main` in the regime this
automation clone actually provides, and **corrects** Pass 4 §1's clone-regime claims, none
of which reproduce here.

---

## 1. Why this pass exists

Pass 4 §1 asserted the automation clone's regime is: **5** PR refs, revision `7d79f38…`
**unresolvable**, and a baseline of **60F / 836P / 45 errors** — with the 45 errors being
`ModuleNotFoundError: No module named 'requests'`. It used that asserted regime to mark
Pass 3's `refs-present` figures unreproduced.

This pass measured the clone the automation actually provides, and **every one of those
three claims is false in it**:

| Pass-4 §1 claim | measured here | instrument |
|---|---|---|
| `7d79f38…` unresolvable | **resolvable** — `git cat-file -t 7d79f38` → `commit` (`gate2: close backend runtime link VERIFIED (discriminating), main 002b189`) | `git cat-file -t 7d79f38` |
| 45 errors are `No module named 'requests'` | `requests` **2.34.2 is installed**; `ModuleNotFoundError` occurrences in the main run = **0** | `python -c "import requests"`; `grep -c ModuleNotFoundError /tmp/p5_main.txt` |
| "5 PR refs" (and Pass 3's "216") | **7** `refs/remotes/pr/*` (143, 150, 215–219); **0** `refs/heads/pr/*` | `git for-each-ref refs/remotes/pr/` |

The 45-error regime is therefore **not reproducible here and is not a `requests` artifact**.
Without `PYTHONPATH=archive/legacy_python` this clone still yields exactly **1** collection
error (`1343 tests collected, 1 error`), not 45.

**The composability conclusion survives** — it is re-proven below on the live tip of #219,
which has moved since Pass 4 measured it.

## 2. Live queue inventory (reconstructed)

Five open PRs, all based on `main 162f574`, all open and non-draft. Base and heads
re-read from the GitHub API this pass (token: ambient `github_token`; `GITHUB_TOKEN` is
empty and `GITHUB_PERSONAL_ACCESS_TOKEN` returns 401).

| PR | head (full SHA) | changed files | +/− |
|---|---|---|---|
| #215 | `0c18fbb40b3dd2572389f04fcc59bd94b48da69e` | 2 | +84/−0 |
| #216 | `4747e4c62ffacd5c965be8acc6a1c756a5eccd23` | 8 | +208/−28 |
| #217 | `3b5e4cdcca3968d74cde944450c990675057d77d` | 2 | +124/−1 |
| #218 | `54e2e988c08ea771403bc6642f3c5eae43142641` | 2 | +108/−2 |
| #219 | `210d6c0a24d2d0ca4b6fe24fd2322e15ed469042` | 7 | +534/−0 |

**#219's head moved.** Pass 4 recorded `a83c538…`; the live head is `210d6c0…`, one commit
further (`gate-hygiene: pass 4 — re-prove open-PR cluster composability from main; correct
Pass-3 refs-present figures`), which is the commit that **added `EVIDENCE_PASS4.md`**. A
composability proof carried over from a prior tip is stale; the composed tree is re-derived
in §4 against `210d6c0`.

`mergeable` is `null` in the list response (GitHub computes it lazily); it is not asserted
here.

## 3. Overlap map (re-confirmed)

Only `tests/test_agents_md_encoding_adjudication.py` is multiply modified — by **#215,
#217, #218** — and the three edits land in **different functions**:

- #215 → adds a `pytest.skip(...)` guard to `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
  (the node that raises `AttributeError` on `main`).
- #217 → `test_exit_code_does_not_call_a_divergent_clean_file_verified`
- #218 → `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`; replaces the
  moving `origin/main` fixture with a pinned `CORRUPTION_COMMIT`.

`AGENTS.md` is written by **#216 and #219** (disjoint regions: #216 edits the mid-file
fingerprint note, #219 appends at EOF). `tests/test_baseline_fingerprint.py` is written by
#216 only.

**Attribution:** `main` fails these two adjudication nodes for the reasons above — #215
supplies the missing skip guard (`AttributeError` → clean skip), and #218 removes the
`origin/main` expiry. Both defects are in `main`, not in the cluster.

## 4. Composability — proven from `main` on the live #219 tip

Sequential `git merge --no-ff` of `#215 → #216 → #217 → #218 → #219` onto `main 162f574`:

```
after #215 -> 43a1ff8
after #216 -> b742fde
after #217 -> 21ab737
after #218 -> 9b88a01
after #219 -> b06399bc005527a8f58cf4ee88ed40299673ccf6   (composed HEAD)
composed tree -> db958f62e8fd91aa45b5656b805a1848eebdb9f1
```

**git-clean at every step** (rc=0; the two `Auto-merging` notices are in-file auto-merges,
not conflicts). **Order-insensitivity re-proven:** the alternate order
`#216 → #218 → #215 → #217 → #219` composes to the **identical tree**
`db958f62e8fd91aa45b5656b805a1848eebdb9f1`; `git diff --stat` between the two orders is
empty.

CP10 mutation boundary (`scripts/cp10_mutation_boundary_policy.py --judge`): **PASS, exit 0**
on the composed diff and **PASS** on each of the five per-PR diffs. `api/main.py` is
untouched by the cluster; composed budget **2582 / 2600**, `py_compile` **OK**.

## 5. Baseline vs composed — attributed by node set

Environment: `PYTHONPATH=archive/legacy_python`,
`python -m pytest tests/ -q --continue-on-collection-errors` (the flag is required; a bare
`pytest tests/` interrupts at the collection error). pytest 9.1.1. **Both trees measured in
this clone, this pass.** `pytest_randomly` is absent, so collection order is deterministic.

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| baseline `main 162f574` | **20** | **1308** | 15 | **1** |
| composed `b06399b` (live #219 tip) | **18** | **1311** | 15 | **1** |

The single error is `ERROR tests/test_autonomy.py` —
`ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'`. It is a
**pre-existing main residual** (the documented `weaver.autonomy` module-vs-package
collision), present identically on both trees; it is not a dependency delta and is not
introduced by the cluster.

### 5.1 Node-set delta (the load-bearing claim)

Sorted `FAILED`/`ERROR` node set:

| set | count | sha256 (`outcomes_fingerprint`) |
|---|---|---|
| baseline `main` | 21 | `4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7` |
| composed `b06399b` | 19 | `c9ffdb6216c7031403b9e259a75f0d173bccc9103c8c66215b52aa04ffd05c01` |

Set difference (baseline → composed):

- **FIXED (2):**
  `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
  and `…::test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`.
- **NEWLY FAILING: 0.** Shared nodes: **19** — every other baseline residual is unchanged.

**Verdict: the composed tree introduces no failing node and fixes exactly the two
adjudication nodes it targets.** This is a node-set claim, not a count claim: counts are
environment-sensitive, node identity is not.

### 5.2 Adjudication module, isolated

- composed `b06399b`: **21 passed, 2 skipped** — all three disputed nodes green.
- baseline `main 162f574`: **2 failed, 19 passed, 2 skipped** — the two nodes above fail.

## 6. Corrections recorded this pass

| Pass-4 §1 claim | this pass | instrument |
|---|---|---|
| `7d79f38…` unresolvable | **resolvable** (`commit`) | `git cat-file -t 7d79f38` |
| baseline 45 errors, `No module named 'requests'` | `requests` **installed**; **0** `ModuleNotFoundError`; **1** error (`test_autonomy.py`) | `import requests`; `grep -c`; pytest |
| "5 PR refs" regime | **7** `refs/remotes/pr/*` (143, 150, 215–219) | `git for-each-ref` |
| Pass 3 `refs-present` = 20F/1308P/1E "unreproduced" | **reproduces here** (20F/1308P/15S/1E, set `4d84e7eb…`) | pytest + `baseline_fingerprint.py` |
| composed `c9ffdb62…` "not reproduced" | **reproduces here** (18F/1311P/15S/1E) | pytest + `baseline_fingerprint.py` |

Pass 4's own table row — "composed set is regime-invariant at `c9ffdb6216c70314` → **not
reproduced**" — is therefore itself corrected: `c9ffdb6216c70314` **is** this clone's
composed fingerprint, and it is stable across the `#219` head move (Pass 4 measured it at
`a83c538`, this pass at `210d6c0`; identical set).

**Structural conclusion:** the clone is **full-history** (`git rev-list --count HEAD` =
1604; no `.git/shallow`) and the `-02` branch carries the **previous passes' documents**, so
the adjudication module's `_rev(...)` fixtures resolve `7d79f38…` and `origin/main` resolves
to the live main. Pass 4's error count and unresolvable revision are consistent with a
*different* clone shape — **a bare / single-branch clone, where the pinned revision and
`origin/main` are absent and the module's fixture paths error instead of skipping**. That
shape was not observed in this automation clone and its cause is recorded, not resolved.

## 7. Merge order (advisory; merge is HUMAN)

Re-measured on the live tip: `#215 → #216 → #217 → #218 → #219` onto `main 162f574` is
git-clean at every step and order-insensitive. Narrative-aligned advisory order unchanged:
**#216, #218, #215, #217**, then **#219** (evidence; safe first or last).

## 8. Remaining uncertainty

- Composability probes are git-object merges and local suite runs; **no** build, deployment,
  or production-parity claim. Counts are dependency- and clone-sensitive; attribution is by
  node set of the composed tree.
- The Pass-4 "45-error / unresolvable-revision" environment was not reproducible here; the
  consistent explanation (a bare/single-branch clone) is recorded, not proven.
- `Vercel – console` status remains a pre-existing blocker behind the cluster's `UNSTABLE`
  state, out of scope for this pass.

## 9. Next bounded task (pinned)

**`gate-hygiene/stale-gate-fixture-retirement-01` — two residual `main` failures that assert
a surface the repository deliberately archived.**

`tests/test_gate_status.py::test_gate_files_and_fetch_handling` and
`tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists` assert the
existence of a root `gate/` directory (`gate/index.html`, `gate/gate.js`, `gate/gate.css`)
and a root `index.html` redirect. Commit `f6718b9` **archived** those files
(`git log --all -- gate/index.html` → `f6718b9 Recalibration: archive dead execution stacks
… orphaned duplicates (gate, …)`; they now live at `archive/legacy_frontend/gate/`). Neither
path is tracked at root, so both tests fail by construction.

- **Scope:** `tests/test_gate_status.py`, `tests/test_gate_serve_script.py` only — retire the
  two stale-surface assertions (or repoint them at `archive/legacy_frontend/gate/`, which
  still tracks all three files). No production source.
- **Evidence:** the two nodes are absent from the failing set; the remaining `test_gate_status`
  node (`test_report_export`) and `scripts/serve-gate.sh` are untouched and stay green.
- **Authority:** test-only; no source, governance, identity, or authority change.
- **Dependency:** none — independent of the `#215–#219` cluster.
- **Boundary:** this is a **separate bounded workstream**; do not fold it into the queue-map
  PR.

## 10. Provenance

- Clone: full-history, `HEAD` = `main` = `162f574b…`; `origin/main` = `162f574b…`.
- PR refs: `refs/remotes/pr/{143,150,215,216,217,218,219}`; **0** `refs/heads/pr/*`.
- Fingerprints: main `4d84e7eb2524d4a5…`, composed `c9ffdb6216c7031403b9e259…`
  (`scripts/baseline_fingerprint.py`).
- Composition: composed HEAD `b06399b…`, tree `db958f62…`; alt-order tree identical.
- Logs: `/tmp/p5_main.txt`, `/tmp/p5_comp_b.txt`; node sets compared in-memory.
