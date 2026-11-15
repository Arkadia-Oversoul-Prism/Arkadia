# Gate 2 — Revocation Consistency Proof

**ARKADIA-CHIEF-001 · branch `feat/chief-agent-foundation-001` · draft PR #657**

Gate 1 is accepted with limitations. This is separately scoped work: prove that
revocation works consistently across **every** route through which delegated
work can actually execute — not only the Weaver boundary Gate 1 hardened.

The agent remains **uncommissioned**. No delegation exists outside a test's
temporary database. No merge, no deploy, no credentials, no L3, no scheduling.

---

## 1. Every delegated execution route

Four routes can execute work. Gate 1 covered one.

| # | Route | Authorization record | Delegation status | Credential epoch | Revocation ledger | Gate |
|---|---|---|---|---|---|---|
| 1 | `weaver/console_adapter.py` `dispatch` | `ew_authorizations` | ✅ Gate 1 | ✅ Gate 1 | ✅ Gate 1 | 1 |
| 2 | `lab/engineering_lab/runtime.py` `_require_authorization_for` | `el_authorizations` | ❌ → ✅ | ❌ → ✅ | n/a (own table) | **2** |
| 3 | `api/lab_routes.py` `POST /engineering/n-atlas/run` | `el_authorizations` | ❌ → ✅ | ❌ → ✅ | n/a | **2** |
| 4 | `solspire/voice_pipeline.py` `execute` | `ew_authorizations` | ❌ → ✅ | ❌ → ✅ | ❌ → ✅ | **2** |

**Route 3 was the worst gap.** `/n-atlas/run` drives a model call directly and
checked only `session["state"] in ("AUTHORIZED","QUEUED")`. It never consulted
the authorization record at all — so a session whose grant had been revoked,
expired or consumed still executed, and a revoked delegation was invisible to
it. It now calls the same gate as every other path.

**Route 4** authorized through the canonical console authority router, so its
`Authorization` is an enterprise row that can carry a delegation linkage — but
`execute()` never called the guard. It now does, before the executor runs.

**Route 2** had a strong grant gate (revoked/expired/consumed, session scoping,
operation naming) but no delegation awareness whatsoever.

### Routes deliberately out of scope

- `solspire/voice_pipeline.py` `_execute_observation` — observation-only
  (knowledge search). It mints no authorization and executes no delegated work;
  it is a read, recorded as evidence. Not a delegated execution route.
- `lab/engineering_lab/runtime.py` `execute_agent_loop` — reaches the same
  `_require_authorization_for` gate as `execute_bounded_task`, so it is covered
  by route 2's fix without a separate change.

---

## 2. One consistent contract

Rather than let three routes grow three copies of the status/expiry/epoch
rules — which is exactly how contracts drift — there is now **one function**:

```python
weaver/authorization_revocation.py::assert_delegation_dispatchable(
    *, delegation_id, delegation_epoch, registry=None, now=None
)
```

- `assert_dispatchable` (Weaver) **delegates to it** — its inline copy was
  removed, so Weaver and the other routes cannot diverge.
- The Lab gate calls it and re-raises as `BoundaryViolation`, the type every
  Lab caller already handles.
- Voice calls `assert_dispatchable` directly, so it gets all three checks.

A `delegation_id` of `None` returns immediately: a plain human authorization is
not agent-associated and must not acquire a delegation requirement. This is
tested (`test_lab_dispatch_ignores_a_plain_human_grant`).

### The cascade now withdraws Lab grants too

`executive_office/revocation.py` previously withdrew only `ew_authorizations`.
It now also calls `EngineeringLabStore.revoke_for_delegation`, which stamps
`revoked_at` on every `el_authorizations` row carrying that `delegation_id`.

This is **belt and braces**: the dispatch guard re-reads the delegation and
would refuse anyway, but a withdrawn grant is *recorded* as revoked rather than
merely refused. A failure in the Lab withdrawal is **reported, not swallowed**
(`lab_revocation_error`) and does not roll back the delegation revocation —
the delegation is already REVOKED, which is the safe direction.

---

## 3. Tests — 22, all passing

```
$ python -m pytest tests/test_gate2_revocation_consistency.py -q
22 passed, 2 warnings in 0.69s
```

Coverage by route and failure mode:

| Failure mode | Shared contract | Lab route | Weaver |
|---|---|---|---|
| Active delegation permits | ✅ | ✅ | ✅ |
| Revoked | ✅ | ✅ | ✅ |
| Suspended | ✅ | ✅ | — |
| Expired | ✅ | — | — |
| Superseded epoch | ✅ | ✅ | — |
| Missing epoch (NULL) | ✅ | — | — |
| Missing record | ✅ | — | — |
| Registry unavailable at dispatch | ✅ | ✅ | — |
| Plain human grant unaffected | ✅ | ✅ | — |
| Cascade withdraws Lab grants | — | ✅ | — |
| Cascade idempotent | — | ✅ | — |
| Cascade reports Lab failure | — | ✅ | — |

Plus three wiring assertions proving each route actually reaches its guard.

### Mutation testing — every guard is load-bearing

| Mutation | Result |
|---|---|
| Remove the Lab delegation guard | **4 tests redden** |
| Remove the voice `assert_dispatchable` call | **1 test reddens** |
| Remove the N-ATLAS gate call | **1 test reddens** |

Files restored byte-identically after each.

**One test was strengthened during this work.** The voice wiring test
originally asserted `"assert_dispatchable" in source` — which passed even with
the call deleted, because the module *imports* the name. It now asserts the
call site (`assert_dispatchable(authorization=`), and the mutation above proves
it fails when the call is removed. A test that cannot fail is not a test.

---

## 4. Full suite

Controlled clean-state runs, back to back, `data/engineering_lab/` removed
before each:

```
$ python -m pytest tests/ -q -p no:randomly --ignore=tests/test_autonomy.py
```

| Tree | Failed | Passed | Skipped | Errors |
|---|---|---|---|---|
| Base `3eba3a39` | 168 | 3887 | 34 | 57 |
| Head | **168** | **3909** | 34 | 57 |

**Failing-node set diff: `IDENTICAL` — zero new, zero removed.**
The +22 is exactly the new Gate 2 tests.

Gate 1 suite unchanged: **87 passed**.

---

## 5. What is proven, and what is not

**Proven**
- All four execution routes now consult the delegation contract.
- Revoked / suspended / expired / missing / superseded / unreadable all deny,
  on every route, demonstrated by test.
- The cascade withdraws Lab grants as well as Weaver's.
- The guards are load-bearing (mutation-tested).
- No new failures; the pre-existing 168/57 are byte-identical.

**Not proven**
- **No live browser verification.** No browser tool exists in this sandbox.
  The API boundary is proven by `TestClient` and direct calls, not a session.
- **The voice route's guard is proven by wiring assertion, not end-to-end
  execution.** Driving a full voice event through ingest → ASR → intent →
  proposal → approval → authorize → execute requires an ASR provider and a
  human approval chain; the guard's *behaviour* is proven on the shared
  contract and on the Lab route, and its *presence* on the voice route.
- **`tests/test_autonomy.py` has a pre-existing collection error**
  (`ImportError: load_autonomy_config`) on the base. Excluded from all counts
  and from the baseline identically. Not fixed — reported.
- **`test_native_natlas_route_live_external_gradio` fails in this sandbox**
  for a missing `pytest-asyncio` plugin, not for a code reason. Verified
  pre-existing by stashing the work and re-running. It is opt-in
  (`N_ATLAS_LIVE_TEST=1`) and skipped in CI.

---

## 6. Remaining risks

1. **`el_authorizations` has no revocation ledger of its own.** The Lab relies
   on the delegation re-read plus the cascade's `revoked_at` stamp. There is no
   append-only ledger equivalent to `ew_authorization_revocations`. If a Lab
   grant were revoked *and* the delegation record were later deleted, the
   re-read would deny (missing record) — so the boundary holds — but the audit
   trail is weaker than Weaver's. **Gate 3 candidate.**
2. **The voice route's `_blocked` path records an attempt only when an
   authorization exists.** A refusal before authorization is recorded as
   evidence with a `voice-event:` source ref instead. That is the existing
   design, unchanged here.
3. **`assert_delegation_dispatchable` imports `DelegationRegistry` lazily.**
   A missing `executive_office` package would raise `ImportError` rather than
   `AuthorizationRevoked`. In practice the package is in-tree; noted for
   completeness.

---

## 7. Status

- **implemented ✅ · tested ✅ · mutation-verified ✅ · browser-verified ❌**
- **Not merged, not deployed, not commissioned.**
- **No delegation, no credentials, no workspace binding, no L3, no scheduling.**
- Human-only authority boundaries unchanged. Approval, Weaver, WorkEvent and
  Evidence chains preserved.
