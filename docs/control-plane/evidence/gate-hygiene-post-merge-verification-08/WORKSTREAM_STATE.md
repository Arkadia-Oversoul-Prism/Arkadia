# WORKSTREAM_STATE — gate-hygiene/post-merge-verification-08

## Current state

- **BASE_MAIN:** `af3a3541d9fedf8c2d38bb7a0aac56856a879523` (merge of #346)
- **Active gate:** GATE-07 (durable Weaver loop) — complete, no open PR
- **This pass:** documentation-only; no code/test/workflow mutation
- **Result:** **IMPLEMENTED** — pass-08 reconstruction + the ARK-$200K Gate 01 plan. No runtime
  change, so no runtime claim is made.

## Evidence

- `EVIDENCE.md` (this directory) — reconstruction, fingerprints, node classification, live PR
  inventory, the discovered sovereign instruction, and the credential correction.
- `docs/readiness/ARK-200K-GATE-01-PLAN.md` — the Gate 01 plan and proof-test proposal.
- Fingerprint at `af3a3541`: outcomes `f3e73647…`, ids `92d344d0…` (11 nodes) — reproduced
  byte-identically from pass-07.
- Recorded fixture: outcomes `9a54f5b4…`, ids `124bfdfd…` (10 nodes) — strict subset.
- Architecture fitness **11/11**; `tests/test_m02a_ci_gate_integrity.py` **64 passed**.
- Boot code compiles; `api/main.py` = 2434/2600. CP10 policy PASS on the staged paths.

## New sovereign instruction (this pass's selected task)

Issue **#345** (`ARK-$200K-G01 · Canonical Portfolio Substrate`) carries a `/weaver` comment
(`6043270954`, 17:32:27Z) authorizing **inspect → map → identify → plan + proof-test proposal**
and prohibiting fabrication, a parallel store, merge, and deploy. Executed as
`docs/readiness/ARK-200K-GATE-01-PLAN.md`. The instruction does not authorize committing a
substrate, so none was committed and `ARK-200K-GATE-01-EVIDENCE.md` was deliberately withheld.

## Blockers (sovereign decisions required)

1. **ARK-$200K-G01 option selection** — the plan's §7 offers A (root slice), B (commercial
   slice), C (full chain), D (defer). No Gate 01 code is written until the sovereign selects.
2. **CE-01** — `weaver/autonomy` package shadows `weaver/autonomy.py`; interrupts collection.
3. **F-01** — `test_no_firebase_persistence_in_gate` deliberately fails as a proxy invalidation.
4. **Refusal-shape (R3)** — `solspire/execution_runtime.py::execute` raises `PermissionError`
   while the R3 test expects a blocked-result (`code == "MUTATION_DISABLED"`).
5. **CP10 zero-test defect** — the SG-02 backend step runs zero tests in CI (CE-01 interrupt)
   and its enforcement step is self-satisfying. Remedy is consequential → requires authority.
6. **`provider-routing.yml` widening to `api/**`** — blocked on the baseline not being red;
   not met (11 debt nodes).

## Next bounded task (requires sovereign selection)

| option | scope | why it is held |
| --- | --- | --- |
| A | **ARK-$200K-G01 option A** — `ew_portfolios` + `ew_initiatives`, traversal proof | needs sovereign selection (§7 of the plan) |
| B | Merge **#347** (landing-headline re-pin) | verified green; sovereign merge required |
| C | Authorize the **CP10 enforcement repair** | consequential; re-arms CI |
| D | Authorize the **CE-01** module/package reconciliation | sovereign-reserved |

## Authorized action for the next heartbeat

1. Reconstruct live state (this file is a snapshot, not truth).
2. If issue #345 has a new sovereign comment selecting an option in §7 → implement that option
   as its own bounded branch with its own proof test, and produce
   `docs/readiness/ARK-200K-GATE-01-EVIDENCE.md` with real test output.
3. If #347 is merged → re-measure the node set (expect 10 nodes, fixture reproduced) and
   re-classify.
4. Otherwise → repeat the documentation-only reconstruction and **do not** select a
   consequential task without authority.

## Forbidden actions

- Merge. Push to `main`. Force-push.
- Committing Gate 01 substrate without the sovereign selecting §7.
- Producing `ARK-200K-GATE-01-EVIDENCE.md` without a real implementation SHA and test output.
- Fabricating portfolio, financial, vendor, contract, or outcome data.
- Weakening or re-pinning a governance boundary (F-01, R3) as "hygiene".
