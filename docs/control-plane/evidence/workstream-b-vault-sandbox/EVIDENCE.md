# Workstream B (test-hygiene) — Test-session vault sandbox — Evidence

**Gate / workstream:** Workstream B follow-on (test-hygiene), the bounded task deferred
by PR #92's ledger entry in `PARKING_LOT.md`. Independent of the GATE-00..13 K-series.
**Authorization:** Human sovereign (review/merge retained exclusively by sovereign).
**BASE_MAIN:** `e9257bf` — "Merge pull request #93 from Arkadia-Oversoul-Prism/gate-01-canonical-authorship"
**Branch:** `gate02/conftest-vault-sandbox`
**Merge:** not performed. Any merge is human-only.

## 1. Repository binding (contract step 01–02)

- `origin/main` = `e9257bf`, a real commit; default branch `main`.
- Ancestry verified, not assumed: `git merge-base --is-ancestor 6038989 e9257bf` → true.
  The clone was shallow (`grafted`), so the ancestry check required `git fetch --deepen`;
  the contract baseline `6038989` is a genuine ancestor of current `main`.
- Credential check: token has `admin/maintain/push/pull/triage`; `git push --dry-run`
  to a new branch succeeded. No read-only-token HARD STOP.
- Live CI on `main` @ `e9257bf`: `mvp2-validation = success`, `browser = success`,
  `weaver_evolution = skipped`.

## 2. The defect (reproduced, not inferred)

`knowledge/vault.py` resolves `VAULT_ROOT = Path("vault")` relative to the process cwd.
Running `pytest tests/` from the repository root therefore writes real note files into the
tracked-adjacent `vault/` tree, including synthetic private-boundary canary material
(`SearchBoundaryQuartz7`, `ARKADIA_PRIVATE_CANARY_USER_A/B`, "secret plans").
`vault/` is not gitignored (only `*.db` is), so those files are stageable by any routine
`git add -A` — an unattended commit could fold synthetic private-canary material into canon.

## 3. Controlled A/B experiment

Two full-suite runs on an **identical clean tree** (`e9257bf`, detached worktree),
identical interpreter and dependencies, each starting from a cleaned `vault/`,
differing in exactly one variable — the presence of the candidate `conftest.py`.

Counting convention, stated so it is reproducible (it matters — the raw figure differs):

```
find vault -name '*.md' -not -path 'vault/Templates/*' -not -path 'vault/Index/*' | wc -l
```

| Condition | Files leaked into `vault/` under the stated convention |
|---|---|
| WITHOUT `conftest.py` (control) | **35** |
| WITH `conftest.py` (this branch) | **0** |

The control figure is deterministic, not a one-off: two consecutive full-suite runs on the
base tree each produced 35 (interestingly, `vault/Ideas/` 30 + `vault/Projects/` 7 = 37
files exists on disk, of which 35 carry the `.md` extension — the convention above is
therefore stated explicitly rather than left to inference).

Test outcome was identical in both runs (see §4), so the isolation does not achieve
"zero leak" by suppressing or skipping tests.

**Correction.** An earlier draft of this section reported the control as **29**, and
attributed the difference from the 35 later observed on `main` to a "counting convention"
(filtering for the tracked `Templates/` and `Index/` scaffold). That explanation was wrong.
Re-measurement shows the base tree leaks **35** under every convention tried, deterministically,
so 29 was simply a bad count and there was no convention discrepancy to explain. Superseded
numbers have been removed rather than reconciled. The load-bearing result never depended on
the exact control count: it is **0 with the fixture vs. non-zero without it**, on the same
commit, with a bit-identical test outcome.

## 4. Regression evidence — failure *sets*, not counts

Both trees run with `--continue-on-collection-errors`, same interpreter, same dependencies,
and — critically — the **same method** for extracting the failure set
(`grep '^FAILED' | awk '{print $2}' | sort | sha256sum`).

| Tree | Result |
|---|---|
| base `e9257bf` (detached worktree, control) | 842 passed / **51 failed** / 12 skipped / 2 errors |
| `e9257bf` + `conftest.py` (this branch) | 842 passed / **51 failed** / 12 skipped / 2 errors |

Sorted FAILED node-ID sets were diffed:

- newly failing on the branch: **none**
- repaired by the branch: **none**
- `sha256` of the sorted FAILED node-ID list — **identical on both sides**:
  `1fc7a2d0b747b90ff03ea658669f5a57c1ec4ccbc324c935333c6ae5495c2502`
  (51 node IDs each)
- collection-error set identical on both: `tests/test_autonomy.py`, `tests/test_render_codex.py`

**Correction to a prior measurement.** An earlier pass in this session recorded the
fingerprint as `4f5fb96968caadf...` and the branch as matching. That value never
reproduced: two fresh, independently executed runs (one on each side, same method) both
yield `1fc7a2d0b747b9...`. The earlier digest was produced by a different extraction
method (`awk` on the summary line vs. `awk` on the `FAILED` lines), so it was not a
like-for-like comparison and has been discarded. The conclusion is unchanged — the sets
are identical — but the canonical digest for this gate is now `1fc7a2d0b747b9...`,
derived by the stated method and reproducible from
`pytest tests/ -q --continue-on-collection-errors | grep '^FAILED' | awk '{print $2}' | sort | sha256sum`.

Architecture suite, unchanged:

| Tree | Result |
|---|---|
| `e9257bf` | 2 failed / 9 passed |
| branch | 2 failed / 9 passed |

Re-verified on the committed head `bbaee7f` (not only on the working tree): full suite
`51 failed, 842 passed, 12 skipped, 2 errors`; architecture `2 failed, 9 passed`;
`vault/` returned to exactly its 4 tracked scaffold files
(`vault/Templates/*.md`, `vault/Index/README.md`) with 0 untracked non-ignored files;
`api/main.py` unchanged at 2607 lines vs base.

The two architecture failures (`test_no_layer_inversions`,
`test_api_main_line_count_within_budget`) are pre-existing on `main`, already recorded in
`PARKING_LOT.md`, and are **not** touched by this change.

### Relationship to the contract's recorded baseline

The contract records `main := 6038989`, `804 passed / 54 failed`. Current `main` is
`e9257bf` and reads `842 passed / 51 failed`. The failure reduction is accounted for by
PR #91's three targeted repairs, independently documented in
`docs/control-plane/evidence/gate10-pr91-verification-heartbeat/EVIDENCE.md`; the pass
growth is accounted for by test modules added in PR #91 and PR #93. This pass does not
claim those deltas — it claims only the baseline-vs-branch comparison in §4, which was
measured directly on the same commit.

## 5. Change under review

| File | Change |
|---|---|
| `conftest.py` (new) | Session-scoped autouse fixture redirecting `ARKADIA_DB_PATH` and `VAULT_ROOT` to a throwaway directory before test modules are imported. Uses `setdefault` on the env var so the existing per-module convention (`tests/test_isolation.py:7` et al.) keeps precedence. Assigns both the module attribute (`knowledge.vault.VAULT_ROOT`) and the package re-export (`knowledge.VAULT_ROOT`), since `from knowledge import VAULT_ROOT` binds at import time. |
| `.gitignore` | Adds `tests/_spine_test.db*`, covering the SQLite WAL/SHM sidecars that the existing `*.db` rule does not match. |

No production module, no `api/main.py`, and no test module was modified.
`git diff --stat e9257bf -- api/main.py` is empty. Boot-code gate still run regardless:
`python -m py_compile api/main.py` → OK.

## 6. Verification of the fix mechanism (falsification)

An earlier measurement in this pass appeared to contradict the fix (a baseline tree with
`conftest.py` copied in still showed a growing file count). That reading was traced to
cumulative state: the candidate `conftest.py` had been copied with `cp` after the control
clean, and earlier runs' artifacts had not been cleaned between measurements, so counts
were accumulating rather than reflecting a single run. Re-measured from a known-clean
starting state, the A/B in §3 is unambiguous. The artifact mtimes (newest `12:22:48`)
predated the conftest run (`12:24`), confirming the files were pre-existing, not newly
written under isolation.

## 7. Result classification

**VERIFIED.** Implementation exists; required tests pass with an unchanged failure
fingerprint; the leak is reduced to zero under a controlled A/B; protected architecture
regression is unchanged; provenance is inspectable in this record and in the commit.

## 8. Remaining uncertainty

- `pytest tests/` is interrupted by default at 2 collection errors (pre-existing); the
  `--continue-on-collection-errors` flag is required to observe the full suite. Unchanged
  by this pass.
- Only 2 of the affected test modules previously sandboxed themselves
  (`test_gate_01_canonical_authorship.py:39`, `test_echofeild_aggregator.py:103`). The
  root fixture now covers all modules, but this has been verified by running the full
  suite rather than by enumerating every writer.
- The `vault/` tree is still not gitignored wholesale; this change makes tests stop
  writing there rather than relying on ignore rules. Adding ignore coverage for
  `vault/*/2*.md` remains available as a defence-in-depth follow-on if the sovereign
  prefers belt-and-braces.

## 9. Authority boundary

No merge performed. No new mutation path, authorization path, or governance surface
introduced. Review and merge remain exclusively human.
