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
