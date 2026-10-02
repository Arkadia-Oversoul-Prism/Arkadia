/**
 * Worked boundary instance: EVIDENCE ≠ VERIFICATION (Boundary Expansion Gate 04).
 *
 * Established by measurement, starting from an actual persisted evidence record
 * in the ARK-WEAVER-01 enterprise chain (the records the control-room projection
 * reads over HTTP). Evidence is created by EnterpriseOrchestrationStore.evidence()
 * and carries a durable id (ev-<uuid>); creating it does NOT create a verification.
 * Verification is a separate, explicit call (verify()), and the link between them
 * is a correlation — ew_verifications.evidence_refs is a JSON text list matched by
 * substring, with no FOREIGN KEY and no reverse column on ew_evidence.
 *
 * The relationship is asymmetric: a verification cannot be created without
 * referencing an existing evidence record, but evidence can exist with no
 * verification at all. That asymmetry is the finding.
 *
 * Everything here is traceable to tests/test_evidence_verification_boundary.py
 * and RECONCILED-BOUNDARY-MAP-01.md §6 item 10. Nothing is asserted beyond the
 * measurement. No relationship was created or repaired to demonstrate it.
 */
import type { BoundaryInstance } from "../lib/boundary";

export const EVIDENCE_NOT_VERIFICATION: BoundaryInstance = {
  id: "evidence-not-verification",
  title: "Evidence ≠ Verification",
  from: "EVIDENCE",
  to: "VERIFICATION",
  means:
    "Capturing evidence and verifying a claim are separate on this substrate. Evidence is a " +
    "durable record; a verification is a separate record that cites evidence by reference. " +
    "Evidence can exist unverified; a verification cannot exist without evidence.",
  priorCollapse:
    "There is no prior collapse to repair: the two records were never the same. The boundary is " +
    "the ABSENCE of a foreign key between them — the link is a correlation, measured not assumed.",
  posture: {
    mechanism: "ENFORCED",
    deployment: { implemented: true, tested: true, deployed: false, productionVerified: false },
    note:
      "Measured on the branch. Evidence is created without a verification; verification is a " +
      "separate call whose evidence_refs is a substring-matched JSON list, not a foreign key. " +
      "NOT DEPLOYED; production UNVERIFIED.",
  },
  nonCollapses: [
    {
      left: "EVIDENCE",
      right: "VERIFICATION",
      enforced: true,
      evidence: [
        "test_evidence_is_persisted_with_a_durable_id_and_creates_no_verification",
        "test_verification_is_created_separately_and_requires_evidence",
      ],
    },
    {
      left: "EVIDENCE CAN EXIST UNVERIFIED",
      right: "VERIFICATION REQUIRES EVIDENCE",
      enforced: true,
      evidence: [
        "test_evidence_can_exist_without_any_verification",
        "test_verification_cannot_reference_evidence_that_does_not_exist",
      ],
    },
    {
      left: "FOREIGN KEY",
      right: "CORRELATION (evidence_refs)",
      enforced: true,
      evidence: ["test_evidence_to_verification_is_a_correlation_not_a_foreign_key"],
    },
  ],
  surfaces: [
    "GET /solspire/enterprise/workspaces/{enterprise_id}/control-room",
  ],
  unresolved: [
    "evidence → verification is a correlation, not a join: ew_verifications.evidence_refs is a JSON text list matched by instr() in the projection, with no FOREIGN KEY and no reverse pointer on ew_evidence.",
    "The relationship is asymmetric: a verification requires an existing evidence reference (write-time check), but evidence may stand alone with no verification — the forward walk returns evidence only.",
    "Both records are append-only: the store contains no UPDATE or DELETE for ew_evidence / ew_verifications.",
    "No HTTP route creates evidence or verification, and no route exposes either as a first-class record; both are readable only through the control-room projection.",
    "The creators (EnterpriseOrchestrationStore.evidence/verify, eden_ops.execute_and_evidence, simulate_eden_supplier_path) are reachable only from tests or unrouted code paths.",
    "Whether evidence should carry a durable forward pointer to its verification is a later architectural decision; the correlation is recorded, not resolved.",
    "Deployment: the branch is not deployed; production posture is UNVERIFIED.",
  ],
  verbs: ["SEE", "DISTINGUISH", "INSPECT", "VERIFY"],
  verbsBlockedByProvisioning: [],
};
