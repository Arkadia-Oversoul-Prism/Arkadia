# NATLAS-LAB-001 — Golden Workflow Evidence

Status: IMPLEMENTATION IN PROGRESS

## Acceptance contract

An authorized Engineering Lab session must be able to:

1. select the N-ATLAS provider;
2. submit a developer prompt;
3. execute a real N-ATLAS request through the dedicated adapter;
4. capture the returned response;
5. run a deterministic evaluation;
6. persist an EvidenceRecord;
7. emit RUN_STARTED → MODEL_TURN → EVIDENCE_RECORDED → RUN_FINISHED telemetry;
8. expose reproduction metadata without claiming hosted-service verification.

## Evidence states

| Check | State |
|---|---|
| Dedicated n_atlas provider exists | IMPLEMENTED |
| OpenAI-compatible adapter exists | IMPLEMENTED |
| No fallback to another model | IMPLEMENTED |
| Missing endpoint reported truthfully | IMPLEMENTED |
| Governed session required | IMPLEMENTED |
| Evidence persistence | IMPLEMENTED |
| Execution telemetry | IMPLEMENTED |
| Deterministic evaluation | IMPLEMENTED |
| Browser Lab surface | IMPLEMENTED |
| Local N-ATLAS execution | PENDING runtime provisioning |
| External beta validation | PENDING |
| Hosted N-ATLAS verification | UNVERIFIED |

## Reproduction boundary

The repository proves the adapter contract and governance path. A successful live integration claim requires an actual N-ATLAS endpoint to be configured and reachable. No mock response is accepted as live evidence.

## Next proof

Provision a self-hosted N-ATLAS OpenAI-compatible endpoint, set N_ATLAS_BASE_URL and N_ATLAS_MODEL, create an authorized Lab session, and run the golden workflow from /n-atlas-lab.