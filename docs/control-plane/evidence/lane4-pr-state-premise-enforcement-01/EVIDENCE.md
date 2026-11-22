# Lane 4 — the Lab PR-state guard's premise is enforced, not assumed

**Workstream:** `lane4-pr-state-premise-enforcement-01`
**Base:** `main` @ `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Branch:** `lane4/pr-state-premise-enforcement-01`
**Scope:** `tests/test_prism_w4_lab_pr_state.py` (+ this record). No product code, no
snapshot, no lane-instruction-doc edit.
**Authority:** implementation, testing and evidence only. Merge, production deployment and
acceptance remain human-only under GOV-03.

## 1. The defect, measured

`tests/test_prism_w4_lab_pr_state.py` asserted its no-token premise in a docstring
("No token in the environment -> the handler must report UNAVAILABLE") but never enforced
it. `api/lab_routes.pr_state` selects its branch from the **ambient** environment:

```python
token = os.environ.get("GITHUB_TOKEN")
if not token:
    return {"state": "UNAVAILABLE", "detail": "no GITHUB_TOKEN in environment", "pr": None}
```

So the guard's verdict depended on **who ran it**:

| environment | result |
| --- | --- |
| `GITHUB_TOKEN` unset (the CI gate installs `requirements.txt` but exports no token) | `19 passed` |
| `GITHUB_TOKEN` set (this sandbox; any operator shell; a token-exporting runner) | **`2 failed, 19 passed`** |

The two red nodes are `test_handler_emits_the_keys_the_projection_reads` and
`test_projection_reads_the_handler_output`. They failed because the handler took the
AVAILABLE branch and actually read PR #623 from GitHub, so the payload had no `detail` key
and `readAvailability` returned `AVAILABLE`.

This is the class the repository has already recorded more than once: *a guard whose verdict
is a function of ambient state is not a guard.* Locally green and CI green were reporting
different properties.

## 2. The second half: the AVAILABLE branch was never executed

With no token the AVAILABLE branch is unreachable, so its key set was pinned by a
**source-text scan**:

```python
source = (REPO_ROOT / "api" / "lab_routes.py").read_text(encoding="utf-8")
...
assert f'"{key}":' in body
```

That assertion passes on a comment and never runs the code it claims to measure — the
test-side literal-pin defect class this repository records elsewhere. The handler's only
external dependency is `urllib.request.urlopen`, so a canned response executes the real
parsing and key construction with no network call.

## 3. The change

1. `test_handler_emits_the_keys_the_projection_reads(monkeypatch)` and
   `test_projection_reads_the_handler_output(monkeypatch)` now call
   `monkeypatch.delenv("GITHUB_TOKEN", raising=False)`. The premise is **enforced**.
2. `test_handler_available_branch_emits_the_measured_record` executes the AVAILABLE branch
   against a canned GitHub response and asserts the emitted key set, the `head.sha` /
   `base.ref` unwrapping, and that the projection reads the record. This *measures* the keys
   instead of scanning for them.
3. `test_negative_control_the_token_branch_fails_closed` proves the token branch is real and
   fails closed: with a token present and the transport answering `401`, the handler returns
   `UNAVAILABLE`, `pr is None`, `detail == "http 401"` — never an invented record. It also
   proves the `delenv` above is load-bearing rather than decorative.

The stubbed transport is deliberate and minimal: the handler's contract under test is *its own
branch selection, parsing and key construction*, and `urlopen` is the single boundary that
would otherwise make the test network- and credential-dependent. The real `pr_state` code
path still runs.

## 4. Verification (measured, this environment)

| check | before | after |
| --- | --- | --- |
| `pytest tests/test_prism_w4_lab_pr_state.py` **with** ambient `GITHUB_TOKEN` | `2 failed, 19 passed` | **`21 passed`** |
| same file **without** a token (`env -u GITHUB_TOKEN -u GH_TOKEN`) | `19 passed` | **`21 passed`** |
| `--collect-only` node count | 19 | **21** (+2 = the two added nodes) |
| derived console-contract domain (`python -m pytest -q $(python scripts/console_contract_domain.py)`) | `12 failed, 1269 passed, 4 skipped` | **`10 failed, 1273 passed, 4 skipped`** |
| `tests/test_prism_console_ci_wiring.py`, both lane suites, `tests/architecture` | — | **`123 passed`** |
| `python -m py_compile api/main.py` | — | **OK** |

The `+4 passed` decomposes as the two repaired nodes plus the two added nodes; no other node
moved.

### Live negative control

Removing the two `monkeypatch.delenv(...)` lines from the real file, with `GITHUB_TOKEN`
present, reddens **exactly** the two original nodes (`2 failed, 19 passed`); restoring the
file byte-identically returns `21 passed`. The repair is therefore attributable to the
`delenv`, not to a coincidence.

### Remaining failures are an environment gap, not branch debt

The 10 remaining domain failures are all in
`tests/test_mission_lifecycle_adapter_contract.py`, which requires the repository TypeScript
compiler at `web/arkadia_console/node_modules/typescript/lib/typescript.js`. This sandbox has
no `pnpm install`; the gate's `Console typecheck` step installs it before this suite runs.
They are identical on `main` and on this branch, and this change does not touch them.

## 5. Non-goals

- No product code changed. `api/lab_routes.py` is untouched.
- No lane-instruction doc or `lane-state.json` edit. The committed snapshot deliberately
  records the post-merge state; recording this PR's own open thread would redden
  `lane-doc-currency` on `main` the instant it merges.
- The AVAILABLE branch's network behaviour is not exercised against live GitHub; that would
  make the guard credential- and network-dependent again, which is the defect being repaired.

## 6. Next permitted action

Human review of this draft PR. Merge is human-only (GOV-03). After merge, the next lane-4
slice opens from freshly fetched `main` inside lane 4's owned paths
(`SHARED-CONTRACTS.md` §1).
