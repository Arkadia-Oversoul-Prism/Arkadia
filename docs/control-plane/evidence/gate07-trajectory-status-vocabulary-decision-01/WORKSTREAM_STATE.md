# WORKSTREAM_STATE — gate07 / trajectory status vocabulary decision 01

| field | value |
|---|---|
| workstream | `gate07/trajectory-status-vocabulary-decision-01` |
| gate | GATE-07 (durable Weaver loop) |
| base | `main` @ `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd` |
| pass | 1 (verification + decision record) |
| status | **IMPLEMENTED** — decision recorded, no execution |
| authority required | sovereign decision on the vocabulary repair (see below) |

## State

- Vocabulary defect re-derived against source: `merged_acceptance_pending` is schema-legal
  but absent from `ACTIVE_STATUSES ∪ TERMINAL_DONE`, so `select_next_move()` cannot route
  the live frontier (`G12-A`, `G12-C`) and fails closed with a named blocker (#322).
- The three candidate repairs were measured and are **not behaviour-equivalent**:
  data-repair → `G12-B`; `TERMINAL_DONE` widen → `G12-B`; `ACTIVE_STATUSES` widen →
  `G12-A` (**already-merged move** — rejected).
- The seam is guarded in one direction only: `router ⊆ schema` is asserted; `schema ⊆
  router` is not.
- Baseline measured twice, stable: `093938e8…` / `5f186112…` (15 nodes). PR #330's
  `f3e73647…` (11 nodes) differs by exactly the 4 `agents_md` nodes.

## Next bounded task

**Sovereign decision** on the vocabulary repair. Recommended: repair the trajectory data
(`G12-A`/`G12-C` → `merged`, backed by merged PR #315/#316 plus `ACCEPT.json` acceptance
evidence). It is a two-line data edit but it enables autonomous routing to `G12-B` and
asserts completion on the sovereign's behalf, so it is human-authority gated.

Follow-on, non-authority-bearing: pin the untested seam direction — every schema-legal move
status must be either routable or explicitly named unroutable — as a bounded guard PR.

## Proposed, not executed

- Vocabulary repair (authority-bearing; see EVIDENCE.md §5-6).
- Seam-direction guard (`schema ⊆ router` classification; see EVIDENCE.md §6).
- `AGENTS.md` encoding adjudication class (separate recorded workstream; 4 failing nodes).
- `test_ais_capability_profile_onboarding` test-side literal pin (separate).

## Deterministic next-action block

- **Current state:** decision record committed on this branch; no source change.
- **Evidence:** this directory.
- **Blockers:** none for this record; the repair itself awaits sovereign decision.
- **Authorized action:** review + merge of PR #329; sovereign decision on the repair.
- **Forbidden actions:** merge, push to `main`, mutate PR #329/#330/#331, execute the
  vocabulary repair without authorization.
- **Completion condition:** the chosen repair is recorded, the seam direction is pinned by
  a guard, and the live trajectory routes without an unrecognized-status blocker.
