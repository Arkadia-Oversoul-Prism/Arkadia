# ARKADIA-CHIEF-001 — Gate 1 Acceptance Package

**Status: PENDING HUMAN ACCEPTANCE.** Nothing here is merged, deployed or commissioned.

| Field | Value |
|---|---|
| Branch | `feat/chief-agent-foundation-001` |
| Head at review start | `b66e8353` |
| Base | `main` @ `a1009ddf` (stated base) |
| PR | #657 — draft, open |
| Review type | Independent acceptance review, not a self-report |

This document is the acceptance package requested by the Gate 1 acceptance
review. It reports what an independent inspection of the branch found, including
**two real defects the previous evidence report did not disclose**, and the
corrections applied.

---

## 1. Independent inspection of the five changed files

Read fresh from the branch at `b66e8353`. The five files changed by the previous
run (`15e8872f..b66e8353`) are:

| File | What it actually does | Matches the report? |
|---|---|---|
| `weaver/authorization_revocation.py` | `AuthorizationRevoked` (a `PermissionError`); `AuthorizationRevocationStore` (durable ledger, `is_revoked`, `revoke_for_delegation`); `_delegation_denial_reason`; `assert_dispatchable` — three independent fail-closed checks. | Yes, with one gap (§3) |
| `weaver/console_adapter.py` | `WeaverConsoleAdapter.dispatch` — the last responsible boundary. Calls `assert_dispatchable` immediately before the sandbox runs. | **No** — the call sat outside the `try` (§2) |
| `weaver/enterprise_orchestration.py` | `EnterpriseOrchestrationStore.authorize()` persists `delegation_id` + auto-stamps `delegation_epoch`; `authorization()` reads both back. | Yes |
| `tests/test_executive_dispatch_revocation_hardening.py` | 14 adversarial tests over the guard. | Yes, but incomplete (§3) |
| `executive_office/GATE1_EVIDENCE_RECONCILIATION.md` | The prior evidence report. | **No** — file count and test split were wrong (§5) |

---

## 2. FINDING 1 — the guard ran outside the `try`, stranding denied attempts

**Severity: high.** The guard denied correctly, but the denial escaped before the
attempt was recorded.

`assert_dispatchable` raises `PermissionError`. In `console_adapter.py` it was
called **before** the `try:` block, while the `except PermissionError:` branch
that marks the attempt `BLOCKED` lives **inside** it. A denied dispatch therefore
raised out of `dispatch()` with the attempt still in `ATTEMPTED` — a state that
reads as "execution started" and that no later step corrects.

Reproduced before the fix:

```
DENIED as expected: delegation is suspended
attempt result_status after denial = 'ATTEMPTED'
FINDING 1 CONFIRMED: guard denied, but the attempt is stranded in ATTEMPTED
  -> the `except PermissionError:` BLOCKED branch never ran
```

**Fix:** the guard now runs as the first statement inside the `try`, so a denial
is recorded as `BLOCKED`. The sandbox is still constructed before the guard, so
the guard remains the last thing to run before execution.

**Regression test:** `test_denied_dispatch_marks_attempt_blocked`.

---

## 3. FINDING 2 — a NULL credential epoch bypassed supersession

**Severity: high.** The supersession check was conditional on the epoch being
present, so an absent epoch meant "no restriction" rather than "cannot prove".

```python
# before
if issued_epoch is not None and current_epoch is not None:
    if int(issued_epoch) != int(current_epoch):
        return "delegation credential epoch superseded"
```

An authorization naming a delegation but carrying a NULL epoch — a row written
before the column existed, or by any caller that bypassed the auto-stamp —
skipped the check entirely and dispatched against a delegation whose epoch had
since been bumped by a suspend.

Reproduced before the fix:

```
reloaded.delegation_id='eodel-3a49de93...' delegation_epoch=None
delegation status=ACTIVE epoch=3
FINDING 6 CONFIRMED: dispatch ALLOWED with a NULL epoch on a bumped delegation
```

**Fix:** a NULL issued epoch is now itself a denial
(`"delegation credential epoch missing on authorization"`).

**Regression test:** `test_null_epoch_on_linked_authorization_denies`.

---

## 4. Dispatch boundary trace — every route into execution

The review asked whether the re-read happens at the *actual* last boundary, and
whether any route reaches execution without it.

| Route | Reaches the guard? | Notes |
|---|---|---|
| `WeaverConsoleAdapter.dispatch` | **Yes** | The only path that runs a sandbox. Guard is the first statement in the `try`, immediately before tool execution. |
| `solspire/console_authority_router.py` | **Yes** | Delegates to the adapter; does not execute directly. |
| `lab/engineering_lab/*` | **N/A — separate system** | Uses its own `el_authorizations` table, not `ew_authorizations`. Out of Gate 1 scope; flagged as a boundary to revisit in Gate 2. |
| `solspire/voice_router.py:242` | **N/A — separate pipeline** | Voice-event store, not `ew_authorizations`. Confirmed by reading the route and its pipeline call. |

**No route was found that reaches execution without the re-read.** The adapter is
the single execution chokepoint.

---

## 5. Registry unavailable *between* load and dispatch

The review asked for the harder case: the authorization loads cleanly and the
registry only fails at dispatch.

**Behaviour, precisely:** the guard calls `registry.get(delegation_id)` inside a
`try` that catches **any** exception and re-raises `AuthorizationRevoked`
(`"delegation could not be verified: OperationalError"`). The caller sees a
denial, not an infrastructure error it might retry past. **No work is queued and
nothing executes** — the guard runs before the sandbox is used. The attempt is
recorded `BLOCKED`. **Fail-closed.**

**Test:** `test_registry_unavailable_between_load_and_dispatch_denies` — loads the
authorization, then monkeypatches `registry.get` to raise `OperationalError`,
asserts `AuthorizationRevoked` and `result_status == "BLOCKED"`.

---

## 6. CI coverage — the tests ran in NO workflow

**Severity: high.** The Gate 1 suite was green locally and **unenforced in CI**.

- `tests/test_executive_identity_governance.py`, `tests/test_executive_api_boundary.py`
  and `tests/test_executive_dispatch_revocation_hardening.py` were named by **no**
  workflow file.
- `executive_office/**` appeared in **no** path filter.
- The workflows that do run pytest (`weaver-mvp2-validation.yml`,
  `prism-execution-workevent-governance.yml`) select explicit file lists that do
  not include them.

A regression in the delegation registry, the broker, the token validator or the
dispatch guard would have merged with every required check green.

**Fix:** added `.github/workflows/executive-office-identity-governance.yml` —
runs on PRs and pushes to `main` touching any of the guard's surfaces, with four
pytest steps plus a structural **"the agent is not commissioned"** step that
asserts no delegation exists, the broker refuses to issue, and the identity
record still declares `PROPOSED_NOT_COMMISSIONED`. That step was executed locally
and passes.

---

## 7. Test results — exact commands and counts

```bash
# Gate 1 suite (all four files)
python -m pytest tests/test_executive_identity_governance.py \
                 tests/test_executive_api_boundary.py \
                 tests/test_executive_dispatch_revocation_hardening.py \
                 tests/test_openapi_security_production_contract.py -q
# → 86 passed
```

| File | Collected |
|---|---|
| `test_executive_identity_governance.py` | 58 |
| `test_executive_api_boundary.py` | 11 |
| `test_executive_dispatch_revocation_hardening.py` | **17** (14 + 3 new) |
| `test_openapi_security_production_contract.py` | 1 |
| **Total** | **87 collected / 86 passed** |

### Full suite — controlled, clean-state comparison

Both runs executed back-to-back with `data/engineering_lab/` removed first, since
that directory accumulates state across runs and contaminates counts.

```bash
python -m pytest tests/ -q -p no:randomly --ignore=tests/test_autonomy.py
```

| | Failed | Passed | Skipped | Errors | Collected |
|---|---|---|---|---|---|
| Base (`b66e8353` without this run's changes) | 168 | 3877 | 34 | 57 | 4135 |
| Head (with this run's changes) | **168** | **3887** | 34 | 57 | **4145** |

**Failing-node set diff: `IDENTICAL` — zero new, zero removed** (225 nodes each).

**Delta fully reconciled — all 10 new nodes named.** `comm` on the collected node
lists shows exactly 10 nodes present at head and absent at base, and **zero**
present at base and absent at head:

| New node | Origin |
|---|---|
| `test_executive_dispatch_revocation_hardening.py::test_denied_dispatch_marks_attempt_blocked` | this run |
| `test_executive_dispatch_revocation_hardening.py::test_null_epoch_on_linked_authorization_denies` | this run |
| `test_executive_dispatch_revocation_hardening.py::test_registry_unavailable_between_load_and_dispatch_denies` | this run |
| `test_ci_gate_trigger_coverage.py::test_architecture_fitness_is_selected_by_the_surfaces_it_judges[executive-office-identity-governance.yml]` | repo meta-test, auto-parametrized |
| `test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[...]` | repo meta-test |
| `test_ci_gate_trigger_coverage.py::test_push_and_pull_request_filters_are_identical[...]` | repo meta-test |
| `test_ci_suite_collection_continuation.py::test_every_broad_suite_step_reaches_the_suite[...]` | repo meta-test |
| `test_ci_suite_collection_continuation.py::test_judging_broad_suite_steps_continue_past_collection_errors[...]` | repo meta-test |
| `test_gate_filter_selection.py::test_executed_files_are_selected_or_the_workflow_is_unfiltered[...]` | repo meta-test |
| `test_workflow_injection_boundary.py::test_no_workflow_interpolates_untrusted_event_text_into_run[...]` | repo meta-test |

The 7 meta-test nodes are **not** tests I wrote. The repository already contains
architecture-fitness tests that parametrize over every workflow file; adding
`executive-office-identity-governance.yml` caused them to generate a new case for
it. **All 7 pass** — so the new workflow is now judged by the repo's own CI
governance suite (trigger coverage, filter symmetry, injection boundary, broad-suite
continuation) and satisfies it. That is independent corroboration that the CI fix
is well-formed, not merely syntactically valid.

> **Correction to an earlier figure.** A first pass reported head as
> `169 failed / 3886 passed`. That run was contaminated by
> `data/engineering_lab/agent_events.jsonl` left by the probe script. The
> controlled re-run above is authoritative: **168 failed / 3887 passed**.

---

## 8. Failure-injection evidence (mutation testing)

Each guard was disabled in turn; the suite was re-run; the file was restored
byte-identically.

| Mutation | Tests reddened |
|---|---|
| Guard moved back outside the `try` | `test_denied_dispatch_marks_attempt_blocked` (1) |
| NULL epoch skips supersession | `test_null_epoch_on_linked_authorization_denies` (1) |
| Delegation re-read disabled | 6 |
| Epoch check removed | 1 |
| Status check removed | 2 |

Every guard is load-bearing.

---

## 9. File-count reconciliation — 26 vs 17 vs 31

The review noted GitHub reported 26 changed files while the report said 17.

**Both were right about different things, and the report was wrong to present 17
as the branch total.**

| Measurement | Command | Result |
|---|---|---|
| Last commit only | `git show --stat HEAD` | **17 files** |
| Cumulative vs stated base | `git diff --name-only a1009ddf..HEAD` | **26 files** (at `18ae97da`) |
| Cumulative vs stated base, now | `git diff --name-only a1009ddf..HEAD` | **31 files** (at `b66e8353`) |

The report quoted a **last-commit** stat as if it were a **branch** stat. GitHub
was correct. The branch has since grown to 31 files across 18 commits.

---

## 10. Provenance

- PR #657 head verified at `b66e8353` via `GITHUB_GET_A_REFERENCE` and
  `git ls-remote` — exact match to local HEAD.
- No git credentials in the sandbox; pushes used a temporary write-enabled deploy
  key, deleted immediately after, with the remote ref read back and confirmed.

---

## 11. What is proven, and what is not

| Claim | Status |
|---|---|
| Guard denies on revoked / suspended / expired / superseded / missing / unreadable | **Tested** |
| Guard runs at the last responsible boundary | **Tested** (trace + regression test) |
| Denied dispatch records `BLOCKED` | **Tested** |
| NULL epoch denies | **Tested** |
| Registry failure between load and dispatch denies | **Tested** |
| Tests run in required CI | **Configured, not yet observed running** — the workflow is new; it has not executed on GitHub |
| Browser verification | **NOT DONE** — no browser tool in this environment |
| Agent is uncommissioned | **Tested** (structural CI step, passes locally) |
| Merged / deployed / accepted | **NO** — human-controlled |

### Known limitations and outstanding risks

1. **The new CI workflow has never run on GitHub.** It is valid YAML and its
   steps pass locally, but "the tests are now enforced" is not yet observed fact.
2. **No browser verification.** The API boundary is proven by `TestClient`, not a
   live session.
3. **`tests/test_autonomy.py` has a pre-existing collection error**
   (`ImportError: load_autonomy_config`) on the base. Excluded from all counts,
   excluded from the baseline too. Not fixed — reported.
4. **The 168 failures / 57 errors are pre-existing** and byte-identical before and
   after.
5. **`lab/engineering_lab` uses a separate authorization table** (`el_authorizations`).
   It is out of Gate 1 scope but is a boundary that Gate 2 must address.
6. **The agent remains uncommissioned.** No delegation, no credentials, no
   workspace binding, no L3, no scheduling.

---

## 12. Constraints honoured

No merge. No deployment. No commissioning. No credential issuance for an active
runtime. No L3 activation or autonomous scheduling. No change to human-only
authority boundaries. Approval, Weaver, WorkEvent and Evidence chains preserved.
No existing test weakened or deleted — the only test file changed gained tests.
