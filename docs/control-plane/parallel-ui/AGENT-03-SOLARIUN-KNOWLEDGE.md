# Agent 03 — Solariun & Knowledge OS

**Active branch:** `feat/prism-next2-03-knowledge-timeline`
**Active PR:** [#431](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/431) — draft, implementation in progress.
**Base revision:** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Task:** build a feature-local Knowledge OS timeline reader against the existing handler.
**Owns:** Solariun/Knowledge OS pages, feature-local components, search/timeline/file/graph features, and their tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Start now — no new prompt required

1. Re-fetch `main`; inspect the current `GET /api/knowledge/timeline` handler/OpenAPI, request parameters, response shape, auth behavior, and data ownership rules. Do not rely on archived UI.
2. Implement a feature-local timeline panel with distinct loading, empty, auth-required, unavailable, and read-failed states. A failed read must never appear as an empty timeline.
3. Add tests proving the handler's intended owner/public semantics for authenticated and anonymous callers, including a negative control that would catch cross-owner leakage. If the current handler violates its intended boundary, fix only feature-owned backend code if authorized by the shared contract; otherwise record the exact blocker and continue with a safe non-overlapping task.
4. Use the canonical API client and `endpoints.knowledgeTimeline`. Do not add a duplicate endpoint, page-local path, or client-side filter as a substitute for server authorization.
5. After the timeline boundary is proven, inspect file browsing/capture surfaces one at a time and implement only real backend contracts. Do not add a second memory store, pretend persistence, or invent audio support.

## Hard boundaries

- No edits to shared routing/navigation/tokens/tests, NovaNet files, or Arkana/Weaver/Lab feature files.
- No auth weakening, private-to-public data promotion, or fabricated search results.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue with a safe non-overlapping task where possible.

## Required evidence

Verified route/schema; owner/public isolation tests and negative controls; loading/empty/error tests; typecheck/build; exact base/head SHAs; baseline comparison; unknowns and next bounded task.
