# Gate 2b — Native Agent Loop Delegation Boundary

**ARKADIA-CHIEF-001 · branch `feat/chief-agent-foundation-001` · draft PR #657**

Gate 1 hardened the Weaver dispatch boundary. Gate 2 extended the same contract
to every *route* that can execute delegated work. This document covers the one
execution surface Gate 2 left behind: the **native agent loop's tool boundary**.

The agent remains **uncommissioned**. No merge, no deployment, no commissioning,
no runtime credentials, no L3, no autonomous scheduling. Human-only authority
boundaries are unchanged.

---

## 1. The gap, reproduced before it was fixed

`execute_agent_loop` derived its tool envelope once, through
`_authorization_operations`. That function checks the *local* grant's usability
— revoked, expired, consumed — but never re-reads the executive delegation. The
envelope was therefore a **snapshot taken before the run started**.

Reproduction (temporary probe, deleted before the commit):

```
delegation eodel-... status=ACTIVE epoch=1
delegation after revoke: status=REVOKED epoch=2
loop_state=DONE result_state=IMPLEMENTED effective_tools=['filesystem.read']
  TOOL filesystem.read ok=True content='# probe\n'

RESULT: tool executed with a REVOKED delegation? True
```

A delegation revoked **before the loop ran** still let `filesystem.read` execute
and return file content. The envelope had already been computed from a grant
that was still locally usable, and nothing re-read the delegation afterwards.

After the fix, the same probe:

```
loop_state=BLOCKED result_state=BLOCKED
reason="tool 'filesystem.read' denied: executive delegation no longer permits
        'read': delegation is revoked"
  TOOL filesystem.read ok=False

RESULT: tool executed with a REVOKED delegation? False
```

---

## 2. What was implemented

### 2.1 A per-call guard at the actual tool boundary

`ToolRegistry.invoke` now runs a `dispatch_guard` **before every other branch** —
before the unknown-tool check, before the grant check, before the sandbox is
touched. This is the point a tool is actually invoked, not where the tool list
was derived.

`EngineeringLabRuntime._agent_loop_dispatch_guard` supplies that callable. Per
call it:

1. re-reads the authorization from the store;
2. re-checks the grant is still usable (revoked / expired / consumed);
3. calls `assert_delegation_dispatchable` — **the same function Weaver's
   dispatch guard calls** — so status, expiry, credential epoch and revocation
   are judged by one implementation, not a second copy.

### 2.2 A denial is terminal, not a retryable observation

`ToolDenied` is a distinct type from `ToolError`. An ordinary tool error is fed
back to the model so it can adjust; a **denial ends the run**. Handing a denial
back as an observation would let the model try a different tool and keep going —
turning a refusal into a negotiation. The loop records the denial as a turn,
emits `TOOL_DENIED` on the live event stream, and returns `BLOCKED`.

### 2.3 Fail-closed twice over

A guard that raises denies. A guard that **itself fails** also denies — an
authority that cannot be verified is not an authority that can be used.

### 2.4 Scope discipline

The guard re-checks the **delegation contract and grant usability** only. It
deliberately does *not* re-impose the grant's scope or operation naming at the
tool boundary: those are envelope concerns already settled when the tool set was
derived, and re-imposing them would change the loop's existing semantics rather
than harden them. (An earlier draft did re-impose them and broke two existing
tests; that over-reach was removed, not the tests.)

---

## 3. Changed files

| File | Change |
|---|---|
| `lab/engineering_lab/tools.py` | `ToolDenied`; `dispatch_guard` parameter; guard runs first in `invoke` |
| `lab/engineering_lab/agent_loop.py` | catches `ToolDenied`, records a `DENIED` turn, emits `TOOL_DENIED`, returns `BLOCKED` |
| `lab/engineering_lab/runtime.py` | `TOOL_OPERATIONS` inverse map; `_tool_operation_kind`; `_agent_loop_dispatch_guard`; guard bound at the single `ToolRegistry` construction |
| `lab/engineering_lab/models.py` | `TOOL_DENIED` added to `AGENT_EVENT_TYPES` |
| `tests/test_lab_execution_boundary_ws2.py` | the single-construction-site pin strengthened to require the guard |
| `tests/test_gate2b_agent_loop_delegation.py` | **new** — 16 tests |
| `.github/workflows/executive-office-identity-governance.yml` | new CI step + path filters for the new files |

`6 files changed, 203 insertions(+), 5 deletions(-)` plus the new test file.

---

## 4. Tests — 16 new, all passing

```
$ python -m pytest tests/test_gate2b_agent_loop_delegation.py -q
16 passed, 1 warning in 1.82s
```

| # | Test | Asserts |
|---|---|---|
| 1 | `test_revoked_delegation_cannot_execute_through_the_agent_loop` | the exact pre-fix reproduction now denies |
| 2 | `test_suspended_delegation_cannot_execute_through_the_agent_loop` | suspended denies |
| 3 | `test_expired_delegation_cannot_execute_through_the_agent_loop` | delegation expires while the grant is unexpired |
| 4 | `test_superseded_credential_epoch_cannot_execute_through_the_agent_loop` | suspend+reactivate bumps the epoch; old grant dead |
| 5 | `test_missing_delegation_record_cannot_execute_through_the_agent_loop` | absent record denies |
| 6 | `test_unverifiable_registry_cannot_execute_through_the_agent_loop` | registry fails **at the tool boundary**, not at load |
| 7 | `test_revocation_between_two_turns_stops_the_second_tool_call` | **the decisive test** — authority withdrawn mid-run |
| 8 | `test_grant_revoked_mid_run_stops_the_next_tool_call` | the grant itself is re-read per call |
| 9 | `test_denial_is_not_offered_back_to_the_model_as_a_retry` | the run stops at the first denial |
| 10 | `test_every_registered_tool_maps_to_an_authorized_operation` | the guard is total — no tool it has no opinion about |
| 11 | `test_plain_human_grant_still_executes_through_the_agent_loop` | the ordinary path still works |
| 12 | `test_active_delegation_still_executes_through_the_agent_loop` | a live delegation is not refused |
| 13 | `test_denial_is_recorded_as_evidence` | refusal is legible in evidence + event stream |
| 14 | `test_tool_registry_denies_when_the_guard_raises` | guard raises ⇒ deny |
| 15 | `test_tool_registry_denies_when_the_guard_itself_fails` | guard crashes ⇒ deny |
| 16 | `test_tool_registry_without_a_guard_is_unchanged` | the guard is additive |

### Gate 1 + Gate 2 + Gate 2b together

```
$ python -m pytest tests/test_executive_identity_governance.py \
    tests/test_executive_api_boundary.py \
    tests/test_openapi_security_production_contract.py \
    tests/test_executive_dispatch_revocation_hardening.py \
    tests/test_gate2_revocation_consistency.py \
    tests/test_gate2b_agent_loop_delegation.py -q
125 passed, 5 warnings in 4.71s
```

Per-file collected: **58 + 11 + 1 + 17 + 22 + 16 = 125**.

---

## 5. Failure-injection evidence — mutation testing

Each guard was disabled in turn and the suite re-run. Files restored
byte-identically afterwards.

| Mutation | Result | Verdict |
|---|---|---|
| M1 — remove the per-call guard from `ToolRegistry.invoke` | **11 failed**, 4 passed | load-bearing |
| M2 — remove `assert_delegation_dispatchable` from the guard | **9 failed**, 6 passed | load-bearing |
| M3 — cache the guard's verdict per run (per-run, not per-call) | **1 failed** (the mid-run test) | load-bearing |
| M4 — feed the denial back as a retryable observation | **9 failed**, 6 passed | load-bearing |
| M5 — remove the grant-usability check | **1 failed** (after adding test 8) | load-bearing |

**M5 initially reddened nothing.** That was a real coverage gap, not a passing
grade: every other test withdraws the *delegation*, none withdrew the *grant*.
Test 8 was written to close it, and M5 now reddens exactly that test. This is
reported because a mutation that survives is evidence of a missing test, and
silently dropping it would have overstated the suite.

---

## 6. Full-suite comparison against the PR base

Both runs from a clean `data/engineering_lab/`, back to back, same command:

```
$ rm -rf data/engineering_lab
$ python -m pytest tests/ -q -p no:randomly --ignore=tests/test_autonomy.py
```

| Tree | Failed | Passed | Skipped | Errors |
|---|---|---|---|---|
| Base (`a1009ddf`) | 168 | 3909 | 34 | 57 |
| Head (this work) | **168** | **3925** | 34 | 57 |

**+16 passed — exactly the 16 new tests. Failing-node set diff: `IDENTICAL`,
zero new, zero removed** (225 failing/erroring node IDs compared, `diff` empty).

`tests/test_autonomy.py` is excluded: it has a **pre-existing collection error**
(`ImportError: load_autonomy_config`) on the base, and is excluded from the
baseline identically. Not fixed — reported.

---

## 7. CI

The new suite is added to the required workflow as its own step, and the new
source files are added to both path filters:

```
- name: Gate 2b native agent loop delegation boundary
  run: python -m pytest tests/test_gate2b_agent_loop_delegation.py -q -rA
```

Path filters now include `tests/test_gate2b_agent_loop_delegation.py`,
`lab/engineering_lab/tools.py`, `lab/engineering_lab/agent_loop.py` and
`lab/engineering_lab/models.py` — so a change to the guard, the loop or the
event types is judged by this gate rather than merging with every check green.

Workflow YAML validated; 10 steps, including the structural
*"The agent is not commissioned"* assertion.

---

## 8. What is proven, and what is not

**Proven**
- A revoked, suspended, expired, superseded, missing or unverifiable delegation
  cannot execute a tool through the native agent loop — each demonstrated by a
  test that asserts the tool did not run.
- The check is **per call**, not per run: a delegation revoked between two turns
  stops the second call (test 7), and a grant revoked mid-run stops the next
  call (test 8).
- A denial is terminal and is recorded in both the evidence trail and the live
  event stream.
- The ordinary human-authorized path and a live delegation both still execute.
- Every guard is mutation-verified as load-bearing.
- No regression: failing-node set identical to base.

**Not proven / limitations**
- **No live browser verification.** No browser tool exists in this environment;
  the API boundary is proven by `TestClient`, not a live session.
- **The new CI step has not run on GitHub yet.** The YAML is valid and the step
  passes locally, but "enforced in CI" is not yet an observed fact for this
  commit.
- **`DelegationRegistry.get` raises `ValueError` for an absent row** rather than
  returning `None`, so a missing delegation surfaces as "could not be verified"
  rather than "delegation record is missing". Both deny; the wording is the
  established contract pinned by the existing hardening suite. Documented in
  test 5 rather than papered over.
- **The 168 failures / 57 errors are pre-existing** on the base and byte-identical
  before and after.
- **`tests/test_autonomy.py` collection error is pre-existing** and unfixed.

---

## 9. Constraints honoured

No merge. No deployment. No commissioning. No credential issuance for an active
runtime. No L3 activation or autonomous scheduling. No change to human-only
authority boundaries. The approval, Weaver, WorkEvent and Evidence chains are
preserved — the guard is additive and the existing single-construction-site pin
was strengthened, not relaxed. No existing test was weakened or deleted; the one
existing test file changed had its assertion made **stricter**.
