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
import type { Posture, EdgeStatus } from "./posture";

export type StageId =
  | "IDENTITY"
  | "AUTHORITY"
  | "AUTHORIZATION"
  | "PROPOSAL"
  | "APPROVAL"
  | "EXECUTION"
  | "JOB"
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

/**
 * A causal edge carrying its own witnessed status. The status is NOT derived
 * from the endpoints: a PRODUCTION-VERIFIED stage may emit a CONTRADICTED edge.
 * Each status is pinned to a runtime witness (F.1–F.4, PR #180).
 */
export interface SpineEdge {
  from: StageId;
  to: StageId;
  status: EdgeStatus;
  /** The witness that fixed this status. */
  witness: string;
}

/** Causal edges (the spine). Rendered as the primary direction. */
export const SPINE_EDGES: SpineEdge[] = [
  { from: "IDENTITY", to: "AUTHORITY", status: "DEMONSTRATED", witness: "F.2 — Guest→403, sovereign-tier passes" },
  { from: "AUTHORITY", to: "AUTHORIZATION", status: "DEMONSTRATED", witness: "F.3 — anon→401 on /api/tools, /api/agent/spawn, /api/plan/run" },
  { from: "AUTHORIZATION", to: "PROPOSAL", status: "DEMONSTRATED", witness: "F.3 — attributed POST /api/approvals/request→200" },
  { from: "PROPOSAL", to: "APPROVAL", status: "DEMONSTRATED", witness: "F.3/F.4 — distinct-authority approve→200" },
  { from: "APPROVAL", to: "EXECUTION", status: "DEMONSTRATED", witness: "F.3/F.4 — run→200, reuse→403, cross-subject→403" },
  { from: "EXECUTION", to: "JOB", status: "CONTRADICTED", witness: "F.3 — a gated run creates no job" },
  { from: "JOB", to: "WORK_EVENT", status: "CONTRADICTED", witness: "Gate 02 — no table joins kernel jobs to the WorkEvent spine" },
  { from: "WORK_EVENT", to: "EVIDENCE", status: "CONTRADICTED", witness: "Gate 03 — disjoint modules, no join" },
  { from: "EVIDENCE", to: "VERIFICATION", status: "CONTRADICTED", witness: "Gate 04 — correlation (evidence_refs), not a foreign key" },
  { from: "VERIFICATION", to: "REVIEW", status: "UNRESOLVED", witness: "no runtime witness of a verification→review act" },
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

// The runtime-witnessed posture for the governance stages: the enforcement is
// live on the merged host and was probed directly (F.1–F.4). The provenance
// stages below deliberately do NOT take this posture — their edges are
// CONTRADICTED, and a stage is not made production-verified by its neighbour.
const PRODUCTION_VERIFIED: Posture = {
  mechanism: "ENFORCED",
  deployment: { implemented: true, tested: true, deployed: true, productionVerified: true },
  note: "DEPLOYED on the merged host (ae847dd); PRODUCTION-VERIFIED by F.1–F.4.",
};

export const STAGES: Stage[] = [
  {
    id: "IDENTITY",
    label: "Identity",
    question: "Who is calling?",
    surface: "GET /api/me, /api/me/identity-spine (bearer token)",
    enforcement: "api/auth.require_auth; production fail-closed guard",
    evidence: ["F.1 — anon→401, valid Firebase JWT→200, /api/me uid mapping"],
    posture: PRODUCTION_VERIFIED,
  },
  {
    id: "AUTHORITY",
    label: "Authority",
    question: "What may this principal decide?",
    surface: "governance/roles.json (Flamekeeper → Govern); access_level >= 3",
    enforcement: "api/approval_routes._has_govern_authority",
    evidence: ["F.2 — Guest→403 on the sovereign route; sovereign-tier passes"],
    posture: PRODUCTION_VERIFIED,
  },
  {
    id: "AUTHORIZATION",
    label: "Authorization",
    question: "Which operations may this principal reach?",
    surface: "route Depends(require_auth); tool registry lookup",
    enforcement: "api/main.run_tool_endpoint; api/loop_routes router deps",
    evidence: ["F.3 — anon→401 on /api/tools, /api/agent/spawn, /api/plan/run"],
    posture: PRODUCTION_VERIFIED,
  },
  {
    id: "PROPOSAL",
    label: "Proposal",
    question: "What intent is being proposed, and by whom?",
    surface: "POST /api/approvals/request",
    enforcement: "subject attribution (subject_ref)",
    evidence: ["F.3 — attributed request→200; subject_ref recorded"],
    posture: PRODUCTION_VERIFIED,
  },
  {
    id: "APPROVAL",
    label: "Approval",
    question: "Has a distinct authority recorded a decision?",
    surface: "POST /api/approvals/{id}/approve | reject",
    enforcement: "Govern authority; self-approval prohibited",
    evidence: ["F.3/F.4 — distinct-authority approve→200; self-approval→403"],
    posture: PRODUCTION_VERIFIED,
  },
  {
    id: "EXECUTION",
    label: "Execution",
    question: "Did the act run — under a recorded decision?",
    surface: "POST /api/tools/{tool_name}/run",
    enforcement: "requires_approval gate; single-use; same-subject",
    evidence: ["F.3/F.4 — run→200, reuse→403, cross-subject→403, consumed_at/by recorded"],
    posture: PRODUCTION_VERIFIED,
  },
  {
    id: "JOB",
    label: "Job",
    question: "What does the kernel loop record as having run?",
    surface: "POST /api/job/create, GET /api/jobs, /api/job/{id}/trace",
    enforcement: "api/loop_routes router auth (BC-3)",
    evidence: ["test_kernel_loop_read_surfaces_require_auth"],
    posture: LOCAL_ONLY,
  },
  {
    id: "WORK_EVENT",
    label: "Work Event",
    question: "What continuity record does the SolSpire spine hold?",
    surface: "POST /solspire/workevents, GET /solspire/workevents",
    enforcement: "api/auth.require_auth; canonical-workspace precondition",
    evidence: ["test_execution_workevent_boundary.py"],
    posture: {
      mechanism: "ENFORCED",
      deployment: { implemented: true, tested: true, deployed: true, productionVerified: true },
      note: "The spine is live and reachable (F.3 probed it under a satisfied workspace precondition). It is a distinct record from a kernel Job — no join exists. Reachability is production-verified; the EXECUTION→WORK_EVENT transition is CONTRADICTED.",
    },
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
    enforcement: "subject-scoped listing (Govern principal sees all)",
    evidence: ["F.4 — Govern principal sees approvals it did not originate (non-empty queue)"],
    posture: PRODUCTION_VERIFIED,
  },
];

export function stageById(id: StageId): Stage {
  const s = STAGES.find((x) => x.id === id);
  if (!s) throw new Error(`unknown stage ${id}`);
  return s;
}
