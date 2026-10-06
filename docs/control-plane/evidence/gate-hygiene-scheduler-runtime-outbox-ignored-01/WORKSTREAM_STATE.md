# WORKSTREAM STATE — gate-hygiene/scheduler-runtime-outbox-ignored-01

## Current state

- BASE_MAIN: `451e41a30fcbff4a65326e897a84818cc623b769` (#317, "advance convergence frontier after G12 merges")
- Branch: `gate-hygiene/scheduler-runtime-outbox-ignored` @ `390501e5`
- PR: **#320**
- Classification: `VERIFIED` (repository-source hygiene + regression guard). No
  production-parity claim.

## Defect closed

`weaver/engineering_worker.py::_record_attention` writes
`docs/control-plane/evidence/attention-events.jsonl` on every worker run. At base main it was
**untracked and not ignored** (`git check-ignore --no-index -q …` → rc=1), so a hygiene pass
running `git add -A` would stage it. Its sibling per-run runtime reports
(`**/session-report.json`, `**/WEAVER-ENGINEERING-RUN.md`) are already ignored.

Recorded as *PROPOSED, not executed* in PR #319's evidence; this workstream executes it.

## Evidence

- `tests/test_repo_hygiene_gitignore.py` — branch **7 passed, 1 failed**; main `451e41a`
  (same clone) **5 passed, 1 failed**; the `+2` is exactly the two new assertions.
- Negative control proven: ignore rule stripped → `test_attention_outbox_is_never_stageable`
  **FAILS** (6 passed, 2 failed). Rule restored → 7 passed, 1 failed.
- The 1 remaining guard failure is **pre-existing**: `test_no_module_resolves_the_repository_canonical_store`
  (`ModuleNotFoundError: fastapi` via `solspire/enterprise_router.py`), identical on main.
- Full suite (same clone, `-q -rEf --continue-on-collection-errors`):
  main **887P / 49F / 18S / 48E** → branch **889P / 49F / 18S / 48E**; identical
  FAILED/ERROR **node set** → zero regression. 49F/48E is pre-existing main debt, recorded
  not fixed.
- `tests/architecture` **11 passed**; `python -m py_compile api/main.py` **OK**;
  `api/main.py` = 2432 lines (budget 2600); CP10 boundary judge on changed paths **PASS** (exit 0).
- PR #320 checks: `Full-history secret scan` **pass**; `Vercel – arkadia-prism` pass;
  `Vercel – console` fail — **pre-existing on main**, not attributable to this PR.

## Measured main defects (recorded, not repaired here)

| item | class | note |
|------|-------|------|
| `fastapi` absent from this environment | environment | pre-existing; 49F/48E full-suite debt on main |
| PR #319 evidence "10 tests" | measurement defect | head `f179d2b1f` measures **9** test functions / **12** collected node ids; correction posted on #319 |
| PR #319 scheduler fail-closed behaviour | open, separate | the hourly job exits 1 when worker status is FAILED; its own bounded workstream, not touched here |
| Gate-2 production parity | `BLOCKED` | provider-side (Vercel Deployment Protection), unchanged |

## Next authorized action

1. Sovereign review + merge of **#320**.
2. Sovereign review of #319 (scheduler trajectory conformance) — open, `UNSTABLE`.
3. `fix/prism-arkana-surface-consolidation` (#318) and `feat/oversoul-prism-9cell-conformance` (#306)
   remain open; not touched this pass.

## Forbidden actions this pass

- No merge. No push to `main`. No production deploy or production-parity claim.
- Do not repair the PR #319 status-vocabulary divergence inside this workstream.
- Do not generalise `tests/test_ci_gate_trigger_coverage.py` (blast-radius rule; measured:
  `sg-02-fe-2-v.yml` names 9 test files absent from its own path filter).
