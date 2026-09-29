# GATE-02 .. GATE-09 — Canonical Intelligence Loop: Implementation Record

Status: IMPLEMENTED (mixed; per-gate states below)
Base SHA: 6038989dc57e871331107b7dde9fc3d749d4d4aa
Branch: gate-01-canonical-authorship (continuous from GATE-01)

## Scope authorized

GATE-02 through GATE-09, sequential, one PR for review. GATE-10 onward is NOT
authorized (touches K15/K3 semantics) and is not started here.

## The central reconnaissance finding

The largest part of GATE-02..09 **already exists and is verified** as
ARK-WEAVER-01 (`weaver/enterprise_orchestration.py`), which §1 of the protocol
lists as "MERGED / VERIFIED". Its append-only store implements the canonical
loop end to end: `ew_canonical_records` → `ew_authority_events` /
`ew_interpretations` → `ew_knowledge_mutations` / `ew_operational_events` →
`ew_proposals` → `ew_authorizations` → `ew_execution_attempts` → `ew_evidence`
→ `ew_verifications`, with `reverse_walk` for traceability and
`simulate_eden_supplier_path` as the acceptance path.

Per LAW-09 (extend, do not replace) and LAW-07 (no second authority path),
GATE-02..09 were therefore executed as **recon → classify → close only the
small genuine deltas**. Rebuilding this spine would have created a parallel
system.

## Per-gate classification

| Gate | Capability | Existing primitive | State after work |
|------|-----------|--------------------|------------------|
| 02 | Human authority event / provenance | `ew_authority_events`, `HumanAuthorityEvent`, `EnterpriseOrchestrationStore.authority_event/authorize` | VERIFIED in base (no delta) |
| 03 | Canonical ingestion boundary | `canonical_record` (immutable, payload_hash), `interpretation` | VERIFIED in base (see GATE-01 for capture) |
| 04 | Evidence / provenance graph | `reverse_walk` (REVERSE) | IMPLEMENTED — added `forward_walk` (FORWARD) |
| 05 | Operational transition stream | `stream` (untyped event names) | IMPLEMENTED — canonical `OPERATIONAL_EVENT_TYPES` + validation |
| 06 | Knowledge OS integration | `ew_knowledge_mutations`, `interpretation` | PARTIAL — no contradiction handling; see debt |
| 07 | Weaver operational state machine | records only, no explicit state enumeration | IMPLEMENTED — `operational_state` projection |
| 08 | Tool / skill routing | `weaver/capabilities.py`, `proposal.tool_selections`, `attempt.tool_channel` | IMPLEMENTED — `explain_execution` rationale |
| 09 | Proposal / decision loop | `ew_proposals` + `authorize` (PROPOSED/AWAITING/AUTHORIZED/REJECTED) | PARTIAL — states now declared; EXPIRED/SUPERSEDED transitions not automated |

## Deltas implemented (all additive; no new table, no new mutation path)

1. **GATE-04 `forward_walk`** — traces a root (canonical record or authority
   event) forward to its consequences by following stored foreign keys. The
   complement to the existing `reverse_walk`. Never invents a link; subject
   isolation enforced.
2. **GATE-05 `OPERATIONAL_EVENT_TYPES`** — canonical transition vocabulary
   (§12), validated in `operational_event`. Existing Eden types
   (`INPUT_RECEIVED`, `UNCERTAINTY_DETECTED`, `SUPPLIER_SIGNAL_INGESTED`) are
   retained; no existing behavior changes.
3. **GATE-07 `operational_state`** — explicit, inspectable operational state
   derived from the append-only records. Enforces stage separation: a PROPOSED
   proposal is never reported AUTHORIZED; a claim is reported VERIFIED only
   when a verification record exists; UNKNOWNs surface from
   `UNCERTAINTY_DETECTED`.
4. **GATE-08 `explain_execution`** — assembles the operational rationale for an
   attempt: objective, proposed tool selections, required authority, actual
   tool channel, result, authorizing human authority event, and resulting
   evidence. A read-only projection.
5. **GATE-09 proposal statuses** — `PROPOSAL_STATUS_DECLARED` adds DRAFT /
   EXPIRED / SUPERSEDED; `PROPOSAL_STATUSES` is the union with the existing
   operational set. Nothing is collapsed.

## Authority and mutation model (unchanged by this work)

- Human authority is a first-class event, distinct from WorkEvent
  (`test_human_authority_event_is_distinct_from_workevent`).
- `authorize` requires a subject-matched, causally-bound authority event whose
  action is AUTHORIZE / APPROVE_PROPOSAL.
- Execution is refused without a valid authorization; execution cannot
  self-assert SUCCEEDED without an EvidenceRecord; verification requires
  existing evidence references.
- The new methods are read-only projections; the sole mutation path is
  unchanged (K15 → K3). No new mutation path was introduced.

## Evidence

- `tests/test_gate_02_09_orchestration_deltas.py` — 11 tests, all passing,
  against the real store (no mocks).
- Spine regression: `test_enterprise_orchestration` (4), `test_eden_ops_01`,
  `test_eden_ops_02`, `test_workevent_spine`, `test_canonical_proposal`,
  `test_phase9_decision_queue`, `test_weaver_k5`, `test_weaver_k6` — all pass.
- Full suite: **54 failed / 833 passed / 12 skipped**. The 54 failures are the
  same pre-existing, out-of-scope subsystems recorded in the GATE-01 baseline
  (prism/ais/steward/solariun/spiral_grove/weaver-mvp2/architecture); no new
  failure is attributable to this work.
- Architecture suite: 2 failures, both pre-existing (api/nodes.py inversions;
  api/main.py line budget).

## Out-of-scope observed (not implemented)

- **GATE-10** — governed execution bridge to K15/K3. NOT started; requires its
  own human authorization because it touches K15/K3 semantics (§17, §25).
- **GATE-06 debt** — contradiction handling and a unified enterprise entity /
  relationship view are not implemented. Conflicting evidence co-exists
  (append-only) but is not reconciled or surfaced as a contradiction.
- **GATE-09 debt** — no store method moves a proposal to EXPIRED (from
  `authorization.expires_at`) or SUPERSEDED; the states are declared only.
- **GATE-11** — the Weaver workbench (`workbench_view.py`) is an engineering
  cockpit projection, not the §18 enterprise-loop canvas. `operational_state`
  is the read model it needs; the surface is not built.
- **GATE-12** — Eden's governed loop is proven by simulation
  (`living_cell_supplier_path`); the first real commercial transaction is
  BLOCKED pending real-world evidence and human authority.
- **GATE-13** — continuous recalibration has no mechanism (SKELETAL).
- Three proposal representations coexist (K5 in-memory, SolSpire `proposals`,
  `ew_proposals`). They are boundary-separated today; consolidating them is a
  future architectural decision, not taken here.

## Verdict

IMPLEMENTED, mixed per gate. No gate is claimed VERIFIED by this author; the
base spine is verified, the deltas are covered by passing tests, and the whole
changeset awaits human review in the PR.
