# GATE-10 · CP10-B broad-suite reachability

**Workstream:** GATE-10 governed execution — CI coverage of the governed-execution substrate
**Branch:** `gate10/cp10-broad-suite-reach-01`
**BASE_MAIN:** `26521e246e575105ec9a42fec26dc66aeb4c98f4` (2026-10-12T12:08:54+01:00)
**Authorization:** this pass. Discovery from the prior reconnaissance pass did not authorize
execution; this pass was authorized to perform the bounded Defect-A repair.

## 1. Defect — a broad-suite step that executes ZERO tests

`.github/workflows/sg-02-fe-2-v.yml` step `CP10-B broader backend regression`
(`id: backend`, lines 235–245 at `26521e24`) ran:

```
python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
```

The known **CE-01** `weaver.autonomy` module-vs-package collision makes a bare
`pytest tests/` **interrupt** the session:

```
ERROR tests/test_autonomy.py
ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 skipped, 1 warning, 1 error in 10.05s
```

### Runtime proof (not prose)

Run **`38240790826`**, job **`114782590860`**, `event=push`, head `26521e24` — the
CP10-B step log. The step's entire test output is the `Interrupted:` line above:
**zero tests executed**. The row is scheduled (a handful of other steps ran) but the
step's payload is a single aborted pytest session, so the 177 test files reachable
only through a broad-suite run were executed **0** times in this job.

`provider-routing.yml` — the sibling whole-suite surface, and the **only** workflow
selected by `weaver/**` that runs the suite — is triggered on `pull_request` +
`workflow_dispatch` only. It declares **no** `pull_request`-free `push` trigger, so a
merge to `main` runs it nowhere. That makes CP10-B the *sole* broad-suite surface on
`main`'s push event, and it aborts.

## 2. Why the guard did not already catch it

`tests/test_ci_suite_collection_continuation.py` asserts the continuation flag over
**judging** broad-suite steps only — `continue-on-error is not True`. CP10-B is
`continue-on-error: true`, so the invariant was deliberately silent on it.

The prior reconnaissance pass recorded this as **Defect C**: that exclusion is
unsupported, and CP10-B is the counterexample. Gating and reaching are different
properties; this repair separates them.

## 3. Repair (bounded)

One token in one already-selected file:

```diff
-        run: python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
+        run: python -m pytest tests/ -q --continue-on-collection-errors 2>&1 | tee cp10-backend.log
```

- The step is non-gating (`continue-on-error: true`), so the flag **cannot turn `main`
  red** for debt it did not introduce. It changes the step's *content* from "nothing"
  to "the suite, reported". It does not touch `continue-on-error`.
- It does not touch `api/main.py` (`python -m py_compile api/main.py` → clean).
- It matches the sibling surface: `provider-routing.yml`'s "Broader test suite" step
  already carries `-q -rEf --continue-on-collection-errors`.
- Measured locally (this environment): the same suite completes in ~137 s reporting
  `98 failed, 1855 passed, 21 skipped, 105 errors` instead of aborting at the first
  collection error.

## 4. Guard added — reachability independent of gating

`tests/test_ci_suite_collection_continuation.py` gains:

- `test_every_broad_suite_step_reaches_the_suite` — parametrized over **every**
  tracked workflow; every broad-suite step, gating or not, must carry the flag.
- `test_the_cp10b_step_is_a_broad_suite_reachability_instance` — pins the repaired
  surface (`id: backend`) so a rewrite of it is a visible change.
- `test_negative_control_reachability_detector_flags_the_pre_fix_step` — feeds the
  exact pre-fix CP10-B line and asserts it lacks the flag (detector signal).
- `test_positive_control_reachability_detector_accepts_the_repaired_step`.

### The guard bites on the real file (live negative control)

Removing the flag from the **real** `sg-02-fe-2-v.yml` in the working tree:

```
FAILED ...::test_every_broad_suite_step_reaches_the_suite[sg-02-fe-2-v.yml]
FAILED ...::test_the_cp10b_step_is_a_broad_suite_reachability_instance
2 failed, 89 passed in 0.80s
```

Restored byte-identically → `91 passed`.

## 5. Regression boundary

Failing/error node **set** compared by identity, same environment, both trees:

| Tree | nodes | sha256 |
|---|---|---|
| `main` `26521e24` | 203 | `03fdc0096773621a5597dd07b365cb5b955b4f8f618e08c995a087565b28f89f` |
| branch head | 203 | `03fdc0096773621a5597dd07b365cb5b955b4f8f618e08c995a087565b28f89f` |

`comm -3` empty — **zero regression**. The pass delta is attributable by
`--collect-only`: `tests/test_ci_suite_collection_continuation.py` collects **48** on
`main` and **91** on the branch (`+43`), exactly the new nodes, because
`test_every_broad_suite_step_reaches_the_suite` is parametrized over the workflow corpus.

Adjacent guards, run together: `test_ci_suite_collection_continuation.py`,
`test_ci_gate_trigger_coverage.py`, `test_m02a_ci_gate_integrity.py`,
`test_ci_verdict_step_integrity.py`, `test_gate_filter_selection.py`,
`test_ci_gate_trigger_coverage_ci_wiring.py` → **312 passed**.

CP10 mutation boundary: `printf '<all three paths>\n' | python
scripts/cp10_mutation_boundary_policy.py --judge` → PASS (exit 0).

## 6. Remaining uncertainty / not claimed

- Local full-suite counts (`98F/1855P/105E`) differ from CI's because this environment
  is dependency-limited (`pydantic`, `requests`, `fastapi`, `httpx`, `google` absent).
  The *node-set identity* claim is environment-independent and holds.
- **CE-01 itself is not repaired** — it is reserved to the sovereign. This change only
  makes the step reach past it and report.
- **Defect B** (`steps.<id>.outcome` self-satisfying enforcement) is owned by PR #459.
  **Defect C** (the exclusion) is addressed here by adding a *separate* invariant
  rather than by editing the judging-step invariant, so the two properties stay
  independently falsifiable.
- No production-parity claim. Repository-source change only.
