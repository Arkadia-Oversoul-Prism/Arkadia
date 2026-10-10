# gate-hygiene — boot-syntax boundary CI wiring

Pass: `gate-hygiene/boot-syntax-ci-wiring-01`
BASE_MAIN at reconstruction: `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
Gate: GATE-10 / gate-hygiene. Evidence plus one bounded CI wiring change.

## 1. Defect (measured, not inferred)

`tests/test_boot_syntax_boundary.py` (added by #297, `8d2d251a`) makes the P1-A guard
continuous and repository-wide: `api/main.py` — the boot surface that shipped a
`SyntaxError` in `cd24bb1` and boot-broke every Render deploy of that revision — and
**every** tracked Python file must parse. It is executed by **no** workflow:

```
$ grep -rn test_boot_syntax .github/workflows/      -> (no matches)
$ grep -rl  test_boot_syntax_boundary .github/workflows/  -> (no matches)
```

The guard therefore holds only when a human runs the suite by hand. This is the
defect class the repository already names and has closed twice
(`tests/test_baseline_fingerprint.py`, then `scripts/baseline_preflight.py`): a guard
no gate executes is decoration.

Why the defect is load-bearing here: `api/main.py` is referenced by exactly **one**
workflow's path filter (`.github/workflows/n-atlas-developer-lab.yml:12`), which runs
three named tests and not the boot guard. The CP10 workflow (`sg-02-fe-2-v.yml`) is
path-filtered to `web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`
and named test files — none of which is `api/main.py`. A commit that boot-breaks
`api/main.py` (the P1-A shape) runs the boot guard **nowhere**.

## 2. The bounded repair — wire the existing guard

Exactly the pattern the repository already uses for its other continuous guards:

- `.github/workflows/boot-syntax.yml` (new) — runs
  `tests/test_boot_syntax_boundary.py` **and** `tests/test_boot_syntax_ci_wiring.py`
  on `pull_request` (path-filtered), `push` to `main`, and `workflow_dispatch`.
  `python -m pytest`, `continue-on-error` off, no secrets, no mutation of the
  repository, default (read) permissions.
- `tests/test_boot_syntax_ci_wiring.py` (new, 6 tests) — states the invariant
  generically over **every** workflow that runs the guard.

No product, authority, identity, mutation-path, or `api/main.py` surface is changed.
This PR does not merge.

### Why the path filter is `**/*.py`, not a named file list

The guard's domain is the whole tracked Python corpus: any tracked module can be
imported at boot. A filter naming a handful of files is **incomplete by construction** —
the next boot-broken module is added at a path no `paths:` entry selects, and the guard
never runs on the pull request that introduced it. Measured at `f9ced6b6`, the tracked
corpus is **556** `.py` files spanning many top-level trees; a hand-maintained list
would omit all but the trees someone remembered. `**/*.py` (plus `*.py` for the
repository root, which a leading `**/` also matches) selects the entire domain and
never needs to be extended.

### Why the guard needs no dependency install

`tests/test_boot_syntax_boundary.py` uses `compile()`, not `import` — pure syntax, no
third-party import. It runs in an environment that never installs `fastapi`/`pydantic`,
so a dependency gap cannot be misreported as a boot break. The workflow installs only
`pytest` and `pyyaml` (the latter for the wiring test's YAML parse).

## 3. The invariant, and the domain is derived not restated

`tests/test_boot_syntax_ci_wiring.py`:

1. `test_runs_guard_detector_distinguishes_the_forms` — detector control; a
   `py_compile api/main.py` step is **not** the guard.
2. `test_selector_accepts_the_forms_github_uses` / `test_selector_rejects_an_incomplete_filter`
   — glob controls for the completeness check.
3. `test_a_workflow_executes_the_boot_syntax_guard` — the headline invariant.
4. `test_guard_workflow_is_selected_by_every_tracked_python_file` — parametrised over
   every workflow that runs the guard; the covered domain is read from
   `git ls-files -- '*.py'` **at test time**, so a new tracked module is judged by the
   same rule without editing the test.
5. `test_guard_step_can_fail_the_job` — `continue-on-error` off.
6. `test_wiring_workflow_selects_its_own_file` — the gate must not reject the branch
   it watches (the omission class that reddened `main` at `d48ad0e` / `a26af408`).

No second hand-maintained copy of the domain exists to drift.

## 4. Proof the boundary bites (negative controls)

Live, against the working tree — not synthetic alone:

- Replace the `**/*.py` filter with `api/main.py` -> coverage test **FAILS**
  (`test_guard_workflow_is_selected_by_every_tracked_python_file` and
  `test_wiring_workflow_selects_its_own_file`); restored -> **passes**.
- The guard's own negative controls (in `test_boot_syntax_boundary.py`, from #297) still
  prove the detector flags the exact PR #293 embedded-newline shape.

Guard + wiring suites: **12 passed** (`tests/test_boot_syntax_boundary.py` 5,
`tests/test_boot_syntax_ci_wiring.py` 6 plus the parametrised coverage node).

## 5. Regression boundary

| measurement | `main` `f9ced6b6` | branch |
|---|---|---|
| architecture (`tests/architecture -q`) | 11 passed | 11 passed |
| full-suite failing/error node set | 16 (15F/1E) | 16 (15F/1E) |
| outcomes / ids fingerprint | `bfcfe592…` / `ed5e4714…` | identical |
| `python -m py_compile api/main.py` | OK | OK |
| `api/main.py` lines | 2450 | 2450 |
| CP10 mutation-boundary judge | — | PASS (RC 0) |

The full-suite node set is compared by **identity**, not count: the branch adds a new
test file, so `+N passed` is expected and is not a regression signal.

Environment note (reproducibility): the canonical 16-node set is reproduced only with
the declared test dependencies installed. Measured this pass, a run missing
`pdfminer.six` (declared in `requirements.txt`) reports **17** nodes — the extra one is
`tests/test_market_data.py` failing at import, exactly the precondition
`scripts/baseline_preflight.py` names. With `pdfminer.six` + `pytest-asyncio` present,
the 16-node set and both fingerprints match the canonical pair byte-for-byte.

## 6. Remaining uncertainty / non-goals

- Gate-2 production parity remains `BLOCKED` on Vercel Deployment Protection.
- The pre-existing 16-node baseline debt is recorded, not repaired.
- This pass does not rewrite any `AGENTS.md` oracle line; the new lesson is a fresh
  append.

## 7. Files changed

- `.github/workflows/boot-syntax.yml` (new)
- `tests/test_boot_syntax_ci_wiring.py` (new)
- `docs/control-plane/evidence/gate-hygiene-boot-syntax-ci-wiring-01/EVIDENCE.md` (this file)
- `docs/control-plane/evidence/gate-hygiene-boot-syntax-ci-wiring-01/WORKSTREAM_STATE.md`
- `AGENTS.md` (append: one lesson)
