# Evidence — GOV-04 conformance input selection (gate-hygiene)

Revision measured: `main` `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24).
Branch: `gate-hygiene/gov04-conformance-input-selection-01`.

## 1. Verified gap

`tests/test_gov04_bounded_merge_delegation.py` asserts the wording of the GOV-04
authorization record and the fail-closed shape of `weaver/execution_adapter.py`. No
workflow's `paths` filter selected the guard or its inputs:

```
$ grep -rn "test_gov04_bounded_merge_delegation" .github/
(no output)
```

The only whole-suite surface is `provider-routing.yml`
(`pytest tests/ -q -rEf --continue-on-collection-errors`). Its filter already carries an
`AGENTS.md` entry for exactly this reason — `tests/test_agents_md_encoding_adjudication.py`
reads it — but the GOV-04 guard's inputs were never enumerated.

The three workflows that select `tests/**` (`economic-seam-engine`, `operator-console-posture`,
`prism-console-contract`) execute named guards, not the whole suite, so a revision touching only
`AUTHORIZATION.md` or only the conformance test ran no gate that executes it.

## 2. Why this is not a duplicate of the open GOV-04 work

| PR | Owns | Does not cover |
|----|------|----------------|
| #724 | `AUTHORIZATION.md` activation record | selection wiring |
| #725 | the conformance test's literal pins (repairs the red node) | selection wiring |
| #726 | platform preconditions (branch protection / rulesets classifier) | conformance selection |

#726's own header names the conformance guard as a separate surface it does not measure.
This change touches `.github/workflows/provider-routing.yml`, which none of them modifies.

## 3. Change

`.github/workflows/provider-routing.yml`: six paths added to the `pull_request` filter —
the conformance guard, this wiring guard, `AUTHORIZATION.md`, `WORKER_CONTRACT.md`,
`PRISM-UI-RECONCILIATION.md`, `SHARED-CONTRACTS.md`.

`tests/test_gov04_conformance_ci_wiring.py` (new): the input list is **derived by AST** from
the conformance guard's own module-level `ROOT / "…"` constants, not restated. The invariant
is existential: at least one workflow must both *execute* the guard and *select* it, and every
such workflow must select each derived input plus itself.

## 4. Measurements

- `python -m pytest tests/test_gov04_conformance_ci_wiring.py -q` → **6 passed**.
- Live negative control: deleting the `AUTHORIZATION.md` line from the real workflow reddens
  exactly `test_a_workflow_selects_every_input_its_guard_reads[provider-routing.yml]` and
  `test_detector_rejects_an_incomplete_filter` (**2 failed, 4 passed**); restored
  byte-identically, sha256 `818d3b71…` before and after → **6 passed**.
- The detector's own negative control caught a real defect in its first draft: it scored
  `echo pytest <guard>` as an execution. Repaired to require `pytest` to be the invoked
  command word of a simple command (`pytest …` or `python -m pytest …`).
- A directory argument (`pytest tests/`) counts only with `--continue-on-collection-errors`.
  `sg-02-fe-2-v.yml` therefore does not satisfy the domain: its CP10-B step aborts on the CE-01
  `weaver.autonomy` collection error and runs zero tests.
- Regression: `test_ci_gate_trigger_coverage`, `test_history_depth_ci_wiring`,
  `test_workflow_injection_boundary`, `test_ci_suite_collection_continuation`,
  `test_gate_filter_selection`, `tests/architecture` → **329 passed**.
- CP10 mutation boundary: `PASS` for both new paths.

## 5. Not claimed

- `main` still carries the red node
  `tests/test_gov04_bounded_merge_delegation.py::test_bounded_merge_is_exact_head_and_protected_fail_closed`.
  It is **owned by PR #725** (verified: `5 passed` at that head in a detached worktree). This
  change does not repair it and must not be read as doing so.
- `provider-routing` compares the candidate against its merge base, so this PR stays green while
  that node remains red — an unchanged baseline node is reported, not failed.
- No merge, deployment, or acceptance is claimed.
