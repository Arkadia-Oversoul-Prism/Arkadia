# gate10/gitleaks-config-guard-ci-wiring-01 — a config guard no gate executed

**Status:** IMPLEMENTED — wiring proven locally by live negative control, PR open, human merge required.
**Branch:** `gate10/gitleaks-config-guard-ci-wiring-01`
**Base:** `main` @ `850216fc99b0eab66a66f8a8290c0db33823b681` ("gate10: repair ADR-016 static-corpus freshness pin")
**Extends:** `docs/control-plane/evidence/gate-hygiene-gitleaks-config-guard-01/` (PR #314, guard introduced)

## 1. Defect (measured, not inferred)

`tests/test_gitleaks_config_guard.py` validates the root `.gitleaks.toml` that the
Full-history secret scan reads (`gitleaks/gitleaks-action@v3` in
`.github/workflows/security-secret-scan.yml`). A config that fails to parse makes
`gitleaks detect` **abort without scanning** — a red "secret scan" that is really a
configuration fault — and an unanchored `allowlist.regexes` entry over-suppresses
findings by matching a substring of any secret value. Both are silent failures at the
boundary the guard holds.

The guard was executed by **no workflow**:

```
$ grep -rln test_gitleaks_config_guard .github/workflows/
(no output)
```

`provider-routing.yml` — the only workflow that runs the full suite — is path-filtered
to `weaver/**`, `providers/**`, `api/lab_routes.py` and named files. A commit editing
`.gitleaks.toml`, or adding the malformed entry the guard rejects, therefore never ran
it. This is the recorded "a guard no workflow executes is decoration" class, already
closed for `test_baseline_fingerprint.py`, `test_boot_syntax_boundary.py` and
`test_ci_gate_trigger_coverage.py`; the config guard was still open.

The inverse direction was also unclosed: nothing asserted that *any* workflow executes
the guard, so the wiring could be deleted without reddening anything.

## 2. Repair (bounded, 2 new files, 0 modified)

### 2.1 `.github/workflows/gitleaks-config-guard.yml` (new executable surface)

Executes the guard and the new wiring guard, is dispatchable (`workflow_dispatch`), and
names **every input the guard reads** in both the `pull_request` and `push` filters:

```
.gitleaks.toml
.github/workflows/gitleaks-config-guard.yml
tests/test_gitleaks_config_guard.py
tests/test_gitleaks_config_guard_ci_wiring.py
```

The guard is stdlib-only (`re`, `tomllib`, `pathlib`), so the job installs `pytest` and
nothing else — a dependency gap cannot be misreported as a config fault.

### 2.2 `tests/test_gitleaks_config_guard_ci_wiring.py` (new boundary guard, 16 tests)

States the invariant generically over every workflow that executes the guard:

1. some workflow executes it with pytest on `pull_request`;
2. that workflow is dispatchable, so the guard can be run against an exact revision;
3. every declared `paths` filter selects **every input the guard reads** — derived from
   the guard's own source by AST (module-level `<root> / "<config>"` constants), not
   restated, so a second hand-maintained copy cannot drift and make the assertion
   vacuous;
4. an executing step can fail the run — no step- or job-level `continue-on-error`, no
   `if: false`.

The filter-coverage rule is applied **per filter**, not over their union: a union can be
complete while the `pull_request` filter omits the input, which is the defect class. A
`paths` glob is compiled to a real regex (`**/` -> `(?:.*/)?`, so `**/*.toml` selects the
root `.gitleaks.toml`), not matched by segment count. Execution is decided by
tokenising the `run` script (`shlex`, comments dropped) and requiring `pytest` to be the
**invoked command** (`pytest x` or `python -m pytest x`), with the contract as an
argument — `echo pytest x` and a comment-only mention are not executions.

## 3. Proof — live negative controls on the real files

Each mutation was applied to the **real** workflow, the guard asserted to redden, and the
file restored byte-identically (`98fd90f52eacb38d14c4b0c0061068a0723ab053511e21f403d9810f47985a19`).

| mutation to `gitleaks-config-guard.yml` | result |
|---|---|
| drop `.gitleaks.toml` from both `paths` filters (the measured defect) | `1 failed, 15 passed` |
| replace the step with `echo pytest ...` (mention, not execution) | `2 failed, 14 passed` |
| job-level `continue-on-error: true` | `2 failed, 14 passed` |
| drop the workflow's own file from its filter | `1 failed, 15 passed` |
| restore | byte-identical, `22 passed` |

The two nodes that flip are exactly
`test_some_workflow_executes_the_gitleaks_config_guard` and
`test_every_candidate_workflow_is_executable_and_can_fail[gitleaks-config-guard.yml-workflow0]`.

A **full-suite** negative control is the decisive one: with the real workflow removed
from the working tree, the same two nodes enter the failing set and nothing else changes.

```
WITH    workflow: 88 failed, 1649 passed, 21 skipped, 96 errors
WITHOUT workflow: 90 failed, 1641 passed, 22 skipped, 96 errors
```

## 4. Regression boundary

- Failure/error **node set** identical on `main` @ `850216fc` and on this branch: 184
  nodes, sha256 `d9dea976adfcf124f06403bcca697745d74508676c619917f51a63f5e6a3d0ff`
  (`comm -3` empty in both directions).
- The `+21 passed` is attributed by **`--collect-only`**, not inferred from the count
  delta: 1756 -> 1777 nodes. Sixteen are this guard file's nodes; five are parametrized
  nodes the generic workflow scanners generate for a new workflow by construction
  (`test_ci_gate_trigger_coverage.py` x3, `test_ci_suite_collection_continuation.py` x1,
  `test_workflow_injection_boundary.py` x1). Zero nodes are removed.
- `tests/architecture` — **11 passed** (unchanged).
- `python -m py_compile api/main.py` — OK. `api/main.py` is untouched (2505 lines,
  budget 2600).
- CP10 boundary judge on both new paths — **exit 0**.

The 88 failed / 96 errors are pre-existing local debt at the same environment (the
documented dependency-set delta; CI's own node set is smaller). None is attributable to
this change, and no baseline debt was repaired.

## 5. Remaining uncertainty / not claimed

- The wiring is proven at the file level and by full-suite negative control. It is
  **not** yet proven by a GitHub Actions run: the first runtime execution of
  `gitleaks-config-guard.yml` occurs on this PR's own `pull_request` event, which is the
  remaining evidence.
- Unchanged and out of scope: the standing Gate-2 production-parity boundary
  (`BLOCKED` on Vercel Deployment Protection) and the pre-existing `Vercel – console` /
  `Vercel – arkadia-prism` commit-status failures on `main` itself.
- No merge, no push to `main`, no allowlist edit, no test weakened, no architecture
  reclassified.

## 6. Next authorized action

Sovereign review and merge of the PR on `gate10/gitleaks-config-guard-ci-wiring-01`.
On merge, confirm the workflow's own `pull_request` run is green — that converts
IMPLEMENTED into VERIFIED for the wiring.
