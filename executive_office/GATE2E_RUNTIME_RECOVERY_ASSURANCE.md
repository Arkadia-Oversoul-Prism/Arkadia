# Gate 2e — Runtime Recovery Assurance

**Scope:** prove that authority survives a restart correctly in *both* directions —
persisted authority is reloaded, and withdrawn authority is not laundered.

**Agent status:** uncommissioned. No delegation exists outside the test databases.
No merge, deployment, commissioning, runtime credentials, workspace binding, L3
activation or autonomous scheduling is authorised by this document.

---

## 1. Why this gate exists

Gates 1, 2, 2b, 2c and 2d all prove that *withdrawal* of authority is enforced
while a process is running. None of them answers the recovery question.

Authority is durable state in SQLite, not process memory. Across a restart three
distinct failures are possible, and only one is obvious:

| # | Failure | Direction | Consequence |
|---|---|---|---|
| 1 | Persisted authority is **lost** | fail-closed | A legitimately delegated agent silently cannot act |
| 2 | Persisted authority is reloaded **stale** | **fail-open** | A credential minted before a revocation keeps working, because the process died before it acted on the withdrawal |
| 3 | Queued work **resumes** under dead authority | **fail-open** | Durable queue + durable delegation = work executes after the reason to execute it is gone |

Row 2 is the dangerous one: a restart is normally a *safe* event, so a
revocation that does not survive one is easy to overlook. Row 3 is its
consequence on a surface that outlives the process.

---

## 2. What "restart" means in this test file

Every test constructs a genuinely new consumer object against the **same**
durable stores:

```python
def _runtime(stores) -> EngineeringLabRuntime:
    stream = EventStream(log_path=str(stores["tmp_path"] / "events.jsonl"))
    return EngineeringLabRuntime(store=EngineeringLabStore(), stream=stream)
```

`stores` monkeypatches the module-level database paths in
`executive_office.registry`, `weaver.authorization_revocation`,
`weaver.enterprise_orchestration` and `lab.engineering_lab.store` — exactly as a
real deployment reads them from the environment. The *objects* are rebuilt; the
*paths* are deliberately left alone, so the second runtime opens the database
the first one wrote. Nothing is carried over in memory.

This is the strongest form available without a supervisor process, and it
exercises the real SQLite read path rather than a mock.

---

## 3. Coverage

`tests/test_gate2e_runtime_recovery_assurance.py` — **11 tests, all passing.**

### 3.1 Restart with an existing active delegation

| Test | Asserts |
|---|---|
| `test_restart_with_active_delegation_still_dispatches` | A new runtime over the durable store finds the persisted session, re-reads an ACTIVE delegation, and the loop reaches `DONE` with the tool actually executed. |
| `test_restart_reloads_persisted_status_and_credential_epoch` | The reloaded record equals the written one field for field: `status == ACTIVE`, `credential_epoch == 1`, plus `policy_digest`, `owner_uid`, `workspace_id`. The append-only `GRANTED` event survives with its epoch. |
| `test_restart_after_suspension_reloads_the_bumped_epoch` | After a suspend, a restarted reader sees `SUSPENDED` and **epoch 2**, not the pre-suspension epoch 1, and `active_for_principal()` returns `None`. |

Reloading the pre-suspension epoch would re-validate exactly the credentials the
suspension invalidated, so the epoch assertion is the load-bearing one.

### 3.2 Restart after revocation — old credentials stay unusable

| Test | Asserts |
|---|---|
| `test_restart_after_revocation_keeps_old_credentials_unusable` | After the cascade, a restarted process sees `REVOKED`, `active_for_principal() is None`, `credential_epoch == old + 1`. The pre-revocation epoch is refused by `assert_delegation_dispatchable` with "delegation is revoked", and the loop ends `BLOCKED` with nothing executed. |
| `test_restart_after_delegation_only_revocation_denies_on_the_delegation` | Revokes the delegation **alone**, leaving the Lab grant unrevoked, unexpired and unconsumed. The run is still refused with "delegation is revoked". |
| `test_restart_after_revocation_refuses_a_token_minted_before_it` | A token minted while valid is verified successfully through a *separate* broker over the same key directory, then refused after revocation — through a fresh broker and a fresh registry over the durable state. |

The delegation-only test is the one that isolates the claim. If the guard
consulted the Lab grant alone, that run would **succeed**, because the grant is
genuinely live. The refusal can only come from the delegation re-read.

### 3.3 Queued work cannot resume under revoked authority

| Test | Asserts |
|---|---|
| `test_queued_work_cannot_resume_after_revocation` | A job is verified dispatchable *before* the revocation (otherwise the test proves nothing), the cascade reports `cancelled_jobs == 1`, and after a restart `job_is_dispatchable(job) is False` with `status == CANCELLED` and a recorded reason. |
| `test_queued_work_for_a_suspended_delegation_is_not_dispatchable` | Suspension does not cancel the row — only a revocation does — so this proves the **guard** stops execution, which is the behaviour that must survive a restart. Loop ends `BLOCKED`, nothing executed. |

### 3.4 Failure stays closed when the registry is unavailable

| Test | Asserts |
|---|---|
| `test_restart_with_unavailable_registry_denies_dispatch` | The registry raises only when the guard re-reads it at the tool boundary. The loop ends `BLOCKED`, nothing executed, reason "could not be verified". |
| `test_registry_read_error_is_reported_as_no_active_delegation` | `active_for_principal()` swallows a store error and reports `None`, so a startup caller that treats it as the answer denies rather than crashing into an unhandled state. |
| `test_broker_refuses_issuance_when_the_registry_is_unavailable` | No token can be minted across a restart while the registry is down. |

---

## 4. Two real findings during development

Recorded because both changed the test, not the production code.

**F1 — the cascade refuses on the grant, before the delegation.** The first
draft asserted "delegation is revoked" in the loop reason after a full cascade.
The actual reason was `authorization is revoked, expired or already consumed`,
because `revoke_delegation_cascade` also revokes the Lab grant and the guard
checks the grant first. That ordering is correct — the most specific available
reason wins — but it means a cascade test cannot isolate the delegation path. I
kept the cascade assertion honest and added
`test_restart_after_delegation_only_revocation_denies_on_the_delegation` to
prove the delegation re-read on its own.

**F2 — the token test verified against the wrong key.** Passing only
`registry=` to `verify_machine_token` let it construct a broker with the default
key directory, so the token failed as *"signature invalid"* rather than as a
revocation. That would have been a false pass: any broken signature would have
satisfied the test. It now passes a broker over the minting key directory and
matches on `"not serviceable"`, so the refusal is provably the revocation.

---

## 5. Test counts

```
$ python -m pytest tests/test_gate2e_runtime_recovery_assurance.py -q
11 passed, 1 warning in 0.69s
```

Gate suite (every Gate 1 / 2 / 2b / 2c / 2d / 2e file, one command):

```
$ python -m pytest tests/test_executive_identity_governance.py \
    tests/test_executive_api_boundary.py \
    tests/test_executive_dispatch_revocation_hardening.py \
    tests/test_gate2_revocation_consistency.py \
    tests/test_gate2b_agent_loop_delegation.py \
    tests/test_gate2c_grant_scope_immutability.py \
    tests/test_lab_execution_boundary_ws2.py \
    tests/test_openapi_security_production_contract.py \
    tests/test_gate2e_runtime_recovery_assurance.py -q
153 passed, 5 warnings in 4.70s
```

Per file, collected = passed in every case:

| File | Collected | Passed |
|---|---|---|
| `test_executive_identity_governance.py` | 58 | 58 |
| `test_executive_api_boundary.py` | 11 | 11 |
| `test_executive_dispatch_revocation_hardening.py` | 17 | 17 |
| `test_gate2_revocation_consistency.py` | 22 | 22 |
| `test_gate2b_agent_loop_delegation.py` | 16 | 16 |
| `test_gate2c_grant_scope_immutability.py` | 7 | 7 |
| `test_lab_execution_boundary_ws2.py` | 10 | 10 |
| `test_openapi_security_production_contract.py` | 1 | 1 |
| `test_gate2e_runtime_recovery_assurance.py` | **11** | **11** |
| **Total** | **153** | **153** |

153 = the previous 142 + the 11 new tests. No existing test was modified,
loosened or removed — `git diff --stat -- tests/` is empty apart from the new
file being untracked.

---

## 6. Full-suite comparison against the PR base

Both trees measured in this same environment, `tests/` excluding
`tests/test_autonomy.py` (a pre-existing collection error present identically on
both).

| Tree | Failed | Passed | Skipped | Errors |
|---|---|---|---|---|
| Base `a1009ddf` | 172 | 3799 | 21 | 57 |
| Head | **162** | **3962** | 21 | 57 |

**Failing-node set diff:**

```
NEW failures (in head, not in base)     : 0
FIXED      (in base, not in head)       : 10
```

Ten nodes in `tests/test_mission_lifecycle_adapter_contract.py` fail on the base
and pass on the head. That file is **byte-identical** between base and head
(`git diff --stat a1009ddf HEAD -- tests/test_mission_lifecycle_adapter_contract.py`
is empty) and its 10 tests pass on head in isolation. The difference is
environmental — the base worktree was a fresh checkout without the working
`data/` state the head tree has — not a behavioural change from this work. I did
**not** claim those 10 as a fix attributable to this branch.

The two measurements agree: 162 failed on head, 0 new, 10 environment-only
recoveries, and 3962 − 3799 = 163 passed gained, consistent with the 10 plus the
153-gate additions across the branch.

---

## 7. What is proven / what is not

### Proven by this gate

- A restart reloads a live delegation, its status, its credential epoch and its
  policy digest unchanged, and the agent still dispatches.
- A restart after a suspension loads the **bumped** epoch, not the stale one.
- A restart does not launder a revocation: the pre-revocation epoch is refused
  by both the Lab guard and the token validator.
- The delegation re-read is independently load-bearing — proven with the Lab
  grant left deliberately live.
- Durable queued work cannot resume after revocation (cancelled) or suspension
  (guard-refused).
- An unreadable registry at restart denies dispatch, denies token issuance, and
  reports "no active delegation" rather than propagating a transient-looking
  error.

### Not proven / not covered

- **No live browser verification.** There is no browser tool in this environment.
  The API boundary is exercised through `TestClient` elsewhere in the suite; this
  gate does not touch HTTP at all.
- **No real process restart.** "Restart" is a new object graph over the same
  SQLite files in the same interpreter. A genuine `SIGKILL` + supervisor restart
  would additionally exercise connection teardown, WAL checkpoint recovery and
  key-file reload. Those paths are unexercised here.
- **WAL recovery after an unclean shutdown is not tested.** Every test closes its
  connections politely. `journal_mode=WAL` recovery from a torn write is a
  different scenario.
- **Multi-process concurrency is not tested.** Two runtimes racing a revocation
  against a dispatch is outside this file's scope.
- **The registry-unavailable path is injected by monkeypatching
  `assert_delegation_dispatchable`**, not by making the SQLite file genuinely
  unreadable. `test_registry_read_error_is_reported_as_no_active_delegation`
  does exercise a real `OperationalError` from `_connect`, but the full guard
  path is simulated.
- **`tests/test_autonomy.py` is excluded** from every count on both trees; its
  collection error is pre-existing and unaddressed.

---

## 8. CI wiring

`.github/workflows/executive-office-identity-governance.yml`, **additive only**
(+10 lines, no existing step or filter altered):

- `tests/test_gate2e_runtime_recovery_assurance.py` added to **both** the
  `pull_request` and `push` path filters, immediately after the Gate 2d entry.
- A named step `Gate 2e runtime recovery assurance` inserted after the Gate 2d
  step, running `python -m pytest tests/test_gate2e_runtime_recovery_assurance.py -q -rA`.

Workflow parses as valid YAML; step count is now **13** (was 12). Every Gate file
is named by a CI step — none unexercised.

**The new step has not yet run on GitHub for this commit.** It passes locally.
Whether CI is green for this head is reported separately from the run data; this
document does not assert it.

---

## 9. Controls preserved

- Gate 1 identity and governance: untouched.
- Gate 2 revocation consistency across Weaver / Lab / SolSpire voice: untouched.
- Gate 2b per-call guard at the tool boundary: untouched.
- Gate 2c operation-naming re-check: untouched.
- Gate 2d Lab WS2 execution boundary: untouched.
- Human-only authority boundaries, approval chain, Weaver / WorkEvent / Evidence
  chains: untouched. No production code changed in this gate at all.
- **Zero production code changed.** This gate adds one test file and ten lines of
  CI configuration. That is the whole diff, and it is why the risk of this
  change is confined to CI runtime.
