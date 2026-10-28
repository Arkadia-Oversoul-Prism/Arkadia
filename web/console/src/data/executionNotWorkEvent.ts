/**
 * Worked boundary instance: EXECUTION ≠ WORK EVENT (Boundary Expansion Gate 02).
 *
 * Re-measured. The substrate keeps two DISTINCT records — an execution
 * (synchronous tool envelope + approval consumption; kernel job execution
 * events) and the SolSpire WorkEvent spine (its own table and its own manager) —
 * and they are no longer merely adjacent: PR #294 added an explicit causal
 * bridge, `weaver/execution_workevent_bridge.py::capture_execution_workevent`,
 * which records exactly one WorkEvent per terminal Weaver execution attempt,
 * carrying `execution_attempt_ref` (with a unique index and a
 * `get_by_execution_attempt` read-back). The distinction survives; the ABSENCE
 * of a join does not.
 *
 * The superseded reading was: "there is no durable execution → WorkEvent
 * identifier and no code path that would create one." That was measured before
 * the bridge existed, and it is retained here only as provenance — a console
 * derived from a map inherits the map's horizon.
 *
 * Everything here is traceable to tests/test_execution_workevent_boundary.py
 * and tests/test_prism_execution_workevent_governance.py.
 */
import type { BoundaryInstance } from "../lib/boundary";

export const EXECUTION_NOT_WORK_EVENT: BoundaryInstance = {
  id: "execution-not-workevent",
  title: "Execution ≠ Work Event",
  from: "EXECUTION",
  to: "WORK_EVENT",
  means:
    "Performing an act and recording a Work Event are separate on this substrate, and they are " +
    "joined explicitly rather than collapsed. Execution leaves evidence (a synchronous envelope, " +
    "consumed_at / consumed_by, kernel job events); a WorkEvent is a distinct continuity record " +
    "in its own spine, created for a terminal execution attempt by an explicit causal bridge " +
    "that carries execution_attempt_ref.",
  priorCollapse:
    "There is no prior collapse to repair: the two records were never the same. The boundary was " +
    "an ABSENCE of a durable execution → WorkEvent identifier — since repaired by PR #294, which " +
    "added weaver/execution_workevent_bridge.py (one WorkEvent per terminal attempt, unique " +
    "execution_attempt_ref). The remaining property is that the bridge is OBSERVATIONAL: it " +
    "records the transition and grants no authority, review, completion, or acceptance.",
  posture: {
    mechanism: "ENFORCED",
    deployment: { implemented: true, tested: true, deployed: true, productionVerified: false },
    note:
      "The surfaces this boundary names are served by the live runtime (POST " +
      "/api/tools/{tool_name}/run, POST /api/job/create, GET /api/jobs, " +
      "POST|GET /solspire/workevents). The bridge is observational and is asserted not " +
      "to mark completion. Production verification by an authorized principal is NOT " +
      "CLAIMED (no operator credential).",
  },
  nonCollapses: [
    {
      left: "EXECUTION",
      right: "WORK_EVENT",
      enforced: true,
      evidence: [
        "test_execution_attempt_creates_one_causally_joined_workevent",
        "test_workevent_capture_does_not_mark_completion",
      ],
    },
    {
      left: "JOB",
      right: "WORK_EVENT",
      enforced: true,
      evidence: [
        "test_kernel_job_records_execution_events_without_a_workevent",
        "test_workevent_model_has_explicit_execution_causal_reference",
      ],
    },
    {
      left: "EXECUTION PATH",
      right: "WORK EVENT SPINE",
      enforced: true,
      evidence: ["test_execution_path_never_imports_the_workevent_spine"],
    },
  ],
  surfaces: [
    "POST /api/tools/{tool_name}/run",
    "POST /api/job/create",
    "GET /api/jobs",
    "POST /solspire/workevents",
  ],
  unresolved: [
    "The execution → WorkEvent bridge is explicit but OBSERVATIONAL: it is invoked from weaver/enterprise_orchestration.py::complete_execution_attempt and grants no authority, review, completion, or acceptance.",
    "The bridge carries execution_attempt_ref, but a kernel job's own execution record (execution.events) is still a third, separate log that is neither the tool envelope nor a WorkEvent.",
    "weaver/enterprise_orchestration.py implements a proposal → authority → authorization → execution → evidence → verification graph with forward_walk / reverse_walk, but exposes no HTTP route — implemented, unexposed. Verified: no forward_walk/reverse_walk route is served, and there is no /solspire/enterprise route; the graph is readable only as the control-room projection.",
    "Deployment: the surfaces this boundary names are served by the live runtime. Production verification by an authorized principal is NOT CLAIMED (no operator credential).",
  ],
  verbs: ["SEE", "DISTINGUISH", "INSPECT", "VERIFY"],
  verbsBlockedByProvisioning: [],
};
