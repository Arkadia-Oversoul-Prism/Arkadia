# gate-hygiene — boot-syntax boundary + cluster #293–#296 verification

Pass: `gate-hygiene/boot-syntax-guard-01`
BASE_MAIN at reconstruction: `4550531e1912e46d231a45f27ca801810def699d`
("Research: define WorkEvent review, completion, and production acceptance (#290)")

This pass authored none of the PRs it verifies. Every claim below is a reproduced
measurement from a fresh clone on `main`, not PR prose.

## 1. Why this pass exists

PR #293 carries a `SyntaxError` in `api/main.py`. The defect was *visible* — every
gate that ran on that PR was green. The reason is structural, not incidental:

**No workflow in `.github/workflows/` runs the Python test suite on a pull request.**
Measured trigger inventory (`yaml.safe_load`, `on:` key):

| workflow | triggers |
|---|---|
| `_diagnose_blank_frontend.yml` | push, workflow_dispatch |
| `arkadia-console-android.yml` | pull_request, push |
| `arkadia-engineering-scheduler.yml` | workflow_dispatch, schedule |
| `build-apk.yml` | push, pull_request, workflow_dispatch |
| `economic-seam-engine.yml` | pull_request, push |
| `gemini-agent-genesis.yml` | issue_comment, workflow_dispatch |
| `keep_alive.yml` | schedule, workflow_dispatch |
| `mie-android-build.yml` | push, pull_request, workflow_dispatch |
| `phase6-persistent-execution.yml` | pull_request, push |
| `provider-routing.yml` | pull_request, workflow_dispatch |
| `security-secret-scan.yml` | pull_request, push, workflow_dispatch |
| `sg-02-fe-2-v.yml` | push, pull_request, workflow_dispatch (path-filtered) |
| `solspire-project-execution.yml` | pull_request, workflow_dispatch |
| `solspire-r{1,2,3,4}-validation.yml` | push, workflow_dispatch |
| `weaver-mvp2-validation.yml` | push, pull_request, workflow_dispatch |

Every `pull_request`-triggered job is either platform-specific (Android/MIE), a
secret scan, or path-filtered to a narrow surface. None imports `api/main.py`.
A boot-broken commit can therefore reach `main` with all visible checks green.

The ledger's only guard against this is the manual note in `AGENTS.md`:
"run `python -m py_compile api/main.py` before every commit that touches boot code."
A manual guard fires only when a human remembers it, and covers one file.

## 2. The bounded repair — a continuous boot-syntax boundary

`tests/test_boot_syntax_boundary.py` (new, 5 tests):

1. `test_api_main_parses` — the P1-A boot surface parses.
2. `test_every_tracked_python_file_parses` — **every** `git ls-files` Python file
   parses, at any path depth.
3. `test_detector_flags_an_embedded_newline_escape` — **negative control**.
4. `test_detector_accepts_a_valid_module` — positive control.
5. `test_detector_reports_a_generic_syntax_error` — generic negative control.

### Why repository-wide rather than `api/main.py` only

PR #293's defect is in `api/main.py`, but the class is not specific to it: any
tracked module can be imported at boot. The full-corpus check costs **0.45 s for
492 files** (measured), so there is no reason to narrow it. The test remains valid
for a nested monorepo because `git ls-files -- '*.py'` matches at any depth.

### Why `compile()` and not `import`

The check must run on a machine without the application's dependencies. This
environment has neither `fastapi` nor `pydantic` installed, yet the guard runs and
passes: `compile()` is pure-syntax and needs no third-party import. An import-based
guard would be unrunnable here and would misreport as a dependency failure.

## 3. Proof the detector catches the real defect

The strongest negative control is the actual PR #293 blob, not a synthetic sample.
Loading the guard's detector and feeding it `git show pr293:api/main.py`:

```
PR#293 api/main.py -> /tmp/pr293_main.py: SyntaxError:
    unexpected character after line continuation character (line 1584)
main  api/main.py  -> None
```

The defect is a collapsed block: the two-character sequence `\n` appears literally
inside one physical line (`if signal:\n            reply = ...`), which CPython
rejects as an invalid line-continuation. The synthetic control in the test file
reproduces exactly this shape so the detector cannot be disarmed by editing the
test without reddening it.

## 4. Guard status on current main and in isolation

```
$ python -m pytest tests/test_boot_syntax_boundary.py -q
5 passed in 0.54s
```

Current main's boot surfaces already compile cleanly
(`python -m compileall -q api kernel weaver solspire lab knowledge providers`
→ exit 0; `python -m py_compile api/main.py` → OK). The guard pins that state; it
is not a repair of main.

## 5. Cluster verification #293–#296 (all four OPEN at reconstruction)

None of the four PRs is merged. Head SHAs resolved via the GitHub API and confirmed
against the fetched `pr293`/`pr294`/`pr296` refs.

| PR | head | `api/main.py` at head | verdict |
|---|---|---|---|
| #293 | `2d0970ab…` | **SyntaxError, line 1584** | CONTRADICTED — do not merge |
| #294 | `351311eb…` | parses, 2805 lines | authority-adjacent, no second authority path |
| #295 | `7116eeea…` | n/a | VERIFIED — fixes CP10 invariant |
| #296 | `3e148653…` | parses, 2594 lines | VERIFIED — restores budget, arch 11/11 |

### #293 — `ARK-02: route Arkana Signal Objects through Commune runtime`

Files: `api/main.py` (+90/−1), `docs/architecture/ARKANA_SIGNAL_GATE_02_RUNTIME.md`.
The head blob raises `SyntaxError` at line 1584. It would also push `api/main.py`
from 2805 to 2894 lines, 294 over the 2600 budget. **Verdict: CONTRADICTED.**

### #295 — `gate10: admit tracked research/ and schemas/ surfaces to the CP10 boundary`

Reproduced on main: **18 non-admitted tracked paths** out of 1799
(`research/oversoul_prism_*/…`, `schemas/arkana/signal/1.0/arkana-signal.schema.json`).
Reproduced on the `pr295` head: **0 non-admitted out of 1800**. The fix is a
`LEGIT` regex extension in `scripts/cp10_mutation_boundary_policy.py` with 60 tests
passing, including negative controls. This is the exact omission class the AGENTS.md
CP10 lesson describes. **Verdict: VERIFIED.**

### #296 — `architecture: restore api/main.py within the 2600-line budget`

Not a docs-only change, despite its prior classification in this workstream's notes.
Files: `api/arkana_signal_routes.py` (new, 258), `api/main.py` (−221),
`docs/…/architecture-main-line-budget-restoration-01/`, `AGENTS.md`.
Reproduced on the `pr296` head: `api/main.py` = **2594 lines**,
`tests/architecture` = **11 passed**. On main the same suite is **1 failed / 10
passed** (`test_api_main_line_count_within_budget`, 2805 > 2600). **Verdict: VERIFIED.**

### #294 — `Prism: bridge ExecutionAttempt to WorkEvent and add governance records`

New workflow `prism-execution-workevent-governance.yml`: `permissions: contents: read`,
no push-to-main, no untrusted `${{ }}` interpolation into `run:` (checked with the
existing `untrusted_interpolations` detector), path-filtered to the surfaces it
governs. 5/5 of `tests/test_prism_execution_workevent_governance.py` pass here; the
companion `test_execution_workevent_boundary.py` cannot collect in this environment
(`fastapi`/`pydantic` absent) — UNKNOWN here, verified by the PR's own workflow.

Authority review of `weaver/enterprise_orchestration.py` (+213): the new
`acceptance`/`review`/`completion`/`production_acceptance` methods each gate on a
prior matching record and an explicit human-supplied authority string. The one
automatic write — `complete_execution_attempt` recording a SolSpire WorkEvent via
`weaver/execution_workevent_bridge.py` — is explicitly observational: its own
docstring states it "does not grant authority, prove correctness, mark completion,
or perform production acceptance". It is idempotent (unique
`execution_attempt_ref` index + `get_by_execution_attempt` retry path). No
second authority path; no self-promotion to authorization. **Verdict: no hard-stop
trigger; merge-safe on the authority dimension.**

## 6. Baseline and regression boundary

- `tests/architecture`: main **1F/10P**; with #296 **11P**. The failure is
  `test_api_main_line_count_within_budget` — the 2805-line overrun, independent of
  this pass.
- This pass adds one file. Full-suite node-set delta from the new file is exactly
  `+5 passed` (measured in isolation). No existing test was modified.
- `python -m py_compile api/main.py` → OK before commit (P1-A rule).
- CP10 `sg-02-fe-2-v.yml` is path-filtered and does not trigger on this branch;
  `tests/test_boot_syntax_boundary.py` and the evidence path are both admitted by
  the policy module (`evaluate_changed_paths` → `(True, 'PASS')`).

## 7. Remaining uncertainty / proposed follow-on

- The full suite could not be run for #294's `test_execution_workevent_boundary.py`
  here (missing `fastapi`/`pydantic`). Not claimed.
- **Proposed, not executed:** a boot-syntax CI job. Adding it needs a dependency
  decision (`compile()`-only needs none; the full suite needs a `requirements.txt`
  install) and touches the CI boundary, which is authority-adjacent. Recorded as
  separate bounded work, not folded into this evidence pass.

## 8. Files changed

- `tests/test_boot_syntax_boundary.py` (new, 5 tests)
- `docs/control-plane/evidence/gate-hygiene-boot-syntax-guard-01/EVIDENCE.md` (this file)
- `docs/control-plane/evidence/gate-hygiene-boot-syntax-guard-01/WORKSTREAM_STATE.md`
