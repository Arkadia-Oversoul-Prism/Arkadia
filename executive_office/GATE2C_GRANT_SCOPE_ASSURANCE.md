# Gate 2c — Grant Scope and Operation Permissions: Assurance Report

**Branch:** `feat/chief-agent-foundation-001` · **PR:** #657 (draft, open)
**Scope:** one remaining assurance question on Gate 2b, plus the N-ATLAS failure cause.
**Status:** implemented, tested, mutation-verified. Not merged, not deployed, not commissioned.

---

## 1. Grant scope and operation permissions

### The question

The Gate 2b per-call guard re-reads grant usability and executive delegation
status, but deliberately did not re-check the grant's `scope_ref` or
`operations_allowed`. Are those fields immutable after creation?

### The answer: one is, one is not

**`scope_ref` — effectively immutable for a live run.**

`attach_authorization` is the only way to bind a grant to a session, and it
refuses any session that has left `PROPOSED`:

```python
# lab/engineering_lab/store.py:262
if session["state"] != "PROPOSED":
    raise ValueError("authorization can only be attached to a PROPOSED session")
```

A session is `AUTHORIZED` before the loop runs, so the authorization reference
cannot be swapped mid-run. Proven by
`test_scope_ref_cannot_be_rebound_once_authorized`.

**`operations_allowed` — NOT immutable. This was a real gap.**

`el_authorizations` stores the whole record as a mutable JSON blob, and every
mutator (`revoke_authorization`, `consume_authorization`,
`revoke_for_delegation`) rewrites that blob wholesale. A narrowing therefore
*can* land after the envelope was computed.

**Reproduced before the fix.** Narrowing the grant mid-run still let
`filesystem.read` execute and return file content:

```
grant now permits: []
loop_state: DONE
  tool: filesystem.read obs: {'ok': True, 'content': '# hi\n'}
executed: True
```

The guard re-read the grant but never checked that the tool's operation was
still named by it, so a human withdrawal made during a run only took effect on
the *next* run.

### The fix

`lab/engineering_lab/runtime.py`, inside `_agent_loop_dispatch_guard`:

```python
operation_kind = _tool_operation_kind(tool_name)
permitted = set(authorization.get("operations_allowed") or ())
if operation_kind not in permitted:
    raise ToolDenied(
        f"tool '{tool_name}' denied: the linked human "
        f"authorization no longer permits '{operation_kind}'",
        tool_name=tool_name,
    )
```

After the fix, the same probe:

```
grant now permits: []
loop_state: BLOCKED
  tool: filesystem.read obs: {'ok': False, 'denied': True,
    'error': "tool 'filesystem.read' denied: the linked human authorization no longer permits 'read'"}
executed: False
```

**It only ever narrows.** A tool outside the envelope is already refused by
`granted` in `ToolRegistry`; this refuses a tool the envelope still lists but
the grant no longer names. It cannot widen authority, so existing
human-authorized execution semantics are preserved, not loosened. The
`test_unchanged_grant_still_executes` test proves the ordinary path still runs.

### Widening is inert

The envelope is frozen at `granted=effective`, so a grant widened mid-run
cannot introduce a tool the run was never given. Verified: widening to
`candidate_write` and calling `filesystem.propose_edit` is refused with
`"not granted to this run"` — and the test asserts the grant really *was*
widened, so the refusal is the envelope, not the grant.

### Tests

`tests/test_gate2c_grant_scope_immutability.py` — **7 tests, all passing.**

| Test | Asserts |
|---|---|
| `test_scope_ref_cannot_be_rebound_once_authorized` | rebinding after AUTHORIZED raises |
| `test_scope_mismatch_is_refused_at_the_dispatch_gate` | wrong scope → `BoundaryViolation` |
| `test_narrowing_operations_mid_run_blocks_the_next_tool_call` | the reproduction, now BLOCKED |
| `test_narrowing_to_a_different_operation_blocks_the_original` | swap read→write still blocks read |
| `test_widening_operations_mid_run_cannot_add_a_tool` | envelope is a ceiling |
| `test_unchanged_grant_still_executes` | permitted path still works |
| `test_operation_naming_is_rechecked_even_without_a_delegation` | plain human grant narrowed too |

### Mutation testing

Disabling the new check (`if False:`) reddens **exactly** the three narrowing
tests and nothing else:

```
FAILED test_narrowing_operations_mid_run_blocks_the_next_tool_call
FAILED test_narrowing_to_a_different_operation_blocks_the_original
FAILED test_operation_naming_is_rechecked_even_without_a_delegation
3 failed, 4 passed
```

The check is load-bearing.

### No existing test weakened

No existing test was modified or loosened. The full Gate 1 + Gate 2 + Gate 2b +
Gate 2c suite: **132 passed** (58 + 11 + 1 + 17 + 22 + 16 + 7).

---

## 2. N-ATLAS external beta workflow — actual failure cause

**This was investigated, not assumed.** The prior reports called it "inferred
flaky". That inference was wrong in its mechanism, and the real cause is
different.

### What the runs show

| Run | Head | Conclusion |
|---|---|---|
| 43744035628 | `7b058dda` | **failure** |
| 43743967786 | `40277680` | **failure** |
| 43729087087 | `308f875a` | success |
| 43728595514 | `2c43e8fc` | success |
| 43727722094 | `3d0d4b4e` | success |
| 43724917103 | `08e272ff` | failure |
| 43683865690 | `3eba3a39` | success |
| 43641094039 | `b134725a` | success |

### Which job actually failed

Not the external beta jobs. On run 43744035628:

- `beta-beta-01-english` — **success**
- `beta-beta-02-hausa` — **success**
- `bundle-beta-evidence` — **success**
- `native-arkadia-golden-workflow` — **failure**, at step 4
  *"Execute Arkadia native N-ATLaS golden path"*

### The decisive evidence: timing

```
step 3 Install Arkadia runtime dependencies  success  17:58:46 → 17:59:13
step 4 Execute Arkadia native N-ATLaS golden path  FAILURE  17:59:13 → 17:59:14
```

**The step failed in one second.** A live inference call to the Space takes
~8–9 seconds when it works. A one-second failure is not a timeout and not a
slow network — it is a fast HTTP error or a collection error.

### Reproduced locally

The step is:

```
python -m pytest -q tests/test_natlas_developer_lab.py -k native_natlas_route_live_external_gradio
```

Run against the live Space from a clean venv built from `requirements.txt`:

```
1 passed, 10 deselected in 8.95s
```

It **passes**. So the code and the dependency set are sound. Simulating a
failing Space endpoint reproduces the CI signature exactly:

```
fastapi.exceptions.HTTPException: 503: N-ATLaS Gradio inference call failed: HTTP Error 404: Not Found
1 failed, 10 deselected in 0.43s
```

**0.43s — the same fast-failure shape as CI's 1s.**

### The mechanism

The Space is `zero-a10g` hardware — **scale-to-zero**. It sleeps when idle and
cold-starts on request. A request arriving while the Space is asleep or
restarting fails fast rather than waiting, which is exactly the observed
one-second failure. The Space is `RUNNING` now and answers in ~0.12s.

### Honest statement of what is proven and what is not

- **Proven:** the failing job is `native-arkadia-golden-workflow`, not the beta
  jobs; it failed in 1 second; the same step passes locally in 8.95s against
  the live Space; a failing Space reproduces the 0.43s signature.
- **Proven:** Gate 2b touched no N-ATLAS file, no `requirements.txt`, and no
  pytest configuration (`git diff --name-only 308f875a 40277680` → none).
- **NOT proven:** the exact HTTP status the Space returned at 17:59:13Z on
  2026-11-15. **The job log is unreachable** — the logs endpoint returns
  `HTTP 403 "Must have admin rights to Repository."` I could not read the
  failure line, and I am not going to claim I did.
- **Therefore:** the cause is a transient external-service failure at the
  provider boundary, established by timing and by local reproduction, not by
  reading the log. It is **not** a code defect in this branch and **not**
  flakiness in the ordinary sense — it is a dependency on a scale-to-zero
  third-party Space.

### Recommendation

Re-run the workflow. If it must be reliable, the golden path should either
retry on a cold-start error or be marked non-required, because a required check
that depends on a sleeping third-party Space will fail intermittently by
construction. **I have not changed the workflow** — that is a CI policy
decision, not a Gate 2c code change.

---

## 3. Full-suite comparison

Measured in the **same environment** (with `pytest-asyncio` installed, which
changes the skip count — the earlier 34-skip figures were taken without it).

| Tree | Failed | Passed | Skipped | Errors |
|---|---|---|---|---|
| Base `a1009ddf` | 171 | 3800 | 21 | 57 |
| Head | **161** | **3952** | 21 | 57 |

Command, both trees:

```
python -m pytest tests/ -q --ignore=tests/test_autonomy.py -p no:randomly
```

**Failing-node set diff: 0 new, 10 fixed.** The 10 fixed are all in
`tests/test_mission_lifecycle_adapter_contract.py` — a pre-existing base
failure that this branch's changes happen to resolve. No new failure was
introduced.

`tests/test_autonomy.py` has a pre-existing collection error on the base and is
excluded from both runs identically.

**Note on the skip count.** Earlier reports cited 34 skipped. That figure was
measured without `pytest-asyncio` installed; with it, 13 async tests are
collected and run instead of being skipped, so the comparable figure is 21 on
both trees. The base and head were measured in the same environment, which is
what makes the comparison valid.

---

## 4. What remains unverified

- **No live browser verification.** No browser tool in this environment. The
  API boundary is proven by `TestClient`, not by a real browser session.
- **CI has not run on this commit yet.** The workflow is valid YAML and the
  steps pass locally, but "enforced" is not yet observed fact for this SHA.
- **N-ATLAS job log unread** (HTTP 403). Cause established by timing and local
  reproduction, not by the log.
- **The agent remains uncommissioned.** No delegation, no runtime credentials,
  no workspace binding, no L3, no autonomous scheduling.

---

## 5. Constraints honoured

No merge. No deployment. No commissioning. No runtime credentials. No L3
activation. No autonomous scheduling. No change to human-only authority
boundaries. No existing test removed or loosened.
