# GATE-HYGIENE · test-session environment leakage — residual module (`test_weaver_w5`)

## 1. Objective

Close the residual case of the test-session environment-leakage class. PR #108
(`gate-hygiene: stop test-session env leakage at import time`) removed import-time
environment writes from four test modules and stated, in its own evidence ledger:

> Out of scope: production code, `tests/test_weaver_w5.py` (owned by PR #107).

PR #107 was titled `GATE-13 · recalibrate stale W5 derived-graph marker` and changed
only two `DERIVED` -> `DERIVED_BOUNDED_SEMANTIC` assertions in the same file. The
environment-leak that #108 deferred to it was never repaired. That module is this
change's entire scope.

## 2. Root cause

`tests/test_weaver_w5.py::test_http_knowledge_isolation` set two process-global
variables in the test body and never restored them:

```python
tmp = tempfile.mkdtemp(prefix="w5_")
os.environ["SOLSPIRE_PROJECTS_DB"] = os.path.join(tmp, "db.sqlite")
os.environ.setdefault("SOLSPIRE_DATA_DIR", tmp)
pm_mod._DB_PATH = store_mod._DB_PATH = os.environ["SOLSPIRE_PROJECTS_DB"]
```

Two independent leaks, of different kinds:

- **Environment**: `SOLSPIRE_PROJECTS_DB` / `SOLSPIRE_DATA_DIR` outlive the test in
  `os.environ`, so every later module in the session inherits a path into a `w5_`
  temporary directory.
- **Module rebinding**: `_DB_PATH` is overwritten *on the imported module objects*.
  This is not environment at all — it is a second, harder-to-see mutation path. An
  env-only repair would leave it live.

Observed on `main` (`8843fd5`) with a temporary probe collected *after* the module:
`SOLSPIRE_PROJECTS_DB=/tmp/w5_pm3ifni0/db.sqlite`, and both `pm._DB_PATH` and
`store._DB_PATH` pointing at that stale tmpdir for the remainder of the session.

## 3. Change

`tests/test_weaver_w5.py` only. No production code touched. `os` and `tempfile`
imports dropped; `pytest` imported.

| Concern | Before | After |
| --- | --- | --- |
| tmp directory | `tempfile.mkdtemp()` never cleaned | pytest's `tmp_path` |
| `SOLSPIRE_PROJECTS_DB` | body write, never restored | `monkeypatch.setenv` |
| `SOLSPIRE_DATA_DIR` | body `setdefault`, never restored | `monkeypatch.setenv` |
| `pm_mod._DB_PATH` / `store_mod._DB_PATH` | direct module rebinding, never restored | `monkeypatch.setattr` (both) |

`monkeypatch` is function-scoped and undone at teardown, so both the environment and
the module attributes return to their ambient values. `monkeypatch.setenv` is used
rather than `setdefault` deliberately: the test's intent is to *point the store at its
own DB*, and `setdefault` silently yields to whatever a previous module leaked — the
exact failure mode being repaired.

## 4. Verification

Environment: `/usr/local/bin/python -m pytest`, `PYTHONPATH=<repo>/archive/legacy_python`.

Leak probe — temporary file collected after the repaired module, then deleted before
commit (not part of the change set):

| | before fix | after fix |
| --- | --- | --- |
| `SOLSPIRE_PROJECTS_DB` | `/tmp/w5_pm3ifni0/db.sqlite` | `None` |
| `SOLSPIRE_DATA_DIR` | `/tmp/w5_pm3ifni0` | `None` |
| `pm._DB_PATH` | stale w5 tmpdir | `data/solspire_projects.db` |
| `store._DB_PATH` | stale w5 tmpdir | `data/solspire_projects.db` |

`pytest tests/test_weaver_w5.py tests/<probe>` -> 6 passed + 1 passed (7).

Full suite — `main` (`8843fd5`) vs this branch:

| | main | this branch |
| --- | --- | --- |
| passed | 962 | **962** |
| failed | 54 | 54 |
| errors | 2 | 2 |
| skipped | 12 | 12 |

Failure fingerprint delta is **empty**: the sorted `FAILED`/`ERROR` node list is
byte-identical before and after (`sha256=13543871…`). No test changed state in either
direction.

This leak was therefore **latent, not active**: it did not cause any currently-failing
test. It is repaired as a correctness and isolation defect, not as a debt reduction,
and this document records that claim explicitly rather than implying a green delta.

`pytest tests/architecture -q` -> **11 passed** (fitness intact, no new debt).
`api/main.py` untouched; boot surface unchanged.

## 5. Residual / out of scope

- **Preferred structural fix not taken.** pytest's `tmp_path` already implies a
  per-module `HOME`; had the w5 module used it for the store path from the start the
  class would not exist. No repair is proposed here.
- **Not the whole class.** Correctly scoped test-body writes that restore themselves
  remain in `tests/test_weaver_mvp2_03.py:138-157` and
  `tests/test_phase5_governed_execution.py` (four sites, each with a `finally` block).
  They mutate `REPO_ROOT`, to which an unverified helper (`weaver/autonomy.py`) reads
  at call time, and the commit path is already `os.chdir`-sensitive. Repairing them is
  a separate bounded decision with a wider regression surface, so it is explicitly
  **not** in this change.
- **Import-time writes.** Three modules write `os.environ["ARKADIA_DB_PATH"]` at import
  (`tests/test_gate_01_canonical_authorship.py:23`, `tests/test_isolation.py:7`,
  `tests/test_oracle_spine.py:27`). They are the same class as the four #108 repaired.
  After two successive PRs over one class without closing it, the remaining inventory
  should be repaired in a single bounded change rather than a third module-by-module
  pass. Not proposed or executed here.
- **Stale bootstrap scratchpad.** `.bootstrap/03_SCOPE.md` still describes session
  `B1.1 — SQLite Schema` while the live workstream is the gate series above. Recorded
  as an observation only; refreshing it would be unrelated scope.
