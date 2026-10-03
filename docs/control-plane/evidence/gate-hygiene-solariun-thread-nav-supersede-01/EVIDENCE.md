# EVIDENCE — `gate-hygiene` / SOLARIUN-THREAD-NAV supersede, pass 2026-10-03

> Test-side change only. No source, workflow, governance, or constitutional file.
> `api/main.py` untouched (2582 / 2600 lines, `py_compile` clean).

## 1. Objective and scope

Execute the bounded task pinned by PR #224 §"Next bounded task":

> Repair `tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`
> (expanded-literal vs actual render).

**Completion condition.** The node is green, and every *other* assertion in the module still
holds. **Regression boundary.** The failing-node set must change by exactly `−1 / +0`.
**Authority boundary.** No merge, no push to `main`, no force-push, no product decision.

## 2. Base identity

| item | value |
|---|---|
| `BASE_MAIN` | `162f574b05dd839540d803aadda7608342618a84` |
| provenance | merge of PR #214, `2026-10-02 18:16:14 +0100` |
| branch | `gate-hygiene/solariun-thread-nav-supersede-01` |
| working tree at branch point | clean |

## 3. Defect classification — supersede, not regression

The node asserts the **old Home mount**, removed by a sovereign merge:

- `git show 6d5f722` (PR #189, merged to `main`) removes
  `import SolariunHomeCockpit from './SolariunHomeCockpit'` and replaces the `overview`
  branch of `LensContent` with `<SolariunInteractionCanvas onNavigate={target=>{…}}>`.
  The commit message records this as *"chore: remove superseded Solariun home import"*.
- `grep -rn SolariunHomeCockpit web/public_prism/src` → **one hit**: the component's own
  `export default`. It is imported and rendered by **nothing**. It is dead code, and the
  CI-gate fitness list (`tests/test_m02a_ci_gate_integrity.py:229`) pins the *path only*,
  so removing the stale render does not strand a tracked surface.

The **thread-navigation invariant is unchanged**. `SolariunInteractionCanvas` offers the same
thread destinations (`weaver`, `knowledge`, `engineering-lab`) plus `commune`; the shell
routes `onNavigate` through the identical `onThreadTarget` lens selector, and the handler is
still typed to the canonical `SolSpireLens` union — no new router, no new state system.

This is therefore a **stale-assertion supersede** (the S2 class in
`BASELINE_TEST_DEBT_CLASSIFICATION.md`), not a code defect. Repairing source to satisfy it
would re-introduce a mount the sovereign deliberately retired.

## 4. Change

One file, one test body:

```text
tests/test_solariun_thread_navigation_01.py
  test_shell_wires_home_to_lens_selection
    - assert "<SolariunHomeCockpit onNavigate={onThreadTarget}/>" in src
    - assert "onThreadTarget={selectSection}" in src
    - assert "onThreadTarget:(s:SolSpireLens)=>void" in src
    + assert "<SolariunInteractionCanvas onNavigate={target=>{" in src
    + assert "onThreadTarget(target as any)" in src
    + assert "onThreadTarget={selectSection}" in src
    + assert "onThreadTarget:(s:SolSpireLens)=>void" in src
```

The superseded/typed-handler assertions are retained; the mount assertion is re-pointed to the
live canvas and the routing target it actually invokes.

## 5. Evidence

Commands, same interpreter and environment, `main` measured live (not inherited):

```bash
PYTHONPATH=archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors
```

| tree | failed | passed | skipped | nodes | node-set fp |
|---|---|---|---|---|---|
| `main 162f574` | 20 | 1306 | 17 | 21 | `a59453b8…` |
| branch head | 19 | 1307 | 17 | 20 | `66a69c50…` |

**Node-set delta (environment-independent):** `−1 / +0`.

- fixed exactly: `tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`
- newly-failing: **none**

Targeted / protected checks:

| check | result |
|---|---|
| `pytest tests/test_solariun_thread_navigation_01.py -q` | **6 passed** (was 1F/5P) |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | OK |
| CP10 `python scripts/cp10_mutation_boundary_policy.py --judge` | exit 0 |

## 6. Remaining uncertainty

None material. The change is a source-level string assertion; no runtime surface changed, so
there is nothing to observe beyond the fitness suite. No production-parity claim is made.

## 7. Authorization

Sovereign merge only. This PR requests none.
