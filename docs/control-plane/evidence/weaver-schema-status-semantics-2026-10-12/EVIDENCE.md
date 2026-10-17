# Evidence — Weaver schema-status semantics repair

**Observed:** 2026-10-12  
**Base:** `main` at `49809f45274f2f81b24e01fefdfb3009e8717495`  
**Branch:** `fix/weaver-schema-status-semantics-2026-10-12`  
**Purpose:** align the schema's permitted status vocabulary with router behavior without granting acceptance or bypassing the worker/attention contract.

## Source evidence

- Live schema: `docs/control-plane/trajectory.schema.json` explicitly permits `merged_acceptance_pending`, `merged`, `blocked`, `failed`, and `aborted`.
- Live trajectory: `docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml` marks G12-A and G12-C `merged_acceptance_pending`; G12-B depends on G12-A; G14 depends on G12-C; G15 depends on G14; G16 depends on G15.
- Router source before this branch: `weaver/engineering_router.py` recognized only active statuses `pending`, `revision_required`, `in_progress` and terminal statuses `completed`, `accepted`, `merged`. Schema-valid gated states were reported as unrecognized.
- Existing worker contract: `EngineeringWorker.run()` returns `NO_LEGAL_MOVE` when no move is legal and composes blockers into the attention event. Existing composition tests explicitly pin this contract.
- Prior decision record: `docs/control-plane/evidence/gate07-trajectory-status-vocabulary-decision-01/EVIDENCE.md` correctly rejected adding `merged_acceptance_pending` to active statuses because that would route already-merged work again. It also identified the human-authority boundary. This repair preserves that safety finding.

## Implemented proposal

The branch introduces three explicit classes:

- **Active/routable:** `pending`, `revision_required`, `in_progress`.
- **Terminal:** `completed`, `accepted`.
- **Non-routable gates:** `merged`, `merged_acceptance_pending`, `blocked`, `failed`, `aborted`.

A gated status produces an explicit blocker stating that human review/acceptance evidence is required. It is not selected, not treated as completion, and cannot satisfy a dependent move. In particular, `merged` is removed from `TERMINAL_DONE`: a merged pull request alone does not establish acceptance. Unknown statuses outside the schema continue to be reported as unrecognized data defects.

The worker result remains `NO_LEGAL_MOVE` when no legal move is available. The worker→attention contract is unchanged; the composed `WEAVER_BLOCKED` event carries the explicit acceptance gate.

## Exact code/test scope

- `weaver/engineering_router.py`
- `tests/test_engineering_router_status_truthfulness.py`
- `tests/test_router_schema_vocabulary_closure.py`
- `tests/test_trajectory_schema_conformance.py`
- `tests/test_worker_attention_composition.py`

The existing Weaver MVP2 validation workflow path-filters these router/worker tests and runs them on pull requests. The scheduler workflow also runs the schema-vocabulary conformance guard.

## Verification state

**NOT YET VERIFIED on this branch.** The commits are proposed changes. Current-head CI must pass before the fix is described as verified. No local test execution is claimed. No merge, production deployment, acceptance, trajectory rewrite, or autonomous dispatch is claimed.

## Dispatch boundary

The recorded scheduler run `38165015207` executed a dry-run orientation and returned `NO_LEGAL_MOVE`. The available connected GitHub tools do not expose a callable OpenHands dispatch-and-run-inspection interface. This branch fixes status semantics; it does not create or simulate an OpenHands dispatch mechanism.
