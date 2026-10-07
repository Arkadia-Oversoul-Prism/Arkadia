# NATLAS-LAB-001 — Golden Workflow Evidence

Status: SEALED

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
| Native Arkadia golden-route live execution | SEALED |
| Native golden evidence artifact | SEALED |

## Existing external proof

- GitHub Actions run: `37692465604`
- repaired commit: `afaa3d833710888d0c8c28284e7ac405fecca80d`
- PR merge ref exercised by native job: `c5a463f4ef953da107a33a2076445511f0c1c486`
- runtime SHA: `b72ca9cfa9d87781b682aa9710df642a3744f177`
- endpoint: `/gradio_api/call/generate`
- model: `N-ATLaS`
- protocol: `gradio`
- English: PASS
- Hausa: PASS
- external evidence bundle artifact ID: `11513398468`
- external evidence bundle SHA-256: `813fc85176a5c2be9c74c69f2b18a753fdfecf973e7761554d8f5fb0d897f366`

These are automated external-runtime validations, not human beta testers.

## Native proof

The native golden workflow executed the actual Arkadia `api.lab_routes.n_atlas_run` path against the verified external runtime with `N_ATLAS_PROTOCOL=gradio`.

Native CI job: `113035915298`

The job completed:

- native live test: PASS (`1 passed, 3 deselected`)
- external runtime reached: PASS
- EvidenceRecord persistence: PASS
- native evidence serialization: PASS
- native evidence upload: PASS

Native golden evidence artifact:

- artifact ID: `11514106569`
- artifact name: `natlas-native-golden-evidence`
- size: 733 bytes
- artifact ZIP SHA-256: `a0b047cfd6f3af384046af995b117e5d435b42297def57caad91e4afa5e97c8d`

The inspected `native-golden.json` records:

- status: `PASS`
- provider: `n_atlas`
- model: `N-ATLaS`
- protocol: `gradio`
- endpoint: `/gradio_api/call/generate`
- provider status: `AVAILABLE`
- integration: `gradio N-ATLaS runtime adapter`
- run ref: `RUN-dd41df858cee`
- prompt SHA-256: `cbde4c54bf982a947662faa5130f9f9a0199ccddb34c805365980ff6180f2f7e`
- response SHA-256: `f82de127ca5268a5368dca2d8c431ba038618afbb51943fdda23998323f743b3`

The response hash recorded at the top level matches the response hash in the persisted evidence record.

## Seal condition

NATLAS-LAB-001 is sealed against GitHub Actions run `37692465604` only after inspection of the native golden evidence artifact `11514106569`. The seal is therefore based on the recorded execution evidence and artifact contents, not on the workflow's green summary alone.

Where evidence stops, claim stops.
