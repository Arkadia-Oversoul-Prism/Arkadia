/**
 * Worked boundary instance: EXECUTION ≠ WORK EVENT (Boundary Expansion Gate 02).
 *
 * Established by measurement, not assumption. The substrate keeps two records
 * that are NOT joined: an execution (synchronous tool envelope + approval
 * consumption; kernel job execution events) and the SolSpire WorkEvent spine
 * (its own table, created only by its own router). There is no durable
 * execution → WorkEvent identifier and no code path that would create one.
 *
 * Everything here is traceable to tests/test_execution_workevent_boundary.py
 * and RECONCILED-BOUNDARY-MAP-01.md §6 item 7. Nothing is asserted beyond the
 * measurement. The absence is the result.
 */
import type { BoundaryInstance } from "../lib/boundary";

export const EXECUTION_NOT_WORK_EVENT: BoundaryInstance = {
  id: "execution-not-workevent",
  title: "Execution ≠ Work Event",
  from: "EXECUTION",
  to: "WORK_EVENT",
  means:
    "Performing an act and recording a Work Event are separate on this substrate, and they are " +
    "not joined. Execution leaves evidence (a synchronous envelope, consumed_at / consumed_by, " +
    "kernel job events); a WorkEvent is a distinct continuity record in its own spine.",
  priorCollapse:
    "There is no prior collapse to repair: the two records were never joined. The boundary is an " +
    "ABSENCE of a durable execution → WorkEvent identifier, measured rather than assumed.",
  posture: {
    mechanism: "ENFORCED",
    deployment: { implemented: true, tested: true, deployed: false, productionVerified: false },
    note:
      "Measured on the branch. A gated run succeeds and consumes its approval while creating no " +
      "job and no WorkEvent; the WorkEvent spine stays empty. NOT DEPLOYED; production UNVERIFIED.",
  },
  nonCollapses: [
    {
      left: "EXECUTION",
      right: "WORK_EVENT",
      enforced: true,
      evidence: [
        "test_gated_execution_creates_no_job_and_no_workevent",
        "test_execution_is_recorded_on_the_approval_not_as_a_workevent",
      ],
    },
    {
      left: "JOB",
      right: "WORK_EVENT",
      enforced: true,
      evidence: [
        "test_kernel_job_records_execution_events_without_a_workevent",
        "test_workevent_model_has_no_execution_or_job_reference_field",
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
    "There is no durable execution → WorkEvent identifier: a job stores no work_ref/work_event_id, and the WorkEvent model has no job_id/task_id/execution_ref.",
    "The only creator of a WorkEvent is its own router (/solspire/workevents); no execution or job module constructs one.",
    "A kernel job's own execution record is a third, separate log (execution.events) that is neither the tool envelope nor a WorkEvent.",
    "weaver/enterprise_orchestration.py implements a proposal → authority → authorization → execution → evidence → verification graph with forward_walk / reverse_walk, but exposes no HTTP route — implemented, unexposed.",
    "Whether to persist an explicit execution ↔ WorkEvent join is a later architectural decision; the absence is recorded, not resolved.",
    "Deployment: the branch is not deployed; production posture is UNVERIFIED.",
  ],
  verbs: ["SEE", "DISTINGUISH", "INSPECT", "VERIFY"],
  verbsBlockedByProvisioning: [],
};
