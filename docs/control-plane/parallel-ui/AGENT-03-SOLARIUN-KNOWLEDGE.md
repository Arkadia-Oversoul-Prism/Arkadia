# Agent 03 — Solariun & Knowledge OS

**Branch:** `feat/prism-parallel-03-solariun-knowledge`  
**PR:** #421 (draft bootstrap)  
**Owns:** Solariun and Knowledge OS page modules, feature-local components, tests, and evidence. Exact paths must be discovered from the current tree and archive before edits.  
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` in PR #419; fetch/review it before edits.

## Mission
Reconcile personal workspace, capture, knowledge exploration/search, and related Solariun interactions with current identity, authorization, file, and knowledge contracts. Preserve personal sovereignty and the distinction between personal/private material and public corpus.

## First tasks
1. Inspect current `main`, PR #418, archive README and relevant archived pages/components; identify exact legacy paths and current page modules. Do not guess file paths from product names.
2. Build a feature/route matrix for Solariun home/workspace, capture, personal Codex/Echofeild, knowledge search/files/graph/timeline and any audio/read-aloud controls actually present.
3. For every capability, inspect actual backend route/OpenAPI, handler, auth requirement, request/response schema, persistence and error behavior. Mark unsupported contracts UNKNOWN/BLOCKED; no endpoint invention.
4. Use existing canonical API client and identity boundary. Prove personal uploads cannot leak into public corpus and public corpus reads cannot expose personal vault data.
5. Implement one bounded vertical slice at a time in feature-owned files. For routes/shared nav/API registry changes, send workstream 1 an integration request instead of editing shared files.

## Hard boundaries
- No edits to `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, global navigation/tokens, shared shell tests, NovaNet files, or Arkana/Weaver/Lab files.
- Do not add a second memory database, fake persistence, pretend audio support, or weaken authorization.
- No merge/deploy/acceptance.

## Acceptance
Evidence-backed route/API contract; real data and honest states; tests for personal/public separation and auth denial; typecheck/build; keyboard/mobile checks when affected; exact SHA and baseline comparison; unknowns recorded rather than filled by assumption.
