# Agent 03 — Solariun & Knowledge OS

**Branch:** `feat/prism-next-03-knowledge-search`  
**PR:** #421 (draft bootstrap)  
**Owns:** Solariun and Knowledge OS page modules, feature-local components, tests, and evidence. Exact paths must be discovered from the current tree and archive before edits.  
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` in `main` (accepted via PR #419); fetch/review it before edits.

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


## Next wave — continue immediately after this PR closes

Coordinator direction (2026-10-11): continue with the next feature-local vertical slice; do not wait for a new prompt. Verify the exact `POST /api/knowledge/search` handler, request/response schema, and owner-filter behavior. Mount `KnowledgeSearchPanel` in `KnowledgePage.tsx` only after confirming the shared endpoint registry contains the verified path; if it does not, send Workstream 1 a precise integration request and continue with a non-conflicting Knowledge OS task. Add tests for private/public separation, auth behavior, loading/empty/error states, and no fabricated results. Then reconcile the timeline and file browsing capabilities from the archive one at a time, implementing only real backend contracts. Preserve the backend's personal/public boundary; never apply a client-side filter as a substitute for server authorization.


## Active branch — next wave

Start from the current main revision observed for this wave: `962434bed1bccb11fbf5edfcb0299317b12a8915`. This branch is already created from that revision. Begin the bounded task in the Next wave section immediately. Do not wait for the coordinator to send another prompt. Keep this PR draft while implementation is in progress; after it merges, create the next branch from fresh main and continue the workstream. Only stop for a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk without a safe path, or a genuine cross-workstream contract conflict. Record such a blocker in the PR thread with exact evidence; otherwise continue with the next non-overlapping task.

## Slice 01 — verified `POST /api/knowledge/search` (branch `feat/prism-next-03-knowledge-search`)

Evidence: `docs/control-plane/evidence/prism-next-knowledge-search-01/EVIDENCE.md`.

Verified the handler contract, then measured and repaired **three** defects on it:
the `references` table DDL used an unquoted SQL reserved word (the table was never
created → **live 500** for the default mode set and `modes=["reference"]`), and
`unified_search` dispatched `project`/`timeline`/`graph` without `user_id`, so an
anonymous caller read every owner's private projects and timeline events.

`KnowledgeSearchPanel` is implemented against the verified contract and mounts from
`KnowledgePage.tsx` **only** when the shared registry carries the path; the registry
entry is a **Workstream 1** integration request (PR #425). Beyond the slices above,
the next non-overlapping task is the Knowledge OS timeline read surface.
