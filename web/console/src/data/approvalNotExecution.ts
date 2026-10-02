/**
 * The first complete boundary instance: APPROVAL ≠ EXECUTION.
 *
 * Chosen because it is machine-enforced AND covered by tests that demonstrate
 * the distinction (architecture §11). If the console can represent this one
 * boundary correctly — authority, posture, evidence, consequences — the first
 * real unit of the reconciled console exists.
 *
 * Everything here is traceable to RECONCILED-BOUNDARY-MAP-01.md and the tests
 * on reconciliation/verified-boundary-01. Nothing is asserted beyond the map.
 */
import type { BoundaryInstance } from "../lib/boundary";

export const APPROVAL_NOT_EXECUTION: BoundaryInstance = {
  id: "approval-not-execution",
  title: "Approval ≠ Execution",
  from: "APPROVAL",
  to: "EXECUTION",
  means:
    "Recording an authorization and performing the permitted action are separate events. " +
    "Approving records a decision; it does not run the tool.",
  priorCollapse:
    "Before BC-2, api/approval_routes.py executed the tool inside the approve handler — " +
    "a single event that both decided and acted.",
  posture: {
    mechanism: "ENFORCED",
    deployment: { implemented: true, tested: true, deployed: false, productionVerified: false },
    note:
      "Enforced in code and covered by tests on the branch. NOT DEPLOYED; the live host " +
      "still runs the pre-hardening collapse.",
  },
  nonCollapses: [
    {
      left: "APPROVAL",
      right: "EXECUTION",
      enforced: true,
      evidence: ["test_approve_decision_does_not_execute", "test_approved_gated_tool_runs_once"],
    },
    {
      left: "IDENTITY",
      right: "AUTHORITY",
      enforced: true,
      evidence: ["test_ordinary_principal_cannot_approve"],
    },
    {
      left: "AUTHORITY",
      right: "AUTHORIZATION",
      enforced: true,
      evidence: [
        "test_distinct_unauthoritative_reviewer_cannot_decide",
        "test_authority_denial_is_forbidden_not_unauthenticated",
      ],
    },
    {
      left: "AUTHORIZATION",
      right: "APPROVAL",
      enforced: true,
      evidence: ["test_authenticated_but_unapproved_gated_tool_is_denied"],
    },
  ],
  surfaces: [
    "POST /api/approvals/request",
    "POST /api/approvals/{id}/approve",
    "POST /api/tools/{tool_name}/run",
  ],
  unresolved: [
    "EXECUTION ≠ EVIDENCE is recorded (consumed_at / consumed_by) but not yet surfaced as its own view.",
    "Deployment: the branch is not deployed; production posture is UNVERIFIED.",
    "Declared vs enforced authority disagree: governance/roles.json grants Govern to Flamekeeper only, but _has_govern_authority also accepts the access_level >= 3 sovereign tier, which existing nodes occupy. Not resolved.",
    "Flamekeeper is UNPROVISIONED, so AUTHORIZE is unreachable for ordinary principals — but not for a sovereign-tier principal.",
  ],
  verbs: ["SEE", "DISTINGUISH", "INSPECT", "VERIFY"],
  verbsBlockedByProvisioning: ["AUTHORIZE"],
};
