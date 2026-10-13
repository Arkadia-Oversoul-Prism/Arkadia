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

## Status — 2026-10-11 (issue #437 follow-up)

**Active branch:** `feat/prism-next2-03-knowledge-timeline-latest-2` (PR #431 is
closed history; PR #445 closed as a duplicate).
**Active PR:** [#450](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/450) — draft, head `22b15091`.
**Base:** `7b67215735945584e89fec50f97fe74dddfcbf28`.

**Issue #437 was fixed on `main` while this pass ran** (PR #442, merge `56ada9dd`,
issue closed). PR #445 duplicated that; it was closed, not merged. #450 is the
non-duplicate residual on top of #442, and changes **no backend file**.

Delivered (reader-side only): the panel's `first` fact renamed to `oldest shown`
(it named `events[0]`, which under #442's newest window is only the oldest event
*still shown*); a `window` fact (`newest`/`complete`) and an extent notice derived
from the response; `TIMELINE_WINDOW_LIMIT` and the window vocabulary in
`knowledgeContracts.ts`. #442's `latest` is now pinned by a test rather than left
implied.

**Gate lesson (new):** `tests/test_prism_console_ci_wiring.py` derives the
console-contract domain from `git ls-files` at test time. A test module that
*names* the console joins that domain, and the executing gate must select the
whole domain **in the same change** — so adding such a test requires editing
`.github/workflows/prism-console-contract.yml` too. Corollary: because the domain
is tracked-content-derived, a **newly added but still untracked** guard is
invisible to it and the guard passes *vacuously* until commit. Measure parity
after committing, not before.

Evidence: `docs/control-plane/evidence/prism-next2-knowledge-timeline-window-02/EVIDENCE.md`.

**Next bounded task (non-overlapping):** a bounded "load older events" control on
the measured `offset` contract; or `GET /api/knowledge/projects/{name_or_uuid}`,
which needs a registry path builder (Workstream 1's file) — a request, not an edit.


## Status — 2026-10-13 (LANE 3, pulse)

**Active branch:** `fix/knowledge-traverse-edge-dedup-01`
**Active PR:** [#526](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/526) — draft, head `eecdc370b677`.
**Base:** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` (measured live this pulse; the
`f390526…` base recorded above is superseded).

Delivered: `knowledge/graph.py::traverse` now emits each edge once. It previously
appended a `graph_edges` row on every hop whose frontier touched it, so a
diamond/back-edge fixture returned the same row more than once. The reachable node
set was already deduped by `visited`; only the edge projection carried the
duplicate, which is why the node-set pins in `tests/test_isolation.py` never saw it.

Guard: `tests/test_knowledge_graph_traverse_boundary.py` (new, 9 nodes) — set
property over the returned edge list at depths 1–3, dedupe does not drop reachable
nodes, relationship filter, ownership boundary, plus a negative control
reconstructing the pre-repair accumulation (must still duplicate on the fixture)
and a detector control. Measured: guard 9 passed; fix reverted 4 failed/5 passed;
guard + `test_isolation` + `test_relational_lineage` 24 passed; architecture 11
passed.

Ownership note: uncommitted LANE-3 console work in the working tree
(`KnowledgeGraphPanel.tsx`, `knowledgeContracts.ts`) was **deliberately left out of
this commit** — PRs #509 and #498 both modify
`web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts`, and a second
un-reconciled variant would manufacture a conflict for the sovereign. It stays on
the working tree only.

Evidence: `docs/control-plane/evidence/prism-lane3-graph-traverse-edge-set-01/EVIDENCE.md`.

**Next bounded task (non-overlapping):** reconcile the node-inspection panel
(`KnowledgeGraphPanel.tsx`) onto #498/#509 once one of them merges, rather than
committing a competing `knowledgeContracts.ts`; or a read-only measurement of the
`/graph/{note_id}/traverse` route contract against the deployed origin.

