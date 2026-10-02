# Engineering Lab — Vertical Slice 01

Status: implementation candidate, awaiting CI and human review.

## Scope

Connect the existing Engineering Lab operational lens to a real, authenticated, read-only agent workflow:

1. Create a WEAVER agent with READ and OBSERVE capabilities.
2. Create a subject/workspace-bound session in PROPOSED.
3. Require an explicit human action to authorize only read, list, and git_status for 30 minutes.
4. Invoke the existing native AgentLoop through the runtime and model gateway.
5. Render turns, tool observations, terminal state, session events, evidence, and artifacts in the same Lab surface.
6. Refresh the operational overview after each state-changing step.

## Authority boundary

This slice exposes no repository write, patch application, commit, push, merge, or deployment operation. The runtime must intersect capability ceiling, agent tool envelope, and linked human authorization. L1 terminal grammar is forced read-only. Consequential repository mutation remains reserved for the existing PassSpec → K15 → K3 path and is not part of this slice.

## Honest limitations

- A run depends on a model provider configured and reachable by the deployed backend. A provider that is unconfigured or unavailable must remain visibly blocked.
- This UI uses a bounded request/response for the first vertical slice. The persisted event log is inspectable after a run; transport-level live streaming is a later gate.
- The Android shell loads the same authenticated Arkadia frontend. This PR does not claim device testing or a release APK.
- No merge or production deployment is implied by implementation or CI success.

## Acceptance

- Frontend production build and TypeScript compile succeed.
- API route tests confirm the new endpoint is authenticated and bounded.
- Lab and architecture regression tests pass, with baseline failures attributed by test-node identity.
- CI provides the actual APK build artifact; install/auth/session smoke test remains required on a physical Android device.
