/**
 * The boundary grammar: the causal spine of the reconciled console.
 *
 * Derived, not asserted. Every stage is grounded in a surface the Verified
 * Boundary Map proves exists, an enforcement point, and a test. No stage is
 * aspirational.
 *
 * The shape is a CYCLE with a causal spine (architecture §9 Q1): REVIEW can
 * change the state of AUTHORIZATION, EVIDENCE can expose an EXECUTION problem,
 * and VERIFICATION can leave a boundary unresolved. The console renders the
 * causal direction but never implies a one-way conveyor belt.
 *
 * Source: RECONCILED-CONSOLE-ARCHITECTURE-01.md §2, §9.
 */
import type { Posture } from "./posture";

export type StageId =
  | "IDENTITY"
  | "AUTHORITY"
  | "AUTHORIZATION"
  | "PROPOSAL"
  | "APPROVAL"
  | "EXECUTION"
  | "WORK_EVENT"
  | "EVIDENCE"
  | "VERIFICATION"
  | "REVIEW";

export interface Stage {
  id: StageId;
  label: string;
  /** The question this stage answers, in the operator's voice. */
  question: string;
  /** Proven backend surface(s). */
  surface: string;
  /** Where the boundary is enforced in code. */
  enforcement: string;
  /** Evidence: test name(s) that exercise it. */
  evidence: string[];
  posture: Posture;
}

/** Causal edges (the spine). Rendered as the primary direction. */
export const SPINE_EDGES: [StageId, StageId][] = [
  ["IDENTITY", "AUTHORITY"],
  ["AUTHORITY", "AUTHORIZATION"],
  ["AUTHORIZATION", "PROPOSAL"],
  ["PROPOSAL", "APPROVAL"],
  ["APPROVAL", "EXECUTION"],
  ["EXECUTION", "WORK_EVENT"],
  ["WORK_EVENT", "EVIDENCE"],
  ["EVIDENCE", "VERIFICATION"],
  ["VERIFICATION", "REVIEW"],
];

/**
 * Feedback edges (the cycle). These are NOT causal continuations; they are the
 * paths by which a later stage changes an earlier one. The console renders them
 * distinctly so the operator never reads them as "the next step".
 */
export interface FeedbackEdge {
  from: StageId;
  to: StageId;
  why: string;
}

export const FEEDBACK_EDGES: FeedbackEdge[] = [
  { from: "REVIEW", to: "AUTHORIZATION", why: "a review may change what is authorized" },
  { from: "REVIEW", to: "PROPOSAL", why: "a review may re-enter the queue as a new proposal" },
  { from: "EVIDENCE", to: "EXECUTION", why: "evidence may expose an execution problem" },
  { from: "VERIFICATION", to: "REVIEW", why: "verification may leave a boundary unresolved" },
];

// The map's posture for BC-1/2/3: implemented + tested locally, not deployed,
// not production-verified. This is the honest baseline and is reused below.
const LOCAL_ONLY: Posture = {
  mechanism: "ENFORCED",
  deployment: { implemented: true, tested: true, deployed: false, productionVerified: false },
  note: "IMPLEMENTED / TESTED locally; NOT DEPLOYED; PRODUCTION UNVERIFIED.",
};

export const STAGES: Stage[] = [
  {
    id: "IDENTITY",
    label: "Identity",
    question: "Who is calling?",
    surface: "GET /api/me, /api/me/identity-spine (bearer token)",
    enforcement: "api/auth.require_auth; production fail-closed guard",
    evidence: ["test_tool_execution_perimeter.py::test_anonymous_cannot_list_tools"],
    posture: LOCAL_ONLY,
  },
  {
    id: "AUTHORITY",
    label: "Authority",
    question: "What may this principal decide?",
    surface: "governance/roles.json (Flamekeeper → Govern); access_level >= 3",
    enforcement: "api/approval_routes._has_govern_authority",
    evidence: [
      "test_ordinary_principal_cannot_approve",
      "test_distinct_unauthoritative_reviewer_cannot_decide",
      "test_authority_is_computed_from_the_principal",
    ],
    posture: LOCAL_ONLY,
  },
  {
    id: "AUTHORIZATION",
    label: "Authorization",
    question: "Which operations may this principal reach?",
    surface: "route Depends(require_auth); tool registry lookup",
    enforcement: "api/main.run_tool_endpoint; api/loop_routes router deps",
    evidence: ["test_kernel_loop_write_surfaces_require_auth"],
    posture: LOCAL_ONLY,
  },
  {
    id: "PROPOSAL",
    label: "Proposal",
    question: "What intent is being proposed, and by whom?",
    surface: "POST /api/approvals/request",
    enforcement: "subject attribution (subject_ref)",
    evidence: ["test_approval_listing_is_subject_scoped"],
    posture: LOCAL_ONLY,
  },
  {
    id: "APPROVAL",
    label: "Approval",
    question: "Has a distinct authority recorded a decision?",
    surface: "POST /api/approvals/{id}/approve | reject",
    enforcement: "Govern authority; self-approval prohibited",
    evidence: ["test_self_approval_is_prohibited", "test_sovereign_access_level_may_approve"],
    posture: LOCAL_ONLY,
  },
  {
    id: "EXECUTION",
    label: "Execution",
    question: "Did the act run — under a recorded decision?",
    surface: "POST /api/tools/{tool_name}/run",
    enforcement: "requires_approval gate; single-use; same-subject",
    evidence: ["test_approved_gated_tool_runs_once", "test_approval_is_not_spendable_by_another_subject"],
    posture: LOCAL_ONLY,
  },
  {
    id: "WORK_EVENT",
    label: "Work Event",
    question: "What does the kernel loop record as having run?",
    surface: "POST /api/job/create, GET /api/jobs, /api/job/{id}/trace",
    enforcement: "api/loop_routes router auth (BC-3)",
    evidence: ["test_kernel_loop_read_surfaces_require_auth"],
    posture: LOCAL_ONLY,
  },
  {
    id: "EVIDENCE",
    label: "Evidence",
    question: "What remains as proof it ran?",
    surface: "job trace; tool result envelope; approval consumed_at / consumed_by",
    enforcement: "recorded at the boundary (not yet separately surfaced)",
    evidence: ["test_approved_gated_tool_runs_once"],
    posture: {
      mechanism: "ENFORCED_UNTESTED",
      deployment: { implemented: true, tested: true, deployed: false, productionVerified: false },
      note: "Recorded, but not yet surfaced as its own view. Enforcement is untested as a distinct boundary.",
    },
  },
  {
    id: "VERIFICATION",
    label: "Verification",
    question: "Did the act stay in bounds?",
    surface: "validate_plan; shell allowlist; read containment",
    enforcement: "BC-3; kernel/tools_real",
    evidence: ["test_shell_allowlist_still_holds_after_approval", "test_read_containment_still_holds"],
    posture: LOCAL_ONLY,
  },
  {
    id: "REVIEW",
    label: "Review",
    question: "What may a reviewer see and decide?",
    surface: "GET /api/approvals",
    enforcement: "subject-scoped listing (Flamekeeper sees all)",
    evidence: ["test_flamekeeper_reviewer_sees_all_pending_approvals"],
    posture: LOCAL_ONLY,
  },
];

export function stageById(id: StageId): Stage {
  const s = STAGES.find((x) => x.id === id);
  if (!s) throw new Error(`unknown stage ${id}`);
  return s;
}
