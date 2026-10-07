# NATLAS-LAB-001 — Golden Workflow Evidence

Status: IMPLEMENTED; native live proof pending CI execution

## Acceptance

An authorized Engineering Lab session must:

1. select N-ATLAS;
2. submit a prompt;
3. execute real N-ATLaS inference through the dedicated adapter;
4. evaluate the response;
5. persist EvidenceRecord;
6. emit RUN_STARTED → MODEL_TURN → EVIDENCE_RECORDED → RUN_FINISHED;
7. expose reproduction metadata.

## Runtime protocols

`N_ATLAS_PROTOCOL` explicitly selects:

- `openai_compatible` → `NAtlasAdapter`
- `gradio` → `NAtlasGradioAdapter`

The Gradio adapter implements POST `/gradio_api/call/generate`, receives an `event_id`, then consumes the SSE result from `/gradio_api/call/generate/{event_id}`. No protocol fallback is performed.

## Evidence

| Check | State |
|---|---|
| Dedicated provider | GREEN |
| OpenAI-compatible adapter | GREEN |
| Real Gradio adapter | GREEN |
| No model fallback | GREEN |
| Truthful unavailable state | GREEN |
| Governed session | GREEN |
| Evidence persistence | GREEN |
| Execution telemetry | GREEN |
| Deterministic evaluation | GREEN |
| Lab surface | GREEN |
| English external inference | GREEN |
| Hausa external inference | GREEN |
| Two external validations | GREEN |
| Native Arkadia golden-route live execution | PENDING CI |
| Native golden evidence artifact | PENDING CI |

## Existing external proof

- GitHub Actions run: `37691220118`
- commit: `3028e45d46cc5a3aec448ea6414e8d9a8235efe1`
- runtime SHA: `b72ca9cfa9d87781b682aa9710df642a3744f177`
- endpoint: `/gradio_api/call/generate`
- model: `N-ATLaS`
- English: PASS
- Hausa: PASS
- evidence bundle SHA-256: `e726477a39279d356b71dd688659aea2465380ae476dcb67e8f98915157a4253`

These are automated external-runtime validations, not human beta testers.

## Native proof gate

The CI workflow now configures the verified external runtime with `N_ATLAS_PROTOCOL=gradio` and executes the actual `api.lab_routes.n_atlas_run` path through the live adapter. It asserts a non-empty model response, EvidenceRecord persistence, and the canonical event sequence.

The claim remains unsealed until that CI execution produces the native golden evidence artifact.

Where evidence stops, claim stops.