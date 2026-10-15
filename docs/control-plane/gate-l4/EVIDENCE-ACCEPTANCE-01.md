# GATE L4 — Exact-SHA Acceptance Record

Record ID: `GATE-L4-OPENHANDS-DISPATCH-ACCEPTANCE-01`  
Candidate code SHA: `f782a3590ff3053e8afa7ed0b7828e18e08c8aab`  
Base SHA: `49809f45274f2f81b24e01fefdfb3009e8717495`  
Pull request: [#500](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/500)  
Scope: request validation, dispatch contract, run-inspection evidence validation.  
Not in scope: live provider dispatch, merge, deployment, production acceptance.

## Acceptance matrix

| Check | State | Evidence |
|---|---|---|
| GATE L4 security tests | PASS | [dispatch-contract job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043405/job/114980469681) |
| GATE L4 run-inspection tests | PASS | Same job executes `tests/test_gate_l4_dispatch_security.py` and `tests/test_gate_l4_run_inspection.py` |
| Dispatch request JSON syntax | PASS | Same job executes `python -m json.tool` against the request schema |
| Boot syntax boundary | PASS | [boot-syntax job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043248/job/114980469530) |
| Full-history secret scan | PASS | [secret scan job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043211/job/114980469255) |
| General repository test workflow | PASS | [test job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043190/job/114980469246) |
| Trigger coverage | PASS | [trigger-coverage job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043274/job/114980469481) |
| Provider routing broader suite | NOT YET ACCEPTED | [provider-routing job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043228/job/114980469319) was still running at record creation |
| Weaver MVP2 validation | NOT YET ACCEPTED | [MVP2 job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043315/job/114980469531) was still running at record creation |
| Console contract | NOT YET ACCEPTED | [console-contract job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043295/job/114980469403) was still running at record creation |
| Native Arkadia golden workflow | NOT YET ACCEPTED | [golden workflow job](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38300043196/job/114980579096) was still running at record creation |
| Real OpenHands dispatch and later inspection | BLOCKED | No verified provider endpoint/API version/authentication or real provider run is configured in the repository/tooling |
| Four-lane end-to-end dispatch | NOT TESTED | No worker was dispatched; the four lane PRs remain independent |
| Human merge/deployment authority boundary | PASS (static contract) | Code rejects evidence that grants merge/deploy permission; worker has no merge/deploy API in this adapter seam |

## Exact conclusion

The request/evidence contract and fail-closed boundary passed the dedicated GATE L4 test job on candidate SHA `f782a3590ff3053e8afa7ed0b7828e18e08c8aab`. This does **not** establish a live OpenHands integration. Live dispatch and inspection remain **BLOCKED** until a real provider binding and a non-production run produce retrievable evidence.

No production run was started. No merge or deployment was performed. The four existing workstreams were not modified.
