# Parking Lot
> Observed issues that are outside current scope.
> No investigation. No fixing. Just record and continue.
> Issues here are picked up during planning, not during implementation sessions.

---

## Format

```
## [short title]
Observed: [what was noticed]
File: [path, if applicable]
Workstream: [which workstream should handle it, if known]
Priority: [low / medium / high]
```

---

## Open Items

## `api/main.py` exceeds its registered 2600-line budget

Observed: `tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
fails on canonical `main` @ `6038989`. `api/main.py` is 2607 lines against a budget of 2600
(the test's own docstring still says "~2506 lines"). Pre-existing, identical on `main` and
on PR #91's head — not introduced by PR #91, which does not touch `api/main.py`.

File: `api/main.py`; gate in `tests/architecture/test_layer_boundaries.py:415`.
Workstream: Phase 2 (api/main.py decomposition). Priority: medium.

*Recorded only. The contract forbids fixing this while executing another gate.*

## `tests/architecture` is 9/11, not the 10/10 stated in `.bootstrap/01_STATE.md`

Observed: `python -m pytest tests/architecture -q` yields 2 failed / 9 passed on main
(`test_no_layer_inversions`, `test_api_main_line_count_within_budget`). `.bootstrap/01_STATE.md`
"Repository Health" claims 10/10, and the WEAVER contract baseline records 9/10. The prose
disagrees with the code and with each other; the code is authoritative.

File: `.bootstrap/01_STATE.md` (Repository Health section).
Workstream: documentation reconciliation. Priority: low.

---

## Closed Items

## Test runs write private material into the tracked-adjacent `vault/` tree

Observed: Running `pytest tests/` from the repository root wrote real note files
into `vault/Ideas/` and `vault/Projects/` (35 untracked files after a full-suite run),
including synthetic private-boundary canary material (`ARKADIA_PRIVATE_CANARY_USER_A/B`,
`SearchBoundaryQuartz7`, `PrivateBoundaryZephyr9`, `user_54267acf` + "secret plans").
`knowledge/vault.py` resolved `VAULT_ROOT = Path("vault")` relative to the process cwd,
so tests did not sandbox their writes; `test_isolation.py` swapped `ARKADIA_DB_PATH` to a
tempdir but the filesystem vault was unaffected. `vault/` is not gitignored, so the files
were stageable by any routine `git add -A`.

Resolved: 2026-09-28, branch `gate02/conftest-vault-sandbox`. A root `conftest.py` now
redirects `ARKADIA_DB_PATH` and `VAULT_ROOT` to a throwaway directory in a session-scoped
autouse fixture, before test modules are imported. Controlled A/B on the same commit
(`e9257bf`), each run starting from a cleaned `vault/`: **35 files leaked without the
fixture, 0 with it** (counted as `find vault -name '*.md' -not -path 'vault/Templates/*'
-not -path 'vault/Index/*'`; the base figure is deterministic across runs), with an
identical test outcome (842 passed / 51 failed / 12 skipped / 2 errors) and an identical
failing-node-ID hash on both sides. `.gitignore` additionally gains `tests/_spine_test.db*`
for SQLite WAL/SHM sidecars.

Evidence: `docs/control-plane/evidence/workstream-b-vault-sandbox/EVIDENCE.md`.

Defence-in-depth still available if desired: ignore patterns for `vault/*/2*.md` while
keeping the tracked scaffold (`.gitkeep`, `vault/Templates/*`, `vault/Index/README.md`).
Not applied — the fixture removes the cause rather than masking it.
