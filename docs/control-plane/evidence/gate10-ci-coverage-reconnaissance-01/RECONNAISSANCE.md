# GATE-10 CI coverage reconnaissance — the "decoration" defect class

Read-only reconnaissance. No application code, no authority surface, no merge.

- **BASE_MAIN** := `850216fc99b0eab66a66f8a8290c0db33823b681` (`gate10: repair ADR-016
  static-corpus freshness pin`, 2026-10-11T20:39:56+01:00)
- **Measured** 2026-10-12 in the canonical clone (`git ls-files` at `850216fc`), pytest
  9.1.1 / PyYAML 6.0.3.
- **Primary task** := PR #460 `gate10/gitleaks-config-guard-ci-wiring-01` (open, CLEAN,
  MERGEABLE, head `6241bdb7`).

## 1. Method

A guard is *judged* only if some workflow both (a) **executes** it — a real `pytest`
invocation whose arguments contain the file, its directory, or `tests/`, with `pytest`
as the invoked command word (`pytest x` or `python -m pytest x`) — and (b) would
actually **run** when a pull request touches that file, i.e. the file matches the
workflow's `pull_request.paths` filter. Condition (b) is the part that is normally
skipped: "a workflow executes this file" is not the same as "a change to this file
executes this workflow".

Both conditions were evaluated against the live tracked corpus, not against prose.

## 2. The measured population

Of **255** tracked `tests/**/test_*.py` files:

| Class | Count |
|---|---|
| Executed by a gate a PR touching the file **would trigger** (named, or a real whole-suite run) | **78** |
| Executed *only* by a broad-suite step | **177** |

The 177 are not decoration per se — the two whole-suite surfaces are
`provider-routing.yml` and `sg-02-fe-2-v.yml`. The question is whether those surfaces
actually reach the suite. Two of them do not.

## 3. Defect A — `sg-02-fe-2-v.yml` CP10-B never reaches the suite (runtime-observed)

`CP10-B broader backend regression` runs `python -m pytest tests/ -q 2>&1 | tee
cp10-backend.log` with `continue-on-error: true`.

The `continue-on-error` is **not** the defect: a non-judging surface need not gate.
The defect is that **it also executes nothing**, so it cannot even *report* — and it is
the only broad-suite surface selected by `spiral_grove/**` and `lab/**`.

Runtime proof, run **`38186457230`** (`event=pull_request`, `conclusion=success`, head
`12f8a0a6`), the CP10-B step log:

```
2026-10-12T00:02:44.3072158Z ##[group]Run python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
2026-10-12T00:02:54.5891640Z !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

Reproduced locally at `850216fc`: a bare `python -m pytest tests/ -q` yields
`1 skipped, 76 errors in 5.70s` — session interrupted, **zero tests executed**. The
collection errors are dependency-shaped in this environment (e.g. `providers/local.py`
→ `ModuleNotFoundError: No module named 'httpx'`) plus the known CE-01
`weaver.autonomy` module-vs-package collision
(`ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'`).

So `spiral_grove/**` and `lab/**` pull requests reach **no** whole-suite execution:
`provider-routing.yml` runs the suite but is not selected by those paths, and CP10-B
aborts. This is the `test_ci_suite_collection_continuation` class, still live on `main`.

**Repair is documented and measured, not proposed blind.** `python -m pytest tests/ -q
--continue-on-collection-errors` on the same tree completes in **124 s**
(`88 failed, 1651 passed, 21 skipped, 96 errors`) instead of aborting. The flag does not
hide debt — the collection errors and pre-existing failures are still reported — it only
stops the session aborting before the suite runs.

**Bounded fix (proposed, not performed in this pass):** add
`--continue-on-collection-errors` to the CP10-B step in `sg-02-fe-2-v.yml`. It is one
token in one already-selected file; it does not touch `continue-on-error`, does not
touch `api/main.py`, and cannot turn `main` red for debt it did not introduce (the step
is non-gating, so its status is unchanged; only its *content* changes from "nothing" to
"the suite, reported"). Sibling ownership check: PR #459 owns the *verdict-step* class
(undeclared `steps.<id>.outcome`, `pipefail`) and PR #458 owns the *executes⇒selects*
invariant; neither owns the CP10-B abort.

## 4. Defect B — the `steps.<id>.outcome` claim is prose-verified, now runtime-verified

AGENTS.md states that `steps.<id>.outcome` "is not available inside a `run:` block".
That is now observed, not asserted. Same run `38186457230`, the terminal enforcement
step:

```
##[group]Run test 'success' = success
test 'success' = success      (×16)
```

Every one of the 16 assertions is the **literal string** `test 'success' = success` —
the substitution is a constant, so the enforcement step is self-satisfying and cannot
fail for any outcome. (`steps.<id>.conclusion` or an `if:` are the workable forms.)
**Owned by PR #459** — recorded here as corroboration only; do not duplicate.

## 5. Defect C — the guard PR #458's exclusion silently drops

`tests/test_gate_filter_selection.py` (PR #458) excludes a directory argument
(`pytest tests/`) from the executes⇒selects invariant "by design". That exclusion is
**unsupported**, and Defect A is the counterexample: a broad-suite step is the *only*
execution site for 177 files, and it can execute zero of them. The three properties
`tests/test_ci_gate_trigger_coverage.py` does assert are narrower than the class:
self-selection, `push`/`pull_request` filter symmetry, and architecture-suite selection.
None of them notices a broad-suite step that never runs.

This is why Defect A is not already caught. It is also why Defect A is worth fixing
rather than only recording.

## 6. Deliberately not treated as defects

- `arkadia-console-android.yml`, `arkana-signal-conformance.yml`,
  `openapi-security-metadata.yml`, `phase6-persistent-execution.yml` and
  `solspire-route-composition.yml` are path-filtered and declare **no**
  `workflow_dispatch`. Unlike `baseline-fingerprint.yml` (which declares one), they
  cannot be dispatched against an exact revision that does not touch their paths. This
  is a real gap but a *different* class — "cannot re-run on demand", not "runs nothing".
  Recorded as proposed work; not expanded into here.
- The 177 broad-suite-only files are **not** classified as decoration. A file-targeted
  gate is not required when a real whole-suite surface covers the path; only the two
  aborting/absent surfaces above break that cover.

## 7. Primary task status — PR #460

`tests/test_gitleaks_config_guard.py` validates the root `.gitleaks.toml` read by
`security-secret-scan.yml`. Measured at `850216fc`:
`grep -rn test_gitleaks_config_guard .github/` → **0 matches** — the guard held only when
a human ran the suite by hand, and a commit editing `.gitleaks.toml` is selected by no
gate. PR #460 wires it into `.github/workflows/gitleaks-config-guard.yml`, which names
the guard, its own file, and `.gitleaks.toml` in **both** filters and is dispatchable.

The wiring is runtime-proven, not source-asserted: the gate's own runs on the branch
are `38197766990` (`failure`, first cut), `38198660357` (`success`), and `38198791620`
(`success`, head `6241bdb7`).

Baseline of the gate-hygiene guards at `850216fc`:
`python -m pytest tests/test_ci_gate_trigger_coverage.py
tests/test_ci_suite_collection_continuation.py tests/test_gitleaks_config_guard_ci_wiring.py
tests/test_m02a_ci_gate_integrity.py -q` → **217 passed**.

## 8. Status and next action

- **Defect A**: OBSERVED (runtime) + repair MEASURED (124 s, 1651 passed) — **IMPLEMENTED
  fix proposed, not performed**. One token in `sg-02-fe-2-v.yml`.
- **Defect B**: OBSERVED (runtime) — owned by PR #459, corroboration only.
- **Defect C**: OBSERVED (source) — the exclusion in PR #458 is unsupported; recorded.
- **PR #460**: READY FOR SOVEREIGN MERGE (open, CLEAN, MERGEABLE, gate green on head).
- **Next bounded action**: apply Defect A's one-token repair as its own PR
  (`gate10/cp10-broad-suite-reach-01`) — subject to sovereign authorization, since this
  pass's authorization covered reconnaissance and PR #460, not a new `sg-02-fe-2-v.yml`
  mutation.
