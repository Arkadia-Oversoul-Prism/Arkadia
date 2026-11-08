# Agent 04 — Arkana, Weaver & Engineering Lab

**Current slice:** PR #428 — read-only Arkana thread history and verified Lab session/run/event/evidence/artifact/agent views.
**After merge:** create the next branch from freshly fetched `main`, open a new draft PR, update the active branch map through Workstream 1, and begin immediately.
**Owns:** Arkana/Oracle, Weaver, Engineering Lab feature-local pages/components/tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Immediate continuation task

Build the next bounded read-only slice: **a traceable run-to-evidence review view** that connects the real session/run/work-event/evidence records already returned by the Engineering Lab handlers.

1. Re-fetch `main`; verify exact handler routes, response shapes, identity/owner scope, and any stable foreign-key/reference fields. Do not join records on guessed identifiers.
2. Show source references and current recorded states; distinguish run completion from evidence existence, verification from review, and review from human acceptance. Missing links must remain visibly unresolved, not inferred.
3. Add tests for owner isolation, empty/missing references, duplicate/partial records, and the negative control where an evidence record exists but no verification/acceptance exists.
4. Keep the interface read-only. No authorize, execute, transition, run-agent, provider, repository-write, merge, or deployment controls.
5. Once this trace is proven, continue with one verified Arkana history improvement or Weaver read surface at a time.

## Hard boundaries

- No edits to shared routing/navigation/tokens/tests, NovaNet/Solariun feature files, runtime/authority model, or deployment configuration.
- No fabricated replies/evidence, hidden execution, auth bypass, or treating a declared agent capability as granted authority.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue with a safe non-overlapping task where possible.

## Required PR evidence

Verified route/auth/data contract; source-bound references; owner/read-only/state-boundary tests; negative controls; typecheck/build; exact SHAs; unresolved links and next bounded move.

## Status — 2026-10-28 (reconciled against live state)

**Active thread:** none

Lane 4 holds no open PR. Measured from live GitHub state at `main` `9195334c`: every PR
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

The forward-looking task recorded above — a traceable run-to-evidence review view — is
**delivered**, not outstanding. Measured from repository source at `main` `4de6fc4d`:

- `web/arkadia_console/src/components/lab/LabRunTrace.tsx` and its projection module
  `labRunTrace.ts` are present (added by `eb874fd6`, "feat(lab): add run trace and model
  gateway projections").
- Pinned by `tests/test_lab_run_trace_contract.py` (22 nodes) and
  `tests/test_prism_w4_run_evidence_trace.py` (29 nodes).

The repository holds **zero open PRs** in every lane, so the idle declaration above is the
current truth. This block adds no pointer declaration, so that idle disposition remains the
last-wins declaration for this lane.

## Status — 2026-10-31 (LANE 4; supersedes the idle declaration above)

**Active branch:** `fix/dea-01-dispatch-session-reconciliation`
**Active PR:** #601 (draft) — head `35f90958814643c4bdfdd5a0fa9610f5f70c4b75`, base `main`
**Base:** `6ccb021fd0af1d34e3fb37aaca44f642c76cbac0` (measured live this pulse; supersedes
every earlier base recorded above).

Lane 4 is no longer idle: it holds one bounded draft PR again, so the idle declaration above
is superseded by this pointer, which is the declaration the guard reads (last-wins).

The slice reconciles the Lab dispatch/session surface — `LabWorkerDispatch.tsx`,
`MissionWorkspace.tsx` and `tests/test_lab_mission_workspace_contract.py`, with evidence in
`docs/control-plane/evidence/arkadia-unified-lab-mvp-01/EVIDENCE.md`. All four paths are
inside lane 4's exclusive ownership (`SHARED-CONTRACTS.md` §1). The PR stays **draft**: the
guard records its live state, it does not assert the slice is ready for review or merge.
Merge, production deployment and acceptance remain human-only.

## Status — 2026-10-31 (LANE 4, idle; supersedes the #601 pointer above)

**Active thread:** none

PR #601 merged as `6776ee103525c9d097d73e3a47493748ff3efc2c`, so the pointer block above
names a merged thread and is superseded by this declaration, which is the declaration the
guard reads (last-wins). Lane 4 holds **no open PR** again.

The merge was performed by the **human sovereign** (`Arkadia-Oversoul-Prism`), not by this
workstream: the governing documents — `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md`
§"Agents may inspect, implement, test, document, commit to their assigned branch, and update
their PR. They may not merge any PR, deploy production, or declare product acceptance." and
`AGENTS.md` — reserve merge, production-deployment and acceptance authority to the human.
This block records the merge; it does not claim it.

Lane 4 at zero open PRs is a **deficit**, not a resting state: the next action is to open
lane 4's next bounded draft PR from freshly fetched `main`, inside the lane's owned paths
(`SHARED-CONTRACTS.md` §1).

## Status — 2026-11-01 (LANE 4; supersedes the idle declaration above)

**Active branch:** `feat/prism-w4-model-gateway-dispatchability`
**Active PR:** #605 (draft) — repair commit `9d83ab3c264ad2264e953134f88cacc9f877bc2e` (the lane-currency commit that records this pointer is the branch tip), base `main`
**Base:** `d14c2598b5b5e9016703b6a834fd44b8def1e5a1` (measured live this pulse; supersedes
every earlier base recorded above).

Lane 4 is no longer idle: it holds one bounded draft PR again, so the idle declaration above
is superseded by this pointer, which is the declaration the guard reads (last-wins).

The slice repairs the Lab model-gateway read projection. `ModelDescriptor.status` ("is this
configured and reachable?") and `dispatchable` ("could a run actually call it right now?",
which additionally needs a bound adapter) are different questions, and the handler already
emits both — but the console projection read only `status`, so a reachable provider with no
adapter bound was presented as a usable worker. That is P0.5's truthfulness rule:
`AVAILABLE != a functioning worker`. The changed paths — `labGateway.ts`,
`LabModelGateway.tsx`, `tests/test_prism_w4_model_gateway.py` and
`tests/test_lab_model_gateway_contract.py` — are inside lane 4's exclusive ownership
(`SHARED-CONTRACTS.md` §1). The PR stays **draft**: the guard records its live state, it does
not assert the slice is ready for review or merge. Merge, production deployment and
acceptance remain human-only.

## Status — 2026-11-01 (LANE 4; snapshot re-derivation; supersedes the head above)

**Active branch:** `feat/prism-w4-model-gateway-dispatchability`
**Active PR:** #605 (draft) — head `e4738a505da763c574eca74ff9a4618ea9f5bc5f` **at derivation time**,
base `main`
**Base:** `d14c2598b5b5e9016703b6a834fd44b8def1e5a1` (re-measured live this pulse).

The head above is scoped to the derivation instant deliberately. Recording a lane PR's tip and
then reading it as the *current* tip is unsatisfiable: the lane-currency commit that records the
head becomes the head, so the field is structurally one commit behind. The tip at `observed_at`
is the claim; the tip now is a different fact. `scripts/lane_state.py` reads `head_sha` nowhere
(0 refs), so neither value is judged — see the recorded oracle gap in `AGENTS.md`.

The lane-currency block above recorded head `9d83ab3c264ad2264e953134f88cacc9f877bc2e`. The same
open thread then advanced three commits to `e4738a505da763c574eca74ff9a4618ea9f5bc5f` (the
gateway projection fix, its test adjustment, and the DEA-01 evidence record), and the snapshot
was re-derived against that head rather than left describing the earlier one.

`lane-state.json` now reads lane 4 `doc_guard: "deferred"` with `deferred_to_pr: 605` — the
correct classification while this doc is mid-repair on its own open PR, and the one the derivation
produces — where it previously read `"current"`. It also records open draft PR #606 under
`unassigned_open_prs` (it matches no lane's exclusive paths) rather than omitting it.

Verified this pulse at `e4738a50`: `scripts/lane_state.py --check` exit 0 and
`--check --verify-live` exit 0 (doc-guard lanes `['1','2','3']`, deferred `['4']`);
`tests/test_lane_instruction_doc_currency.py` **49 passed**; `tests/architecture` **11 passed**.
Merge, production deployment and acceptance remain human-only.

## Status — 2026-11-01 (LANE 4, idle; supersedes the #605 pointer above)

**Active thread:** none

PR #605 merged as `9de0e0fbfea1fc0f25a57445b0f33ab19bbbd130`, so the pointer block above names a
merged thread and is superseded by this declaration, which is the declaration the guard reads
(last-wins). Lane 4 holds **no open PR** again.

This block is a **reconciliation**, not a new slice. Measured at `main` `dd498913`: the
`lane-doc-currency` gate was **red on `main`** (`run 41317998445`, `push` at `9de0e0fb`) because
`lane-state.json` still recorded #605 under lane 4 `open_prs` *and* `deferred_to_pr` while the PR
was merged. The snapshot was re-derived with
`scripts/lane_state_refresh.py --write --base-main dd49891385eb944dfacdfa69ceaef603c79b665d`,
which moves #605 into `merged_prs` (`9de0e0fb`), empties lane 4 `open_prs`, and returns
`doc_guard: "idle"`; the stale `unassigned_open_prs` entry for #606 (merged as `dd498913`) is
cleared by the same derivation.

Lane 4 at zero open PRs is a **deficit**, not a resting state: the next action is to open lane 4's
next bounded draft PR from freshly fetched `main`, inside the lane's owned paths
(`SHARED-CONTRACTS.md` §1). Merge, production deployment and acceptance remain human-only.

## Status — 2026-11-08 (LANE 4: control integrity in the two model-gateway guards, no active PR declared)

**Active branch:** `feat/prism-w4-gateway-control-integrity-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638 set for lane 3.

Lane 4's next bounded slice, opened from freshly fetched `main` `14aa82e0` under
`11 — LANE NEW-PR AUTHORIZATION`. It is the same defect class #631/#634/#636/#637 (Lane 1),
#635 (Lane 2) and #638 (Lane 3) repaired, in the two lane-4 model-gateway guards those passes
did not reach.

**Objective.** Bind five vacuous `test_negative_control_*` nodes to the detectors they claim to
prove, in `tests/test_lab_model_gateway_contract.py` and `tests/test_prism_w4_model_gateway.py`.

Measured at `main` `14aa82e0`: neutering each live detector's own expression (AST-scoped to that
function) left the live node red and its control **green** (`2 passed`) — the control could not
fail for any edit to the detector it protects. One control additionally parsed a synthetic
snippet and asserted on *that snippet*, never on the shipped `describe_gateway`.

The detectors move to module-level functions (`_wiring_violations`, `_purity_violations`,
`_projected_classes`, `_side_effects_in_function`) that the live assertions and their controls
both call, and each control also asserts the repaired input is *not* reported. Node count is
unchanged at 43 — this strengthens controls, it adds none.

Lane 4's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.

## Status — 2026-11-08 (LANE 4: Arkana provenance control integrity, no active PR declared)

**Active branch:** `feat/lane4-arkana-provenance-control-integrity-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639 set for lanes 3 and 4.

Lane 4's next bounded slice, opened from freshly fetched `main` `d1d7c601` under
`11 — LANE NEW-PR AUTHORIZATION`. It is the same defect class #631/#634/#636/#637 (Lane 1),
#635 (Lane 2), #638 (Lane 3) and #639 (Lane 4) repaired, in the Arkana provenance guard those
passes did not reach.

**Objective.** Bind the orphaned detector `renders_provenance_from_a_constant` in
`tests/test_prism_rec_arkana_provenance.py` to the live assertion it exists for.

Measured at `main` `d1d7c601` with AST-scoped mutation: neutering the detector body
(`return False`, `return True`, `return None`) reddened **only** the two `test_negative_control_*`
nodes and **no live node**. Every other assertion in the file is a substring check, so the
detector's property — the provenance the panel renders is normalised from the response, not
invented — was guarded by nodes labelled as controls and by nothing else.

The live `test_arkana_page_renders_the_provenance_panel` now also asserts
`not renders_provenance_from_a_constant(page)`, and the second control asserts the opposite
polarity. Node count is unchanged at 15 — this binds a control, it adds none.

Lane 4's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.


## Status — 2026-11-08 (LANE 4: Lab resume control integrity, no active PR declared)

**Active branch:** `feat/prism-l4-lab-resume-control-integrity-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639/#641 set for lanes 3 and 4.

Lane 4's next bounded slice, opened from freshly fetched `main` `e07ee81e` under
`11 — LANE NEW-PR AUTHORIZATION`. It is the same defect class #631/#634/#636/#637 (Lane 1),
#635/#640 (Lane 2), #638 (Lane 3) and #639/#641 (Lane 4) repaired, in the Lab mission-workspace
guard those passes did not reach.

**Objective.** Bind the orphaned detector `_resume_reconstructs_authorization` in
`tests/test_lab_mission_workspace_contract.py` to the live assertion it exists for.

Measured at `main` `e07ee81e` with AST-scoped mutation: neutering the detector body
(`return False`, `return True`, `return None`) reddened **only** the control node
`test_negative_control_resume_detector_flags_a_reconstructed_authorization` and **no live node**.
The live node that states the same property, `test_resume_never_reconstructs_an_authorization`,
restates it inline (`assert "setAuthorization" not in body`), so the detector was guarded by a
node labelled as a control and by nothing else.

The live node now also asserts `not _resume_reconstructs_authorization(workspace)`. Node count is
unchanged at 29 — this binds a control, it adds none.

Lane 4's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.


## Status — 2026-11-08 (LANE 4: scheduler report control integrity, no active PR declared)

**Active branch:** `feat/prism-l4-scheduler-report-control-integrity-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639/#641/#642 set for lanes 3 and 4.

Lane 4's next bounded slice, opened from freshly fetched `main` `1550a5a1` under
`11 — LANE NEW-PR AUTHORIZATION`. It is the same defect class #631/#634/#636/#637 (Lane 1),
#635/#640 (Lane 2), #638 (Lane 3) and #639/#641/#642 (Lane 4) repaired, in the scheduler
trajectory guard those passes did not reach.

**Objective.** Bind the orphaned detector `_report_names_blockers` in
`tests/test_scheduler_trajectory_conformance.py` to the live assertion it exists for.

Measured at `main` `1550a5a1` with AST-scoped mutation: neutering the detector body
(`return False`, `return True`, `return None`) reddened **only** the control node
`test_negative_control_pre_fix_report_is_silent` and **no live node**. The live node that states
the same property, `test_session_report_surfaces_router_blockers`, reached the workflow text only
through the neighbouring `_report_program` helper, which returns the embedded program but does not
assert it names the blockers — so the detector was guarded by a node labelled as a control and by
nothing else.

The live node now also asserts `_report_names_blockers(step.get("run") or "")`. Node count is
unchanged at 23 — this binds a control, it adds none.

Lane 4's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.


## Status — 2026-11-08 (LANE 4: AO-006 canvas control integrity, no active PR declared)

**Active branch:** `lane4/ao006-canvas-control-integrity-01` (recorded for provenance only).
**Active PR:** none declared — the snapshot below is the judge.

A lane PR cannot declare itself open at merge time: the merge that lands it closes it. This
section therefore declares no active PR and leaves the lane's status to the derived snapshot,
the convention #638/#639/#641/#642/#643 set for lanes 3 and 4.

Lane 4's next bounded slice, opened from freshly fetched `main` `d82c266c` under
`11 — LANE NEW-PR AUTHORIZATION`. It is the same defect class #631/#634/#636/#637 (Lane 1),
#635/#640 (Lane 2), #638 (Lane 3) and #639/#641/#642/#643 (Lane 4) repaired, in the newest
guard on `main` — the one those passes did not reach because it arrived with the newest file.

**Objective.** Bind the vacuous negative control
`test_negative_control_a_subject_parameter_would_be_detected` in
`tests/test_ao006_canvas_contract.py` to the detector its live assertion uses.

Measured at `main` `d82c266c` with AST-scoped mutation: neutering the live node's own
`offenders.append` expression left **both** the live node
`test_no_canvas_route_accepts_a_subject_parameter` and its control **green**. The live assertion
and the control each restated the same predicate inline, independently, so the control exercised
only its own copy and could not fail for any edit to the detector the live assertion uses.

The predicate now lives once in a module-level `_caller_supplied_scope_offenders(routes)` that
both nodes call, and the control additionally asserts a route taking no scope parameter is *not*
reported. Node count is unchanged at 16 — this binds a control, it adds none.

Recorded, not repaired: this guard is executed by no effective gate (it is outside the derived
console-contract domain, and the `sg-02-fe-2-v.yml` broad-suite step aborts at collection).
Wiring it into a gate is a separate bounded workstream — see the evidence doc.

Evidence: `docs/control-plane/evidence/lane4-ao006-canvas-control-integrity-01/EVIDENCE.md`.

Lane 4's next bounded PR opens only after this one merges. Merge, production deployment and
acceptance remain human-only.
