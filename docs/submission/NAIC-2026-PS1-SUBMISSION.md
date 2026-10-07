# NAIC 2026 — PS1 Submission Evidence Packet

## Submission posture

Problem statement: **PS1 — Developer Infrastructure**

Core claim:

> Arkadia provides a governed Engineering Lab path for integrating, executing, evaluating, and evidencing N-ATLaS through a dedicated runtime adapter. The sealed PS1 proof reaches a real external N-ATLaS deployment and persists the result as verifiable evidence.

This packet is deliberately minimal. It uses the sealed NATLAS-LAB-001 result as the primary technical proof and does not claim evidence that has not been directly established.

## 1. Working Artefact

**Arkadia repository:** `Arkadia-Oversoul-Prism/Arkadia`

Relevant implementation:
- `lab/engineering_lab/natlas.py` — dedicated N-ATLaS adapters, including the real Gradio protocol.
- `lab/engineering_lab/gateway.py` — explicit provider/protocol routing with no silent fallback.
- `api/lab_routes.py` — governed native execution path, evaluation, telemetry, and EvidenceRecord persistence.
- `web/console/src/surfaces/NAtlasLab.tsx` — Engineering Lab surface.
- `tests/test_natlas_developer_lab.py` — adapter and native live-path verification.
- `.github/workflows/n-atlas-external-beta.yml` — external validation and native golden workflow.

## 2. N-ATLAS Integration Evidence

### Sealed proof

Verification record: `docs/verification/NATLAS-LAB-001.md`

Seal:
- Workflow run: `37692465604`
- Native job: `113035915298`
- Native evidence artifact: `11514106569`
- Artifact SHA-256: `a0b047cfd6f3af384046af995b117e5d435b42297def57caad91e4afa5e97c8d`
- N-ATLaS runtime SHA: `b72ca9cfa9d87781b682aa9710df642a3744f177`
- Protocol: `gradio`
- Endpoint: `/gradio_api/call/generate`
- Model: `N-ATLaS`

The inspected native evidence records:
- provider: `n_atlas`
- provider status: `AVAILABLE`
- integration: `gradio N-ATLaS runtime adapter`
- native run reference: `RUN-dd41df858cee`
- non-empty real model response
- prompt SHA-256: `cbde4c54bf982a947662faa5130f9f9a0199ccddb34c805365980ff6180f2f7e`
- response SHA-256: `f82de127ca5268a5368dca2d8c431ba038618afbb51943fdda23998323f743b3`

The native proof was sealed only after inspecting the uploaded evidence artifact, not from the green workflow summary alone.

## 3. Real-World Validation

The sealed workflow contains two automated external-runtime validations:
- English: PASS
- Hausa: PASS

External evidence bundle:
- Artifact ID: `11513398468`
- SHA-256: `813fc85176a5c2be9c74c69f2b18a753fdfecf973e7761554d8f5fb0d897f366`

**Important boundary:** these are automated validations against an external live N-ATLaS deployment. They are **not two human external beta testers**.

Therefore the PS1-specific requirement of at least two external beta testers is **NOT YET DIRECTLY PROVEN** by the current evidence.

## 4. Technical Documentation

Primary technical record:
- `docs/verification/NATLAS-LAB-001.md`

The record documents:
- provider selection
- explicit protocol selection
- real Gradio event/SSE contract
- no fallback
- governed session boundary
- execution telemetry
- deterministic evaluation
- evidence persistence
- reproducibility metadata
- artifact sealing

## 5. Video Demonstration

A 3–5 minute demonstration should show exactly one path:
1. Open the N-ATLAS Developer Lab.
2. Show provider/model selection.
3. Show the explicit Gradio runtime configuration.
4. Submit the governed prompt.
5. Show the real N-ATLaS response.
6. Show the resulting evidence record and execution events.
7. Show the sealed NATLAS-LAB-001 proof and artifact identifiers.
8. State the boundary: automated external runtime validation is proven; two human beta testers remain a submission requirement.

See `docs/submission/NAIC-2026-PS1-DEMO-SCRIPT.md`.

## 6. Team Profile

**Submission data required from applicant:**
- Applicant/team name
- Member names
- Affiliations
- Roles
- Nigerian citizenship / entity status as required by the selected track

No team facts are invented in this packet.

## 7. Endorsement / Registration

Provide the document required by the selected track:
- Academia & Research: institutional endorsement
- Innovation & Enterprise: CAC certificate / required applicant ID documentation

This is an administrative submission requirement and is not represented by the technical seal.

---

# Judging-criteria reconciliation

| Competition criterion | Direct evidence now possessed | Status |
|---|---|---|
| Working Artefact & Technical Rigour | Native Arkadia route executed against real external N-ATLaS; evidence persisted and artifact inspected | **DIRECT** |
| N-ATLAS Integration | Dedicated adapter + real Gradio contract + live native execution + sealed artifact | **DIRECT / SEALED** |
| Real-World Validation | Real external runtime validation in English and Hausa | **PARTIAL** |
| Impact Potential | Developer-infrastructure use case is articulable, but no independent impact metric/user evidence is sealed | **NARRATIVE ONLY** |
| Scalability & Sustainability | Architecture supports explicit provider/protocol adapters and governed evidence, but no scale/load/cost study is sealed | **NARRATIVE ONLY** |
| Team Capability | Technical implementation demonstrates delivery capability, but applicant/team credentials are not yet attached | **PARTIAL / ADMINISTRATIVE** |

## Hard remaining proof gap

**PS1 requires at least two external beta testers.**

Current evidence does not satisfy that criterion because the two existing validations are automated CI validations, not human testers.

### Smallest closure

Obtain two independent external testers to exercise the N-ATLAS Developer Lab against the same sealed workflow and record, for each tester:
- tester identity or stable pseudonym
- date/time
- prompt used
- observed N-ATLaS response
- success/failure
- evidence/run reference
- brief tester confirmation

Do not rewrite the sealed artifact. Add a separate PS1 beta-validation evidence record that links back to NATLAS-LAB-001.

## Submission principle

The submission should make one narrow, defensible claim:

> **Arkadia is a working N-ATLAS developer-infrastructure build with a real, governed integration path and sealed execution evidence.**

It should not claim two human beta testers, production scale, broad adoption, or judge acceptance until those things are directly evidenced.

## External tester path

A temporary focused tester route is provided at:

- `/n-atlas-tester`

The tester flow intentionally removes Arkadia-specific architecture from the interface:

1. Start Test
2. N-ATLaS is selected and shown as ready
3. Enter a prompt
4. Run N-ATLaS
5. Inspect the response
6. Inspect the evidence and reproduction record

The Start Test action creates a bounded 30-minute session and records the tester's explicit human authorization for that session. It does not create model authority, write access, merge authority, or deployment authority.

This surface exists only to reduce external-beta friction. The canonical Engineering Lab and sealed NATLAS-LAB-001 evidence remain unchanged.
