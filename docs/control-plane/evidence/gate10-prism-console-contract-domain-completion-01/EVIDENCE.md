# gate10/prism-console-contract-domain-completion-01 — complete the console-contract gate after its domain grew

**Status:** IMPLEMENTED — repair proven locally, PR open, human merge required.
**Branch:** `gate10/prism-console-contract-domain-completion-01`
**Base:** `main` @ `17988afdde8460cfcaf778258bc43aed1fc9d21f`
**Supersedes the state of:** `docs/control-plane/evidence/prism-console-contract-ci-gating-01/` (PR #435, merge `18a450d0`)

## 1. Defect (measured, not inferred)

`tests/test_prism_console_ci_wiring.py` (introduced by PR #435) derives the console-contract
domain from `git ls-files` at test time and requires the gate
`.github/workflows/prism-console-contract.yml` to execute **the whole derived domain**. The
domain is content-derived: a tracked test module belongs to it when it names
`web/arkadia_console` or `api/frontend_routes`.

The gate names its guards **explicitly** (both in its step and in its `paths` filters). Three
console guards merged after #435 therefore entered the derived domain without entering the gate:

| guard | introduced by | merge commit |
|---|---|---|
| `tests/test_prism_opportunity_entry_flow.py` | #430 | `7b378cec` |
| `tests/test_knowledge_projects_boundary.py`, `tests/test_knowledge_timeline_boundary.py` | #431 | `bcc6a8b4` |

`#429` (`65403304`) landed **before** the guard itself, so no single pull request could have
observed the drift: the guard only exists from `18a450d0` onward, and by then the sibling
branches had already been cut from `f390526a`. Measured on `main` @ `17988afd`: derived domain
**16**, gate executes **13**, missing **3**.

## 2. Runtime evidence — `main` is red

The two wiring-guard nodes fail on `main` itself:

```
FAILED tests/test_prism_console_ci_wiring.py::test_a_workflow_executes_the_whole_console_contract
FAILED tests/test_prism_console_ci_wiring.py::test_wiring_workflow_is_a_complete_gate_that_selects_itself
2 failed, 17 passed, 2 skipped
```

And the gate workflow ran on the two pushes that caused it:

```
38146786696 65403304b6 push main success  2026-10-11T14:20:37Z
38146791182 7b378cecee push main failure  2026-10-11T14:20:41Z   <- #430
38146795295 bcc6a8b4c0 push main failure  2026-10-11T14:20:45Z   <- #431
```

Attribution is exact: the only nodes that changed between `f390526` (19 failing/error nodes) and
`17988afd` (21) are these two. Full-suite node set sha256 at `17988afd`:
`c2b6e0998382af6f3b75011f5fd8de899d966e68624211990eb2e3e0a3a8c5c4`.

## 3. Repair (bounded, 9 inserted lines in one file)

`.github/workflows/prism-console-contract.yml` only:

- the `pull_request` `paths` filter — 3 guards added;
- the `push` `paths` filter — the same 3 guards added;
- the executing step — the same 3 guards added.

No test was weakened, no assertion relaxed, no allowlist edited, no architecture reclassified.
The three guards already existed and pass; the gate simply did not run them.

## 4. Proof

| check | before | after |
|---|---|---|
| `pytest tests/test_prism_console_ci_wiring.py` | **2 failed**, 17 passed | **21 passed** |
| domain / executed | 16 / 13 (missing 3) | **16 / 16 (missing none)** |
| exact gate-step command | — | **279 passed** |
| full suite failing/error nodes | 21 (sha256 `c2b6e099…`) | **19 — `comm -3` empty vs the `f390526` baseline** |
| architecture fitness | 11 passed | **11 passed** |
| CP10 mutation boundary | — | **PASS** (`--judge` admits the changed path) |
| YAML parse | — | valid, one job `console-contract` |

**Live negative control** (proves the detector bites on the real file, not a synthetic fixture):
removing `tests/test_knowledge_timeline_boundary.py` from the step reddens both nodes
(`2 failed, 17 passed`); restoring the file returns `21 passed`. The working tree was restored
byte-identically — `git diff --stat` reports the repair only (`1 file changed, 9 insertions(+)`).

## 5. Recurrence risk (recorded, not repaired here)

The gate's explicit name list must be updated by hand in the same change that adds a console
guard, in three places. A structural repair — a step that executes the domain the guard derives,
so no list can drift — is **proposed, not executed**: it widens an execution surface and is a
separate bounded workstream for sovereign review. Two viable shapes:

1. a thin, **committed** `scripts/run_prism_console_contract.py` that derives the domain and
   execs `pytest` over it (CP10-admitted, no network fetch at run time); or
2. `pytest tests/` with a `-k` selection derived from the same needles.

This PR deliberately keeps the minimal repair that restores `main`, per the rule that discovery
does not authorize execution.

## 6. Authority

`api/main.py` untouched. No merge, no deployment, no production claim. Human merge required.
