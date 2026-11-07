# Agent 01 — Shell, Navigation, Design System & Integration

**Active branch:** `feat/prism-l1-nexus-subview-disposition-01` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.
**Base revision:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
**Task:** advance the Lane-1 shared shell/navigation seam; the next bounded task is repairing lane instruction-doc drift against a machine-readable lane-state snapshot (`docs/control-plane/parallel-ui/lane-state.json`), guarded by `tests/test_lane_instruction_doc_currency.py`.

> Superseded pointers (2026-10-15): the earlier `feat/prism-next2-01-shell-contract-map` branch and wave PRs (#423/#425/#426/#427/#429) are **merged and closed** history; the live Lane-1 threads are PR #507 and PR #529. Do not reopen or continue a merged thread.

**Owns:** shared app shell, `App.tsx`, router/surface registry, global navigation/lenses/tokens, shared shell/endpoint contract tests, `lib/endpoints.ts`, `lib/types.ts`, and integration seams.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Start now — no new prompt required

1. Verify current `main` is descended from the stated base, then refresh the four active branch/PR/head entries in `SHARED-CONTRACTS.md` after the four next-wave PRs exist. Keep the merged #425–#428 wave as history, not active work.
2. Re-verify the actual served handler and URL encoding for Workstream 4's recorded requests. Add `labAutomations: "/api/lab/engineering/automations"` to the canonical registry and add a typed, encoded `labCanvas(id)` path builder derived from `endpoints.labArtifacts`. `labSession(id)` already exists; verify it remains correct. Do not add paths that are not served.
3. Add focused positive/negative contract tests for those builders and their served routes. Run endpoint-registry guards, TypeScript/build, and route-table checks.
4. Review the merged Opportunity Radar Projects mount against the actual board handler; make a shared integration change only if evidence proves one is needed. Do not take over the feature-local implementation.
5. Continue with the highest-value remaining shell/navigation gap in the live inventory. Work in bounded commits and keep the PR updated.

## Measured contract facts (do not re-derive from memory)

- **`useRouter` normalises the address bar on load** (`lib/router.ts`, this branch). It resolves the inbound pathname and `replaceState`s the canonical path when they differ, so `/nexus`, a trailing slash, or an unrouted path does not leave the address bar holding a path no surface declares. Reconciled from the archived Prism (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:102 history.replaceState`). `tests/test_console_shell_nav_contract.py` evaluates the real router in Node rather than pinning its text.
- **`PATH_ALIASES` reconciles legacy inbound links to one canonical surface, never a second route.** Currently `/nexus` → `novanet` and `/oracle` + `/commune` → `arkana`. The archived Prism's route table declares `commune: '/oracle'` and accepts both `/oracle` and `/commune`, and its home surface sends the Oracle portal to `commune`; the console names that surface `arkana`. Without the aliases those paths fell through `resolvePath` to `home`, and the address-bar normalisation then wrote `/`, making the loss permanent for a shared link. **Verify a candidate alias against `app.openapi()["paths"]` and `_RESERVED_PREFIXES` before adding it** — a legacy path that collides with a real backend route must not become a UI alias. Not yet reconciled: `/home` (same case as `/`) and `/gate` + `/living-gate` (the archived `gate` view — the console has no such surface, so reconciling it is a product decision, not a routing one).
- The alias-soundness suite (`_path_aliases` / `_alias_defects`) already asserts every alias targets a declared surface and never collides with a canonical path. **Extend it rather than adding a second detector** — a duplicate guard is not a guard, and the first draft of this pass's alias tests failed on helper scope because `strip_types` is nested inside `_js_route_resolver`.
- The canvas route is a **sibling** of artifacts, not a sub-resource. Served: `/api/lab/engineering/artifacts` (GET), `/api/lab/engineering/canvas/{artifact_id}` (GET). **Not** served: `/api/lab/engineering/artifacts/{artifact_id}`, and `/api/lab/engineering/canvas` alone is not a route. This is why `labCanvas` derives its base by substitution and why a `labCanvasRoot` registry entry would fail the served-path guard.
- `/api/commune/resonance` and `/api/knowledge/search` are **POST-only**; a GET probe returning 405/404 is not a defect.
- Workstream 2's merged evidence explicitly requests **no** shared endpoint constant for `/solspire/buyer-recon`; that path is handler-derived in its own contract module. Do not add it to the registry. Its served shapes are `/solspire/buyer-recon/projects/{project_id}` and `/…/entries` (verified against `app.openapi()`), and the Projects mount is `SolSpirePage.tsx:33` → `OpportunityRadarSection` → `ProjectOpportunityRadar` (reviewed this pass; no shared change needed).
- `knowledgeSearch` was already added by `67696372`; do not re-add it.
- **A concurrent commit on this branch may land the same work.** Two landed while this pass's copies were uncommitted or in flight: `9b1b3ef1` ("reconcile shared endpoint contract against merged feature slices") added `labAutomations` + `labCanvas`, and `e8b0b77a` ("widen the one-registry guard to apiRequest literals") took the detector-widening that this pass had recorded as its own next move. `git fetch` + compare against `origin/<branch>` **before** committing and again before pushing; drop a duplicate rather than re-landing it, rebase the non-overlapping work onto the remote head, and keep **both** sides of a documentation conflict rather than picking one.

## Hard boundaries

- Do not implement NovaNet/Opportunity, Knowledge OS, Arkana/Weaver/Lab feature internals.
- Do not change backend authority/runtime contracts or deployment configuration.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk without a safe path, or genuine cross-workstream contract conflict. Record exact evidence in the PR thread and continue with a safe non-overlapping task where possible.

## Required evidence

Exact base/head SHAs; route/OpenAPI verification; ownership/overlap check; targeted tests and negative controls; typecheck/build; baseline failure-node comparison; current branch map; one next bounded task.

## Status — 2026-10-24 (LANE 1, lane-currency truth repair)

**Active branch:** `feat/prism-l1-nexus-subview-disposition-01` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.
**Base:** `68acf89f3045a01b0ba04038fabac4edfb5f937e` (measured live this pulse; every
earlier base recorded above is superseded).

The pointers above are stale and were repaired by *appending* this block, per the
last-wins convention already used by lanes 2–4. Measured live this pulse: **all four**
lane docs named a dead thread — `AGENT-01` named PR #507 (closed without merging),
`AGENT-02` #430 (merged), `AGENT-03` #526 (closed without merging), `AGENT-04` #428
(merged). A successor agent reading any of them would have resumed a closed thread,
which is the continuity failure the lane model exists to prevent.

Two of those four were *hidden by the deferral mechanism*, which is the more important
finding: `AGENT-03`'s `#526` was installed by open PR #548 and `AGENT-04`'s `#536` by
open PR #555, each while its own lane was `deferred`, so the currency guard judged
neither pointer. `scripts/lane_state.py --verify-live` now judges liveness on the
*document*, for every lane, independently of disposition.

Repaired in this pass:

- Freshness no longer compares SHAs. `snapshot.base_main == current main` reddened on
  any unrelated merge (31 commits had landed since the recorded base; two touched a
  guarded path). Staleness is now "a lane doc changed after the snapshot was recorded".
- `--verify-live` adds an authoritative PR-state oracle (GitHub reads API, read-only):
  OPEN / MERGED / CLOSED_UNMERGED / UNKNOWN, with UNKNOWN failing closed.
- The snapshot is now *derived* (`scripts/lane_state_refresh.py --write`) instead of
  hand-transcribed — the transcription step is what let ten closed PRs stay recorded
  as open.

Ownership note: this pass repaired only Lane 1's own instruction doc. `AGENT-03` and
`AGENT-04` are owned by PRs #548 and #555; their dead pointers are recorded here as a
measured handoff, not edited from a lane that does not own them.

Evidence: `docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md`.

**Next bounded task:** once #548 and #555 land or are superseded, re-point `AGENT-03`
and `AGENT-04` at their live lane threads, then re-run
`python scripts/lane_state.py --check --verify-live` and expect it to be clean.

## Status — 2026-10-28 (reconciled against live state)

**Active thread:** none

Lane 1 holds no open PR. Measured from live GitHub state at `main` `9195334c`: every PR
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

The forward-looking handoff recorded above is **discharged**, not outstanding. Measured
from live GitHub state at `main` `4de6fc4d`:

- PR #548 and PR #555 are **closed without merging**. The instruction to "re-point
  `AGENT-03` and `AGENT-04` once #548 and #555 land or are superseded" no longer has a
  subject: neither PR will land, and both lanes were already re-pointed to their idle
  disposition by PR #584. No successor action remains on that handoff.
- The repository holds **zero open PRs** in every lane, so this lane's own idle
  declaration above is the current truth.

Retained as provenance. This block adds no pointer declaration, so the idle disposition
recorded above remains the last-wins declaration for this lane.

## Status — 2026-10-29 (LANE 1, endpoint-registry oracle repair)

**Active branch:** `feat/prism-l1-nexus-subview-disposition-01` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.
**Base:** `b5bc34cb178d0ec8a804ce6f5761e4bd5e0c7989` (measured live this pulse; supersedes
every earlier base recorded above).

Lane 1 is no longer idle: the lane holds one bounded draft PR again. The task-currency
block above discharged its forward-looking handoff and its own last-wins idle declaration
is now superseded by this pointer, which is the declaration the guard reads.

The slice repairs the served-path oracle in this lane's own guard
(`tests/test_console_endpoint_registry_contract.py`). Measured at `b5bc34cb`, the oracle
stripped `/api/` from the *advertised* value only, so it was wrong in both directions —
a served `/api/...` route read as unserved, and an invented `/api/solspire/proposals`
read as served by collapsing onto its real bare twin. The extractor feeding it also
keyed by file, leaving three of `SolSpirePage.tsx`'s four `NotYetWired` panels unjudged.
`RECORDED_ADVERTISED_DRIFT` drops 6 → 1; the survivor is another workstream's display
copy and is recorded, not edited (§1). Evidence:
`docs/control-plane/evidence/lane1-endpoint-registry-oracle-symmetry-01/EVIDENCE.md`.

Reconciliation was exhausted before this PR was opened: the repository held **zero open
PRs** across all four lanes, so N1–N8 are satisfied and no lane's PR was duplicated or
continued.

## Status — 2026-10-31 (LANE 1, idle; supersedes the #588 pointer above)

**Active thread:** none

Lane 1 holds **no open PR** again. PR #588 merged as `df7899b9` ("Lane 1: repair the
endpoint-registry served-path oracle in both directions"), and the lane has not opened its
next bounded slice yet. The pointer block above therefore names a merged thread and is
superseded by this declaration, which is the one the guard reads (last-wins).

This is the truthful idle form, not silence: `scripts/lane_state.py` requires an idle lane
to *state* that it holds no active thread, and cross-checks the claim against the snapshot —
a lane that declares idle while the snapshot still lists its own open PRs is reported.

Measured at `main` `6ccb021fd0af1d34e3fb37aaca44f642c76cbac0`; snapshot refreshed the same
pulse. Lane 1 at zero open PRs is a **deficit**, not a resting state: the next action is to
open lane 1's next bounded draft PR from freshly fetched `main`, inside the lane's owned
paths (`SHARED-CONTRACTS.md` §1).

## Status — 2026-11-02 (LANE 1, active; supersedes the idle declaration above)

**Active branch:** `feat/prism-l1-nexus-subview-disposition-01` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.

Lane 1 is **active** again. The idle declaration above is superseded by this block
(last-wins, the convention already merged for lanes 2 and 3); it is retained as
provenance rather than rewritten.

The slice repairs the checked *domain* of `tests/test_console_legacy_route_coverage.py`.
The guard judged only the archive's two route maps, but `resolvePath` also accepts two
families a route map cannot express: the regex family `/^\/solariun(?:\/([^/]+))?$/` and
the exact-string branches `/solspire` and `/solspire/voice`. Measured at `main`
`fb1d03e4`, all four fell outside the partition — `/solspire` and `/solspire/voice`
resolving to `/`, a silent loss, because `/solspire` is a reserved backend namespace
(`api/frontend_routes.py::_RESERVED_PREFIXES`) the SPA cannot serve. The declaration is
now bound to the archive's own source and the partition covers every inbound path
`resolvePath` accepts, with a negative control on the real file.

Reconciliation was exhausted before this PR was opened: no eligible merge, no actionable
dependency, no safe bounded repair outstanding, and lane 1 held no open PR — so N1–N8
are satisfied and no lane's PR was duplicated or continued. Verified live:
`scripts/lane_state.py --check --verify-live` → exit 0.

## Status — 2026-11-03 (LANE 1, idle; supersedes the #610 pointer above)

**Active thread:** none

PR #610 merged as `6b28ddba`, so the pointer block above names a merged thread and is
superseded by this declaration, which is the declaration the guard reads (last-wins). Lane 1
holds **no open PR** again.

This block is a **reconciliation**, not a new slice. Measured at `main` `e67c1faf`: the
`lane-doc-currency` gate was **red on `main`** (`Lane Doc Currency`, `push` at `6b28ddba`)
because `lane-state.json` still recorded #610 under lane 1 `open_prs` while the PR was merged,
and this doc still pointed at it. The snapshot was re-derived with
`scripts/lane_state_refresh.py --write --base-main e67c1faf0a12a8ba232cfc4f34a39944c29b3553`,
which moves #610 into `merged_prs` (`6b28ddba`), empties lane 1 `open_prs`, and returns
`doc_guard: "idle"`.

Lane 1 at zero open PRs is a **deficit**, not a resting state: the next action is to open
lane 1's next bounded draft PR from freshly fetched `main`, inside the lane's owned paths
(`SHARED-CONTRACTS.md` §1). Merge, production deployment and acceptance remain human-only.

## Status — 2026-11-03 (LANE 1: slice record, no active PR declared)

**Active branch:** `feat/prism-l1-nexus-subview-disposition-01` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.
from base `f2a7158f11ade7edeaaa297cef2769a82c6f7ebc`; its opening head was
`eb6087119522c72578a7b2f2e7d847c424feb420`. The tip moves as the slice is appended to, so this
names the opening head rather than claiming a current one — read the live head from the PR.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it, so the
snapshot would contradict live state the instant it merged. This section therefore declares no
active PR and leaves the lane's status to the derived snapshot.
(last-wins). Lane 1 again holds **one** open draft PR, so it is no longer a deficit.

This is the **continuation** the idle block called for — lane 1's next bounded slice, opened from
freshly fetched `main` under `11 — LANE NEW-PR AUTHORIZATION`. It is not a continuation of #610:
that PR merged as `6b28ddba` and its subject (route-map record currency) is closed. The slice
landed as PR #614; once merged, lane 1 is idle again until its next bounded PR is opened.

**Objective.** The four archived hub sub-views recorded as gaps in
`tests/test_console_legacy_route_coverage.py::LEGACY_GAP_DISPOSITIONS` (`/nexus/ims`,
`/nexus/grove`, `/nexus/larder`, `/nexus/distribution`) each said only *"a NovaNet/nexus sub-view
whose backend contract is UNKNOWN"*. That is true and incomplete: the `/nexus` alias branch carries
a single remainder segment, so each path resolves to its NovaNet section and renders that surface's
own `NotYetWired` state. Measured at `main` `f2a7158f`: `resolvePath('/nexus/ims')` → `/novanet/ims`
while the ledger named no canonical path, and **no existing guard fired** because both halves were
true. A reader could not distinguish a reconciled sub-view from a discarded link.

**Bounded scope.** `tests/test_console_legacy_route_coverage.py` only — lane-1 owned
(`SHARED-CONTRACTS.md` §1; `scripts/lane_state_refresh.py` lane 1 `paths`). No route, alias,
surface, or backend contract changed; the record now matches the router. The disposition entries
name the canonical path, and `_nexus_subview_dispositions()` compares the record against the
resolver's own answer so the ledger cannot drift from the router. The canonical path is matched as
a whole path token, not a substring — the first cut accepted `/novanet/distribution-elsewhere` and
its own negative control caught it.

**Evidence bound to `eb608711`.** Targeted `14 passed` (was 12); a **live** negative control
(revert the ledger to the pre-repair strings) yields `2 failed, 12 passed`, and the file was
restored byte-identically; the gate that executes this guard
(`pytest $(python scripts/console_contract_domain.py)`) reports `1046 passed`; architecture +
console wiring `41 passed`; adjacent lane-1 guards `83 passed`; `scripts/lane_state.py --check`
exit 0.

**Snapshot.** Re-derived with
`scripts/lane_state_refresh.py --write --base-main f2a7158f11ade7edeaaa297cef2769a82c6f7ebc`,
which returns lane 1 `doc_guard: "current"` with `active_pr: 614`. The snapshot is derived, not
hand-edited.

Merge, production deployment and acceptance remain human-only. Lane 1 opens its next bounded PR
only after #614 merges.


## Status — 2026-11-03 (LANE 1: sub-view contract binding, no active PR declared)

**Active branch:** `feat/prism-l1-nexus-subview-contract-binding-01` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it, so the
snapshot would contradict live state the instant it merged. This section therefore declares no
active PR and leaves the lane's status to the derived snapshot.

This is lane 1's next bounded slice, opened from freshly fetched `main` under
`11 — LANE NEW-PR AUTHORIZATION`. It is **not** a continuation of #614: that PR merged as
`0c615bda` and its subject (recording *where* each `/nexus` sub-view resolves) is closed. The
residue #614 left is a different claim.

**Objective.** #614 made each `/nexus/<view>` disposition name the canonical path the alias
produces, but left the *other* half of the record untouched: every entry still read "a
NovaNet/nexus sub-view whose backend contract is UNKNOWN". That statement is true and
**unfalsifiable** — nothing tied it to the backend, so it could survive the route appearing or
disappearing, and it did not distinguish four genuinely different situations. Measured at `main`
`46d85e2d`: `/api/ims/` serves 5 paths (with `/api/ims/inquiries` gated on the `x-sovereign-key`
header), `/api/distribution/` serves 6, and `/api/grove/` and `/api/larder/` serve none. The
record now states that asymmetry and is bound to the served app.

**Bounded scope.** `tests/test_console_legacy_route_coverage.py` only — lane-1 owned
(`SHARED-CONTRACTS.md` §1; `scripts/lane_state_refresh.py` lane 1 `paths`). No route, alias,
surface, or backend contract changed. `_nexus_subview_contract_defects()` parses the family claim
from the disposition text itself (a present claim, its `No …` negation, and the sovereign-gate
claim) rather than keeping a second hand-written table, and `_sovereign_gated_paths()` reads the
gate from `api/main.py` because the served OpenAPI document declares no security scheme at all —
the schema cannot express a header check inside a handler body.

**Evidence.** Targeted `19 passed` (was 16); a **live** negative control on the real file (restore
the pre-repair ledger) reddens exactly
`test_recorded_nexus_subview_contracts_agree_with_the_served_app` and
`test_the_served_family_claims_are_not_uniformly_true_or_false` (`2 failed, 17 passed`), and the
file was restored byte-identically; the gate that executes this guard
(`pytest $(python scripts/console_contract_domain.py)`) reports `1052 passed`; console wiring
`30 passed`; `tests/architecture` `11 passed`; `scripts/lane_state.py --check` and
`--check --verify-live` both exit 0.

Merge, production deployment and acceptance remain human-only. Lane 1 opens its next bounded PR
only after this one merges.

## Status — 2026-11-07 (LANE 1: control integrity in the unified-interface guard, no active PR declared)

**Active branch:** `feat/prism-l1-vacuous-control-integrity-02` (recorded for provenance only).
**Active PR:** none declared — this section records the slice's objective; the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it, so the
snapshot would contradict live state the instant it merged. This section therefore declares no
active PR and leaves the lane's status to the derived snapshot.

This is lane 1's next bounded slice, opened from freshly fetched `main` under
`11 — LANE NEW-PR AUTHORIZATION`. It is **not** a continuation of #631: that PR merged as
`b2d33c80` and repaired two vacuous controls in `test_console_surface_error_boundary.py` and
`test_console_shell_nav_contract.py`. This slice is the same defect class in the **third**
Lane-1 guard, which #631 did not reach.

**Objective.** `tests/test_console_unified_interface_contract.py` (added by `b9297ab9`, AO-002)
carried **six** `test_negative_control_*` nodes, and every one restated its detector inline
instead of calling it — so a control could not fail for any edit to the live assertion it was
supposed to protect. The file's own header claims the opposite. One of the six
(`…a_fabricated_worker_list_would_be_detected`) was additionally **orphaned**: it named a
`const WORKERS` roster that no live assertion in the file guards at all.

**Bounded scope.** `tests/test_console_unified_interface_contract.py` only — lane-1 owned
(`SHARED-CONTRACTS.md` §1, "shared shell/endpoint contract tests"). No console source, backend
contract, registry, or other lane's file is touched. Six detectors move to module-level
functions that the live assertion and its control both call; each control now asserts the
repaired input is not reported as well as the mutated one is.

**Evidence.** Targeted `24 passed` (node count unchanged at 24 — this strengthens controls and
adds none). A **live** mutation control on the real file: neutering each shared helper body
reddens **both** the live node and its control; on the pre-repair file, neutering the live
detector's own expression reddened the live node while the control stayed green (the vacuity).
The orphaned roster control was proven attached to no live assertion. The gate that executes
this guard (`pytest $(python scripts/console_contract_domain.py)`) reports `1123 passed` (10
failures are the documented missing-`node_modules` TypeScript toolchain, matching #633's
baseline); console wiring `31 passed`; `tests/architecture` `11 passed`; lane suites
`67 passed`; `scripts/lane_state.py --check` and `--check --verify-live` both exit 0.

Evidence: `docs/control-plane/evidence/lane1-unified-interface-control-integrity-01/EVIDENCE.md`.

Merge, production deployment and acceptance remain human-only. Lane 1 opens its next bounded PR
only after this one merges.
