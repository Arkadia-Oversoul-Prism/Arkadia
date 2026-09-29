# GATE-HYGIENE · test-session environment leakage

## 1. Objective

Stop the test session from leaking environment overrides out of one test module and
into every other module in the same process, so `pytest tests/` cannot corrupt the
tracked-adjacent `vault/` tree or destabilise unrelated modules.

Scope: the four test modules that mutated corpus/env paths at **import time**.
Out of scope: production code, `tests/test_weaver_w5.py` (owned by PR #107).

## 2. Root cause

pytest imports *every* collected module before running *any* test. A module-level
`os.environ[...] = ...` therefore executes during the collection phase and remains
in force for the whole session. No fixture teardown can undo it, and the ordering
that exposes the damage is not stable — two modules can pass in isolation and fail
together.

`knowledge.vault.VAULT_ROOT = Path("vault")` resolves relative to the process CWD,
so an override that redirects a data directory out from under a later module lets
that module write into the repository's real `vault/` tree, which holds synthetic
private-boundary canary material.

## 3. Change

Environment control moved from import time to execution time.

| File | Before | After |
| --- | --- | --- |
| `tests/test_echofeild_aggregator.py` | module-level `ARKADIA_DB_PATH` + `SOLSPIRE_PROJECTS_DB` writes | module constant `_SOL_DB`; `client` fixture sets `_DB_PATH` via `monkeypatch.setattr` |
| `tests/test_m01_persistence.py` | module-level `SOLSPIRE_PROJECTS_DB` + `SOLSPIRE_DATA_DIR` writes | no module-level write; `test_db_path_honours_data_dir_env(monkeypatch)` uses `monkeypatch.context()` |
| `tests/test_solspire_ownership.py` | module-level `SOLSPIRE_PROJECTS_DB` write + `setdefault` leak | module constant `_SOL_DB`; `client` fixture points stores at it and restores |
| `tests/test_weaver_w4.py` | unconditional `os.environ` writes in the test body | `test_solspire_weaver_routes_owner_isolation(monkeypatch)` via `monkeypatch.setenv` / `setattr` |

`tests/test_m01_persistence.py` keeps its second `importlib.reload(store_mod)` after
the monkeypatch block: the reload at that point re-bakes `_DB_PATH` from the ambient
environment, and the module's own `_isolate` fixture re-points the store per test.
The reload is deliberate, not redundant.

## 4. Verification

Environment: `/usr/local/bin/python -m pytest`, `PYTHONPATH=<repo>/archive/legacy_python`,
`-p no:randomly --continue-on-collection-errors` (the last two are required for the
session to run at all; see §6).

Edited modules in isolation:

```
84 passed, 1 warning in 17.96s
```

Full suite — pristine `main` (`a26af40`) vs this branch:

| | main | this branch |
| --- | --- | --- |
| passed | 903 | **904** |
| failed | 49 | **48** |
| errors | 2 | 2 |
| skipped | 12 | 12 |

Failure fingerprint delta (baseline → branch) is exactly one entry:

```
- FAILED tests/test_m01_persistence.py::test_db_path_honours_data_dir_env
```

No other test changed state in either direction.

`tests/architecture`: **11 passed** (fitness intact, no new debt).

The earlier intermediate run of this workstream reported `53 errors`, including
collection errors across `tests/test_solspire_ownership.py` and a spurious
`ImportError collecting tests/test_autonomy.py`. All 53 are gone; the residual
2 errors are the documented pre-existing `test_autonomy.py` / `test_render_codex.py`
collection errors.

### Vault integrity

`git status --porcelain` after the full suite:

```
 M tests/test_echofeild_aggregator.py
 M tests/test_m01_persistence.py
 M tests/test_solspire_ownership.py
 M tests/test_weaver_w4.py
```

`git diff --name-only | grep -c 'vault/'` → `0`. No tracked-adjacent `vault/` file was
touched by the run.

## 5. Regression boundary

Only test-session env handling changed. No production module edited, so no boot path,
route, or authority surface is affected. `api/main.py` is untouched (no `py_compile`
gate required; line budget unchanged).

## 6. Remaining uncertainty

- Three further import-time `ARKADIA_DB_PATH` writes remain, on a different env key:
  `tests/test_gate_01_canonical_authorship.py:23`, `tests/test_isolation.py:7`,
  `tests/test_oracle_spine.py:27`. They do not produce an observed failure in the
  current ordering and are **not** fixed here — widening scope inside a bounded pass
  is prohibited. Proposed as a separate bounded workstream.
- The `2 errors` and the ~48 baseline failures are pre-existing debt, unchanged in
  fingerprint. Not addressed.
- `vite build` remains environment-blocked (no npm registry access).

## 7. Authority

No merge, no authorization change, no identity or governance code touched. The
mutation surface is test-only. Human merge required.
