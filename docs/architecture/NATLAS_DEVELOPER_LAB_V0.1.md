# Arkadia N-ATLAS Developer Lab v0.1

Status: implementation track for NAIC 2026 PS1.

## Product

A governed developer workspace for integrating, testing, evaluating, and producing evidence from N-ATLAS.

The first golden workflow is intentionally narrow:

**N-ATLAS -> run -> inspect -> evaluate -> evidence -> verify/reproduce**

## Integration boundary

Arkadia uses a dedicated `n_atlas` provider in the Engineering Lab Model Gateway.
The provider talks to an OpenAI-compatible N-ATLAS deployment at:

- `N_ATLAS_BASE_URL` (default local development target: `http://localhost:8000/v1`)
- optional `N_ATLAS_API_KEY`
- `N_ATLAS_MODEL` (default: `N-ATLaS`)

The adapter does not fall back to Gemini, OpenAI, Anthropic, Ollama, or a mock.
If the N-ATLAS endpoint is absent or unreachable, the state is reported as `UNCONFIGURED` or `UNAVAILABLE`.

This allows a self-hosted N-ATLAS deployment without waiting for a hosted API credential, while preserving a clean boundary for a future authorized hosted endpoint.

## Evidence

Each governed N-ATLAS run records:
- run id
- authenticated subject
- session and authorization scope
- N-ATLAS provider/model
- request and response metadata
- prompt hash
- response hash
- evaluation result
- evidence id
- live event sequence

The response itself is never silently replaced by a fixture.

## Live boundary

A local/self-hosted N-ATLAS execution proves the N-ATLAS integration path.
It does not prove hosted endpoint behavior, hosted authentication, latency, or production quota behavior.

## Golden acceptance test

`NATLAS-LAB-001`:
1. an authorized Engineering Lab session exists;
2. the developer submits a prompt;
3. the configured `n_atlas` adapter calls N-ATLAS;
4. the response is captured;
5. a deterministic non-empty-response evaluation runs;
6. evidence is persisted;
7. execution telemetry is emitted;
8. the result can be inspected/reproduced from recorded metadata.

## Non-goals for v0.1
- generic multi-model playground
- voice/ASR
- fine-tuning
- autonomous repository mutation
- merge/deploy
- hosted N-ATLAS claims without live verification