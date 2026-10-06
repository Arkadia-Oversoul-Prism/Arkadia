# EVIDENCE — scheduler runtime outbox ignored (gate-hygiene)

**Gate / workstream:** gate-hygiene (hourly bounded-execution loop integrity)
**Branch:** `gate-hygiene/scheduler-runtime-outbox-ignored`
**Base main:** `451e41a30fcbff4a65326e897a84818cc623b769`
**Classification:** VERIFIED (repository-source), regression boundary unchanged

## 1. Defect (evidence-backed)

`weaver/engineering_worker.py::_record_attention` appends to
`docs/control-plane/evidence/attention-events.jsonl` on **every** worker run, so the file
materialises the moment a scheduler session — or a local test session that runs the worker
— executes. It is untracked and, measured at base main, **not ignored**:

```
git check-ignore --no-index -q docs/control-plane/evidence/attention-events.jsonl  → rc=1 (not ignored)
git ls-files | grep attention-events                                                → 0 paths (untracked)
git status --porcelain                                                              → ?? docs/control-plane/evidence/attention-events.jsonl
```

`.gitignore` already ignores the outbox's sibling per-run runtime reports
(`**/session-report.json`, `**/WEAVER-ENGINEERING-RUN.md`) with the stated rationale that
they are transient runtime output. The outbox is the same class of artifact but was omitted,
so a hygiene pass running `git add -A` would stage it.

This was recorded as **PROPOSED, not executed** in PR #319's evidence
(`gate-hygiene-scheduler-trajectory-conformance-01`, §"Proposed, not executed"). This
workstream executes that proposal as its own bounded change.

## 2. Change

- `.gitignore` — one anchored rule, `docs/control-plane/evidence/**/attention-events.jsonl`,
  placed in the existing session-evidence block next to its sibling rules.
- `tests/test_repo_hygiene_gitignore.py` — two assertions:
  - `test_attention_outbox_is_never_stageable` — the outbox must be ignored, asked of git
    itself via `git check-ignore` (tracks any equivalent rule).
  - `test_attention_outbox_control_is_not_ignored` — **negative control**: a non-outbox file
    under the evidence tree (`__hygiene_control__.txt`) must **not** be ignored, so a future
    blanket tree-ignore cannot satisfy the first assertion while hiding durable acceptance
    records.

`api/main.py` untouched (2432 lines, budget 2600).

## 3. Measured result

Guard file, this environment (fastapi absent):

| run | result |
|---|---|
| branch | **7 passed, 1 failed** |
| branch, ignore rule stripped (negative control) | **6 passed, 2 failed** — `test_attention_outbox_is_never_stageable` FAILS |
| branch, rule restored | **7 passed, 1 failed** |
| main `451e41a` (same clone) | **5 passed, 1 failed** |

The single remaining failure in every row is
`test_no_module_resolves_the_repository_canonical_store` — a **pre-existing** environment
failure (`ModuleNotFoundError: No module named 'fastapi'` via `solspire/enterprise_router.py`)
present identically on main. The `+2 passed` is exactly the two new assertions.

Full suite, same clone, `-q -rEf --continue-on-collection-errors`:

| tree | passed | failed | skipped | errors |
|---|---|---|---|---|
| main `451e41a` | 887 | 49 | 18 | 48 |
| branch | 889 | 49 | 18 | 48 |

- **Zero regression:** identical failure/error node set; the `+2 passed` is exactly the new
  assertions. The 49F/48E is pre-existing main debt, recorded not fixed.
- `tests/architecture`: **11 passed** (main's own baseline).
- `python -m py_compile api/main.py`: **OK**.
- CP10 mutation boundary judge on changed paths (`git diff --name-only main`): **PASS** (exit 0).

## 4. Non-goals / proposed (NOT executed)

- The unrelated status-vocabulary divergence recorded in PR #319 §5 remains a separate
  bounded workstream; not touched here.
- Generalising `tests/test_ci_gate_trigger_coverage.py` remains proposed (blast-radius rule).

## 5. Authorization boundary

Human-only review, merge, and deploy. No production-parity claim is made — this is a
repository-source hygiene fix plus a regression guard, not a runtime observation.
