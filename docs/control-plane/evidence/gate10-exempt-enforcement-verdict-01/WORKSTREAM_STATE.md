# WORKSTREAM STATE — gate10/exempt-enforcement-verdict-01

Persisted so the next heartbeat reconstructs from evidence, not memory.

## Current state

| Field | Value |
|---|---|
| Workstream | `gate10/cp10-broad-suite-execution-coverage` (decoration class) |
| Branch | `gate10/exempt-enforcement-verdict-01` |
| Base main | `6109c72ab9eedc2593d2cc6c50ebd01596c80072` |
| Head | `e8bcb4414d34cae99d57340e172a6b8c98774026` |
| PR | #483 (open, MERGEABLE, 10/10 checks success) |
| Result | **IMPLEMENTED** — detector + controls green; corpus clean, so no repair |
| Baseline debt | full suite 207 failing/error nodes at `6109c72` — pre-existing, unchanged |

## Evidence

- Guard: `21 passed`. Wiring guard: `12 passed`. CI gate `verdict-step-integrity`:
  **33 passed** on the PR head (run `38233888774`).
- Workflow-scanning + CP10 integrity suites: `281 passed`. Architecture: `11 passed`.
- Regression by node identity: failing/error set sha256
  `5682e540f8018b4c56b53e359bd32fc5b568deef62d08ea1f0da25694f3642c0` on both `main` and the
  branch (207 nodes, `comm -3` empty). `+8 passed` == the 8 new tests.
- Live negative control on the real `sg-02-fe-2-v.yml`: exempting the enforcement step reddens
  exactly 2 corpus invariants (2F/19P); byte-identical restore (sha256 `f1423a50…`) -> 21P.
- `python -m py_compile api/main.py` OK; `api/main.py` = 2505 lines (budget 2600). CP10 judge
  on the changed paths: PASS, exit 0.

## Blockers

None. No 403/401 encountered — `gh` credential helper configured
(`git config credential.helper '!gh auth git-credential'`, `GIT_TERMINAL_PROMPT=0`).

## Authorized action (this pass, completed)

Extend the pure-source verdict-step-integrity guard with Detector 3 (exempt enforcement) plus
its controls and inventory. Committed to a dedicated branch, pushed, PR #483 opened, glance
posted. **No merge.**

## Forbidden actions

Merge; push to `main`; force-push; mutate `.github/workflows/**` in this PR; repair pre-existing
full-suite debt; edit `api/main.py`; add a second authority or mutation path.

## Next bounded task (proposed — NOT authorized)

**Shell-level disarm detector.** §4 of `EVIDENCE.md`: the corpus enforcement's 17 assertions are
live only because the default shell is `bash -e {0}`. A `shell:` override or `set +e` would
disarm them silently and trip no current detector. Proposed as a separate bounded pass on a new
branch; discovery does not authorize execution.

Secondary, also unauthorised: `tests/test_ci_verdict_step_integrity_ci_wiring.py` needs no
change (verified), so no work is queued there.

## Exact completion condition

PR #483 merged by the sovereign, and the next heartbeat re-derives `main`, the node set, and the
gate state from live evidence rather than from this file.

## Authority boundary

No merge, deployment, or acceptance claimed. Human merge authority is final.
