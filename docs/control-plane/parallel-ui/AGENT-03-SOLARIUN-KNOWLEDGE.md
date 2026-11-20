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

## Status — 2026-11-07 (LANE 3: control integrity in two lane-3 guards, no active PR declared)

**Active branch:** `feat/prism-l3-control-integrity-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot.

Lane 3's next bounded slice, opened from freshly fetched `main` under
`11 — LANE NEW-PR AUTHORIZATION`. It is the same defect class #631/#634/#636/#637 repaired in
Lane 1, in two lane-3 guards that the Lane 1 passes did not reach.

**Objective.** Bind two vacuous `test_negative_control_*` nodes to the detectors they claim to
prove, in the guards for this lane's `PersonalFieldPanel` (Solariun `memory` lens) and
`KnowledgeGraphPanel` (Knowledge OS graph).

- `tests/test_prism_solariun_memory_lens.py` — `test_negative_control_detects_confident_zeros_for_unavailable_sources`
  asserted a literal was absent from a hand-written string and called no detector.
- `tests/test_knowledge_graph_provenance_boundary.py` — the two attribution controls restated
  their regexes inline; they were also the *only* enforcement of the "no literal attribution"
  invariant, so the property was guarded by nodes labelled as controls rather than by a live
  assertion.

Measured at `main` `03220c95`: forcing the Solariun live predicate to a constant left the file
7 passed, and disarming both attribution regexes left the provenance file 24 passed. Neither
control could fail for any edit to the detector it protects.

Both files now hold a module-level detector (`_degraded_reading_defects`,
`_hardcoded_attribution_hits`) that the live assertions and their controls both call, and each
control also asserts the repaired input is *not* reported, so a detector that matches
everything cannot pass either. Node count is unchanged in both files (7 and 24).

Lane 3's next bounded PR opens only after this one merges.

## Status — 2026-11-09 (LANE 3: timeline paging control binding, no active PR declared)

**Active branch:** `feat/prism-l3-knowledge-control-binding-02` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639/#641/#642/#643/#645/#646/#647 set for lanes 3 and 4.

Lane 3's next bounded slice, opened from freshly fetched `main` `24f0c9e1` under
`11 — LANE NEW-PR AUTHORIZATION`. Reconciliation was exhausted first (measured live: **0** open
PRs repo-wide, all four lanes `doc_guard: idle`, `lane_state.py --check` and `--check
--verify-live` both exit 0), so N1 holds.

**Objective.** Bind the vacuous negative control
`test_detector_flags_the_pre_repair_two_state_viewer` in
`tests/test_knowledge_timeline_paging.py` to the detectors the live assertions use.

The control restated the live assertions' regexes inline and ran no detector: it asserted
facts about strings it had just written, so it could not fail for any edit to the predicates it
names. Measured at `main` `24f0c9e1` with AST-scoped mutation: neutering the live detector's own
regex left the live node **and** its control both green.

Three module-level detectors now hold the predicates — `_pending_scope_defects`,
`_pending_classifier_defects` and `_pending_viewer_defects` — and the live assertions and their
control both call them. The control feeds each detector the pre-repair shape and asserts it is
reported, **and** feeds it the live input and asserts it is *not* reported, so a detector that
reports unconditionally cannot pass either. Node count is unchanged at 19 — this binds a control,
it adds none.

The file is executed by the derived console-contract domain
(`scripts/console_contract_domain.py`), so no new wiring is needed.

Evidence: `docs/control-plane/evidence/lane3-knowledge-timeline-control-binding-01/EVIDENCE.md`.

Lane 3's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.

## Status — 2026-11-09 (LANE 3: knowledge status-read control binding, no active PR declared)

**Active branch:** `feat/prism-l3-knowledge-status-control-binding-03` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639/#641/#642/#643/#645/#646/#647/#649 set for lanes 3 and 4.

Lane 3's next bounded slice, opened from freshly fetched `main` `9ba62a01` under
`11 — LANE NEW-PR AUTHORIZATION`. Reconciliation was exhausted first (measured live: **0** open
PRs repo-wide after #649 merged, all four lanes `doc_guard: idle`, `lane_state.py --check` exit
0), so N1 holds.

**Objective.** Bind the three `test_negative_control_*` nodes in
`tests/test_knowledge_status_read_boundary.py` to the predicates the live assertions use.

Each control restated its predicate inline and called no detector: the first asserted a probe
value it had just built, the second was **orphaned** (its structural assertion had no live
partner in the file), and the third restated a substring check of the contract module. A
control that shares no predicate with a live assertion cannot fail when that predicate is
edited. Measured at `main` `9ba62a01` by AST-scoped mutation of the live expression: neutering
the live `readStatus` check left the live node green.

Four module-level detectors now hold the predicates — `_contract_refusal_defects`,
`_reader_wiring_defects`, `_blanket_refusal_defects` and `_naive_reader_defects` — and the live
assertions and their controls both call them. Each control feeds its detector the pre-repair
shape and asserts it is reported, **and** feeds it the live input and asserts it is *not*
reported, so a detector that reports unconditionally cannot pass either. Node count 14 → 19
(+4 live assertions that give the previously orphaned predicate a live partner, +1 control).

The file is executed by the derived console-contract domain
(`scripts/console_contract_domain.py`), so no new wiring is needed.

Evidence: `docs/control-plane/evidence/lane3-knowledge-status-control-binding-01/EVIDENCE.md`.

Lane 3's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.

## Status — 2026-11-15 (LANE 3: positional-read scanner bound to its detector)

**Active branch:** `feat/prism-l3-positional-read-detector-binding-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639/#641/#642/#643/#645/#646/#647/#649/#650 set for lanes 3 and 4.

Lane 3's next bounded slice, opened from freshly fetched `main` `19697a6a` under
`11 — LANE NEW-PR AUTHORIZATION`. Reconciliation was exhausted first (measured live: **2** open
PRs repo-wide, #658 a draft owning lane 1's shell contract and #657 a governance draft owning
no lane's paths and recorded under `unassigned_open_prs`; lane 3 holds none), so N1 and N2 hold
and no lane's PR was duplicated or continued.

**Objective.** Bind `test_no_other_module_reads_a_row_positionally` to a detector rather than an
inline expression. The predicate was written inside the test body, so it shared no symbol a
control could call — there was no control at all, and the guard could be disarmed by editing the
very expression it depends on.

**Measured vacuity at base `19697a6a`.** With a positional read planted in
`knowledge/graph_health.py` (`return int(list(row)[0])`) **and** the inline predicate rewritten
to `if False:`, the node still **passed** (`1 passed`). That planted defect is exactly the
`_count()` defect #621 repaired, so the guard for its recurrence did not see it.

**Repair.** The predicate moves to a module-level `_positional_row_reads(source)` with its
vocabulary hoisted to `POSITIONAL_ROW_READ_SHAPES`, and the live sweep and a new control both
call it. The control asserts **both** polarities — the pre-repair shape is reported, and the
shipped module is *not* — so a detector that reports unconditionally cannot pass either. Node
count 11 → 12 (+1, exactly the new control).

**Evidence bound to the commit.** Two **live** negative controls on the real file: neutering the
shared detector to `return []` reddens the control (`1 failed, 11 passed`); neutering it to
`return ["always-dirty"]` reddens the sweep **and** the control (`2 failed, 10 passed`), so the
control is not satisfied by a detector that reports everything. The file was restored
byte-identically (`md5 6940eb90…`).

The file is executed by the derived `knowledge-connection-lifecycle-guard.yml` step and is a
declared input of `tests/test_knowledge_graph_health_ci_wiring.py`, so no new wiring is needed.

Evidence: `docs/control-plane/evidence/lane3-positional-read-detector-binding-01/EVIDENCE.md`.

Lane 3's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.

## Status — 2026-11-19 (LANE 3; supersedes the idle declaration above)

**Active branch:** `lane3/graph-row-cap-disclosure-01`
**Active PR:** [#667](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/667) — draft, head `31835b1641c446774aef049073b2598a69312c82`, base `main`.

Lane 3 is not idle: it holds one bounded draft PR, so the idle declaration above is
superseded by this pointer, which is the declaration the guard reads (last-wins).

The slice is `KnowledgeGraphPanel.tsx` + `knowledgeContracts.ts` — discloses the knowledge-
graph row cap. Every path it touches is inside lane 3's exclusive ownership (`SHARED-
CONTRACTS.md` §1).

This block was appended by the aggregate integration ledger
(`docs/control-plane/evidence/ewor-integration-baseline-2026-11-18/`) because its derived
`lane-state.json` correctly records lane 3 as holding an open PR while this doc still
declared idle — a disagreement that reddened `lane-doc-currency` on the combined tree. It
records the live thread and asserts nothing about the slice's readiness: the PR stays
**draft**. Merge, production deployment and acceptance remain human-only.

## Status — 2026-11-20 (LANE 3, idle; supersedes the #667 pointer above)

**Active thread:** none

Lane 3 holds **no open PR**. PR #667 merged as `97dbe012` ("Lane 3: disclose the knowledge-graph row cap"), and the four
lane threads #664-#667 landed together in the integration squash `5f40e65c7a13b934f63f24310ffda90d5b18b351` (PR #668), which
was already `main` when this block was written.

The #667 pointer above is retained as provenance, not as live work; this declaration is the
one the guard reads (last-wins). It is the truthful idle form, not silence:
`scripts/lane_state.py` requires an idle lane to *state* that it holds no active thread, and
cross-checks the claim against `lane-state.json` — a lane that declares idle while the
snapshot still lists its own open PRs is reported as drift.

Measured at `main` `5f40e65c7a13b934f63f24310ffda90d5b18b351`; the snapshot was re-derived in the same change, so the docs and
the snapshot cannot disagree. Lane 3 at zero open PRs is a **deficit**, not a resting
state: the next action is to open lane 3's next bounded draft PR from freshly fetched
`main`, inside the lane's owned paths (`SHARED-CONTRACTS.md` §1). Merge, production
deployment and acceptance remain human-only under GOV-03.
