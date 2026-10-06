# WORKSTREAM STATE — gate-hygiene/scheduler-session-result-ignored-01

## Current state

- BASE_MAIN: `1775f3e1271842688f5026b59bfb0d393db6db04` (Merge PR #318) — re-confirmed via the
  GitHub API `branches/main` at 2026-10-06T05:06Z; matches the local clone tip.
- Branch: `gate-hygiene/scheduler-session-result-ignored`
- Head: `ec1ad1cb450f67e13f1e8f2428f34ff74922a562`
- PR: **#327** (open, `mergeable: true`, base `main` @ `1775f3e`) — sovereign merge pending.
- Classification: `VERIFIED` (repository-source hygiene + regression guard). No
  production-parity claim.

## Defect closed

The hourly scheduler writes `engineering-session-result.json` to the repository root on every
session and uploads it as a build artifact. At base main it was **untracked and not ignored**
(`git check-ignore --no-index -q …` → rc=1), so a hygiene pass running `git add -A` would
stage a transient run result. Its sibling per-run runtime reports
(`**/session-report.json`, `**/WEAVER-ENGINEERING-RUN.md`) are already ignored.

This is the second artifact of the same worker run that PR #320 covers
(`attention-events.jsonl`). Neither rule depends on the other; both may merge independently.

## Evidence

- `tests/test_repo_hygiene_gitignore.py` — branch **7 passed, 1 failed**; base main `1775f3e`
  (same clone) **5 passed, 1 failed**; the `+2` is exactly the two new assertions.
- Negative control proven: ignore rule stripped → `test_scheduler_session_result_is_never_stageable`
  **FAILS** (6 passed, 2 failed). Rule restored → 7 passed, 1 failed.
- The 1 remaining guard failure is **pre-existing**: `test_no_module_resolves_the_repository_canonical_store`
  (`ModuleNotFoundError: fastapi` via `solspire/enterprise_router.py`), identical on base main.
- Full suite, same clone, `-q -rEf --continue-on-collection-errors`, compared by failing/error
  **node set**: identical between base main and branch → zero regression (see `VERIFICATION.md`).
- `tests/architecture`: baseline unchanged.
- `python -m py_compile api/main.py`: **OK**; `api/main.py` untouched.
- CP10 boundary judge on changed paths: **PASS** (exit 0).

## Measured main defects (recorded, not repaired here)

| item | class | note |
|------|-------|------|
| `fastapi` absent from this environment | environment | pre-existing; the guard's 1F and the full-suite debt on main |
| trajectory structure of `TRAJECTORY-CONSOLE-COMPLETION-01.yaml` | **open, separate** | `moves` nested under `trajectory`; router raises `invalid trajectory structure` → worker `FAILED` → hourly job exits 1. That is **PR #319's** workstream; not touched here |
| `attention-events.jsonl` not ignored | **open, separate** | PR #320; not touched here |
| Gate-2 production parity | `BLOCKED` | provider-side (Vercel Deployment Protection), unchanged |

## Open-PR + CI inventory (measured 2026-10-06, BASE_MAIN `1775f3e`)

10 open PRs. `origin/main` tip re-read from the API = `1775f3e…` (matches local clone).

| PR | head | bad check-runs | Vercel |
|----|------|----------------|--------|
| #306 | `ddc1a1b3` | — | prism ✗ / console ✗ |
| #319 | `3d1829db` | — | prism ✓ / console ✗ |
| #320 | `d5adcba6` | — | prism ✓ / console ✗ |
| #321 | `e611edd8` | — | prism ✓ / console ✗ |
| #322 | `9d0f1cea` | **provider-routing** | prism ✓ / console ✗ |
| #323 | `cd749ea4` | **provider-routing** | prism ✗ / console ✗ |
| #324 | `e6784c30` | — | prism ✓ / console ✗ |
| #325 | `77ae53ef` | **provider-routing** | prism ✓ / console ✗ |
| #326 | `55acddb5` | — | prism ✗ / console ✗ |
| #327 (this) | `ec1ad1cb` | — | prism ✓ / console ✗ |

- **`Vercel – console` fails on `main` itself** at `1775f3e` (`Deployment has failed`). It is
  therefore **pre-existing and not attributable to any PR** — do not report it as a new red gate.
- `provider-routing` red on #322 / #323 / #325 is the **gate07** workstream, not this one.
- This PR's own checks: `Full-history secret scan` **success**, `Vercel Preview Comments` success.

## Next authorized action

1. Sovereign review + merge of **#320** and **#327** (independent one-line ignore rules; either
   may merge without the other).
2. Sovereign review of the gate07 cluster (#319 / #321–#325) — `provider-routing` red on three.
3. `feat/oversoul-prism-9cell-conformance` (#306) and #326 remain open; not touched this pass.

## Forbidden actions this pass

- No merge. No push to `main`. No production deploy or production-parity claim.
- Do not repair the trajectory-structure defect inside this workstream (PR #319 owns it).
- Do not modify or duplicate PR #320's attention-outbox rule.
- Do not attribute the `Vercel – console` failure to this PR; it is red on `main`.
