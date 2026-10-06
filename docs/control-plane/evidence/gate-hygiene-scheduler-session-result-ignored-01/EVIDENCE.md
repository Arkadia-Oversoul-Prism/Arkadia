# EVIDENCE — scheduler session-result ignored (gate-hygiene)

**Gate / workstream:** gate-hygiene (hourly bounded-execution loop integrity)
**Branch:** `gate-hygiene/scheduler-session-result-ignored`
**Base main:** `1775f3e1271842688f5026b59bfb0d393db6db04`
**Classification:** VERIFIED (repository-source), regression boundary unchanged

## 1. Defect (evidence-backed)

One worker run materialises **two** untracked runtime artifacts. The hourly scheduler
(`.github/workflows/arkadia-engineering-scheduler.yml`) writes both:

| artifact | written by | ignored at base main |
|---|---|---|
| `docs/control-plane/evidence/attention-events.jsonl` | `weaver/engineering_worker.py::_record_attention` | **no** — covered by PR #320 |
| `engineering-session-result.json` (repo root) | scheduler step *Session + Engineering Runner* | **no** — this workstream |

Measured at base main `1775f3e`, reproducing the scheduler's own writer exactly
(`EngineeringWorker(repo_root=".", dry_run=True).run()` then
`Path("engineering-session-result.json").write_text(json.dumps(result, indent=2))`,
the literal body of the workflow step):

```
git check-ignore --no-index -q engineering-session-result.json      → rc=1 (not ignored)
git ls-files engineering-session-result.json                        → 0 paths (untracked)
git status --porcelain   after the run →  ?? docs/control-plane/evidence/attention-events.jsonl
                                          ?? engineering-session-result.json
git add -A --dry-run                →  add 'engineering-session-result.json'
```

`.gitignore` already ignores the *sibling* per-run runtime reports
(`**/session-report.json`, `**/WEAVER-ENGINEERING-RUN.md`) with the stated rationale that
they are transient runtime output, not review state. The root-level session result is the
same class of artifact and was omitted, so a hygiene pass running `git add -A` would stage
a transient run result and commit it to `main`.

## 2. Change

- `.gitignore` — one anchored rule, `engineering-session-result.json`, placed in the
  existing session-evidence block next to its sibling rules.
- `tests/test_repo_hygiene_gitignore.py` — two assertions:
  - `test_scheduler_session_result_is_never_stageable` — the run result must be ignored,
    asked of git itself via `git check-ignore`, so any equivalent rule tracks.
  - `test_session_result_ignore_is_scoped_to_the_run_result` — **negative control**: the
    tracked root manifests (`railway.json`, `vercel.json`) must **not** be ignored, so a
    future blanket root-JSON ignore cannot satisfy the first assertion while hiding durable
    repository state.

`api/main.py` untouched. No workflow, authority, or boot-code surface is modified.

## 3. Measured result

Guard file, this environment (`fastapi` absent):

| run | result |
|---|---|
| base main `1775f3e` | 5 passed, 1 failed |
| branch | **7 passed, 1 failed** |
| branch, ignore rule stripped (negative control) | 6 passed, **2 failed** — `test_scheduler_session_result_is_never_stageable` FAILS |
| branch, rule restored | 7 passed, 1 failed |

The `+2 passed` is exactly the two new assertions. The single remaining failure in every row
is `test_no_module_resolves_the_repository_canonical_store` — a **pre-existing** environment
failure (`ModuleNotFoundError: No module named 'fastapi'` via `solspire/enterprise_router.py`),
identical on base main.

Full suite, same clone, `-q -rEf --continue-on-collection-errors` — compared by failing/error
**node set**, not counts:

| tree | passed | failed | skipped | errors | FAILED/ERROR node-set sha256 |
|---|---|---|---|---|---|
| base main `1775f3e` | 1005 | 69 | 20 | 48 | `16493ff39e67ff9a55dfffbad585b8226b9b0db46c4b2ff6d444c5496c5d3c43` (117 nodes) |
| branch | 1007 | 69 | 20 | 48 | `16493ff39e67ff9a55dfffbad585b8226b9b0db46c4b2ff6d444c5496c5d3c43` (117 nodes) |

- **Zero regression:** identical failure/error node set; the `+2 passed` is exactly the two
  new assertions. 69F/48E is pre-existing main debt in this environment (fastapi and other deps absent), recorded not fixed.
- `tests/architecture`: baseline unchanged.
- `python -m py_compile api/main.py`: **OK**.
- CP10 mutation boundary judge on changed paths: **PASS** (exit 0).

## 4. Non-goals / proposed (NOT executed)

- PR #320's attention-outbox rule is **not** duplicated or modified here; the two rules are
  independent and either may merge without the other.
- The PR #319 status-vocabulary divergence remains a separate bounded workstream.
- The scheduler's fail-closed behaviour on worker `FAILED` (the trajectory-structure defect
  that reds the hourly job) remains **PR #319's** workstream, not this one.

## 5. Authorization boundary

Human-only review, merge, and deploy. No production-parity claim is made — this is a
repository-source hygiene fix plus a regression guard, not a runtime observation.
