# Agent 03 — Solariun & Knowledge OS

**Current slice:** PR #427 — verified multi-mode Knowledge OS search, schema repair, and owner-scoped search modes.
**After merge:** create the next branch from freshly fetched `main`, open a new draft PR, update the active branch map through Workstream 1, and begin immediately.
**Owns:** Solariun/Knowledge OS pages, feature-local components, search/timeline/file/graph features, and their tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Immediate continuation task

Build the next bounded feature: **Knowledge OS timeline retrieval**, using the existing `GET /api/knowledge/timeline` contract only after re-verifying its handler, auth behavior, response shape, and personal/public ownership rules.

1. Re-fetch `main`; inspect the current handler and OpenAPI rather than relying on archived UI or this instruction.
2. Implement a feature-local timeline panel with distinct loading, empty, auth-required, unavailable, and read-failed states. Do not represent a failed read as an empty timeline.
3. Add backend tests proving authenticated users can read only their own plus explicitly public records, while anonymous callers see only public records. Include negative controls that would catch cross-owner leakage.
4. Request any shared endpoint/type registry entry from Workstream 1; do not create a page-local endpoint or edit shared files.
5. Only after the timeline boundary is proven, inspect file browsing/capture surfaces one at a time and implement the next real contract. Do not add a second memory store, pretend persistence, or client-side filtering as a substitute for server authorization.

## Hard boundaries

- No edits to shared routing/navigation/tokens/tests, NovaNet files, or Arkana/Weaver/Lab feature files.
- No auth weakening, private-to-public data promotion, fabricated search results, or invented audio support.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue with a safe non-overlapping task where possible.

## Required PR evidence

Verified route and response schema; owner/public isolation tests and negative controls; loading/empty/error tests; typecheck/build; exact base/head SHAs; baseline comparison; unknowns and next bounded task.
