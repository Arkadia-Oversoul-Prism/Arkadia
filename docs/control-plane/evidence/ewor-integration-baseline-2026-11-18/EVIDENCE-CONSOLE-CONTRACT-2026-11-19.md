# Prism Console Contract Failure — Investigation and Repair

**Date:** 2026-11-19
**Branch:** `integration/ewor-evidence-baseline-2026-11-18`
**Repair commit:** `f4f372ff547a7bc52bba02233a0faa4f1a930b03`
**Repair tree:** `52e4a66786da8d63f2d86bb998916a842329a7b1`
**Main base:** `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` — **unchanged**

This section is appended. No earlier evidence in this directory was modified or
erased. The historical CI results recorded for `31a8793f`, `6dcdf038`,
`0fdf4ca8`, `5e147892` and `a8aa66d3` remain as recorded.

---

## 1. The failure, as observed

| Field | Value |
|---|---|
| Workflow | Prism Console Contract |
| Run | `44461878090` |
| Job | `135350372926` |
| Failing step | 11 — *Workspace layout assertions (rendered, authenticated test identity)* |
| Head | `5793b27173b3ca8bbf4b5de31cc00c7571ecd222` |

**The log was retrieved.** `GET /actions/jobs/{id}/logs` returns HTTP 403
("Must have admin rights to Repository") from the sandbox, but the configured
GitHub integration's `GITHUB_DOWNLOAD_JOB_LOGS_FOR_A_WORKFLOW_RUN` returned the
full job log. The earlier reports in this directory correctly recorded the log
as unreachable *at that time*; it is reachable now, and the cause below is read
from the log, not inferred.

### What the log actually says

```
PASS: all routes and viewports satisfy the layout contract
...
"session_state_after_execution": "READY_FOR_REVIEW"
"run_state": "VERIFYING"
"canonical_session_view": {
  "session_state": "AUTHORIZED",
  "run_states": [],
  "evidence_ids": [],
  "event_types": ["SESSION_CREATED", "SESSION_TRANSITION"]
}
"api_execute_statuses": [400, 200]
FAIL: canonical session view did not reach READY_FOR_REVIEW: AUTHORIZED
```

Two facts settle the diagnosis:

1. **The layout contract passed.** The step is named for layout assertions, and
   the layout contract in that same step reported `PASS`. The failure is in the
   mission-workspace flow that runs in the same step, not in layout.
2. **The product was correct.** The surface reached `READY_FOR_REVIEW` and the
   run reached `VERIFYING`. The *captured payload* said `AUTHORIZED` with no
   runs and no evidence — a state that precedes execution.

The captured payload is the **pre-execute poll**, not the settled view.

---

## 2. Root cause

`web/arkadia_console/exercise_mission_workspace.py` captured the canonical
session view with `page.expect_response(...)`, which resolves on the **first**
matching response. But `MissionWorkspace.tsx` polls
`GET /api/lab/engineering/sessions/{id}` every `EXECUTE_POLL_MS` (1500 ms)
while an execute request is in flight. The first matching response is therefore
frequently the poll issued *before* the execute result was applied — a session
still at `AUTHORIZED`, with `run_states: []` and `evidence_ids: []`.

A second, smaller race sat in the same flow: the surface appends its
`originated_by human` note only after its own post-authorize refresh resolves,
which can land after the `AUTHORIZED` state is already visible. Sampling the
timeline once could miss the note.

**Both are harness defects. Neither is a product defect, and neither is caused
by any contribution in #663–#667.**

### Why this is a race and not a regression

| Evidence | Observation |
|---|---|
| `web/` tree hash | **identical** at `6dcdf038` (green), `f9bd8da9` (main), and every failing head |
| `api/` tree hash | **identical** across the same commits |
| Workflow file hash | **identical** across the same commits |
| `main` `f9bd8da9` | this step **passes** in runs `44044565413`, `44313658543` and **fails** in `43923778351`, `43993655851` |
| Step duration | ~40 s in both passing and failing runs — an assertion failure, not a startup timeout |

`main` both passing and failing the same step on byte-identical code is the
decisive proof: the outcome depends on timing, not on the tree.

### Local reproduction

With the backend and Vite dev server running locally, the **original** harness
passed 6/6 runs and the **fixed** harness passed 6/6 runs. The race does not
reproduce on an idle single-core sandbox; it needs CI's concurrent load to lose
the poll-versus-refresh ordering. This is recorded as a limitation: the local
runs demonstrate the fix does not break the flow, but they do **not** reproduce
the failure. The CI run on the repair commit is the evidence that the race is
closed.

---

## 3. The repair

`web/arkadia_console/exercise_mission_workspace.py` only. **No product code
changed.**

1. **The canonical view is read explicitly, after the surface settles.** A new
   `_read_canonical_session_view()` fetches
   `/api/lab/engineering/sessions/{id}` with the surface's own bearer token
   (`localStorage.arkadia_token`) once the rendered state has reached
   `READY_FOR_REVIEW`. The racy `expect_response` capture is gone.
2. **The authorization note is awaited, not sampled.** A `wait_for_function`
   guards `originated_by human` before the failure is recorded.

### What was deliberately *not* done

- **No assertion was removed, loosened or skipped.** Every property the harness
  proved before is still proved: the review boundary, the `VERIFYING` run, the
  run evidence, the human-origin record, the pre-authorization refusal, the
  human-acceptance boundary, the evidence-reference resolution, and the
  canonical event set.
- **The harness still fails closed** — non-zero exit and a `FAIL` verdict.
- **The authenticated-identity requirement is untouched** — the harness still
  refuses a render that stopped at the sign-in threshold.
- **The poll was not removed.** The fix is robust *to* the poll rather than
  dependent on its absence; a test pins the poll's continued existence.

---

## 4. Regression tests

`tests/test_mission_workspace_harness_determinism.py` — **8 tests, all passing.**

| Test | Pins |
|---|---|
| `test_session_view_is_read_explicitly_not_captured_from_a_poll` | the racy `expect_response` capture is gone; the explicit reader exists, targets the canonical endpoint and authenticates |
| `test_session_view_read_happens_after_the_surface_settles` | the read is ordered *after* the rendered review boundary |
| `test_authorization_timeline_waits_for_the_note` | the note is awaited before the failure can be recorded |
| `test_the_substrate_assertions_are_still_present` | all 8 substrate assertions survive |
| `test_the_harness_still_fails_closed` | non-zero exit and `FAIL` verdict |
| `test_the_harness_still_requires_an_authenticated_identity` | the sign-in threshold is still enforced |
| `test_the_workspace_polls_the_session_view_during_execute` | the poll still exists — the fix must not depend on its absence |
| `test_the_workspace_reaches_ready_for_review_after_execute` | the surface still settles at the review boundary |

**The tests were proven to catch the defect.** Reverting the harness to its
original form and re-running them produced **3 failures**; restoring the fix
produced **8 passes**.

```
$ python3 -m pytest tests/test_mission_workspace_harness_determinism.py -q
8 passed
```

---

## 5. Verification

```
$ python3 -m pytest tests/test_lab_mission_workspace_contract.py \
                    tests/test_mission_workspace_harness_determinism.py \
                    tests/test_lane_instruction_doc_currency.py \
                    tests/test_lane_currency_ci_wiring.py \
                    tests/test_lane_aggregate_pr_classification.py -q
123 passed
```

### Full suite vs PR base (same environment, both trees)

| Tree | Failed | Passed | Skipped | Errors |
|---|---|---|---|---|
| Base `f9bd8da9` | 180 | 3801 | 21 | 60 |
| Head `f4f372ff` | **169** | **3845** | 31 | 64 |

**New failures: 0.** Eleven fewer failures than base. The +4 errors are
`test_prism_opportunity_entry_flow.py` and `test_prism_w4_arkana_thread_time_truth.py`
failing on a missing `node_modules` in the base worktree — environment, not
behaviour. `tests/test_autonomy.py` is excluded from both trees (pre-existing
collection error).

### Lane-state gates

```
$ python3 scripts/lane_state.py --check
lane instruction docs consistent with snapshot (4 guarded lanes)
OFFLINE_EXIT=0

$ python3 scripts/lane_state.py --check --verify-live
LIVE_EXIT=1   # live PR state unavailable (no GitHub token)
```

**The offline gate passes. The live gate is BLOCKED, not passed.** No
`GH_TOKEN` exists in this environment, and this follow-up explicitly forbids
substituting an unauthenticated transport for the authenticated acceptance
gate. The live gate therefore remains **unmet** and is reported as such.

---

## 6. CI on the repair commit `f4f372ff`

12 workflow runs on this exact head. **11 success, 1 failure.**

| Workflow | Run | Conclusion |
|---|---|---|
| **Prism Console Contract** | `44469267828` | **success** — step 11 now passes |
| Lane Doc Currency | `44469267909` | success |
| Baseline Fingerprint Verification | `44469267833` | success |
| Boot Syntax Boundary | `44469267889` | success |
| Canonical Render Runtime Probe | `44469267887` | success |
| Operator Console Posture Currency | `44469267984` | success |
| N-ATLAS Developer Lab | `44469267842` | success |
| N-ATLAS provider forensics | `44469268012` | success |
| economic-seam-engine | `44469267929` | success |
| security-secret-scan | `44469267825` | success |
| SG-02-FE.2-V | `44469267824` | in progress at time of writing |
| **N-ATLAS external beta validation** | `44469267948` | **failure** |

**Prism Console Contract step 11 — the step that was failing — now reports
`success`.** This is the direct evidence that the repair closes the failure.

### The one remaining failure — N-ATLAS, read from its log

`beta-beta-02-hausa` failed; `beta-beta-01-english` **passed** in the same run.
This is the **reverse** of the previous head, where english failed and hausa
passed. The branch does not touch `n-atlas-external-beta.yml` (empty diff).

The log shows the actual cause:

```
"status": "FAILED",
"reason": "external runtime did not return usable inference",
"errors": []
```

The job probed the external Hugging Face Space
`KoladeOdunope/ednai-natlas-runtime` and got **no usable inference back**,
with an **empty error list** — meaning no HTTP exception was raised; the
Gradio call simply produced no `response_text` within its window. The Space
itself reported `"stage": "RUNNING"` with `zero-a10g` hardware at the time.

`bundle-beta-evidence` then failed at *Verify bundle shape* because the hausa
job produced no passing evidence artifact.

**Attribution:** an external dependency (a third-party Hugging Face Space on
ZeroGPU) intermittently failing to return inference. It is **not** caused by
this branch, and it is **not** a pre-existing condition on `main` — it is a
flaky external service whose failing job alternates between runs. It should be
re-run before merge.

---

## 7. Governance

- `main` remains `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` — **unchanged**.
- **No PR merged, closed, reopened or retargeted.** #668 remains open and draft.
- **#668 remains aggregate-excluded** from lane ownership.
- **#657 remains unassigned** and separately reviewed.
- **#663–#667 remain separate contribution records.**
- No deployment, commissioning, runtime credentials, workspace binding, L3
  activation or autonomous scheduling.
- Push used a temporary write-enabled deploy key (`170405291`), deleted
  immediately; `deploy_keys` confirmed `[]`; private half shredded.
- **Human acceptance is not issued.**

---

## 8. What remains

1. **Live lane-state gate is BLOCKED** — needs a `GH_TOKEN` in an authorized
   environment. The offline gate passes.
2. **N-ATLAS external beta** — re-run to confirm the external Space's
   transience. Not caused by this branch.
3. **SG-02-FE.2-V** was still running when this section was written; its
   conclusion is not claimed here.
4. **The race was not reproduced locally** — the fix is evidenced by the CI run
   on `f4f372ff`, not by a local failure reproduction.

**Recommendation: CONDITIONALLY READY — SPECIFIC EVIDENCE REMAINS.**
