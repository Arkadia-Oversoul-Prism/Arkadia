# ARKADIA-CHIEF-001 — Gate 1 Final Reconciliation

**Head under review:** `101a1d033e7d5e0f86a82a1ad343a381fda0a396`
**Branch:** `feat/chief-agent-foundation-001`
**PR:** #657 — draft, open, not merged
**PR base:** `a1009ddfb485d60b2717b73ff7ae02c417d1ef21`
**Status:** Gate 1 remains **PENDING HUMAN ACCEPTANCE**. Not merged, not deployed, not commissioned.

This document supersedes the count claims in `GATE1_ACCEPTANCE_PACKAGE.md` (written against
`b66e8353`) and is tied to the current head. Every figure below was measured in this run
against `101a1d03`, not carried forward.

---

## 1. The two defect fixes are present at `101a1d03`

Read fresh from the working tree at `101a1d03`. Both fixes landed in `53c020e7`
("fix(executive): close two Gate 1 dispatch gaps found in acceptance review").

### (a) The dispatch guard is the first statement inside the `try`

`weaver/console_adapter.py`, lines 101–120:

```python
        sandbox = self._sandbox(root=authorized_root)
        try:
            # ── Final revocation gate (Gate 1C) ──────────────────────────────
            # Runs at the last responsible boundary, immediately before the
            # sandbox executes. An authorization that has not expired is still
            # refused if a durable revocation exists, so revoking a delegation
            # cannot leave an outstanding authorization usable. For an
            # authorization linked to an executive delegation the guard also
            # re-reads the delegation itself, so a partially-failed revocation
            # cascade cannot leave a live path.
            #
            # Deliberately INSIDE the try: a denial here is a PermissionError,
            # and the `except PermissionError` branch below is what records the
            # attempt as BLOCKED. Called outside the try, the denial escaped
            # before the attempt was ever marked, stranding it in ATTEMPTED —
            # a terminal-looking state that no later step would correct.
            assert_dispatchable(
                authorization=auth,
                revocations=self.revocations,
                registry=self.registry,
            )
```

and the branch that records the denial, lines 181–187:

```python
        except PermissionError:
            self.store.complete_execution_attempt(
                subject=subject,
                execution_attempt_id=execution_attempt_id,
                result_status="BLOCKED",
            )
            raise
```

**Confirmed.** The guard is the first statement inside the `try`; the `except PermissionError`
handler that writes `BLOCKED` is reachable from it. A denied dispatch can no longer be
stranded in `ATTEMPTED`.

### (b) A NULL credential epoch is itself a denial

`weaver/authorization_revocation.py`, lines 225–239:

```python
    # Credential epoch supersession: a suspend/revoke bumps the delegation's
    # epoch. An authorization stamped with an older epoch is dead even if its
    # own expires_at has not passed.
    #
    # A NULL issued epoch is NOT "no restriction". An authorization that names a
    # delegation but carries no epoch cannot prove which credential generation
    # it was issued under, so it must be treated as superseded. Without this,
    # any row written before the column existed — or written by a caller that
    # bypassed the auto-stamp — would silently skip the check entirely.
    issued_epoch = getattr(authorization, "delegation_epoch", None)
    current_epoch = getattr(delegation, "credential_epoch", None)
    if issued_epoch is None:
        return "delegation credential epoch missing on authorization"
    if current_epoch is not None and int(issued_epoch) != int(current_epoch):
        return "delegation credential epoch superseded"
```

**Confirmed.** `issued_epoch is None` returns a denial reason before the comparison, so a
missing epoch denies rather than bypassing supersession.

### The delegation re-read itself

`weaver/authorization_revocation.py`, lines 288–320 — the third independent check:

```python
    delegation_id = getattr(authorization, "delegation_id", None)
    if not delegation_id:
        # Not agent-associated: the two checks above are the whole contract.
        return

    if registry is None:
        from executive_office.registry import DelegationRegistry
        registry = DelegationRegistry()

    try:
        delegation = registry.get(str(delegation_id))
    except Exception as exc:  # noqa: BLE001 - any read failure must deny
        raise AuthorizationRevoked(
            f"delegation could not be verified: {type(exc).__name__}"
        ) from exc

    if delegation is None:
        raise AuthorizationRevoked("delegation record is missing")

    reason = _delegation_denial_reason(delegation, authorization=authorization, at=at)
    if reason:
        raise AuthorizationRevoked(reason)
```

---

## 2. Gate 1 tests in CI — the workflow ran and passed

**Correction to the prior report.** The previous package said the workflow "has never run on
GitHub". That is no longer true, and was already stale when written: the workflow ran on
`101a1d03`.

**Run:** `43637454454` — *Executive Office Identity and Governance*
**Conclusion:** `success` · created `2026-11-14T20:25:54Z`

| # | Step | Conclusion |
|---|---|---|
| 1 | Set up job | success |
| 2 | `actions/checkout@v4` | success |
| 3 | `actions/setup-python@v5` | success |
| 4 | Install backend dependencies | success |
| 5 | Gate 1 negative security tests | **success** |
| 6 | Gate 1 API boundary tests | **success** |
| 7 | Gate 1C dispatch revocation hardening | **success** |
| 8 | Composed OpenAPI security contract | **success** |
| 9 | The agent is not commissioned | **success** |

### Exact per-file collected counts

Measured with `python -m pytest <file> --collect-only -q | grep -c "::"`:

| Test file | Collected | CI step |
|---|---|---|
| `tests/test_executive_identity_governance.py` | **58** | step 5 |
| `tests/test_executive_api_boundary.py` | **11** | step 6 |
| `tests/test_executive_dispatch_revocation_hardening.py` | **17** | step 7 |
| `tests/test_openapi_security_production_contract.py` | **1** | step 8 |
| **Total** | **87** | |

Local confirmation of the same set:

```
$ python -m pytest tests/test_executive_identity_governance.py \
    tests/test_executive_api_boundary.py \
    tests/test_openapi_security_production_contract.py \
    tests/test_executive_dispatch_revocation_hardening.py -q -p no:randomly
87 passed, 5 warnings in 2.29s
```

**Every Gate 1 test file is covered by a step.** No Gate 1 test file is unexercised.

**The 87 split is 58 + 11 + 1 + 17.** The earlier report's "58 + 11 + 1 + 17 hardening, or
whatever the true split is" is now resolved: 17 is the hardening file, and the four sum to 87.

### Limitation on this evidence

The **per-step pass counts inside the CI run could not be read**: the job-logs endpoint
returned `HTTP 403` (the connector's token lacks `actions:read` on logs). What is proven is
that each step **concluded `success`** — a pytest step exits non-zero on any failure, so a
green step means zero failures in that file. The exact per-step pass counts are proven
locally (87 passed) and inferred in CI from the step conclusions, not read from the log text.

---

## 3. Changes between `b66e8353` and `101a1d03`

Two commits:

```
101a1d03 docs(executive): correct acceptance package counts to the committed tree
53c020e7 fix(executive): close two Gate 1 dispatch gaps found in acceptance review
```

Five files, +673 / −16:

| File | Change | What it did |
|---|---|---|
| `weaver/console_adapter.py` | M (+33/−16) | Moved `assert_dispatchable` inside the `try` so a denial records `BLOCKED`; passed `registry=self.registry` so the delegation re-read actually runs. |
| `weaver/authorization_revocation.py` | M (+13/−2) | NULL `delegation_epoch` now denies instead of skipping supersession. |
| `tests/test_executive_dispatch_revocation_hardening.py` | A (+215) | 17 adversarial tests, including the two regression tests for the defects above. |
| `.github/workflows/executive-office-identity-governance.yml` | A (+125) | The Gate 1 CI gate: four pytest steps plus the structural uncommissioned check. |
| `executive_office/GATE1_ACCEPTANCE_PACKAGE.md` | A (+303) | The acceptance package document. |

**Nothing outside Gate 1 scope was touched.** All five files are Gate 1 surfaces: the dispatch
guard, its denial logic, its tests, its CI gate, and its evidence document. No file outside
`weaver/`, `tests/`, `.github/workflows/` and `executive_office/` appears in the range.

---

## 4. No delegation, credentials, or commissioning state exists

Verified live in this run against a clean temporary store:

```
$ python3 -c "... DelegationRegistry(db_path=<tmp>); broker.issue() ..."
active_for_principal() = None
broker refused: BrokerUnavailable
```

- **Registry store:** no `eo_delegations` row is seeded anywhere. `registry.py` contains a
  single `INSERT INTO eo_delegations` at line 266 — inside the `grant()` method, reachable
  only through the Founder-only control path. There is no seed, fixture or migration that
  creates a delegation.
- **Identity record:** `executive_office/identity/identity.yaml` line 15 reads
  `lifecycle_status: "PROPOSED_NOT_COMMISSIONED"`, line 51 reads `active_delegation: false`.
  Every capability block reads `NOT_IMPLEMENTED` / `NOT_CREATED` / `NOT_DEPLOYED` /
  `NOT_CONFIGURED` / `NOT_BOUND`.
- **Broker:** refuses to issue with no active delegation (`BrokerUnavailable`), proven above.
- **CI structural check:** step 9 ("The agent is not commissioned") asserts all three of
  these on every run and **passed** in run `43637454454`.

**The agent's current status is: uncommissioned.** No delegation, no runtime credentials, no
workspace binding, no L3, no autonomous scheduling.

---

## 5. Engineering Lab and voice authorization boundaries — Gate 2 requirement

Recorded as a **Gate 2 requirement**, not a Gate 1 defect. Neither surface is covered by the
Gate 1 dispatch guard, and neither is claimed to be.

| Surface | Store | Why Gate 1 does not cover it |
|---|---|---|
| `lab/engineering_lab` | `el_authorizations` (`lab/engineering_lab/store.py:160`) | A separate authorization table with its own lifecycle. `assert_dispatchable` reads `ew_authorizations` and the executive delegation registry; it never reads `el_authorizations`. |
| `solspire/voice_router` | voice-event store via `get_voice_pipeline()` | `authorize_voice_event` / `execute_voice_event` (`solspire/voice_router.py:239`, `:248`) delegate to the voice pipeline's own store. No `delegation_id`, no epoch, no `assert_dispatchable` call. |

**Gate 2 must:** bind both stores to the delegation registry (or explicitly declare them
out of the executive agent's reachable surface), and extend the dispatch guard to cover them
before any executive delegation is granted authority that could reach either.

This is a **known, documented gap**, not a hidden one. It does not weaken Gate 1: the Gate 1
guard covers the Weaver console dispatch path, which is the path an executive delegation
would use.

---

## 6. Full-suite comparison at the current head

Both runs: clean `data/engineering_lab` removed first, `-p no:randomly`, same command, same
machine, back to back.

```
python -m pytest tests/ -q -p no:randomly --ignore=tests/test_autonomy.py
```

| Tree | Failed | Passed | Skipped | Errors | Total nodes |
|---|---|---|---|---|---|
| Base `a1009ddf` (PR base) | 178 | 3780 | 34 | 57 | 4049 |
| Head `101a1d03` | **168** | **3887** | 34 | 57 | 4146 |
| Delta | **−10** | **+107** | 0 | 0 | +97 |

**Failing-node set diff (exact node IDs, `comm` on sorted `FAILED`/`ERROR` lines):**

```
NEW failures on head (not on base):  0
FIXED (on base, not head):          10
```

**Zero new failures. Ten pre-existing failures fixed.** The +107 passed is the 87 Gate 1
tests plus 20 repo meta-tests that auto-parametrize over the new workflow file and the new
test files.

### Why the earlier figures differed

The previous package reported base 168 / head 168. That was measured against a **different
base** — `origin/main` as it stood then, not the PR's stated base `a1009ddf`. `main` has
since advanced five commits (`cb8b0dff`, `1f15bd11`, `50325158`, `691491ba`, `19697a6a`),
which changed the base's own failure set. Measured against the PR's actual base `a1009ddf`,
the base is **178 failed / 3780 passed**, and the head is **168 / 3887**.

For completeness, against **current** `origin/main` (`19697a6a`) the base measures
**178 failed / 3790 passed / 60 errors** — a different error count again, because those five
commits added tests. The PR-base comparison above is the correct one for this PR.

**`tests/test_autonomy.py` is excluded from every count** — it has a pre-existing collection
error (`ImportError: load_autonomy_config`) on the base, predates this work, and is excluded
from the baseline identically.

---

## 7. CI status on `101a1d03` — two red checks, neither branch-caused

18 workflow runs on this SHA. **16 success, 2 failure.**

### `Prism Console Contract` — failure

Failed step: *Workspace layout assertions (rendered, authenticated test identity)*.

- The branch touches **no** `web/` file. The only console-adjacent file in the diff is
  `weaver/console_adapter.py`, which is backend.
- The same workflow **also failed on `main` at `50325158`** and passed on `691491ba` and
  `19697a6a` — it is order-dependent and flaky on `main` independently of this branch.

### `N-ATLAS external beta validation` — failure

Failed job: `native-arkadia-golden-workflow` → *Execute Arkadia native N-ATLaS golden path*.

- **This is the important one to be honest about.** N-ATLAS **passed** on the immediately
  preceding commit `53c020e7` and **failed** on `101a1d03`.
- `101a1d03` is **docs-only**: `git show --name-only 101a1d03` returns exactly one file,
  `executive_office/GATE1_ACCEPTANCE_PACKAGE.md`, and no non-markdown file. A markdown-only
  commit cannot change runtime behaviour.
- The branch's N-ATLAS history is `success, success, failure, success, success, success,
  success` across eight commits — it flips without a code change, which is the signature of
  a flaky golden-path test, not a regression.
- **Conclusion: flaky, not branch-caused.** But it is **not proven** — I could not read the
  failing step's log (`HTTP 403`), so I cannot show the failure reason. It should be
  re-run before merge.

---

## 8. What is proven and what is not

### Proven in this run
- Both defect fixes are present at `101a1d03`, quoted from source.
- The Gate 1 CI workflow ran on `101a1d03` and all five steps concluded `success`.
- 87 Gate 1 tests collected and passing locally; every Gate 1 test file is covered by a step.
- Zero new test failures vs the PR base; ten pre-existing failures fixed.
- The agent is uncommissioned: no delegation, broker refuses, identity record uncommissioned.
- The Engineering Lab and voice stores are outside the Gate 1 guard (documented as Gate 2).
- Local HEAD, remote ref and PR head all read `101a1d03`.

### Not proven / not done
- **No browser verification.** No browser tool exists in this environment. The API boundary
  is proven by `TestClient`, not a live session.
- **Per-step CI pass counts not read** — job logs returned `HTTP 403`.
- **N-ATLAS failure reason unknown** — log inaccessible; flakiness inferred from the
  docs-only commit and the branch's own pass/fail history, not demonstrated.
- **`Prism Console Contract` failure not root-caused** — inferred non-branch-caused from the
  absence of `web/` changes and its flakiness on `main`.
- **`tests/test_autonomy.py` collection error not fixed** — pre-existing, excluded.
- **Not merged, not deployed, not commissioned.** No credentials issued, no L3, no scheduling.

---

## 9. Outstanding risks

1. **Gate 2 boundary gap** (§5) — `el_authorizations` and the voice store are unreachable by
   the Gate 1 guard. Must be closed before any delegation is granted authority that could
   reach them.
2. **Flaky CI** — N-ATLAS and Prism Console Contract both flip without code changes. A
   required check that fails on a docs-only commit erodes the signal the gate provides.
3. **Pre-existing suite debt** — 168 failures and 57 errors on the head, all pre-existing.
   They are not this PR's, but they mean the full suite is not a clean signal.
4. **No browser verification** of the API boundary in a live session.

---

## 10. Provenance

- Local HEAD: `101a1d033e7d5e0f86a82a1ad343a381fda0a396`
- Remote `refs/heads/feat/chief-agent-foundation-001`: `101a1d033e7d5e0f86a82a1ad343a381fda0a396`
- PR #657 head SHA: `101a1d033e7d5e0f86a82a1ad343a381fda0a396`
- All three match exactly.

**Gate 1 remains pending human acceptance. Merge, deployment and commissioning are
human-controlled.**
