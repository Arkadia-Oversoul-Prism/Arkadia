# WORKSTREAM STATE — gate-hygiene / test-session DB isolation 01

Persisted so the next heartbeat reconstructs from evidence, not memory.

## Pass identity

| field | value |
|---|---|
| clock | HOURLY (one bounded pass) |
| base main | `002b189` (merge of PR #141) |
| branch | `gate-hygiene/test-session-db-isolation-01` |
| head | `9b63ea0` |
| classification | `VERIFIED` |
| authority required | merge only |

## Established this pass

The diagnostic focus was **full-suite test pollution creating the canonical SolSpire DB**
`data/solspire_projects.db`. The claim is now measured, not inferred.

Baseline worktree (`origin/main` = `002b189`, **without** the fix) after one full suite run:

    -rw-r--r-- 1 openhands openhands 102400 data/solspire_projects.db   # CREATED

Same command at branch head `9b63ea0` (**with** the fix):

    ls: cannot access 'data/solspire_projects.db*': No such file or directory

That pair is the negative control: the baseline reproduces the defect, the branch does not.
`data/solspire_projects.db` is not tracked, so the pollution was invisible to `git status` —
the only observable was a mutated local file, which is exactly why it survived unnoticed.

## Root cause (measured)

Thirteen modules snapshot the store path at **import** time:

    _DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
        os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
    )

(`solspire/*.py`, `weaver/enterprise_orchestration.py`, `lab/engineering_lab/store.py`.)
A test that patches only the two or three copies it happens to import leaves the remainder
writing to the repository's real store. The affected tests **still pass**, so the leak is
silent. `test_eden_solspire_01_instantiation.py` and `test_enterprise_onboarding.py` leaked
this way.

## Baseline comparison (fingerprint, not narrative)

Full suite, `--continue-on-collection-errors` (both runs, same invocation):

| tree | result |
|---|---|
| baseline `002b189` | 20 failed, **1039** passed, 13 skipped, 2 errors |
| branch `9b63ea0` | 20 failed, **1045** passed, 13 skipped, 2 errors |

`diff` of the sorted `FAILED`/`ERROR` lines: **identical**. No new failures, no repaired
failures. The `+6` passed is exactly the six new assertions in
`tests/test_repo_hygiene_gitignore.py`. Baseline debt is unchanged and unattributed.

Architecture fitness `11/11`. `api/main.py` untouched at 2519 lines (budget 2600);
`python -m py_compile api/main.py` OK.

## Note on the contract's stated baseline

The run contract carries `main := 6038989`, `architecture := 9/10`,
`full_suite := 804 passed / 54 failed`. Measured at `002b189` it is `11/11` and
`1039 passed / 20 failed`. The contract's numbers are stale; per Principle 11 the live
measurement governs. Recorded here so the next pass does not re-derive the discrepancy.

## Two claims corrected in the PR body this pass

Both were written as prose in pass 1 and were wrong. The PR description now carries the
correction rather than the claim.

1. **"the guard is not vacuous"** — the guard asserts a *current* invariant, not a
   delta. The valid demonstration is the fixture-deletion negative control, not a
   pre-fix failure. Corrected to say so.
2. **"renaming the autouse fixture would disable it"** — **false**. Independently
   reproduced in an isolated probe: a renamed `@pytest.fixture(scope="session",
   autouse=True)` still runs. The guard's `_sandbox_solspire_store` name coupling is
   therefore a *coupling* concern, not a *silent-disable* concern. Corrected in the
   body; the docstring and assertion message were already accurate.

## Files changed

| file | delta |
|---|---|
| `.gitignore` | +5 |
| `conftest.py` | +41 |
| `tests/test_repo_hygiene_gitignore.py` | +100 |
| this evidence directory | +2 files |

## Next bounded task (proposed, NOT authorised)

`SH-05` (PR #142) remains at the sovereign boundary and is **not** advanced here: its
disposition (retire / relocate into `web/public_prism` / restore) is a product answer, and
the two candidate repairs are opposite. Do not merge it on the basis of this pass.

Open PRs observed: #142 (`gate-hygiene/sh05-gate-artifact-provenance-01` @ `59fbb53`),
#143 (`gate-hygiene/gate2-production-parity-02`), #144 (this branch).

## Constraints honoured

No source, workflow, governance or constitutional file modified beyond the three above.
No merge, no push to `main`, no force-push, no self-authorization.
