# GATE-10 — exempt enforcement: an enforcement step that cannot fail the job

Workstream: `gate10/cp10-broad-suite-execution-coverage` (Defect class: "decoration" —
a CI step that appears to enforce a verdict while being unable to fail).
Branch: `gate10/exempt-enforcement-verdict-01`.
Base: `main` @ `6109c72ab9eedc2593d2cc6c50ebd01596c80072`.

## 1. Bounded objective

Extend the existing pure-source guard `tests/test_ci_verdict_step_integrity.py` with a
detector for the **uncovered** member of the decoration class: an *enforcement step* that is
itself exempted from failing — `continue-on-error` at either the step or the job level, or a
condition other than `always()` — so the `test '${{ steps.<id>.outcome }}' = success`
assertions it runs cannot fail the job.

The pre-existing guard detects masked verdict steps (a step whose exit status is destroyed by
`| tee` without `pipefail`) and enforces that every referenced step id resolves. Neither
property sees the enforcement step's *own* exemption.

## 2. Scope

| Path | Change |
|---|---|
| `tests/test_ci_verdict_step_integrity.py` | +8 tests, +1 inventory constant, +1 detector |

Non-goals: no application code, no authority surface, no workflow mutation. The live
enforcement step is sound (measured in §4), so this pass adds a **detector**, not a repair.
`api/main.py` untouched. No `AGENTS.md` edit in this PR — PR #482 also edits that file
(+45 lines), so workstream state is persisted here instead to keep this change bounded and
conflict-free.

## 3. The defect class, precisely

An enforcement step is *decoration* when it runs an assertion but its exit status cannot fail
the job. Three forms, all measured against the live corpus:

1. **Step-level `continue-on-error: true`** — the assertion runs, the step's `outcome` is
   `failure`, the job's conclusion is `success`.
2. **Job-level `continue-on-error: true`** — discards every step's status in that job, so the
   enforcement is decoration however the step itself is written.
3. **A non-`always()` condition** (e.g. `if: success()`) — the enforcement is *skipped* exactly
   when something failed, which is the one case it exists for.

The corpus form that is correct is `if: always()` with no `continue-on-error`.

## 4. Measured corpus state at `6109c72`

`sg-02-fe-2-v.yml`, job `validate`:

- Enforcement steps: **2** — `CP10 evidence summary` and `Enforce CP10 executable gates`.
- Each carries **17** `steps.<id>.outcome` assertions (`grep` count; an earlier pass recorded
  16 — re-measured here).
- Both are `if: always()`, `continue-on-error: None` at step **and** job level.
- Detector result: `exempt_enforcement_inventory() == {}` — no offender. The corpus is sound.

**The trailing `exit 0` is load-bearing and the guard rests on it.** The enforcement step ends
`... echo 'Executable CP10 gates: PASS ...'` then `exit 0`. A shell that continues after a
failing `test` would reach that `exit 0` and the job would pass regardless. GitHub's default
shell for a `run:` step on Linux is `bash -e {0}`, and the step overrides no `shell:`. Proven
with a control script of exactly that shape:

```
bash -e enforce_control.sh   -> exit=1   (first failing `test` aborts; trailing exit 0 unreachable)
bash    enforce_control.sh   -> exit=0   ("UNREACHABLE: enforcement passed" printed)
```

So the assertions are live **only because of `bash -e`**. This is recorded rather than
"repaired": the enforcement is sound today, and a future `shell: bash` (no `-e`) or a
`set +e` would silently disarm all 17 assertions — which is the defect the new detector's
third form covers only partially (it catches an `if:`/`continue-on-error` exemption, not a
shell change). A shell-level detector is **proposed**, not implemented: it widens the
detector's surface and belongs in its own bounded pass.

## 5. The detector

```python
def _is_exempt(step, job) -> bool:
    if job.get("continue-on-error") or step.get("continue-on-error"):
        return True
    condition = step.get("if")
    if isinstance(condition, str) and condition.strip() and not _ALWAYS.search(condition):
        return True
    return False
```

`exempt_enforcement_steps(workflow)` reports every step whose `run` matches `_ENFORCEMENT`
(`test '${{ steps.<id>.outcome }}' = success`) **and** is exempt. `exempt_enforcement_inventory()`
maps the result over every tracked workflow file, as a `{(file, step): []}` inventory.

The registry `REGISTERED_EXEMPT_ENFORCEMENT_STEPS` is **empty and is an inventory, not a
filter** — the same discipline as `REGISTERED_MASKED_VERDICT_STEPS`. Two invariants hold it
in both directions: a newly exempted enforcement fails
`test_enforcement_steps_are_not_exempt_from_failing`; a repaired entry fails
`test_registered_exempt_enforcement_steps_are_still_exempt` rather than sitting stale.

## 6. Proof — negative controls

Detector-level (synthetic):

| Control | Result |
|---|---|
| step-level `continue-on-error` | reported |
| job-level `continue-on-error` | reported |
| `if: success()` | reported |
| `if: always()`, no exemption (positive control) | silent |
| soft step with no `.outcome` assertion | silent |

**Live negative control on the real file** — `test_the_corpus_enforcement_step_is_reported_when_exempted`
loads the live `sg-02-fe-2-v.yml`, asserts the corpus is clean, then sets
`continue-on-error: true` on the real enforcement step **in memory only** and asserts it is
reported. Proven end-to-end by mutating the file on disk:

```
mutation: continue-on-error added to `Enforce CP10 executable gates` (sha256 f1423a50…)
  -> 2 failed, 19 passed
     FAILED test_enforcement_steps_are_not_exempt_from_failing
     FAILED test_the_corpus_enforcement_step_is_reported_when_exempted
restore byte-identical (sha256 f1423a50… verified) -> 21 passed
```

A synthetic fixture alone would not prove the detector reads the real file.

## 7. Regression boundary

Measured in this environment at `6109c72`, same tree, both sides:

| Metric | `main` (guard stashed) | branch |
|---|---|---|
| failing/error node set sha256 | `5682e540f8018b4c56b53e359bd32fc5b568deef62d08ea1f0da25694f3642c0` | same |
| node count | 207 | 207 |
| `comm -3` | — | **empty** |
| suite counts | 102 failed / 1806 passed / 105 errors | 102 failed / 1814 passed / 105 errors |

The `+8 passed` is exactly the 8 new test functions (`20 - 12` by `grep '^def test_'`),
confirmed by node identity, not inferred from the count delta.

- Architecture fitness: `11 passed`.
- Guard: `21 passed`. Wiring guard: `12 passed`. Combined 33.
- Workflow-scanning + CP10 integrity suites (`test_ci_gate_trigger_coverage.py`,
  `test_m02a_ci_gate_integrity.py`, `test_workflow_injection_boundary.py`,
  `test_ci_suite_collection_continuation.py`, both verdict-step files): **281 passed**.
- `python -m py_compile api/main.py` → OK; `api/main.py` = 2505 lines (budget 2600).
- CP10 judge on the changed path: `Mutation boundary PASS (M02A legitimate-surface +
  constitutional denylist)`, exit 0.

## 8. Result

**IMPLEMENTED** — detector + controls + registry, all green; regression node-set unchanged.
Not `VERIFIED` in the runtime sense: this is a pure-source guard, and the live corpus is clean,
so there is no production/runtime observation to make. The new guard's CI wiring
(`.github/workflows/ci-verdict-step-integrity.yml`) already selects and executes it.

## 9. Remaining uncertainty / proposed follow-on

- `test_ci_verdict_step_integrity_ci_wiring.py` was inspected and needs no change: it already
  covers execution (not mere mention), whole-corpus selection, self-selection, both exemption
  levels, and dispatchability.
- Full-suite debt (155 nodes locally at `6109c72`) is pre-existing and unchanged; not repaired here.

## 11. Pass 2 — shell-level disarm detector (Detector 4)

Pass 1 (§1–§10) recorded the shell-level disarm as a *proposed, unauthorized* follow-on. This
pass executes it, on the same branch and the same guard file — composing into PR #483 rather
than opening a competing PR that would conflict on the one file.

### 11.1 The defect, precisely

Pass 1's §4 established that the live corpus enforcement's 16 assertions are live *only*
because the default shell is `bash -e {0}`: the first failing `test` aborts the step. That
property is undeclared and unguarded. A `shell:` override without `-e`, or a `set +e` inside
the script, makes every assertion evaluate and the trailing `exit 0` unconditional — the step
then reports success whatever the named steps did. No pass-1 detector sees this: pass 1 covers
an *exempted* step (status discarded), Detector 4 covers a *non-abortive* step (status never
produced).

### 11.2 Change

| Path | Change |
|---|---|
| `tests/test_ci_verdict_step_integrity.py` | +9 tests, +1 inventory constant, +1 detector |

- `_ERREXIT` / `_SET_PLUS_E` + `_shell_aborts(shell, run)`: an enforcement step aborts iff its
  effective shell carries `-e`/`errexit` **and** the script does not clear it with `set +e`.
  Step `shell:` wins, else `defaults.run.shell` on the job, else GitHub's `bash -e {0}`.
- `abortless_enforcement_steps(workflow)` / `abortless_enforcement_inventory()`.
- `REGISTERED_ABORTLESS_ENFORCEMENT_STEPS` — empty, because `shell:` is declared in **no**
  workflow in the corpus (measured), so every enforcement runs under the abortive default.

### 11.3 A precision defect found by probing the new regex, and fixed

The first `_ERREXIT` used `(?:^|[\s-])-[A-Za-z]*e[A-Za-z]*`, whose class admits a second dash.
Measured: `bash --noprofile {0}` → `aborts: True`. The long option `--noprofile` contains an
`e`, so an *abortless* enforcement under it went **unreported** — a silent hole in the very
detector written to close silent holes. Repaired to `(?:^|\s)-[A-Za-z]*e[A-Za-z]*(?=\s|$)`,
which requires a single-dash token. Pinned by
`test_errexit_detection_does_not_read_a_long_option_as_errexit` over
`bash --noprofile {0}`, `bash -x {0}`, `bash --norc {0}`.

### 11.4 Evidence

- Guard: **30 passed** (was 21). Focused guards + architecture: **265 passed**, architecture
  **11 passed**.
- Live negative control on the real `sg-02-fe-2-v.yml`, twice:
  - `shell: bash {0}` on the enforcement step → exactly **2** corpus invariants redden
    (2F/27P).
  - `shell: bash --noprofile {0}` → exactly the same 2 redden (2F/28P), which is the control
    that catches the §11.3 precision defect.
  - Restored byte-identically both times: sha256 `f1423a5087cc14dc00e7e63182daaa1a0a40b30b1ec9d15811dd1d88d06cbcd0`.
- Regression by node identity: failing/error set sha256
  `d0541c6c1303f03b242b69d206beeb68b3a9becb5f25477d14fb16ba19823f26` (155 nodes) on **both**
  `main` `6109c72` and the branch, `comm -3` empty. The `+17 passed` (1926 → 1943) is exactly
  the guard's collect delta (13 → 30 nodes), measured with `--collect-only`, not inferred.
- `python -m py_compile api/main.py` → OK; `api/main.py` = 2505 lines (budget 2600).
  CP10 judge on the changed path: PASS, exit 0.

### 11.5 Result

**IMPLEMENTED** — detector + controls green; the corpus is clean, so this is a detector, not a
repair. Not `VERIFIED` in the runtime sense: a pure-source guard with no runtime observation to
make. `AGENTS.md` is deliberately untouched (PR #482 edits it; workstream state persists here).

## 12. Authority boundary

No merge, no production deployment, no acceptance. Human merge authority is final.
