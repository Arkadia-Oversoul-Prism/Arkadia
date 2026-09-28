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

## Test runs write private material into the tracked-adjacent `vault/` tree

Observed: Running `pytest tests/` from the repository root writes real note files
into `vault/Ideas/` and `vault/Projects/`. On 2026-09-28 a full-suite run created
35 untracked files, including synthetic private-boundary canary material
(`ARKADIA_PRIVATE_CANARY_USER_A/B`, `SearchBoundaryQuartz7`, `PrivateBoundaryZephyr9`,
`user_54267acf` + "secret plans"). `knowledge/vault.py` resolves `VAULT_ROOT = Path("vault")`
relative to the process cwd, so the test does not sandbox its writes; the
`test_isolation.py` module swaps `ARKADIA_DB_PATH` to a tempdir but the filesystem vault
is unaffected.

Impact: `vault/` is **not** covered by `.gitignore` (`*.db` is, which is why
`data/runtime.db` is safe). Verified with `git check-ignore` and `git add --dry-run`:
these files are stageable by any routine `git add -A` / `git commit -a`. A commit made
without checking `git status` would fold synthetic private-vault material into the
canonical tree — the exact failure mode corrected by hand at the end of the prior
GATE-10 verification pass.

File: `knowledge/vault.py:17` (`VAULT_ROOT`), writers in `tests/test_oracle_spine.py`
and `tests/test_isolation.py` (vault-backed note creation); exposure boundary in `.gitignore`.
Workstream: Workstream B follow-on (test-hygiene) — otherwise independent of the K-series.
Priority: medium (high if any pass commits with `-a` ahead of review).

*Not fixed here: this pass was a bounded verification run and `.gitignore` was outside its
scope. Candidate fixes (each a separate bounded task): sandbox `VAULT_ROOT` to `tmp_path`
via monkeypatch, and/or add `vault/*/2*.md` to `.gitignore` while keeping the tracked
scaffold (`.gitkeep` + `vault/Templates/*` and `vault/Index/README.md`).*

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

*(moved here when resolved, with resolution note)*
