# Agent 04 — Arkana, Weaver & Engineering Lab

**Branch:** `feat/prism-parallel-04-arkana-weaver-lab`  
**PR:** #422 (draft bootstrap)  
**Owns:** Arkana/Oracle, Weaver and Engineering Lab feature-local page modules/components/tests/evidence. Exact paths must be discovered from the current tree and archive before edits.  
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` in PR #419; fetch/review it before edits.

## Mission
Recover useful Oracle/Arkana conversation and governed operational-workspace interactions while exposing only capabilities backed by real contracts and required authorization. Make proposal, approval, execution, work event, evidence, verification and review visibly distinct.

## First tasks
1. Inspect live `main`, PR #418, archive README, legacy Arkana/Oracle, Weaver and Engineering Lab files, and current backend modules. Record exact source paths and SHAs.
2. Create a feature matrix for conversation/history/source references/voice controls only where supported; Weaver workstreams/runs/approvals/evidence; and Engineering Lab workspace, events, diffs, and read-only capabilities.
3. Verify each route/method/schema/auth requirement against actual handlers/OpenAPI. Do not infer streaming, memory, citations, model-provider readiness, repository writes, or execution authority from legacy UI.
4. Preserve human approval and read-only capability ceilings. A UI action must not silently turn observation into mutation or proposal into execution.
5. Implement bounded feature-local slices and tests. Request route/shared shell/API registry integration from workstream 1 instead of editing shared files.

## Hard boundaries
- No edits to `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, global navigation/tokens, shared shell tests, NovaNet/Solariun files, runtime/authority model, or deployment configuration.
- No fabricated replies/evidence, hidden execution, authorization bypass, merge/deploy/acceptance.

## Acceptance
Real backend contract and auth; honest unavailable/error states; tests for unauthorized/read-only boundaries and state distinctions; typecheck/build; evidence bound to exact SHA; known gaps and one next bounded move.
