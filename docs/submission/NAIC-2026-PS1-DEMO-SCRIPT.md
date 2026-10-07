# NAIC 2026 PS1 — 3–5 Minute Demo Script

## 0:00–0:25 — Problem

“N-ATLaS needs developer infrastructure that makes integration, execution, evaluation, and evidence reproducible rather than ad hoc. Arkadia's Engineering Lab provides that governed path.”

## 0:25–1:10 — The build

Show the N-ATLAS Developer Lab.

Point out:
- N-ATLaS provider
- explicit runtime protocol
- governed session
- no silent model fallback

Say:

“The important boundary is that selecting N-ATLAS does not merely label an OpenAI-compatible request. Arkadia has a dedicated N-ATLaS adapter, including the actual Gradio event-stream contract used by the external runtime.”

## 1:10–2:00 — Real execution

Submit the demonstration prompt.

Show:
- real N-ATLaS response
- execution events
- evaluation result
- evidence record

Say:

“This is the native Arkadia route. The request leaves Arkadia through the dedicated adapter, reaches a real external N-ATLaS deployment, returns a model response, and is persisted as evidence.”

## 2:00–2:45 — Proof

Open `docs/verification/NATLAS-LAB-001.md`.

Show:
- workflow run `37692465604`
- native job `113035915298`
- artifact `11514106569`
- artifact SHA-256
- runtime SHA
- model and endpoint
- matching response hash

Say:

“We did not seal this from a green CI badge. We inspected the materialized native evidence artifact and verified that the response hash in the persisted evidence matches the top-level result.”

## 2:45–3:25 — External validation

Show the English and Hausa validation results.

Say:

“We also validated the external runtime in English and Hausa. These are automated live-runtime validations.”

Then state explicitly:

“These are not being presented as the two human beta testers required by PS1. That remains the final validation gap.”

## 3:25–4:00 — Why it matters

“Arkadia turns N-ATLaS integration into a governed developer workflow: explicit provider routing, real execution, evaluation, event telemetry, evidence persistence, and reproducibility metadata. The same substrate can support additional N-ATLaS workflows without replacing the model-specific integration boundary.”

## Closing

“The result is deliberately narrow: a working N-ATLAS developer-infrastructure path with sealed evidence. Where the evidence stops, the claim stops.”