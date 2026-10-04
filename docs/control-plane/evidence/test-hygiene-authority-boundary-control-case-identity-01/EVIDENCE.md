# test-hygiene/authority-boundary-control-case-identity-01 — SH-08

**BASE_MAIN**: `ddc08f86e0c6f600b8e5e3eb5822ac2b79606d72` (`governance: recognize Console evidence and verification routes`)
**Branch**: `gate-hygiene/authority-boundary-control-case-identity-01`
**Workstream**: `gate-hygiene` -> baseline test-debt drain
**Queue item**: `SH-08` (recorded in `BASELINE_TEST_DEBT_CLASSIFICATION.md` by the
`gate-hygiene-boundary-ruling-verification-and-queue-reconciliation-01` pass, PR #260)
**Scope**: test-side assertion only. No production source, no governance surface,
no authority path, no workflow, no `api/main.py`.

## Objective (bounded)

Repair the single stale control-case assertion in
`tests/test_authority_api_enterprise_boundary.py`. The module contract now requires an
authenticated `actor_identity` on `EdenOps.decide_proposal(..., action="APPROVE")` -- an
`actor` string is provenance text, not proof of authority (`solspire/eden_ops.py:340`).
The control-case call still passes only `actor=`, so it raises *before* reaching the
assertions it owns.

## Defect class

`STALE_ASSERTION`: the test exercises the correct surface (the authority boundary), but
calls it with the pre-reconciliation signature. The fix is to supply the authenticated
identity the contract requires -- never to relax the contract.

## Change (one call site)

`tests/test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records`

```diff
         actor="authorized-subject",
+        actor_identity={
+            "uid": "authorized-subject",
+            "role": "Flamekeeper",
+            "access_level": 0,
+        },
     )
```

The identity is exactly the one the sibling test
(`tests/test_upstream_causal_continuity_01.py:86`) already uses for its authorized
control case, and the same one the same file's bridge assertion already uses -- the
`uid` matches `actor` and the role holds `Govern` (`Flamekeeper`), so the call reaches
its own assertions.

## Verification (run on this tree)

```
python -m py_compile api/main.py                                                 -> OK (untouched, 2582 / 2600)
python -m pytest tests/test_authority_api_enterprise_boundary.py -q               -> 3 passed
python -m pytest tests/test_authority_api_enterprise_boundary.py \
  tests/test_upstream_causal_continuity_01.py -q                                  -> 6 passed
python -m pytest tests/architecture -q                                            -> 11 passed
```

## Node-set delta (attribution is by node set, never by count)

| suite | baseline `main` @ `ddc08f8` | this head |
|---|---|---|
| `test_authority_api_enterprise_boundary.py` | 2 failed / 1 passed | **3 passed** |
| full suite (`--continue-on-collection-errors`) | 10 failed / 1412 passed / 20 skipped / 1 error | **9 failed / 1413 passed / 20 skipped / 1 error** |

Node-set delta by name: **−1** (`test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records`), **+0** added. The repaired node is removed from the failure set; every other baseline failure is unchanged and untouched.

### Baseline node set (measured locally at `ddc08f8`)

```
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_compress_to_choices
ERROR tests/test_autonomy.py
```

Note: a bare environment without `fastapi`/`pytest-asyncio` also reports
`test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge` as
failing. That is a dependency-collection artifact, not repository debt: with the
repository's own `requirements.txt` installed plus `pytest-asyncio`, the node passes and
the file's only real failure is the SH-08 control case. Reproduce with the full
dependency set before attributing either node.

## Regression boundary

Test-only, one call site. The repository's live baseline fingerprint
(`tests/fixtures/baseline_node_set.txt`, 18 nodes) is not the same set this environment
measures (11 nodes) -- a known clone/environment delta recorded in the classification
ledger, not created here. This change adds no node and removes exactly one (the repaired
one); the two suites above are the direct regression boundary and they pass.

## Authority boundary

- No merge, no push to `main`, no force-push.
- No production code, no governance/authority path, no constitutional surface touched.
- No product decision required: the contract is implemented; the test now exercises it.
- Merge is the sovereign's act.
