/**
 * Forward and reverse lineage, implemented only where the substrate actually
 * supports it.
 *
 * What the substrate records (verified against api/approval_routes.py,
 * api/main.py, kernel/jobs.py):
 *
 *   • An approval carries `subject_ref` (who proposed) and, after execution,
 *     `consumed_at` / `consumed_by` — the consumption marker.
 *   • A job carries `intent` (an arbitrary object) and `source`; when a tool run
 *     is enqueued, the intent carries `tool_name` and `subject_ref`.
 *   • Neither side persists the other's id. There is no approval_id on the job,
 *     and no job_id on the approval.
 *
 * Therefore lineage is INFERRED, not joined, and is labelled as such. The
 * inference is deliberately tight: same tool, same subject, and the job created
 * within a short window of the consumption. Ambiguity is surfaced as candidates,
 * never collapsed into a single confident answer. Where the substrate records
 * nothing (no `consumed_at`), there is no forward link and the console says so.
 */
import type { Approval, Job } from "../api/types";

/** Seconds after consumption within which an execution job is attributable. */
export const LINK_WINDOW_SECONDS = 120;

export interface InferredExecution {
  job: Job;
  /** Always true — the substrate does not record an explicit join. */
  inferred: true;
  basis: string;
}

/** The exact, recorded consumption facts on an approval (no inference). */
export interface RecordedConsumption {
  consumed: boolean;
  consumed_at: string | null;
  consumed_by: string | null;
}

export interface Lineage {
  /** Recorded, exact: whether and by whom the approval was consumed. */
  consumption: RecordedConsumption;
  /** Inferred: the execution job(s) attributable to this approval. */
  executions: InferredExecution[];
  /** Truthful note about what could and could not be resolved. */
  note: string;
}

function epochSeconds(iso: string | null): number | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms / 1000;
}

function intentField(job: Job, key: string): unknown {
  return job.intent && typeof job.intent === "object" ? job.intent[key] : undefined;
}

/** The job's own recorded forward key (substrate sets task_id from intent). */
export function jobRecordedKey(job: Job): string | null {
  const t = job.execution?.task_id ?? intentField(job, "proposal_id") ?? intentField(job, "task_id");
  return t ? String(t) : null;
}

/** True iff *job* is attributable to *approval* by the tight inference. */
function attributable(approval: Approval, job: Job): { ok: boolean; basis: string } {
  const jobTool = intentField(job, "tool_name");
  const jobSubject = intentField(job, "subject_ref");
  const consumedAt = epochSeconds(approval.consumed_at);
  const created = typeof job.created_at === "number" ? job.created_at : null;

  if (approval.consumed_at == null) return { ok: false, basis: "approval not consumed" };
  if (jobTool !== approval.tool_name) return { ok: false, basis: "tool mismatch" };
  if (jobSubject !== approval.subject_ref) return { ok: false, basis: "subject mismatch" };
  if (consumedAt == null || created == null) return { ok: false, basis: "missing timestamp" };
  const delta = created - consumedAt;
  if (delta < -2 || delta > LINK_WINDOW_SECONDS) {
    return { ok: false, basis: `outside ${LINK_WINDOW_SECONDS}s window` };
  }
  return {
    ok: true,
    basis: `same tool+subject; job created ${delta.toFixed(1)}s after consumption`,
  };
}

/** Forward lineage: approval → recorded consumption → inferred execution record(s). */
export function executionFor(approval: Approval, jobs: Job[]): Lineage {
  const consumption: RecordedConsumption = {
    consumed: approval.consumed_at != null,
    consumed_at: approval.consumed_at,
    consumed_by: approval.consumed_by,
  };
  if (!consumption.consumed) {
    return {
      consumption,
      executions: [],
      note: "Not consumed. The decision is recorded; no act has been performed under it.",
    };
  }
  const executions = jobs
    .map((job) => ({ job, verdict: attributable(approval, job) }))
    .filter((x) => x.verdict.ok)
    .map<InferredExecution>((x) => ({ job: x.job, inferred: true, basis: x.verdict.basis }));

  if (executions.length === 0) {
    return {
      consumption,
      executions: [],
      note:
        "Consumed — the act is recorded on the approval (consumed_at/consumed_by). But no " +
        "execution job is attributable: a tool run consumes the approval without enqueuing a " +
        "job, and the substrate persists no approval_id on a job. Absence is shown, not guessed.",
    };
  }
  return {
    consumption,
    executions,
    note:
      executions.length === 1
        ? "One execution record attributable by the tight inference (same tool+subject, within window)."
        : `${executions.length} candidate execution records — the inference is ambiguous and shown as such.`,
  };
}

/** Reverse lineage: job → approval(s) whose consumption this job could realise. */
export function approvalsForJob(job: Job, approvals: Approval[]): Approval[] {
  return approvals.filter((a) => attributable(a, job).ok);
}

/** True when the substrate records the tool as approval-gated. */
export function isGated(toolName: string, requiresApproval: Record<string, boolean>): boolean {
  return requiresApproval[toolName] === true;
}
