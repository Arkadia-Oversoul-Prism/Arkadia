# EVIDENCE — gate07 session report truthfulness (the hourly stop must name its cause)

Pass: `gate07/scheduler-session-report-truthfulness-01`
Reconstructed: 2026-10-06 · BASE_MAIN `17e626cd27f8ea1e31f711fb787e6c7e5027ec70` (#333)

## Objective

Make the hourly engineering session's human-readable report name **why** it stopped, not only
**that** it stopped.

Bounded engineering fix. No router, schema, or trajectory change. No attention-bus change. No
vocabulary repair (that is PR #332's sovereign decision). No gate promotion, no authority change,
no merge.

## Defect (observed live, not inferred)

`arkadia-engineering-scheduler.yml` ends with a `Session report` step that echoes `Status` and
`Move`. It does **not** echo the router's `blockers`, which live only in
`engineering-session-result.json`.

Run **37523927861** (hourly schedule, `2026-10-06T20:06:45Z`, SHA `17e626cd…`) printed:

```
=== ARKADIA ENGINEERING SESSION ===
SHA:    17e626cd27f8ea1e31f711fb787e6c7e5027ec70
Status: NO_LEGAL_MOVE
Move:   NONE
Trigger:schedule
Merge:  FORBIDDEN
Deploy: FORBIDDEN
```

while the same run's session result carried a **typed, actionable** cause:

```
"blockers": [
  "unrecognized move status: G12-A ('merged_acceptance_pending'), G12-C ('merged_acceptance_pending')
   — cannot route; expected one of accepted, completed, in_progress, merged, pending, revision_required"
]
```

A live frontier therefore reads, in the run log, as a clean stop with no work to do. The
machine-readable HIGH-severity `WEAVER_BLOCKED` attention event is the other channel, but this
environment reports `attention_delivery` = `NOT_CONFIGURED`, so the run log is the **only**
human-readable artifact of the session.

## Relationship to adjacent open PRs (no duplication)

| PR | what it does | relationship |
|---|---|---|
| #331 `scheduler-failure-path-reporting-01` | moves the `GITHUB_OUTPUT` write **before** the `sys.exit(1)` in the python heredoc, so the report is not blank on `FAILED` | **adjacent, not overlapping.** #331 makes the report *non-blank* on failure; it does not make it name the *cause*. This PR edits only the report step body; #331 edits only the session heredoc. |
| #322 `router-status-truthfulness-01` | router names an unrecognized status instead of skipping | predecessor; this PR surfaces that name to the human |
| #334 `router-schema-vocabulary-closure-01` | pins `schema ⊆ router` | same seam, different direction; no file overlap |
| #332 `trajectory-status-vocabulary-decision-01` | sovereign decision on closing the vocabulary | untouched — this PR reports the seam either way |

The report step already reads `engineering-session-result.json` **implicitly** (the file is
uploaded as evidence on every path). This PR only prints it.

## Files changed

- `.github/workflows/arkadia-engineering-scheduler.yml` — `Session report` step only (report step
  body + explanatory comment). No other step touched.
- `tests/test_scheduler_trajectory_conformance.py` — 4 new tests (this file is already in the
  workflow's `pull_request` paths filter **and** executed by the workflow's guard step, so the
  guard is judged by the workflow it protects).
- `docs/control-plane/evidence/gate07-session-report-truthfulness-01/EVIDENCE.md` (this file)
- `docs/control-plane/evidence/gate07-session-report-truthfulness-01/WORKSTREAM_STATE.md`

No boot code touched; `api/main.py` unchanged (2434 lines, budget 2600).

## Non-vacuity (negative control)

The workflow was reverted to its committed pre-fix form and the guard re-run:

```
FAILED tests/test_scheduler_trajectory_conformance.py::test_session_report_surfaces_router_blockers
FAILED tests/test_scheduler_trajectory_conformance.py::test_session_report_states_an_absent_session_result
FAILED tests/test_scheduler_trajectory_conformance.py::test_negative_control_pre_fix_report_is_silent
3 failed, 17 passed
```

`test_negative_control_pre_fix_report_is_silent` feeds the detector the literal pre-fix echo-only
body and asserts it is reported as **not** naming blockers. Because that control is in the failing
set, the guard cannot be satisfied by reverting the report step to echo-only, nor by asserting a
status string alone. The fix was then restored and the guard re-run green.

## Tests

| check | result |
|---|---|
| `pytest tests/test_scheduler_trajectory_conformance.py` | **20 passed** (was 16; +4) |
| scheduler/attention/router guard set (6 files) | **61 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| CP10 mutation boundary judge over changed paths | **PASS** |
| `python -m py_compile api/main.py` | n/a — boot code untouched |
| end-to-end: report program against a real session result | prints the blocker text |

## Baseline comparison (node-set identity, not counts)

Command: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`
Fingerprint: `python scripts/baseline_fingerprint.py <log>`

```
main 17e626cd : 10 failed, 1588 passed, 17 skipped, 1 error
branch        : 10 failed, 1592 passed, 17 skipped, 1 error

outcomes fingerprint : f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48  (both)
ids fingerprint      : 92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413  (both)
```

The failing/error node set is **identical** on both sides (11 nodes, same fingerprint); passed
moved by exactly **+4**, the new tests. No regression attributable to this change. The
pre-existing failures are environment debt, recorded not repaired.

## Live CI observation (this PR's first run)

Run `37528620179` / job `112491935001` (`engineering-scheduler`, **success**), head
`15cbfe20…`, trigger `pull_request` — the branch this pass flagged as unobserved. The
`Session report` step printed:

```
=== ARKADIA ENGINEERING SESSION ===
SHA:    15cbfe2038ca983f5b4d797c535381021abd0e82
Status:
Move:
Trigger:pull_request
Merge:  FORBIDDEN
Deploy: FORBIDDEN
Blockers: (session result unavailable)
```

The runner step is correctly gated off on `pull_request`, so there is no session result and
the report says so rather than printing a bare `Status:`. The branch is now **OBSERVED**, not
merely test-covered.

Check runs at this head: `Full-history secret scan` pass, `engineering-scheduler` pass,
`Vercel – arkadia-prism` pass, `Vercel Preview Comments` pass.
`Vercel – console` **fail** — measured as **failure on `main` `17e626cd` itself**
(`commits/17e626cd…/status` → `Vercel – console  failure`), therefore **pre-existing and not
attributable to this PR**. It is not a merge blocker for a change that touches no frontend
surface.

## Remaining uncertainty

- ~~The `pull_request` branch has not been observed in a live run.~~ **Closed** by the
  observation above.
- The four unroutable statuses (`aborted`, `blocked`, `failed`, `merged_acceptance_pending`) are
  **reported, not repaired** — intentionally. The sovereign decision is PR #332.
- The scheduled (`NO_LEGAL_MOVE` + blockers) branch is not re-observed here because a scheduled
  run cannot be triggered without dispatching the live workflow; its behaviour is proven
  end-to-end against a real session result and by the guard.

## Verification commands

```
python -m pytest tests/test_scheduler_trajectory_conformance.py -q -rEf
python -m pytest tests/architecture -q -rEf
python -m pytest tests/ -q -rEf --continue-on-collection-errors
python scripts/baseline_fingerprint.py <log>
```

## Authorization required

Sovereign review and merge. This PR does not merge, deploy, or promote any gate.
