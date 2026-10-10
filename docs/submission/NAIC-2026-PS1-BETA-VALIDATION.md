# NAIC 2026 PS1 — Human External Beta Validation Record

Status: **OPEN — no human tester confirmations recorded yet**

This record is separate from the sealed `NATLAS-LAB-001` technical proof and from automated English/Hausa CI checks. Do not mark a tester PASS until a real independent person has completed the deployed tester flow and confirmed their observation.

## Instructions for each tester

1. Open the public canonical tester route: `https://arkadia-qzu4.onrender.com/n-atlas-tester`.
2. Select **Start Test** and use the provided N-ATLaS test session.
3. Submit a prompt of your choice, then inspect the model response and the displayed run/evidence identifiers.
4. Record whether the response appeared, whether the evidence details were visible, and any failure encountered.
5. Send the completed confirmation back to the project maintainer. Do not send credentials, access tokens, or private information.

The test session is short-lived and limited to the N-ATLaS tester path. Do not enter personal, confidential, or sensitive information into the prompt.

## Separate provider-forensics observation (not human beta evidence)

- Workflow run: [37956314731](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/37956314731), conclusion **SUCCESS**.
- Workflow head: `9536175a8aff23dfa51fb04fa10f827efd7e30ec`.
- Artifact: [natlas-provider-forensics, ID 11628790151](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/37956314731/artifacts/11628790151); SHA-256 `f035e15718de087cc0f6d09fcb6fe124255cce105366106a997c61b936435767`.
- Runtime submit: HTTP 200; event ID `0677708e7bc7422bb82e817700010bda`.
- SSE terminal event: `complete`; terminal payload parsed and includes a response claiming model `NCAIR1/N-ATLaS`, provider `ednai_zerogpu`, and usage totals of 87 tokens (68 prompt, 19 completion).
- Observed output: “Kindly forward the document at your earliest convenience for our review ahead of the meeting.”
- Runtime source metadata SHA: `b72ca9cfa9d87781b682aa9710df642a3744f177`.
- Authenticated Hugging Face runtime events/logs: **SKIPPED**, because the GitHub Actions `HF_TOKEN` secret was absent. No provider runtime exception was retrieved. This run demonstrates a successful public inference response in this reproduction; it does **not** explain the earlier event or establish its root cause.
- This automated forensic run is not a human beta test and must not be counted as tester A or B.

## Tester record A

- Independent tester stable pseudonym or name:
- Affiliation/role (optional):
- Test date/time with timezone:
- Tester confirmed they ran the test themselves: **NOT RECORDED**
- Prompt used (redact personal/confidential content):
- Run ID:
- Evidence ID:
- Response observed (yes/no):
- Evidence/reproduction details inspected (yes/no):
- Result: **NOT RUN**
- Issues or notes:
- Tester confirmation in their own words:
- Confirmation received by project maintainer (date/time):
- Evidence attachment or reference:
- Reviewer and review date:

## Tester record B

- Independent tester stable pseudonym or name:
- Affiliation/role (optional):
- Test date/time with timezone:
- Tester confirmed they ran the test themselves: **NOT RECORDED**
- Prompt used (redact personal/confidential content):
- Run ID:
- Evidence ID:
- Response observed (yes/no):
- Evidence/reproduction details inspected (yes/no):
- Result: **NOT RUN**
- Issues or notes:
- Tester confirmation in their own words:
- Confirmation received by project maintainer (date/time):
- Evidence attachment or reference:
- Reviewer and review date:

## Acceptance rule

Each record must correspond to a different real external person. A CI job, synthetic identity, developer self-test, or copied confirmation does not count. Preserve each run/evidence reference and the tester's own confirmation. Keep the state **OPEN** until both records are independently reviewed. Do not alter the sealed `NATLAS-LAB-001` artifact to retrofit beta evidence.

## Evidence status

- Human tester A: **MISSING**
- Human tester B: **MISSING**
- PS1 external human-beta criterion: **NOT YET PROVEN**
