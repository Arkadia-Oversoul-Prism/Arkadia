# EVIDENCE — `tests/test_render_codex.py` collection error is a naming defect, not a missing dependency

**Workstream:** gate-hygiene / baseline test debt
**Branch:** `gate-hygiene/render-codex-collection-error-provenance-01`
**BASE_MAIN:** `002b189d` (merge of PR #141)
**Bucket (ledger):** `COLLECTION_ERROR` — previously left as *"pre-existing, documented"*
**Outcome:** classification corrected and repaired. **One** collection error removed; **zero**
assertions lost.

---

## 1. The recorded claim, and why it is wrong

The baseline ledger (`BASELINE_TEST_DEBT_CLASSIFICATION.md` §4.5) records two collection
errors and explains the second one as an environment dependency:

> `tests/test_render_codex.py` → imports `archive/legacy_python/codex_brain.py`, which imports
> `arkadia_drive_sync` (absent). `AGENTS.md` records this as expected when
> `PYTHONPATH=<repo>/archive/legacy_python` is set.

`AGENTS.md` repeats it, and it is carried in `PARKING_LOT.md`, `CONTINUATION_LEDGER.md`,
`M01-CLOSURE.md`, and `P1-A_FINAL.md`.

**Every pass in this workstream has treated that as settled, so it was never checked.** It is
wrong on the load-bearing point, and the error is a *file-name* defect, not a dependency
defect.

### 1.1 The file is not a test module

`tests/test_render_codex.py` contains **no pytest tests at all**:

```
grep -cE '^def test_|^async def test_|^class Test' tests/test_render_codex.py   ->  0
```

It is a 46-line manual console probe: a `main()` coroutine that constructs `CodexBrain` with
**placeholder API keys** (`<YOUR_GEMINI_KEY>`, `<YOUR_OPENAI_KEY>`), sends two hard-coded
prompts to live model providers, prints the replies, and is guarded by
`if __name__ == "__main__": asyncio.run(main())`.

It asserts nothing. It has never been able to assert anything. Its only interaction with
pytest is that its `test_`-prefixed file name makes pytest import it.

### 1.2 The recorded revision was never green — and could not have been

| revision | `tests/test_render_codex.py` | `arkadia_drive_sync.py` |
|---|---|---|
| `9ab26fc` Genesis | **absent** | present |
| `88a0cafd^` | **absent** | present |
| `88a0cafd` (2026-03-11) | **absent** | **deleted** |
| `784acb4d` (2026-03-11) | **added by rename** | absent |
| `002b189` (main) | present | absent |

```
$ git log --diff-filter=A --format='%H %ad %s' --date=short -- tests/test_render_codex.py
784acb4dc379559966692ee13fa4e6fa9186f8ef 2026-03-11 Rename test_render_codex.py to tests/test_render_codex.py

$ git log --diff-filter=AD --format='%H %ad %s' --date=short -- arkadia_drive_sync.py
88a0cafdbff322718846c4a73be754445e7b6a98 2026-03-11 Delete arkadia_drive_sync.py
9ab26fc9f82f2672e770bf81dc2294d8230bac71 2026-01-01 Genesis: Stone 5 Ascension Finalized
```

The rename is content-preserving — `784acb4d` records `0 insertions(+), 0 deletions(-)`.

**The decisive ordering.** `88a0cafd` deletes `arkadia_drive_sync.py` at **10:50:58** on
2026-03-11. `784acb4d` adds `tests/test_render_codex.py` on the same day. The dependency was
already gone when the file entered `tests/`. There is **no revision** — not Genesis, not
`88a0cafd^`, not any commit since — at which this file could have collected, because it has
never contained a test to collect and its import has been unsatisfiable since the moment it
was named `test_*`.

This is the discriminator against the `F-02` / `SH-05` findings, which were settled by locating
a *green revision* and proving a regression. **Here the negative control has no green
revision to find** — the failure is not a regression at all.

### 1.3 The documented remedy does not work

The recorded explanation offers a remedy: set `PYTHONPATH=<repo>/archive/legacy_python`. That
path was already set for every measurement in this workstream. Applied explicitly:

```
$ PYTHONPATH=/workspace/project/Arkadia/archive/legacy_python python3 -m pytest tests/test_render_codex.py -q
E   ModuleNotFoundError: No module named 'arkadia_drive_sync'
ERROR tests/test_render_codex.py
1 error in 0.12s
```

The import fails because `arkadia_drive_sync.py` no longer exists in the repository *at all* —
not at the root, not under `archive/legacy_python/`:

```
$ ls archive/legacy_python/ | grep -i arkadia_drive    ->  (no match)
```

`codex_brain.py` was itself archived by `377cdb3` (2026-03-23), which is *after* the file
entered `tests/`. So the recorded explanation is also chronologically impossible: at the time
the file was placed in `tests/`, the module it supposedly needed had already been deleted, and
the archiving that the explanation implies had not happened yet.

`PYTHONPATH` was never the variable. Nothing an operator can set makes this file collectable.

## 2. What the real defect is

A **manual console probe** was filed under `tests/` with a `test_` prefix. The `test_` prefix
is what forces pytest to import it; the import is unsatisfiable; the whole suite reports a
collection error that reads like missing infrastructure.

Nothing is missing. The file is in the wrong place with the wrong name.

## 3. The repair

`git mv tests/test_render_codex.py tests/render_codex_probe.py` — rename only, content
**byte-identical** (`0 insertions(+), 0 deletions(-)`).

This is the repository's own established convention: `tests/render_test_console.py` — the
identical sibling probe, sharing the same `from codex_brain import CodexBrain` import — has
*always* been named without a `test_` prefix and is likewise invisible to pytest. The repair
makes the odd one out match the convention the repository already set for this exact kind of
file.

### 3.1 Why not the alternatives

| option | rejected because |
|---|---|
| delete the file | destroys a runnable operator probe to silence a collector; the probe is a diagnostic tool, not dead code |
| add `collect_ignore` / `norecursedirs` | adds bespoke pytest configuration to hide a naming error that one rename fixes; there is no pytest config file in this repository today |
| stub or vendor `arkadia_drive_sync` | manufactures an outbound Google-Drive credential path (`GOOGLE_SERVICE_ACCOUNT_JSON_FILE`, `googleapiclient`) purely to make an import succeed. That is a **new external consequential path** created by a hygiene pass — a hard stop. |
| make the import lazy so collection succeeds | converts a hard failure into a silently-skipped non-test, preserving the false "documented, expected" record and adding no coverage |

### 3.2 What is *not* changed

- **No assertion is lost.** The file defines zero tests (proved above); the collected test
  count is unchanged.
- **No executable product code is touched.** No `api/`, `kernel/`, `weaver/`, `lab/`,
  `solspire/`, or `web/` file is modified.
- **The probe still runs.** `python tests/render_codex_probe.py` behaves exactly as before
  (subject to its own `codex_brain` / `arkadia_drive_sync` import, unchanged).
- **`tests/render_test_console.py` is untouched** — it is the same kind of file, already
  correctly named, and it is not this pass's scope.

## 4. Verification

```
pytest tests/architecture -q                     -> 11 passed
pytest tests/ -q --continue-on-collection-errors -> see §5
python -m py_compile api/main.py                 -> OK   (api/main.py = 2519 / 2600)
scripts/cp10_mutation_boundary_policy.py --judge -> PASS
```

### 4.1 Falsifiability (negative controls)

| control | mutation | expected | result |
|---|---|---|---|
| NC-1 | re-add the `test_` prefix (`git mv` back) | collection error returns | **ERROR tests/test_render_codex.py** — reproduced |
| NC-2 | run the documented `PYTHONPATH` remedy at `002b189` | recorded claim is false | **still `ModuleNotFoundError`** — claim falsified |
| NC-3 | collect-only at `002b189` | file contributes 0 tests | **0 tests from this file** — no coverage to lose |

NC-1 is the load-bearing control: it proves the error is caused by the *name*, not by the
environment, because restoring only the name restores the error while the environment is
untouched.

### 4.2 Negative control for the rename itself (proves the fix is real)

```
at 002b189 (before) : 1071 tests collected, 2 errors
on this branch      : 1071 tests collected, 1 error
```

The collected count is **identical**, and the error count falls by exactly one. That is the
signature of a pure naming repair: nothing gained, nothing lost, one phantom failure gone.

## 5. Baseline comparison

Both runs use `--continue-on-collection-errors` (without it the suite aborts at collection and
the comparison is meaningless).

```
BASE_MAIN 002b189 : 20 failed / 1039 passed / 13 skipped / 2 warnings / 2 errors
this branch       : 20 failed / 1039 passed / 13 skipped / 2 warnings / 1 error
delta             :  0 failed /   +0 passed / 0 skipped / -1 error
```

pytest reports collection errors **separately** from the `failed` count, so the `failed`
figure is unchanged — as it must be for a file that contained no tests. The load-bearing
comparison is the **node list**, which is the check the workstream's own ledger prescribes
("compare by name, never by count alone"):

```
$ diff <(grep -E '^(FAILED|ERROR) ' baseline.txt | sed 's/ - .*//' | sort) \
       <(grep -E '^(FAILED|ERROR) ' branch.txt   | sed 's/ - .*//' | sort)
2d1
< ERROR tests/test_render_codex.py
```

**Exactly one node removed, nothing else moved** — no failure added, none masked, no pass
gained or lost. That is the signature of a pure naming repair.

## 6. Corrections to recorded state

1. **`COLLECTION_ERROR` bucket, second node** — the cause is a file-name defect in
   `tests/`, not a missing dependency. The bucket is right; the *explanation* is wrong and has
   been propagated into `AGENTS.md`, `PARKING_LOT.md`, `CONTINUATION_LEDGER.md`,
   `M01-CLOSURE.md`, and `P1-A_FINAL.md`. Those are **not** edited here (out of this
   workstream's scope and two are other workstreams' artifacts) — recorded for the sovereign.
2. **`test_autonomy.py`** remains a genuine `COLLECTION_ERROR` and is **not** addressed. It is
   the `weaver/autonomy.py` module-vs-package collision, already escalated as `CONTRADICTED`
   (autonomous mutation path — sovereign decision). The two errors are **not** the same kind of
   thing and must stop being reported as a pair.
3. **Baseline in the automation contract** (`main := 6038989`, `804 passed / 54 failed`,
   `arch := 9/10`) is stale. Live at pass start: `002b189`, `1039 passed / 20 failed / 13
   skipped / 2 errors`, `arch := 11/11`.

## 7. Remaining uncertainty

- The 18 remaining failures are pre-existing `main` debt, fingerprint-unchanged, and are
  **not** addressed here.
- `tests/render_test_console.py` shares the shape of the repaired file. It is correctly named
  today and is therefore **not** a defect; it is recorded as a candidate for the same
  disposition only if the probe family is ever retired as a group. Not this pass.
- `vite build` remains environment-blocked; not attempted.
- **No production/runtime claim.** The Gate-2 `main → deployment → runtime` boundary is
  untouched; this is repository-history and test-substrate evidence only.

## 8. Authorization

**READY_FOR_SOVEREIGN_MERGE.** Human-only merge. No self-merge, no push to `main`, no
force-push, no self-authorization. This pass advances **no** gated move.
