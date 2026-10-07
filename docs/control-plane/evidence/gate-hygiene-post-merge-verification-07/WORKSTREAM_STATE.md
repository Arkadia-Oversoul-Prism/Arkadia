# WORKSTREAM_STATE — gate-hygiene/post-merge-verification-07

## Current state

- **BASE_MAIN:** `af3a3541d9fedf8c2d38bb7a0aac56856a879523` (merge of #346)
- **Active gate:** GATE-07 (durable Weaver loop) — **complete, no open PR**
- **This pass:** artifact-only reconstruction; no code/test/workflow mutation
- **Result:** **IMPLEMENTED** (reconstruction + two ledger corrections; no runtime change
  to prove)

## Evidence

- `EVIDENCE.md` (this directory) — full reconstruction, fingerprints, node classification,
  live PR inventory, proposal dispositions.
- Fingerprint at `af3a3541`: outcomes `f3e73647…`, ids `92d344d0…` (11 nodes).
- Recorded fixture: outcomes `9a54f5b4…`, ids `124bfdfd…` (10 nodes) — strict subset.
- Architecture fitness: **11/11**. `tests/test_m02a_ci_gate_integrity.py`: **64 passed**.
- Boot code compiles; `api/main.py` = 2434/2600.
- CP10 policy: PASS on this pass's paths.

## Blockers (sovereign decisions required)

1. **CE-01** — `weaver/autonomy` package shadows `weaver/autonomy.py`; interrupts test
   collection. Reserved to the sovereign.
2. **F-01** — `test_no_firebase_persistence_in_gate` deliberately fails as a proxy
   invalidation awaiting a sovereign decision.
3. **Refusal-shape (R3)** — `solspire/execution_runtime.py::execute` raises
   `PermissionError` while `test_solspire_r3_execution_runtime.py` expects a blocked-result
   (`code == "MUTATION_DISABLED"`). Product/governance call; not in the agent envelope.
4. **CP10 zero-test defect** — the SG-02 backend regression step runs zero tests in CI
   (CE-01 collection interrupt) and its enforcement step is self-satisfying because
   `steps.<id>.outcome` is unavailable in a `run:` block. Remedy is **consequential**
   (re-arms the gate, reddens `main` while debt is red) → requires authority.
5. **`provider-routing.yml` widening to `api/**`** — blocked on the baseline not being red;
   not met (11 debt nodes).

## Next bounded task (requires sovereign selection)

| option | scope | why it is held |
| --- | --- | --- |
| A | Merge **#347** (landing-headline re-pin) | verified green (4P); **sovereign merge required** |
| B | Authorize the **CP10 enforcement repair** (read `steps.<id>.conclusion` / move to `if:`, add `--continue-on-collection-errors`, neutralise CE-01) | consequential; re-arms CI |
| C | Authorize a **refusal-shape decision** for the R3 mutation boundary (raise vs blocked-result) | product/governance call |
| D | Authorize the **CE-01** module/package reconciliation | sovereign-reserved |

No option is within the pre-authorized envelope. **Awaiting sovereign instruction.**

## Authorized action for the next heartbeat

1. Reconstruct live state (this file is a snapshot, not truth).
2. If #347 is merged → record the merge SHA, re-measure the node set (expect 10 nodes,
   fixture reproduced), and re-classify.
3. If a new sovereign instruction exists on a PR/issue → execute that bounded task.
4. Otherwise → repeat the artifact-only reconstruction and **do not** select a consequential
   task without authority.

## Forbidden actions

- Merge. Push to `main`. Force-push.
- Follow-on work inside #347 (sovereign-merge contract step 11).
- Touching `api/main.py`, workflows, tests, or product surfaces without authority.
- Weakening or re-pinning a governance boundary (F-01, R3) as "hygiene".
