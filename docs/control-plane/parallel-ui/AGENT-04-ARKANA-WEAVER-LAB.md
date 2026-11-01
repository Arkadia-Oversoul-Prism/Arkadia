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
