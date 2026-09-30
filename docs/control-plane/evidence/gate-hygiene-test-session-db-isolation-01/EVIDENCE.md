# EVIDENCE — gate-hygiene / test-session DB isolation 01

Reproducible record of the defect and its repair. Every number below was produced by a
command in this document, run against the stated tree.

## Defect

A full `pytest` run creates the repository's canonical SolSpire store at
`data/solspire_projects.db`.

## Reproduction — negative control

The control is a baseline worktree at `origin/main`, which lacks the fix. Same command,
same interpreter, same session.

```bash
git worktree add --detach /tmp/baseline_wt origin/main   # 002b189

# BASELINE (no fix)
cd /tmp/baseline_wt && python -m pytest tests/ -q --continue-on-collection-errors
ls -la data/solspire_projects.db*
# -> -rw-r--r-- 1 openhands openhands 102400 data/solspire_projects.db

# BRANCH (fix applied)
cd /workspace/project/Arkadia && python -m pytest tests/ -q --continue-on-collection-errors
ls -la data/solspire_projects.db*
# -> ls: cannot access 'data/solspire_projects.db*': No such file or directory
```

The file is untracked, so `git status` stays clean either way. The mutation is only
observable on the filesystem — which is why the defect persisted.

## Baseline fingerprint

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| baseline `002b189` | 20 | 1039 | 13 | 2 |
| branch `9b63ea0` | 20 | 1045 | 13 | 2 |

```bash
diff /tmp/base_fail.txt /tmp/head_fail.txt && echo IDENTICAL
# -> IDENTICAL
```

Failure and error **names** are identical; only the pass count moves, by exactly the six
new assertions in `tests/test_repo_hygiene_gitignore.py`. Baseline debt is neither
attributed to nor repaired by this change.

The 2 collection errors are the pre-existing documented pair (`test_autonomy.py` →
`load_autonomy_config`; `test_render_codex.py` → `arkadia_drive_sync`), present on both
trees.

## Protected-surface evidence

| check | command | result |
|---|---|---|
| architecture fitness | `python -m pytest tests/architecture -q` | `11 passed` |
| new guard | `python -m pytest tests/test_repo_hygiene_gitignore.py -q` | `6 passed` |
| boot compile | `python -m py_compile api/main.py` | OK |
| boot line budget | `wc -l < api/main.py` | `2519` (budget 2600) |
| CP10 boundary | policy judge over changed paths | PASS |
| CI (head `9b63ea0`) | check-runs API | 2/2 success |

## Guard design — what it does and does not prove

`tests/test_repo_hygiene_gitignore.py` pins two distinct invariants:

1. The whole WAL SQLite family (`…db`, `…db-wal`, `…db-shm`) is never stageable. The
   pre-existing `*.db` rule covered only the database file; WAL mode materialises the
   sidecars the moment a session touches the store.
2. No imported module resolves `_DB_PATH` to the repository's canonical store — the
   load-bearing assertion, because it is what `conftest.py::_sandbox_solspire_store`
   guarantees. Without it, deleting the fixture leaves every test green while silently
   re-pointing thirteen modules at the real store.

The guard asserts a **current invariant**, not a delta. It therefore does **not** prove
non-vacuity by failing before the fix. The fixture-deletion check is the valid
demonstration: remove `_sandbox_solspire_store` and the guard goes red while the rest of
the suite stays green.

## Correction: a claim from pass 1 was wrong

Pass 1 asserted that renaming the autouse fixture would silently disable it. **That is
false.** Reproduced in isolation:

```bash
mkdir -p /tmp/autouse_probe && cd /tmp/autouse_probe
printf 'import pytest\n\n@pytest.fixture(scope="session", autouse=True)\ndef renamed_fixture():\n    open("/tmp/autouse_probe/TOUCHED","w").write("yes")\n    yield\n' > conftest.py
printf 'def test_anything():\n    assert True\n' > test_probe.py
rm -f TOUCHED && python -m pytest test_probe.py -q
test -f TOUCHED && echo "YES — renaming does NOT disable autouse"
# -> YES — renaming does NOT disable autouse
```

A renamed `autouse=True` fixture still runs. The name coupling in the guard's docstring is
a **coupling** concern (an edit must update the reference), not a silent-disable hazard.
The PR body has been corrected; the docstring and assertion message were already accurate.

## Authority

Evidence-only classification. No merge, no push to `main`, no force-push, no
self-authorization. Merge remains the sovereign's call.

*This evidence was produced by an AI agent (OpenHands) on behalf of the sovereign.*
