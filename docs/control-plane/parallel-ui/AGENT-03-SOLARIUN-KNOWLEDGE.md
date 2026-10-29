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


## Status — 2026-10-28 (reconciled against live state)

**Active thread:** none

Lane 3 holds no open PR. Measured from live GitHub state at `main` `9195334c`: every PR
previously listed for this lane has merged or closed without merging, so the lane has no
live thread and no successor agent should be sent to one of the pointers recorded above.

This declaration is positive and machine-checked, not silence. `scripts/lane_state.py`
requires an idle lane to *state* that it holds no active thread, because a doc that simply
omits its pointer is indistinguishable from a doc that forgot to declare one — which is the
defect this guard exists to catch. The guard also cross-checks the claim against the
snapshot: a lane that declares itself idle while it still lists open PRs is reported.

The earlier pointers above are retained as provenance, not as live work. When this lane
opens its next bounded PR, append a new pointer block; the guard reads the *last*
declaration, so the appended block supersedes this status.

## Task currency — 2026-10-28 (reconciled against live state)

The forward-looking task recorded above — a bounded "load older events" control — is
**delivered**, not outstanding. Measured from repository source at `main` `4de6fc4d`:

- `web/arkadia_console/src/components/knowledge/KnowledgeTimelinePanel.tsx` implements
  `loadOlder` (line 88), passes it as `onLoadOlder` (line 142), and renders the
  "Load older events" control (line 223), with the bounded newest-window description at
  line 110.
- Pinned by `tests/test_knowledge_timeline_paging.py` (19 nodes) and
  `tests/test_knowledge_timeline_window.py` (18 nodes).

The repository holds **zero open PRs** in every lane, so the idle declaration above is the
current truth. This block adds no pointer declaration, so that idle disposition remains the
last-wins declaration for this lane.
