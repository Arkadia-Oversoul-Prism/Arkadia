# Lane 1 — the composition-root case detector read comments as code

**Workstream:** Lane 1 (shell / navigation / design system / integration seam).
**Base:** `main` `19697a6a358ec114265e665fcc22eea8d5018ac2` (measured live this pulse).
**Branch:** `feat/prism-l1-composition-case-comment-blindness-01`.
**Owned file:** `tests/test_console_shell_nav_contract.py` (Lane 1 owns the shared shell contract tests).

## The defect

`test_every_declared_surface_is_composed_in_the_app_root` exists to catch a declared
surface with no `case` in the composition root: such a surface silently renders the
default page — no type error, no runtime error. Its detector was

```python
def _composition_root_surface_ids(text: str) -> set[str]:
    return set(re.findall(r'case "([^"]+)":', text))
```

Two ways a *non-dispatch* satisfies that pattern:

1. **A commented-out case.** `// case "workspace":` still matches `case "workspace":`,
   so a surface whose only case is a comment reads as composed.
2. **A case in a different switch.** The pattern searched the whole file, so a
   `case "ghost":` in any unrelated `switch` counted as a surface dispatch.

The detector also had **no live binding**: the only control
(`test_detector_flags_a_declared_surface_with_no_composition_case`) fed it synthetic
strings and never touched `App.tsx`, so nothing tied the detector to the real file.

## Measured vacuity (before the repair)

Live mutation on the real `web/arkadia_console/src/App.tsx` at base `19697a6a`:
comment out the actual `case "workspace":` line.

```
$ python -m pytest tests/test_console_shell_nav_contract.py -q
50 passed
```

A surface that no longer dispatches left the suite **green**. `workspace` is the
surface the auth threshold redirects into, so the loss is not cosmetic.

## The repair

```python
_SURFACE_SWITCH = re.compile(
    r"switch\s*\(\s*route\.surface\s*\)\s*\{(.*?)\n\s*\}", re.DOTALL
)
_COMPOSITION_CASE = re.compile(r'case "([^"]+)":')

def _composition_root_surface_ids(text: str) -> set[str]:
    match = _SURFACE_SWITCH.search(_without_ts_comments(text))
    if match is None:
        return set()
    return set(_COMPOSITION_CASE.findall(match.group(1)))
```

* `_without_ts_comments` (an existing helper in this file, reused — not a second
  comment stripper) removes block and full-line comments, so a commented case is
  not a dispatch.
* The domain is narrowed to the `switch (route.surface)` block, so a case in any
  other switch is not a surface dispatch.

## Controls

Three controls, each failing against the pre-repair shape and passing after:

| Control | Pre-repair | Post-repair |
|---|---|---|
| `test_detector_does_not_count_a_commented_out_case_as_composed` | FAIL | pass |
| `test_detector_reads_only_the_route_surface_switch` | FAIL | pass |
| `test_composition_root_detector_agrees_with_the_live_app` (binds the detector to the real `App.tsx`; asserts a non-empty domain so a detector that matched nothing cannot pass) | FAIL | pass |

Each control asserts **both polarities** — the defective input is reported, and the
repaired input is not — so a detector that matches everything cannot pass either.

## Live negative control (the load-bearing proof)

Commenting out the real `case "workspace":` in `App.tsx`:

* **pre-repair:** `50 passed` — blind.
* **post-repair:** `2 failed, 51 passed` —
  `test_every_declared_surface_is_composed_in_the_app_root` and
  `test_composition_root_detector_agrees_with_the_live_app`.

`App.tsx` was restored byte-identically afterwards (`git status --porcelain` empty)
and the suite returned to `53 passed`.

## Attribution

`--collect-only` on the file: **50 → 53** nodes, `+3` — exactly the three new
controls. No other node moved.

## Wiring

No new wiring is required: `tests/test_console_shell_nav_contract.py` is already in the
derived console-contract domain (`scripts/console_contract_domain.py` → 70 files,
including this one), so the gate executes the repaired detector without an edit to any
workflow.

## Commands and results (this branch, this head)

| Command | Result |
|---|---|
| `python -m pytest tests/test_console_shell_nav_contract.py -q` | **53 passed** |
| `python -m pytest tests/test_console_endpoint_registry_contract.py tests/test_console_shell_nav_contract.py tests/architecture -q` | **85 passed** |
| `python scripts/lane_state.py --check` | exit **0** |

## Baseline (measured at `19697a6a`, not inherited)

Full suite once: `19 failed, 4025 passed, 18 skipped, 1 error`. Failing/error node set
(20 nodes) sha256
`c2af82276bd93928f68c9a4a7a95eb8fd3d4162e6af5347eb48ff8e27492e021`. Architecture
`11 passed`. This change adds no failing node: the only failing/error nodes are
pre-existing `main` debt, and the three new controls pass.

## Boundaries

No console source changed (the `App.tsx` mutation was restored byte-identically and is
not part of the diff). No backend, authority, identity, deployment, or another lane's
file is touched. Merge, deployment, and acceptance remain human-only.

## Flaky check observed (not branch-caused)

On the first CI run for this head (`ccd34a86`), `Prism Console Contract`
(`.github/workflows/prism-console-contract.yml`, run `43662539712`) failed at the
step **"Workspace layout assertions (rendered, authenticated test identity)"** with
`canonical session view did not reach READY_FOR_REVIEW: AUTHORIZED`, while
`success` was recorded for the same workflow on `main` `19697a6a`
(run `43635356668`).

It is **not attributable to this branch**:

- The diff touches only `tests/test_console_shell_nav_contract.py`,
  `docs/control-plane/parallel-ui/{AGENT-01-SHELL.md,lane-state.json}`, and this
  evidence doc. The failing step boots the real `api.main` and drives a rendered
  mission-lifecycle flow; it reads none of them.
- `gh run rerun 43662539712 --failed` → the same job (rerun `132655729884`)
  **passed** (3m10s) with no change to the tree. A failure that clears on an
  identical re-run is environmental, not a regression this diff introduced.

Final state at head `ccd34a86`: **11/11 checks pass**, `MERGEABLE` / `CLEAN`.

## Final PR state

PR **#658**, draft, head `ccd34a86cc629e7ae1b4290505c26c2e2faf081c`, base `main`
`19697a6a358ec114265e665fcc22eea8d5018ac2`. Merge, deployment, and acceptance
remain human-only.
