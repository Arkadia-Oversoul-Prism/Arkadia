/**
 * Worked boundary instance: WORK EVENT ≠ EVIDENCE (Boundary Expansion Gate 03).
 *
 * Established by measurement, not assumption. Starting from an actual WorkEvent:
 * creating one produces no evidence and no verification; the WorkEvent carries
 * only opaque reference fields (artifact_refs, decision_ref, witness_ref) that
 * no code resolves; and the runtime evidence chain that does exist (the
 * ARK-WEAVER-01 enterprise store) binds evidence to an *execution attempt*, not
 * to a WorkEvent. No table joins the two spines.
 *
 * Everything here is traceable to tests/test_workevent_evidence_boundary.py and
 * RECONCILED-BOUNDARY-MAP-01.md §6 item 9. Nothing is asserted beyond the
 * measurement. The absence is the result.
 */
import type { BoundaryInstance } from "../lib/boundary";

export const WORK_EVENT_NOT_EVIDENCE: BoundaryInstance = {
  id: "workevent-not-evidence",
  title: "Work Event ≠ Evidence",
  from: "WORK_EVENT",
  to: "EVIDENCE",
  means:
    "Recording continuity and producing evidence are separate on this substrate, and they are " +
    "not joined. A WorkEvent is a continuity record carrying opaque references; evidence is a " +
    "distinct record that binds to an execution attempt in a different spine.",
  priorCollapse:
    "There is no prior collapse to repair: the two records were never joined. The boundary is an " +
    "ABSENCE of a durable WorkEvent → Evidence identifier, measured rather than assumed.",
  posture: {
    mechanism: "ENFORCED",
    deployment: { implemented: true, tested: true, deployed: false, productionVerified: false },
    note:
      "Measured on the branch. A WorkEvent created through its router produces no evidence and no " +
      "verification; its reference fields stay opaque strings. NOT DEPLOYED; production UNVERIFIED.",
  },
  nonCollapses: [
    {
      left: "WORK_EVENT",
      right: "EVIDENCE",
      enforced: true,
      evidence: [
        "test_a_workevent_carries_only_opaque_reference_fields",
        "test_creating_a_workevent_produces_no_evidence_or_verification",
      ],
    },
    {
      left: "WORK_EVENT TABLE",
      right: "EVIDENCE / VERIFICATION TABLES",
      enforced: true,
      evidence: ["test_no_table_joins_a_workevent_to_evidence_or_verification"],
    },
    {
      left: "WORK EVENT MANAGER",
      right: "ENTERPRISE EVIDENCE STORE",
      enforced: true,
      evidence: ["test_workevent_and_evidence_are_created_by_disjoint_modules"],
    },
    {
      left: "EVIDENCE",
      right: "VERIFICATION",
      enforced: true,
      evidence: [
        "test_evidence_binds_to_an_execution_attempt_not_a_workevent",
        "test_verification_references_evidence_not_a_workevent",
      ],
    },
  ],
  surfaces: [
    "POST /solspire/workevents",
    "GET /solspire/workevents",
    "GET /solspire/workevents/{work_event_id}",
  ],
  unresolved: [
    "There is no durable WorkEvent → Evidence identifier: a WorkEvent carries no evidence_ref, and no evidence table references a work_event_id.",
    "A WorkEvent's reference fields (artifact_refs, state_before_ref, state_after_ref, decision_ref, witness_ref) are opaque — no code resolves them to a record.",
    "The runtime evidence chain is a different spine: weaver/enterprise_orchestration.py binds ew_evidence to an execution_attempt_id, and a verification's evidence_refs is a string list, not a foreign key.",
    "The enterprise evidence → verification → proposal chain is read over HTTP only as a projection (GET /solspire/workspaces/{id}/control-room); the forward_walk / reverse_walk graph itself has no HTTP route — implemented, unexposed.",
    "No dedicated route exposes evidence or verification as first-class records; the console cannot list them.",
    "Whether a WorkEvent should produce or reference evidence is a later architectural decision; the absence is recorded, not resolved.",
    "Deployment: the branch is not deployed; production posture is UNVERIFIED.",
  ],
  verbs: ["SEE", "DISTINGUISH", "INSPECT", "VERIFY"],
  verbsBlockedByProvisioning: [],
};
