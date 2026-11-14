# Gate 1 Evidence Reconciliation — ARKADIA-CHIEF-001

**Mission:** Gate 1 security and evidence reconciliation.
**Branch:** `feat/chief-agent-foundation-001`
**PR:** #657 (draft, open — updated, not duplicated)
**Status:** Gate 1 remains **pending human acceptance**. The agent remains **uncommissioned**.

---

## 1. What this run changed

The Gate 1C revocation cascade revokes the delegation **first**, then writes
authorization revocations. If that second write fails, the revocation ledger has
no record and an unexpired authorization would otherwise still dispatch. The
dispatch guard checked authorization expiry and the revocation ledger, but never
re-read the linked delegation.

**Root cause (deeper than the reported symptom):** the `Authorization` record did
not carry its delegation linkage at all. `authorize()` persisted `delegation_id`
to the row, but the dataclass had no such field and `authorization()` never read
it back — so the guard could not have seen the delegation even if it had tried.

| File | Change |
|---|---|
| `weaver/enterprise_orchestration.py` | `Authorization` gains `delegation_id` + `delegation_epoch`, read back on every load; `delegation_epoch` column added and auto-stamped at issuance; unresolvable delegation refuses authorization |
| `weaver/authorization_revocation.py` | `assert_dispatchable` adds a third independent check: re-read the delegation, deny on status/expiry/epoch/missing/read-error |
| `weaver/console_adapter.py` | Registry wired into the dispatch guard at the last responsible boundary |
| `tests/test_executive_dispatch_revocation_hardening.py` | **New**, 14 adversarial tests |

---

## 2. Authorization linkage — every creation path

`ew_authorizations` rows are created in exactly **one** place:
`EnterpriseOrchestrationStore.authorize()` (`weaver/enterprise_orchestration.py`).

| Caller | Persists `delegation_id`? |
|---|---|
| `solspire/eden_ops.py:381` | Yes — passes through `authorize()`; `delegation_id` defaults to `None` (not agent-associated) |
| `weaver/enterprise_orchestration.py:1040` (Eden pilot) | Yes — same path, `None` |
| `api/executive_routes.py` | No direct creation; delegates to the store |
| `solspire/voice_router.py:242` | **Not an `ew_authorizations` path** — `get_voice_pipeline().authorize()` is a separate voice-event pipeline with its own store. Confirmed by reading the route and the pipeline call. |

**Result:** one creation path, and it now persists both `delegation_id` and
`delegation_epoch`. No path was found that creates an `ew_authorizations` row
without going through `authorize()`.

---

## 3. Adversarial tests — 14, all passing

Command:
```
python -m pytest tests/test_executive_dispatch_revocation_hardening.py -q
→ 14 passed
```

| # | Test | Asserts |
|---|---|---|
| 1 | `test_revoked_delegation_denies_even_when_revocation_write_fails` | **The exact reported gap.** Delegation REVOKED, `revoke_for_delegation` raises, ledger clean (`is_revoked` → False), dispatch still denied |
| 2 | `test_suspended_delegation_denies_unexpired_authorization` | Suspended delegation, authorization unexpired → denied |
| 3 | `test_delegation_expiring_before_authorization_denies` | Delegation expires at T+60, authorization at T+7200, dispatch at T+120 → denied |
| 4 | `test_credential_epoch_supersession_denies` | Suspend→reactivate bumps epoch; delegation ACTIVE again, authorization valid by its own expiry → denied |
| 5 | `test_revocation_racing_queued_dispatch_denies` | Stale authorization object loaded before revocation → denied at the gate |
| 6 | `test_registry_unavailable_denies` | Registry read raises → denied |
| 7 | `test_missing_delegation_record_denies` | Delegation row deleted → denied |
| 8 | `test_revocation_store_unavailable_denies` | Revocation store read raises → denied |
| 9 | `test_authorization_persists_delegation_id` | Linkage survives a fresh store read |
| 10 | `test_authorization_auto_stamps_current_epoch` | Epoch stamped at issuance |
| 11 | `test_authorization_without_delegation_has_null_linkage` | Non-agent rows stay NULL |
| 12 | `test_unresolvable_delegation_refuses_authorization` | Cannot mint an unverifiable linkage |
| 13 | `test_active_delegation_permits_dispatch` | Happy path still works |
| 14 | `test_non_agent_authorization_unaffected_by_registry` | Non-agent auth never reads the registry |

---

## 4. Mutation testing — the guards are load-bearing

Each mutation was applied, the suite run, then the file restored byte-identically.

| Mutation | Result |
|---|---|
| Disable the delegation re-read (`delegation_id = None`) | **6 failed**, 8 passed |
| Remove the credential-epoch check | **1 failed** (`test_credential_epoch_supersession_denies`) |
| Remove the status check | **2 failed** (the cascade-failure test + suspended test) |

---

## 5. Reconciled numbers — and why the earlier figures were wrong

### 5.1 File count: **26 is correct**

The earlier report said **17 files changed**. GitHub reported **26**.

- **17** was the file count of the **last commit only** (`git show --stat HEAD` → `17 files changed, 2853 insertions(+), 6 deletions(-)`).
- **26** is the count against the report's own stated base, `a1009ddfb485d60b2717b73ff7ae02c417d1ef21`:

```
git diff --stat a1009ddfb485d60b2717b73ff7ae02c417d1ef21..HEAD
→ 26 files changed, 3855 insertions(+), 6 deletions(-)
git diff --name-only a1009ddfb485d60b2717b73ff7ae02c417d1ef21..HEAD | wc -l
→ 26
```

**Why the error:** the report quoted the single-commit stat as if it were the
branch stat. The branch carries the Gate 0 documentation commits plus the Gate 1
commit, so the branch diff is larger than the last commit. GitHub's 26 is right;
the report's 17 was a mis-scoped `git show` rather than a `git diff <base>..HEAD`.

Note: `a1009ddf` is **not** an ancestor of the local `main` tip (`cd8914d5`), so
diffing against local `main` gives a different, larger number (48) that includes
unrelated main-side work. The correct comparison is against the stated base.

### 5.2 Test count: **70 is correct, but the split was wrong**

The earlier report claimed **58 + 12 + 3 = 73** while also saying "70 new tests" —
the three figures did not even sum to its own total.

Actual, measured this run:

| Command | Report claimed | Actual |
|---|---|---|
| `pytest tests/test_executive_identity_governance.py -q` | 58 | **58 passed** |
| `pytest tests/test_executive_api_boundary.py -q` | 12 | **11 passed** |
| `pytest tests/test_openapi_security_production_contract.py -q` | 3 | **1 passed** |
| **Total collected** | 70 | **70 collected** |

```
python -m pytest tests/test_executive_identity_governance.py \
                 tests/test_executive_api_boundary.py \
                 tests/test_openapi_security_production_contract.py --collect-only -q
→ 70 tests collected
```

**Why the error:** the total (70) was right; the per-file split was not. The
`test_openapi_security_production_contract.py` file already had 1 test at the
base and gained 1 more, not 3. The `test_executive_api_boundary.py` file is new
and has 11 tests, not 12. The report appears to have carried forward an
intermediate count from before the final test files were trimmed.

### 5.3 Full-suite delta

```
python -m pytest tests/ -q -p no:randomly --ignore=tests/test_autonomy.py
```

| | Baseline (`18ae97da`) | After (`348a5961`) | Δ |
|---|---|---|---|
| failed | 171 | 171 | 0 |
| passed | 3856 | **3870** | **+14** |
| skipped | 34 | 34 | 0 |
| errors | 57 | 57 | 0 |

**+14 passed, failing-node set identical.** The 14 new tests are the only change.

---

## 6. Provenance

| Field | Value |
|---|---|
| Branch | `feat/chief-agent-foundation-001` |
| Commit (this run) | `348a596107c3f627c8c797b14ac52b1b67add440` |
| Parent | `18ae97da7e3e1d00c977801ee589165284191808` (Gate 1, unchanged) |
| Stated base | `a1009ddfb485d60b2717b73ff7ae02c417d1ef21` |
| PR | #657 — draft, open, head updated to `348a5961` |

The remote ref is verified to match the local SHA exactly (see §8).

---

## 7. Implemented / tested / unverified

| | Status |
|---|---|
| **Implemented** | ✅ Delegation re-read at dispatch; epoch stamping; linkage persistence; registry wiring; 14 adversarial tests |
| **Tested** | ✅ 14/14 new; 58/58 existing Gate 1; full-suite delta clean; 3 mutation checks redden the suite |
| **Browser verified** | ❌ No browser tool in this environment — the API boundary is proven by `TestClient`, not a live session |
| **Accepted** | ❌ Pending human acceptance |
| **Merged** | ❌ Not merged |
| **Deployed** | ❌ Not deployed |
| **Commissioned** | ❌ Not commissioned — no delegation, no credentials, no workspace binding, no L3, no scheduling |

---

## 8. Remaining limitations

1. **`tests/test_autonomy.py` has a pre-existing collection error** on the base
   (`ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'`
   — a package/directory shadowing issue). It predates this work, is excluded
   from all counts above, and was excluded from the baseline too. Not fixed here.
2. **No browser verification** — no browser tool exists in this sandbox.
3. **The 171 failures / 57 errors are pre-existing** on the base and byte-identical
   before and after; they are not caused by this change.
4. **No PR comment posted** — the connector exposes no comment/update-PR tool; the
   head updated automatically on push.

---

## 9. Constraints honoured

- No merge, no deployment, no production configuration change.
- No commissioning, no credential issuance for an active runtime, no L3 activation,
  no autonomous scheduling.
- No changes to human-only authority boundaries.
- Existing approval, Weaver, WorkEvent and Evidence chains preserved.
- No existing test weakened or deleted.
